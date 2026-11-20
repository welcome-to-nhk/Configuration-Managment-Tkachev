"""Проверки этапа 1, включая все пять настроек."""

import tempfile
import unittest
from pathlib import Path

from src.config import read_options
from src.errors import AppError

BASE = ["--package", "crc32fast", "--repository", "https://index.crates.io"]


class ConfigTests(unittest.TestCase):
    """CLI должен отвергать ошибки до начала сетевой работы."""

    def test_defaults(self):
        """Пустой фильтр допустим и означает отсутствие фильтрации."""
        options = read_options(BASE)
        self.assertEqual(options.exclude, "")
        self.assertFalse(options.test)

    def test_all_invalid_parameters(self):
        """Каждая предметная настройка имеет отрицательный пример."""
        invalid = [
            ["--package", "bad/name"],
            ["--repository", "ftp://example.com"],
            ["--test"],
            ["--output", "graph.png"],
            ["--filter", "\n"],
            ["--filter", "crc"],
            ["--repository", "http://host:bad"],
            ["--repository", "http://[bad"],
        ]
        for extra in invalid:
            with self.subTest(extra=extra), self.assertRaises(AppError):
                read_options(BASE + extra)

    def test_test_file(self):
        """Тестовый файл должен существовать; имена только A–Z."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "repo.json"
            path.write_text('{"A": []}', encoding="utf-8")
            options = read_options([
                "--package", "A", "--repository", str(path), "--test"])
            self.assertTrue(options.test)
