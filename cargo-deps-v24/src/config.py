"""Опции командной строки и проверка всех настроек этапа 1."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

from .errors import AppError

CARGO_NAME = r"[A-Za-z][A-Za-z0-9_-]*"
TEST_NAME = r"[A-Z]+"
STAGES = range(1, 6)


def parser():
    """Создать CLI; параметры предметной области не читаются из конфига."""
    result = argparse.ArgumentParser(
        description="Вариант 24: граф зависимостей Cargo")
    result.add_argument("--package", required=True, help="Имя пакета")
    result.add_argument("--repository", required=True,
                        help="URL sparse-индекса или JSON при --test")
    result.add_argument("--test", action="store_true",
                        help="Использовать тестовый JSON-репозиторий")
    result.add_argument("--output", default="out/graph.svg")
    result.add_argument("--filter", default="", dest="exclude",
                        help="Не учитывать имена с этой подстрокой")
    result.add_argument("--stage", type=int, choices=STAGES, default=5)
    result.add_argument("--renderer", choices=["builtin", "plantuml"],
                        default="builtin", help="Способ отрисовки SVG")
    return result


def validate_source(options):
    """Проверить существование файла либо синтаксис URL репозитория."""
    if options.test:
        if not Path(options.repository).is_file():
            raise AppError("Тестовый репозиторий: файл не найден")
        return
    try:
        url = urlparse(options.repository.removeprefix("sparse+"))
    except ValueError as error:
        raise AppError("Репозиторий: неверный URL") from error
    if url.scheme not in {"http", "https"} or not url.hostname:
        raise AppError("Репозиторий: нужен HTTP(S) URL sparse-индекса")
    if url.query or url.fragment or url.username or url.password:
        raise AppError("URL не должен содержать query, fragment или пароль")
    try:
        url.port
    except ValueError as error:
        raise AppError("Репозиторий: неверный номер порта") from error


def validate_output(value):
    """Проверить SVG-путь и ближайший существующий родитель."""
    path = Path(value)
    if path.suffix.lower() != ".svg" or path.is_dir():
        raise AppError("Выходной файл должен иметь расширение .svg")
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir():
        raise AppError("Родитель выходного файла не является каталогом")


def read_options(argv=None):
    """Прочитать и проверить настройки; argparse проверяет типы и флаги."""
    options = parser().parse_args(argv)
    pattern = TEST_NAME if options.test else CARGO_NAME
    if not re.fullmatch(pattern, options.package):
        raise AppError("Имя пакета неверно (в тестовом режиме нужны A–Z)")
    validate_source(options)
    validate_output(options.output)
    if any(ord(char) < 32 for char in options.exclude):
        raise AppError("Фильтр не должен содержать управляющие символы")
    if options.exclude and options.exclude in options.package:
        raise AppError("Фильтр исключает сам анализируемый пакет")
    return options


def print_options(options):
    """Вывести все пять предметных настроек в формате ключ=значение."""
    for key in ("package", "repository", "test", "output", "exclude"):
        print(f"{key}={getattr(options, key)}")
