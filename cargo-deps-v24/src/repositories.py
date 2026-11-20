"""Тестовый JSON и HTTP sparse-индекс Cargo без менеджеров пакетов."""

import json
import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from .errors import AppError
from .versions import select_record, version_key

MAX_RESPONSE = 32 * 1024 * 1024
TIMEOUT = 20
USER_AGENT = "cargo-deps-v24/1.0 (educational sparse-index reader)"


def index_path(name):
    """Вычислить путь Cargo: 1/a, 2/ab, 3/a/abc или ab/cd/abcd."""
    name = name.lower()
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
        raise AppError(f"Неверное имя crate: {name}")
    size = len(name)
    if size <= 2:
        return f"{size}/{name}"
    if size == 3:
        return f"3/{name[0]}/{name}"
    return f"{name[:2]}/{name[2:4]}/{name}"


def read_url(url):
    """Прочитать UTF-8 по HTTP с тайм-аутом и ограничением объема."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            data = response.read(MAX_RESPONSE + 1)
    except (URLError, TimeoutError, OSError) as error:
        raise AppError(f"Не удалось получить {url}: {error}") from error
    if len(data) > MAX_RESPONSE:
        raise AppError("Ответ репозитория слишком большой")
    return data.decode("utf-8")


def parse_records(text, name):
    """Самостоятельно разобрать JSONL-файл метаданных crate."""
    try:
        records = [json.loads(line) for line in text.splitlines()
                   if line.strip()]
        for item in records:
            if item["name"].lower() != name.lower():
                raise ValueError("Имя в индексе не совпадает с запросом")
            if not isinstance(item["deps"], list):
                raise ValueError("deps должен быть массивом")
            if "-" not in item["vers"]:
                version_key(item["vers"])
            for dependency in item["deps"]:
                index_path(dependency.get("package") or dependency["name"])
                if not isinstance(dependency["req"], str):
                    raise ValueError("req должен быть строкой")
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise AppError(f"Неверные метаданные {name}: {error}") from error
    if not records:
        raise AppError(f"Пустой индекс для {name}")
    return records


class TestRepository:
    """Строгий граф {A: [B, C], B: [], C: []}."""

    def __init__(self, path):
        """Проверить JSON, имена, списки и замкнутость ссылок."""
        try:
            self.graph = json.loads(Path(path).read_text(encoding="utf-8"))
        except ValueError as error:
            raise AppError(f"Неверный JSON: {error}") from error
        if not isinstance(self.graph, dict) or not self.graph:
            raise AppError("Тестовый репозиторий: нужен непустой объект")
        for name, deps in self.graph.items():
            if not re.fullmatch(r"[A-Z]+", name):
                raise AppError("Имена тестовых пакетов: только A–Z")
            if not isinstance(deps, list):
                raise AppError(f"Зависимости {name}: нужен массив")
            for dep in deps:
                if not isinstance(dep, str) or dep not in self.graph:
                    raise AppError(f"Неизвестная зависимость {name}: {dep}")

    def root(self, name):
        """Найти начальную вершину."""
        if name not in self.graph:
            raise AppError(f"Пакет не найден: {name}")
        return name

    def dependencies(self, node, exclude=""):
        """Вернуть уникальные прямые зависимости в стабильном порядке."""
        return sorted(dep for dep in set(self.graph[node])
                      if not exclude or exclude not in dep)


class CargoRepository:
    """Чтение sparse-индекса; кэш действует в пределах одного запуска."""

    def __init__(self, url):
        """Сохранить базовый URL и пустые кэши."""
        self.url = url.removeprefix("sparse+").rstrip("/")
        self.records = {}
        self.selected = {}

    def resolve(self, name, constraint="*"):
        """Разрешить одно ребро; версия входит в идентификатор вершины."""
        name = name.lower()
        if name not in self.records:
            text = read_url(f"{self.url}/{index_path(name)}")
            self.records[name] = parse_records(text, name)
        record = select_record(self.records[name], constraint)
        node = f"{name}@{record['vers']}"
        self.selected[node] = record
        return node

    def root(self, name):
        """Для корня без версии выбрать новейший стабильный релиз."""
        return self.resolve(name)

    def dependencies(self, node, exclude=""):
        """Обязательные normal/build, объединенные для всех target."""
        result = set()
        for dep in self.selected[node]["deps"]:
            if dep.get("kind") == "dev" or dep.get("optional", False):
                continue
            if dep.get("registry"):
                raise AppError("Зависимости другого registry не поддержаны")
            name = dep.get("package") or dep["name"]
            if not exclude or exclude not in name:
                result.add(self.resolve(name, dep["req"]))
        return sorted(result)


def open_repository(options):
    """Выбрать источник; чтение графа не вызывает Cargo или pip."""
    if options.test:
        return TestRepository(options.repository)
    return CargoRepository(options.repository)
