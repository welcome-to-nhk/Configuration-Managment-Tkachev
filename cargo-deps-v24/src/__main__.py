"""Точка входа: python -m src."""

import sys

from .config import print_options, read_options
from .errors import AppError
from .graph import build_graph, print_graph
from .repositories import open_repository
from .order import loading_order
from .plantuml import save_diagram


def run(options):
    """Выполнить выбранный этап; этапы 1/2/4 не создают изображение."""
    if options.stage == 1:
        print_options(options)
        return
    repository = open_repository(options)
    root = repository.root(options.package)
    if options.stage == 2:
        print(f"Пакет: {root}")
        print("Прямые зависимости:")
        for dep in repository.dependencies(root):
            print(f"  {dep}")
        return
    graph = build_graph(repository, root, options.exclude)
    if options.stage == 4:
        order = loading_order(graph)
        print("Порядок загрузки (зависимости раньше потребителей):")
        print(" -> ".join(order))
        return
    if options.stage == 5:
        source, image = save_diagram(graph, options.output, options.renderer)
        print(f"PlantUML: {source}")
        print(f"SVG: {image}")
        if graph.cycles:
            print("Внимание: граф содержит циклы; они сохранены на диаграмме")
        return
    print_graph(graph)


def main(argv=None):
    """Показать понятную ошибку и вернуть ненулевой код при неудаче."""
    try:
        run(read_options(argv))
        return 0
    except (AppError, OSError, UnicodeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
