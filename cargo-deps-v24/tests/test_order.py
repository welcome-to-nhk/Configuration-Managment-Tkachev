"""Свойства порядка загрузки, а не только один ожидаемый список."""

import unittest

from src.errors import AppError
from src.graph import build_graph
from src.order import loading_order
from src.repositories import TestRepository


class OrderTests(unittest.TestCase):
    """Независимые ветки допускают разные корректные перестановки."""

    def test_dependency_before_consumer(self):
        """Каждое ребро должно вести к более ранней позиции списка."""
        for file in ["chain", "diamond", "isolated", "filter"]:
            repo = TestRepository(f"examples/{file}.json")
            graph = build_graph(repo, "A")
            order = loading_order(graph)
            self.assertEqual(set(order), set(graph.edges))
            self.assertEqual(len(order), len(set(order)))
            for parent, deps in graph.edges.items():
                for dep in deps:
                    self.assertLess(order.index(dep), order.index(parent))

    def test_diamond_order(self):
        """D должен загрузиться один раз, до B и C."""
        repo = TestRepository("examples/diamond.json")
        self.assertEqual(loading_order(build_graph(repo, "A")),
                         ["D", "B", "C", "A"])

    def test_cycle_is_error(self):
        """Не выдавать некорректный частичный порядок за правильный."""
        for file in ["cycle", "self"]:
            repo = TestRepository(f"examples/{file}.json")
            with self.assertRaisesRegex(AppError, "цикл"):
                loading_order(build_graph(repo, "A"))
