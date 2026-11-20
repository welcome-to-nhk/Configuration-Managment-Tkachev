"""Парсер штатного cargo tree без запуска внешнего менеджера в тестах."""

import unittest

from src.errors import AppError
from tools.compare_cargo import parse_tree


class CompareTests(unittest.TestCase):
    """Префикс глубины позволяет восстановить общие зависимости."""

    def test_parse_tree(self):
        """Отделить проверочный wrapper и сохранить повторяющиеся ребра."""
        text = ("0v24-comparison v0.1.0\n1alpha v1.0.0\n"
                "2beta v1.0.0\n3delta v1.0.0\n"
                "2gamma v1.0.0\n3delta v1.0.0\n")
        edges = parse_tree(text)
        self.assertEqual(edges["gamma@1.0.0"], {"delta@1.0.0"})
        self.assertEqual(len(edges), 4)

    def test_bad_tree(self):
        """Не принимать неизвестный формат за пустой граф."""
        with self.assertRaises(AppError):
            parse_tree("not cargo tree")
