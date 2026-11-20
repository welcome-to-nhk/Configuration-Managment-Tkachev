# Справочник функций

Описание соответствует текущим docstring исходников.

## src/__init__.py

## src/__main__.py
- `run(options)` — Выполнить выбранный этап; этапы 1/2/4 не создают изображение.
- `main(argv=None)` — Показать понятную ошибку и вернуть ненулевой код при неудаче.

## src/config.py
- `parser()` — Создать CLI; параметры предметной области не читаются из конфига.
- `validate_source(options)` — Проверить существование файла либо синтаксис URL репозитория.
- `validate_output(value)` — Проверить SVG-путь и ближайший существующий родитель.
- `read_options(argv=None)` — Прочитать и проверить настройки; argparse проверяет типы и флаги.
- `print_options(options)` — Вывести все пять предметных настроек в формате ключ=значение.

## src/errors.py

## src/graph.py
- `build_graph(repository, root, exclude='')` — Обойти зависимости в глубину с рекурсией, не теряя ребра цикла.
- `print_graph(graph)` — Показать список смежности и обнаруженные циклы.
- `visit(node)` — GRAY — в текущем пути, BLACK — уже полностью обработан.

## src/order.py
- `loading_order(graph)` — Получить DFS postorder; при цикле корректного порядка нет.
- `visit(node)` — Добавить вершину только после всех ее зависимостей.

## src/plantuml.py
- `to_plantuml(graph)` — Стабильные alias n0... не зависят от символов в именах пакетов.
- `official_svg(source)` — Выполнить локальный PlantUML, без отправки графа на сервер.
- `save_diagram(graph, output, renderer='builtin')` — Сохранить исходный .puml и изображение .svg рядом.

## src/repositories.py
- `index_path(name)` — Вычислить путь Cargo: 1/a, 2/ab, 3/a/abc или ab/cd/abcd.
- `read_url(url)` — Прочитать UTF-8 по HTTP с тайм-аутом и ограничением объема.
- `parse_records(text, name)` — Самостоятельно разобрать JSONL-файл метаданных crate.
- `open_repository(options)` — Выбрать источник; чтение графа не вызывает Cargo или pip.
- `__init__(self, path)` — Проверить JSON, имена, списки и замкнутость ссылок.
- `root(self, name)` — Найти начальную вершину.
- `dependencies(self, node, exclude='')` — Вернуть уникальные прямые зависимости в стабильном порядке.
- `__init__(self, url)` — Сохранить базовый URL и пустые кэши.
- `resolve(self, name, constraint='*')` — Разрешить одно ребро; версия входит в идентификатор вершины.
- `root(self, name)` — Для корня без версии выбрать новейший стабильный релиз.
- `dependencies(self, node, exclude='')` — Обязательные normal/build, объединенные для всех target.

## src/svg.py
- `element(parent, tag, attributes=None, text=None)` — Добавить SVG-элемент; XML-библиотека экранирует текст.
- `parse_subset(source)` — Прочитать component "label" as n0 и n0 --> n1.
- `positions(labels, edges, width)` — Разместить компоненты по кратчайшим расстояниям от корня.
- `arrow_path(start, end, width, index)` — Кривые вперед и по внешней стороне для обратных ребер.
- `draw_edges(svg, edges, points, width)` — Стрелка означает «пакет зависит от», а не порядок загрузки.
- `draw_nodes(svg, labels, points, width)` — Читаемые подписи и выделение корня цветом, не только порядком.
- `render_subset(source)` — Рендерить генерируемое нами подмножество, не весь язык PlantUML.

## src/versions.py
- `version_key(text)` — Разобрать стабильную x.y.z; build-метаданные не меняют порядок.
- `upper_bound(parts, caret=False)` — Верхняя исключающая граница для ^, ~ и wildcard.
- `comparator(text)` — Построить предикат одного стабильного ограничения Cargo.
- `requirement(text)` — Скомпилировать AND-список через запятую (без prerelease).
- `select_record(records, constraint='*')` — Выбрать новейшую неотозванную стабильную подходящую версию.

## tools/audit.py
- `inspect(path)` — Проверить длину строк, файлов, функций и наличие docstring.
- `main()` — Не заменяет полноценный линтер или проверку сложности.

## tools/compare_cargo.py
- `parse_tree(text)` — Преобразовать cargo tree --prefix depth --no-dedupe в ребра.
- `edge_set(edges)` — Набор пар для точного сравнения ребер, включая версии.
- `prepare_project(directory, name, version)` — Создать отдельный Cargo-проект для сверки, не меняя исходники.
- `compare(package, destination, repository)` — Выполнить cargo tree и сопоставить вершины, ребра и порядок.
- `main()` — Cargo требуется только здесь; основной программе он не нужен.

## tools/demo.py
- `sparse_server()` — Временный loopback HTTP-сервер, автоматически закрывающийся.
- `execute(arguments, log, expected=0)` — Запустить реальный CLI и проверить ожидаемый exit code.
- `letter_examples(log)` — Показать все пять этапов, фильтр, цикл и отдельную вершину.
- `main()` — Создать SVG/PlantUML и проверяемый журнал реальных запусков.
- `log_message(self, *args)` — Отключить служебные сообщения HTTP-сервера.
