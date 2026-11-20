"""Собственная обработка стабильного подмножества Cargo SemVer."""

import operator
import re

from .errors import AppError

WIDTH = 3
FIRST = 0
OPS = {">=": operator.ge, "<=": operator.le, ">": operator.gt,
       "<": operator.lt, "=": operator.eq}


def version_key(text):
    """Разобрать стабильную x.y.z; build-метаданные не меняют порядок."""
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\+[\w.-]+)?", text)
    if not match:
        raise AppError(f"Неподдерживаемая стабильная версия: {text}")
    return tuple(map(int, match.groups()))


def upper_bound(parts, caret=False):
    """Верхняя исключающая граница для ^, ~ и wildcard."""
    index = min(len(parts) - 1, 1)
    if caret:
        index = next((i for i, n in enumerate(parts) if n),
                     len(parts) - 1)
    bound = list(parts) + [0] * (WIDTH - len(parts))
    bound[index] += 1
    for tail in range(index + 1, WIDTH):
        bound[tail] = 0
    return tuple(bound)


def comparator(text):
    """Построить предикат одного стабильного ограничения Cargo."""
    match = re.fullmatch(r"(>=|<=|>|<|=|\^|~)?\s*([0-9xX*]+(?:"
                         r"\.[0-9xX*]+){0,2})", text.strip())
    if not match:
        raise AppError(f"Неподдерживаемое ограничение версии: {text}")
    op, raw = match.groups()
    fields = raw.split(".")
    wild = next((i for i, n in enumerate(fields)
                 if n in {"*", "x", "X"}), len(fields))
    if any(n not in {"*", "x", "X"} for n in fields[wild:]):
        raise AppError(f"Неверный wildcard: {text}")
    parts = tuple(map(int, fields[:wild]))
    if not parts:
        return lambda value: True
    low = parts + (0,) * (WIDTH - len(parts))
    if wild < len(fields):
        high = upper_bound(parts, caret=False)
        if len(parts) == WIDTH - 1:
            high = (parts[0], parts[1] + 1, 0)
        return lambda value: low <= value < high
    if op in OPS:
        compare = OPS[op]
        if len(parts) < WIDTH:
            return lambda value: compare(value[:len(parts)], parts)
        return lambda value: compare(value, low)
    high = upper_bound(parts, caret=op != "~")
    return lambda value: low <= value < high


def requirement(text):
    """Скомпилировать AND-список через запятую (без prerelease)."""
    checks = [comparator(part) for part in text.split(",")]
    return lambda value: all(check(value) for check in checks)


def select_record(records, constraint="*"):
    """Выбрать новейшую неотозванную стабильную подходящую версию."""
    check = requirement(constraint)
    candidates = []
    for record in records:
        if record.get("yanked") or "-" in record["vers"]:
            continue
        key = version_key(record["vers"])
        if check(key):
            candidates.append((key, record))
    if not candidates:
        raise AppError(f"Нет стабильной версии для ограничения {constraint}")
    return max(candidates, key=lambda item: item[0])[1]
