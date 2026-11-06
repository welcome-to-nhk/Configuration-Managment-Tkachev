"""Консольный эмулятор оболочки для практической работы, вариант 24."""

from __future__ import annotations

import argparse
import getpass
import json
import shlex
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass
class Config:
    """Параметры запуска эмулятора."""

    vfs_path: Path
    startup_script: Path | None


class ShellError(Exception):
    """Ошибка выполнения команды эмулятора."""


class VirtualFileSystem:
    """Копия дерева файловой системы, хранящаяся только в оперативной памяти."""

    def __init__(self) -> None:
        self.tree: dict = {}
        self.source: Path | None = None

    def load(self, source: Path) -> None:
        """Загружает каталог рекурсивно в память, не изменяя исходные файлы."""
        if not source.exists():
            raise ShellError(f"каталог VFS не найден: {source}")
        if not source.is_dir():
            raise ShellError(f"источник VFS должен быть каталогом: {source}")
        self.source = source.resolve()
        self.tree = self._read_directory(self.source)

    def _read_directory(self, directory: Path) -> dict:
        """Преобразует один каталог в словарь узлов VFS."""
        result = {}
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
            for child in children:
                if child.is_symlink():
                    continue
                if child.is_dir():
                    result[child.name] = {
                        "type": "directory",
                        "children": self._read_directory(child),
                    }
                elif child.is_file():
                    try:
                        content = child.read_bytes()
                    except OSError as error:
                        raise ShellError(
                            f"не удалось прочитать файл {child}: {error}"
                        ) from error
                    result[child.name] = {
                        "type": "file",
                        "content_base64": __import__("base64").b64encode(
                            content
                        ).decode("ascii"),
                    }
        except OSError as error:
            raise ShellError(
                f"не удалось прочитать каталог {directory}: {error}"
            ) from error
        return result

    def summary(self) -> tuple[int, int]:
        """Возвращает количество каталогов и файлов в загруженном дереве."""
        directories = 1
        files_count = 0
        for node in self.tree.values():
            if node["type"] == "directory":
                nested_dirs, nested_files = self._count_node(node)
                directories += nested_dirs
                files_count += nested_files
            else:
                files_count += 1
        return directories, files_count

    def _count_node(self, node: dict) -> tuple[int, int]:
        """Считает узлы внутри каталога, не включая сам каталог."""
        directories = 1
        files_count = 0
        for child in node["children"].values():
            if child["type"] == "directory":
                nested_dirs, nested_files = self._count_node(child)
                directories += nested_dirs
                files_count += nested_files
            else:
                files_count += 1
        return directories, files_count


def parse_command(line: str) -> list[str]:
    """Разбирает строку оболочки с поддержкой одинарных и двойных кавычек."""
    try:
        return shlex.split(line, comments=False, posix=True)
    except ValueError as error:
        raise ShellError(f"ошибка разбора команды: {error}") from error


class ShellEmulator:
    """Интерактивная оболочка с заглушками команд ls и cd."""

    def __init__(
        self,
        config: Config,
        input_stream: TextIO = sys.stdin,
        output_stream: TextIO = sys.stdout,
    ) -> None:
        self.config = config
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.vfs = VirtualFileSystem()
        self.running = True
        self.last_error = False
        self._load_vfs()

    def _load_vfs(self) -> None:
        """Загружает VFS и сообщает результат."""
        self.vfs.load(self.config.vfs_path)
        dirs, files_count = self.vfs.summary()
        print(
            f"VFS загружена: {self.vfs.source} "
            f"(каталогов: {dirs}, файлов: {files_count})",
            file=self.output_stream,
        )

    def prompt(self) -> str:
        """Формирует приглашение на основе пользователя и имени хоста."""
        username = getpass.getuser()
        hostname = socket.gethostname()
        return f"{username}@{hostname}:~$ "

    def execute(self, line: str) -> bool:
        """Выполняет одну команду; возвращает False при завершении оболочки."""
        self.last_error = False
        try:
            args = parse_command(line)
            if not args:
                return True
            command, *parameters = args
            if command == "exit":
                self._require_count(command, parameters, 0)
                self.running = False
                return False
            if command in {"ls", "cd"}:
                print(
                    f"{command}: заглушка; аргументы: "
                    f"{parameters if parameters else '[]'}",
                    file=self.output_stream,
                )
                return True
            if command == "vfs-info":
                self._require_count(command, parameters, 0)
                dirs, files_count = self.vfs.summary()
                print(f"Источник: {self.vfs.source}", file=self.output_stream)
                print(f"Каталогов: {dirs}; файлов: {files_count}",
                      file=self.output_stream)
                return True
            raise ShellError(f"неизвестная команда: {command}")
        except ShellError as error:
            self.last_error = True
            print(f"Ошибка: {error}", file=self.output_stream)
            return True

    @staticmethod
    def _require_count(command: str, args: list[str], expected: int) -> None:
        """Проверяет точное количество аргументов команды."""
        if len(args) != expected:
            raise ShellError(
                f"{command}: ожидалось аргументов: {expected}, "
                f"получено: {len(args)}"
            )

    def run_script(self, script_path: Path) -> None:
        """Выполняет стартовый скрипт и останавливается на первой ошибке."""
        if not script_path.is_file():
            raise ShellError(f"стартовый скрипт не найден: {script_path}")
        try:
            lines = script_path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise ShellError(
                f"не удалось прочитать стартовый скрипт: {error}"
            ) from error
        for line_number, line in enumerate(lines, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            print(self.prompt() + line, file=self.output_stream)
            before = self.running
            result = self.execute(line)
            if not result and not self.running:
                break
            if before and self._last_command_failed(line):
                raise ShellError(
                    f"стартовый скрипт остановлен: ошибка в строке "
                    f"{line_number}"
                )

    def _last_command_failed(self, line: str) -> bool:
        """Определяет ошибку по последней строке вывода команды."""
        # Ошибки запоминаются execute, чтобы скрипт останавливался корректно.
        return getattr(self, "last_error", False)

    def repl(self) -> None:
        """Запускает интерактивный цикл чтения команд."""
        while self.running:
            try:
                line = input(self.prompt())
            except EOFError:
                print(file=self.output_stream)
                break
            except KeyboardInterrupt:
                print(file=self.output_stream)
                continue
            self.execute(line)


def parse_args(argv: list[str] | None = None) -> Config:
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки ОС, вариант 24"
    )
    parser.add_argument(
        "--vfs", required=True, type=Path,
        help="путь к каталогу, используемому как источник VFS",
    )
    parser.add_argument(
        "--script", type=Path,
        help="путь к стартовому скрипту команд эмулятора",
    )
    args = parser.parse_args(argv)
    return Config(vfs_path=args.vfs, startup_script=args.script)


def main(argv: list[str] | None = None) -> int:
    """Точка входа: печатает конфигурацию и запускает скрипт или REPL."""
    try:
        config = parse_args(argv)
        print("Параметры эмулятора:")
        print(f"  vfs = {config.vfs_path}")
        print(f"  script = {config.startup_script}")
        emulator = ShellEmulator(config)
        if config.startup_script:
            try:
                emulator.run_script(config.startup_script)
            except ShellError as error:
                print(f"Ошибка стартового скрипта: {error}", file=sys.stderr)
                return 1
        else:
            emulator.repl()
        return 0
    except ShellError as error:
        print(f"Ошибка запуска: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
