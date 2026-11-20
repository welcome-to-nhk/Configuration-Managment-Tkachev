# Cargo dependency visualizer — вариант 24

Практическая работа по «Конфигурационному управлению».
Условие: **ИКБО-24-25-1.pdf, с. 77–79**. Язык: Python 3.10+.
Программа анализирует метаданные Rust/Cargo, но сама написана на Python.
Сторонних Python-зависимостей нет. Ничего устанавливать через pip не нужно.

## Сначала прочитать

- **docs/DEFENSE.md** — простое объяснение и сценарий защиты.
- **docs/API.md** — перечень функций с описаниями.
- **docs/COMPARISON.md** — как выполнить честную сверку с Cargo.
- **docs/VERIFICATION.md** — что проверено, а что здесь не запускалось.

Реализованы программные режимы всех пяти этапов. Формальные действия,
которые остаются на компьютере студента: фактическая сверка с установленным
Cargo, при необходимости официальный рендер PlantUML и публикация Git.
Публичный репозиторий автоматически не создавался.

## Быстрый старт

Распакуйте архив, откройте терминал в **cargo-deps-v24**.
На Windows установите Python 3.10+; на Linux/macOS используйте `python3`.
В командах ниже `python` означает доступную команду Python 3.10+.
На Windows можно заменить ее на `py -3`.

```sh
python --version
python -m unittest discover -s tests -v
python tools/demo.py
```

Последняя команда автономна: проходит пять этапов на буквенном графе,
показывает цикл, фильтр и три настоящих имени Cargo-пакетов по учебному
срезу метаданных. Временный HTTP-сервер слушает только 127.0.0.1,
интернет не требуется. После команды сервер останавливается.
Готовые `.svg`, `.puml` и журнал запусков появятся в **out/**.
SVG открывается обычным браузером. В архиве примеры уже есть.

Сборка не нужна. Запуск приложения: `python -m src` или `run.bat` / `./run.sh`.
Всегда запускайте команды из корня проекта, не из папки `src`.

## Пять этапов: команды и реализация

### 1. Минимальный CLI и настройки

```sh
python -m src --package A --repository examples/diamond.json --test --stage 1
```

Настройки печатаются как `ключ=значение`.
`src/config.py`: argparse, проверка имени, URL/пути, флага, выхода и фильтра.
Ошибки параметров: неверное имя, отсутствующий файл, неверный URL или порт,
не-SVG выход, управляющий символ в фильтре, фильтр исключает корень.
Неверное значение флага или служебной опции отвергает argparse.
Проверки: `tests/test_config.py`.

### 2. Прямые зависимости Cargo

При наличии интернета:

```sh
python -m src --package crc32fast --repository https://index.crates.io --stage 2
```

`src/repositories.py`: вычисляет sparse-путь, получает JSONL через urllib,
самостоятельно разбирает записи JSON. `src/versions.py` выбирает новейшую
подходящую стабильную неотозванную версию. Cargo не вызывается.
Этап 2 печатает прямые **обязательные normal/build** зависимости,
без фильтра: фильтрация начинается на этапе 3.
Автономная проверка того же HTTP-кода: `python tools/demo.py`.

### 3. Граф, рекурсивный DFS, фильтр и циклы

```sh
python -m src --package A --repository examples/diamond.json --test --stage 3
python -m src --package A --repository examples/filter.json --test --filter X --stage 3
python -m src --package A --repository examples/cycle.json --test --stage 3
```

`src/graph.py`: рекурсивная функция `visit`, серые и черные вершины.
DFS ромба: A, B, D, C. Общий D раскрывается один раз, оба ребра сохраняются.
При цикле граф все равно строится; бесконечной рекурсии нет.
Фильтр удаляет вершину до сетевого запроса и не обходит ее ветку.

Формат тестового файла (JSON):

```json
{"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
```

Все имена — одна или несколько заглавных латинских букв.
Каждая упомянутая вершина обязана присутствовать в файле.

### 4. Порядок загрузки

```sh
python -m src --package A --repository examples/diamond.json --test --stage 4
python -m src --package A --repository examples/cycle.json --test --stage 4
```

`src/order.py`: DFS postorder, вершина добавляется после зависимостей.
Для ромба: **D -> B -> C -> A**. Корень включен последним.
При цикле возвращается ошибка, код завершения 1.
Это допустимый зависимостный порядок, а не прогноз хронологии HTTP Cargo.
Сверка с менеджером: **docs/COMPARISON.md**.

### 5. PlantUML и SVG

```sh
python -m src --package A --repository examples/diamond.json --test --output out/diamond.svg
```

По умолчанию `--stage 5`. Сохраняются **out/diamond.puml** и **out/diamond.svg**.
`src/plantuml.py` формирует PlantUML. `src/svg.py` читает генерируемое
подмножество PlantUML и автономно сохраняет SVG. Это собственный небольшой
рендерер, **не полная реализация PlantUML**. Он не требует Java или сети.

Для отрисовки именно официальным PlantUML:

```sh
python -m src --package A --repository examples/diamond.json --test --renderer plantuml --output out/official.svg
```

Нужна установленная команда `plantuml` либо Java и переменная
`PLANTUML_JAR` с путем к скачанному пользователем `plantuml.jar`.
Если сборка PlantUML требует Graphviz, команда `dot` должна быть в PATH.
В PowerShell: `$env:PLANTUML_JAR = 'C:\tools\plantuml.jar'`.
В Bash: `export PLANTUML_JAR=/path/to/plantuml.jar`.
Затем повторите команду выше. Внешнему серверу диаграмма не отправляется.
Официальный рендерер в среде подготовки не запускался.

Три примера реальных пакетов воспроизводятся через `python tools/demo.py`:
**crc32fast 1.5.0**, **miniz_oxide 0.8.9**, **itoa 1.0.15**.
Это выбранные версии учебного среза, не обещание последних версий crates.io.
У первых двух есть обязательная зависимость; itoa демонстрирует лист.
Источники и ограничения среза: `examples/sparse/README.md`.

## Все настройки

| Опция | Значение и проверка |
|---|---|
| `--package` | Обязательное имя crate; в `--test` только A–Z |
| `--repository` | Обязательный HTTP(S) URL sparse-индекса или путь к JSON |
| `--test` | Флаг без значения; переключает на буквенный JSON-граф |
| `--output` | SVG-путь, по умолчанию `out/graph.svg` |
| `--filter` | Исключаемая подстрока, по умолчанию пустая; регистр важен |
| `--stage` | Служебный режим 1–5, по умолчанию 5 |
| `--renderer` | Служебный режим builtin/plantuml, по умолчанию builtin |

Нет дополнительных требуемых параметров версии/глубины: в варианте 24
они не указаны. Сетевой тайм-аут 20 секунд, предел ответа 32 MiB.
Коды: 0 — успех, 1 — ошибка приложения/ввода-вывода, 2 — ошибка argparse.

## Границы модели Cargo — важно для защиты

Это анализатор **обязательных normal/build зависимостей**:

- dev и optional пропускаются, даже если optional активируется default features;
- features и features2 не разрешаются и не объединяются;
- target-зависимости объединяются для всех платформ, cfg не вычисляется;
- на каждом ребре независимо выбирается новейшая подходящая версия;
- нет общего constraint solver, backtracking, Cargo.lock и учета MSRV;
- нестандартный registry у зависимости вызывает явную ошибку;
- поддержаны стабильные ^, ~, =, сравнения, wildcard и AND через запятую;
- prerelease-релизы пропускаются, prerelease-ограничения отвергаются;
- только sparse HTTP-индексы; Git-индекс и исходники crate не загружаются.

Поэтому для сложных пакетов возможны отличия от `cargo tree`.
Не утверждайте на защите, что это полный resolver Cargo.

## Проверка ошибок вручную

```sh
python -m src --package bad/name --repository https://index.crates.io --stage 1
python -m src --package A --test --repository no-such-file.json --stage 1
python -m src --package crc32fast --repository ftp://example.com --stage 1
python -m src --package A --test --repository examples/diamond.json --output x.png --stage 1
python -m src --package A --test --repository examples/diamond.json --filter A --stage 1
python -m src --package A --test true --repository examples/diamond.json --stage 1
```

Тесты также проверяют управляющие символы фильтра, HTTP 404,
поврежденные метаданные, ошибку DNS, циклы и отсутствующий PlantUML.

## Структура

```text
src/          CLI, репозитории, SemVer, DFS, порядок, PlantUML, SVG
tests/        unit- и интеграционные проверки (unittest)
examples/     буквенные графы и сокращенный sparse-срез
tools/        автономная демонстрация, сверка с Cargo, аудит
 docs/        пояснения, API и памятка для защиты
out/          результаты запусков; игнорируются Git
run.sh        запуск Linux/macOS
run.bat       запуск Windows
.gitignore    запрет служебных файлов и артефактов
```

## Тесты, аудит и Git

```sh
python -m unittest discover -s tests -v
python tools/audit.py
git log --oneline --decorate
git tag
```

История содержит пять реальных коммитов развития и метки `stage-1`...`stage-5`.
Они созданы автоматически при подготовке, автор — Project Builder,
это не утверждение о личной истории работы студента.
Посмотреть отдельный этап, не меняя текущий: `git show stage-3:src/graph.py`.
Для старого состояния: `git switch --detach stage-3`, возврат: `git switch main`.
В ранних коммитах еще нет возможностей поздних этапов.

Перед дальнейшими своими изменениями настройте имя и email Git.
Создайте **пустой публичный** репозиторий у выбранного Git-сервиса,
добавьте его адрес и отправьте историю:

```sh
git remote add origin АДРЕС_ВАШЕГО_РЕПОЗИТОРИЯ
git push -u origin main
git push origin --tags
```

Замените адрес своим. ZIP не добавляйте в Git. Не коммитьте `out/`,
`__pycache__/`, JAR и бинарные файлы. Настройки редактора также исключены.
