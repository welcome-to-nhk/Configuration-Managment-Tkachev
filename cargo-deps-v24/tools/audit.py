"""Простой проверяемый аудит части правил оформления из методички."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_LINE = 80
MAX_FUNCTION = 40
MAX_ARGS = 7
MAX_FILE = 1000


def inspect(path):
    """Проверить длину строк, файлов, функций и наличие docstring."""
    text = path.read_text(encoding="utf-8")
    errors = []
    if len(text.splitlines()) > MAX_FILE:
        errors.append(f"{path}: слишком большой файл")
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) > MAX_LINE:
            errors.append(f"{path}:{number}: строка длиннее {MAX_LINE}")
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.end_lineno - node.lineno + 1 > MAX_FUNCTION:
            errors.append(f"{path}:{node.name}: функция длиннее 40 строк")
        if len(node.args.args) + len(node.args.kwonlyargs) > MAX_ARGS:
            errors.append(f"{path}:{node.name}: больше 7 аргументов")
        if not ast.get_docstring(node):
            errors.append(f"{path}:{node.name}: нет docstring")
    return errors


def main():
    """Не заменяет полноценный линтер или проверку сложности."""
    errors = []
    for folder in ["src", "tests", "tools"]:
        for path in (ROOT / folder).glob("*.py"):
            errors.extend(inspect(path))
    for message in errors:
        print(message)
    if not errors:
        print("OK: строки <=80, файлы <=1000, функции <=40, "
              "аргументы <=7; у функций есть docstring")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
