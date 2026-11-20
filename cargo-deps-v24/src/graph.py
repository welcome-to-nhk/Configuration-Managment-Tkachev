"""Рекурсивный DFS: построение графа и фиксация обратных ребер."""

from dataclasses import dataclass, field

from .errors import AppError

GRAY = 1
BLACK = 2


@dataclass
class Graph:
    """Ребро parent -> dependency; cycles содержит замкнутые пути."""

    root: str
    edges: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)


def build_graph(repository, root, exclude=""):
    """Обойти зависимости в глубину с рекурсией, не теряя ребра цикла."""
    graph = Graph(root)
    colors = {}
    path = []

    def visit(node):
        """GRAY — в текущем пути, BLACK — уже полностью обработан."""
        if colors.get(node) == GRAY:
            graph.cycles.append(path[path.index(node):] + [node])
            return
        if colors.get(node) == BLACK:
            return
        colors[node] = GRAY
        path.append(node)
        graph.edges[node] = repository.dependencies(node, exclude)
        for dep in graph.edges[node]:
            visit(dep)
        path.pop()
        colors[node] = BLACK

    try:
        visit(root)
    except RecursionError as error:
        message = "Граф слишком глубок для рекурсивного DFS Python"
        raise AppError(message) from error
    return graph


def print_graph(graph):
    """Показать список смежности и обнаруженные циклы."""
    for node, dependencies in graph.edges.items():
        print(f"{node} -> {', '.join(dependencies) or '(нет)'}")
    for cycle in graph.cycles:
        print(f"Цикл: {' -> '.join(cycle)}")
