"""Проверки DFS: ромб, циклы, фильтр, отсутствие лишних чтений."""

import unittest
from unittest.mock import Mock, patch

from src.graph import build_graph
from src.repositories import CargoRepository, TestRepository


class GraphTests(unittest.TestCase):
    """В графе сохраняются все ребра, но вершины раскрываются один раз."""

    def test_dfs_diamond(self):
        """Это именно DFS: A, B, D, C, а не BFS: A, B, C, D."""
        repo = TestRepository("examples/diamond.json")
        graph = build_graph(repo, "A")
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C"])
        self.assertEqual(graph.edges["C"], ["D"])
        self.assertEqual(graph.cycles, [])

    def test_cycles(self):
        """Обычный цикл и петля не приводят к бесконечной рекурсии."""
        for file, expected in [("cycle", ["A", "B", "C", "A"]),
                               ("self", ["A", "A"])]:
            repo = TestRepository(f"examples/{file}.json")
            graph = build_graph(repo, "A")
            self.assertEqual(graph.cycles, [expected])

    def test_filter_prunes_branch(self):
        """Удалить пакет с X и все недостижимое за ним поддерево."""
        repo = TestRepository("examples/filter.json")
        graph = build_graph(repo, "A", "X")
        self.assertEqual(set(graph.edges), {"A", "B", "D"})

    def test_no_dependency(self):
        """Изолированный корень все равно входит в граф."""
        repo = TestRepository("examples/isolated.json")
        self.assertEqual(build_graph(repo, "A").edges, {"A": []})

    def test_shared_node_read_once(self):
        """Общая зависимость не загружается повторно."""
        repo = TestRepository("examples/diamond.json")
        with patch.object(repo, "dependencies", wraps=repo.dependencies) as fn:
            build_graph(repo, "A")
            self.assertEqual(fn.call_count, 4)

    def test_filtered_cargo_not_fetched(self):
        """Исключенный crate даже не запрашивается по сети."""
        repo = CargoRepository("https://example.org")
        repo.selected["a@1.0.0"] = {
            "deps": [dict(name="hidden", req="*")]}
        repo.resolve = Mock(side_effect=AssertionError("Network forbidden"))
        self.assertEqual(repo.dependencies("a@1.0.0", "hidden"), [])
