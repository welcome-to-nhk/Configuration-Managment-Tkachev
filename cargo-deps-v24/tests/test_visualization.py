"""Проверки корректного PlantUML, SVG и обоих рендереров."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as element_tree

from src.errors import AppError
from src.graph import build_graph
from src.plantuml import official_svg, save_diagram, to_plantuml
from src.repositories import TestRepository
from src.svg import parse_subset, render_subset


class VisualizationTests(unittest.TestCase):
    """Изолированная вершина и циклические ребра не теряются."""

    def test_round_trip(self):
        """Все вершины и ребра проходят через PlantUML в SVG."""
        for file in ["diamond", "cycle", "self", "isolated"]:
            repo = TestRepository(f"examples/{file}.json")
            graph = build_graph(repo, "A")
            source = to_plantuml(graph)
            labels, edges = parse_subset(source)
            self.assertEqual(set(labels.values()), set(graph.edges))
            self.assertEqual(len(edges), sum(map(len, graph.edges.values())))
            svg = element_tree.fromstring(render_subset(source))
            self.assertTrue(svg.tag.endswith("svg"))
            text = [n.text for n in svg.iter() if n.tag.endswith("text")]
            self.assertTrue(set(graph.edges).issubset(text))

    def test_save_files(self):
        """Создать каталог и два непустых выходных файла."""
        repo = TestRepository("examples/diamond.json")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested/graph.svg"
            source, image = save_diagram(build_graph(repo, "A"), path)
            self.assertTrue(source.read_text().startswith("@startuml"))
            self.assertTrue(image.read_bytes().startswith(b"<?xml"))

    def test_unsupported_plantuml(self):
        """Встроенный рендерер не притворяется полной заменой PlantUML."""
        with self.assertRaises(AppError):
            render_subset("@startuml\nAlice -> Bob\n@enduml")

    def test_missing_official_renderer(self):
        """Понятная ошибка, если отсутствует необязательный PlantUML."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("shutil.which", return_value=None):
                with self.assertRaises(AppError):
                    official_svg("@startuml\n@enduml")