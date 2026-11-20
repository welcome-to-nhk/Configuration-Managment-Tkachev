"""Генерация PlantUML и запуск официального необязательного рендерера."""

import os
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

from .errors import AppError


def to_plantuml(graph):
    """Стабильные alias n0... не зависят от символов в именах пакетов."""
    aliases = {node: f"n{i}" for i, node in enumerate(graph.edges)}
    lines = ["@startuml", "left to right direction",
             "skinparam componentStyle rectangle", "skinparam shadowing false"]
    for node, alias in aliases.items():
        safe = node.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'component "{safe}" as {alias}')
    for node, deps in graph.edges.items():
        for dep in deps:
            lines.append(f"{aliases[node]} --> {aliases[dep]}")
    return "\n".join(lines + ["@enduml", ""])


def official_svg(source):
    """Выполнить локальный PlantUML, без отправки графа на сервер."""
    jar = os.environ.get("PLANTUML_JAR")
    command = ["plantuml", "-tsvg", "-pipe"]
    if jar:
        if not Path(jar).is_file():
            raise AppError("PLANTUML_JAR указывает на отсутствующий файл")
        command = ["java", "-jar", jar, "-tsvg", "-pipe"]
    elif not shutil.which("plantuml"):
        raise AppError("PlantUML не найден: задайте PLANTUML_JAR "
                       "или используйте --renderer builtin")
    try:
        result = subprocess.run(command, input=source.encode("utf-8"),
                                capture_output=True, timeout=60, check=True)
    except (OSError, subprocess.SubprocessError) as error:
        raise AppError(f"Не удалось запустить PlantUML: {error}") from error
    try:
        root = ET.fromstring(result.stdout)
        if not root.tag.endswith("svg"):
            raise ValueError("ответ не SVG")
    except (ET.ParseError, ValueError) as error:
        raise AppError("PlantUML не вернул корректный SVG") from error
    return result.stdout


def save_diagram(graph, output, renderer="builtin"):
    """Сохранить исходный .puml и изображение .svg рядом."""
    from .svg import render_subset

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    source = to_plantuml(graph)
    path.with_suffix(".puml").write_text(source, encoding="utf-8")
    svg = official_svg(source) if renderer == "plantuml" else render_subset(
        source)
    path.write_bytes(svg)
    return path.with_suffix(".puml"), path
