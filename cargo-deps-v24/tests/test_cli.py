"""Интеграционные проверки реального CLI и HTTP sparse-индекса."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from src.__main__ import main
from src.errors import AppError
from src.repositories import read_url
from tools.demo import sparse_server

BASE = ["--package", "A", "--test", "--repository", "examples/diamond.json"]


class IntegrationTests(unittest.TestCase):
    """Не только unit-тесты: все стадии проходят через точку входа."""

    def test_all_stages(self):
        """Этапы доступны независимо служебным переключателем."""
        with tempfile.TemporaryDirectory() as folder:
            for stage in range(1, 6):
                args = BASE + ["--stage", str(stage), "--output",
                               str(Path(folder) / "graph.svg")]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(args), 0)

    def test_three_real_package_snapshots_over_http(self):
        """Живой локальный HTTP, а не mock и не буквенный тестовый граф."""
        with sparse_server() as url:
            for package, dep in [("crc32fast", "cfg-if@1.0.4"),
                                 ("miniz_oxide", "adler2@2.0.1"),
                                 ("itoa", "Прямые зависимости:")]:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    code = main(["--package", package, "--repository", url,
                                 "--stage", "2"])
                self.assertEqual(code, 0)
                self.assertIn(dep, output.getvalue())

    def test_http_404_is_friendly(self):
        """Несуществующий crate дает код 1, без traceback."""
        with sparse_server() as url, contextlib.redirect_stderr(
                io.StringIO()) as output:
            code = main(["--package", "missing", "--repository", url,
                         "--stage", "2"])
            self.assertEqual(code, 1)
            self.assertIn("404", output.getvalue())

    def test_cycle_exit_code(self):
        """Граф строится, но порядок при цикле невозможен."""
        args = BASE + ["--repository", "examples/cycle.json", "--stage", "4"]
        with contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main(args), 1)
            self.assertIn("цикл", output.getvalue())

    def test_network_failure(self):
        """DNS/сетевая ошибка оборачивается в AppError."""
        with patch("src.repositories.urlopen", side_effect=URLError("DNS")):
            with self.assertRaises(AppError):
                read_url("https://unreachable.invalid")
