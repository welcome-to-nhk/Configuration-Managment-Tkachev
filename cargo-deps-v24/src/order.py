"""Топологический порядок: каждая зависимость раньше потребителя."""

from .errors import AppError


def loading_order(graph):
    """Получить DFS postorder; при цикле корректного порядка нет."""
    if graph.cycles:
        cycle = " -> ".join(graph.cycles[0])
        raise AppError(f"Порядок загрузки невозможен: цикл {cycle}")
    visited = set()
    result = []

    def visit(node):
        """Добавить вершину только после всех ее зависимостей."""
        if node in visited:
            return
        visited.add(node)
        for dep in graph.edges[node]:
            visit(dep)
        result.append(node)

    try:
        visit(graph.root)
    except RecursionError as error:
        message = "Граф слишком глубок для рекурсивной сортировки"
        raise AppError(message) from error
    return result
