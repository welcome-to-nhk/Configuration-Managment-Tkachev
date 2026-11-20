"""Автономный рендерер ТОЛЬКО подмножества PlantUML этого проекта."""

import re
from collections import deque
from xml.etree import ElementTree as ET

from .errors import AppError

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
NODE_HEIGHT = 56
X_GAP = 112
Y_GAP = 104
TOP = 104
LEFT = 48


def element(parent, tag, attributes=None, text=None):
    """Добавить SVG-элемент; XML-библиотека экранирует текст."""
    child = ET.SubElement(parent, f"{{{NS}}}{tag}", attributes or {})
    child.text = text
    return child


def parse_subset(source):
    """Прочитать component \"label\" as n0 и n0 --> n1."""
    labels = {}
    edges = []
    ignored = {"@startuml", "@enduml", "left to right direction",
               "skinparam componentStyle rectangle",
               "skinparam shadowing false", ""}
    for line in source.splitlines():
        node = re.fullmatch(r'component "([A-Za-z0-9_@.+-]+)" as (n\d+)',
                            line)
        edge = re.fullmatch(r"(n\d+) --> (n\d+)", line)
        if node:
            labels[node[2]] = node[1]
        elif edge:
            edges.append(edge.groups())
        elif line not in ignored:
            raise AppError("Автономный рендерер: неизвестный синтаксис")
    if not labels or any(a not in labels or b not in labels for a, b in edges):
        raise AppError("Автономный рендерер: некорректные вершины")
    return labels, edges


def positions(labels, edges, width):
    """Разместить компоненты по кратчайшим расстояниям от корня."""
    root = next(iter(labels))
    distance = {root: 0}
    queue = deque([root])
    adjacency = {key: [] for key in labels}
    for source, target in edges:
        adjacency[source].append(target)
    while queue:
        node = queue.popleft()
        for dep in adjacency[node]:
            if dep not in distance:
                distance[dep] = distance[node] + 1
                queue.append(dep)
    rows = {}
    result = {}
    for key in labels:
        level = distance.get(key, 0)
        row = rows.get(level, 0)
        rows[level] = row + 1
        result[key] = (LEFT + level * (width + X_GAP), TOP + row * Y_GAP)
    return result


def arrow_path(start, end, width, index):
    """Кривые вперед и по внешней стороне для обратных ребер."""
    x1, y1 = start
    x2, y2 = end
    if x2 > x1:
        a, b = x1 + width, x2
        y1 += NODE_HEIGHT / 2
        y2 += NODE_HEIGHT / 2
        middle = (a + b) / 2
        return f"M {a} {y1} C {middle} {y1}, {middle} {y2}, {b} {y2}"
    a, b = x1 + width / 2, x2 + width / 2
    if start == end:
        return (f"M {a} {y1} C {a-44} {y1-72}, {a+44} {y1-72}, "
                f"{a+16} {y1}")
    lane = 24 + (index % 4) * 12
    return f"M {a} {y1} C {a} {lane}, {b} {lane}, {b} {y2}"


def draw_edges(svg, edges, points, width):
    """Стрелка означает «пакет зависит от», а не порядок загрузки."""
    for index, (source, target) in enumerate(edges):
        element(svg, "path", {
            "d": arrow_path(points[source], points[target], width, index),
            "fill": "none", "stroke": "#54718c", "stroke-width": "2",
            "marker-end": "url(#arrow)"})


def draw_nodes(svg, labels, points, width):
    """Читаемые подписи и выделение корня цветом, не только порядком."""
    root = next(iter(labels))
    for key, label in labels.items():
        x, y = points[key]
        element(svg, "rect", {
            "x": str(x), "y": str(y), "width": str(width),
            "height": str(NODE_HEIGHT), "rx": "8",
            "fill": "#E5F2FC" if key == root else "#F9F8F7",
            "stroke": "#2783DE" if key == root else "#B9C5CF"})
        element(svg, "text", {
            "x": str(x + width / 2), "y": str(y + 34),
            "text-anchor": "middle", "font-family": "Arial, sans-serif",
            "font-size": "16", "fill": "#2C2C2B"}, label)


def render_subset(source):
    """Рендерить генерируемое нами подмножество, не весь язык PlantUML."""
    labels, edges = parse_subset(source)
    width = max(176, max(map(len, labels.values())) * 9 + 32)
    points = positions(labels, edges, width)
    canvas_width = max(480, max(x for x, y in points.values())
                       + width + LEFT)
    canvas_height = max(y for x, y in points.values()) + NODE_HEIGHT + 80
    svg = ET.Element(f"{{{NS}}}svg", {
        "viewBox": f"0 0 {canvas_width} {canvas_height}",
        "width": str(canvas_width), "height": str(canvas_height),
        "role": "img", "aria-labelledby": "title"})
    element(svg, "title", {"id": "title"}, "Cargo dependency graph")
    element(svg, "rect", {"width": "100%", "height": "100%",
                          "fill": "#FFFFFF"})
    defs = element(svg, "defs")
    marker = element(defs, "marker", {
        "id": "arrow", "viewBox": "0 0 10 10", "refX": "10", "refY": "5",
        "markerWidth": "7", "markerHeight": "7", "orient": "auto"})
    element(marker, "path", {"d": "M 0 0 L 10 5 L 0 10 z",
                             "fill": "#54718c"})
    draw_edges(svg, edges, points, width)
    draw_nodes(svg, labels, points, width)
    element(svg, "text", {"x": str(LEFT), "y": str(canvas_height - 28),
                          "font-family": "Arial, sans-serif",
                          "font-size": "14", "fill": "#526270"},
            "A -> B: A depends on B | blue: root package")
    return ET.tostring(svg, encoding="utf-8", xml_declaration=True)
