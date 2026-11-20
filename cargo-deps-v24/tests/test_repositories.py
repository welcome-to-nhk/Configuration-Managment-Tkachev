"""Проверка Cargo JSONL, собственного SemVer и тестового источника."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.errors import AppError
from src.repositories import CargoRepository, TestRepository, index_path
from src.repositories import parse_records
from src.versions import requirement, select_record


def record(name="alpha", version="1.0.0", deps=None, **kwargs):
    """Небольшая запись формата Cargo sparse-index."""
    return dict(name=name, vers=version, deps=deps or [], **kwargs)


class VersionTests(unittest.TestCase):
    """Стабильные диапазоны Cargo не сравниваются как строки."""

    def test_semver_ranges(self):
        """Проверить ^, ~, wildcard, AND, точную и неполную версии."""
        cases = [
            ("^1.2.3", (1, 9, 0), True),
            ("^1.2.3", (2, 0, 0), False),
            ("^0.2.3", (0, 3, 0), False),
            ("^0.0.3", (0, 0, 4), False),
            ("~1.2.3", (1, 3, 0), False),
            ("1.*", (1, 9, 0), True),
            ("1.2.*", (1, 3, 0), False),
            (">=1.2, <2", (1, 5, 0), True),
            ("=1.2.3", (1, 2, 4), False),
            ("0", (0, 9, 0), True),
            ("^0.0", (0, 0, 9), True),
        ]
        for text, version, expected in cases:
            with self.subTest(text=text, version=version):
                self.assertEqual(requirement(text)(version), expected)

    def test_version_selection(self):
        """Исключить yanked/prerelease и выбрать численно 1.10 > 1.9."""
        records = [record(version="1.9.0"), record(version="1.10.0"),
                   record(version="2.0.0", yanked=True),
                   record(version="3.0.0-beta")]
        self.assertEqual(select_record(records)["vers"], "1.10.0")
        with self.assertRaises(AppError):
            select_record(records, "^8")
        with self.assertRaises(AppError):
            requirement("1.0-beta")


class RepositoryTests(unittest.TestCase):
    """Сеть подменяется; сам парсер работает с реальным форматом."""

    def test_paths(self):
        """Все четыре правила sparse-путей."""
        for name, path in [("a", "1/a"), ("ab", "2/ab"),
                           ("abc", "3/a/abc"), ("serde", "se/rd/serde")]:
            self.assertEqual(index_path(name), path)

    def test_cargo_dependencies(self):
        """Переименование, build, optional, dev и кэш."""
        deps = [dict(name="alias", package="beta", req="^1"),
                dict(name="ignored", req="*", optional=True),
                dict(name="ignored", req="*", kind="dev"),
                dict(name="beta", req="^1", kind="build")]
        texts = [json.dumps(record(deps=deps)),
                 json.dumps(record(name="beta"))]
        with patch("src.repositories.read_url", side_effect=texts) as read:
            repo = CargoRepository("https://index.crates.io")
            root = repo.root("alpha")
            self.assertEqual(repo.dependencies(root), ["beta@1.0.0"])
            repo.dependencies(root)
            self.assertEqual(read.call_count, 2)

    def test_invalid_records(self):
        """Пустой или поврежденный индекс — понятная ошибка."""
        for text in ["", "broken", "{}", json.dumps(record(name="other"))]:
            with self.subTest(text=text), self.assertRaises(AppError):
                parse_records(text, "alpha")

    def test_invalid_test_repository(self):
        """Нельзя молча превращать отсутствующую зависимость в лист."""
        invalid = ["[]", "{}", '{"a": []}', '{"A": ["B"]}',
                   '{"A": "B"}', '{"A": [3]}', "broken"]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repo.json"
            for text in invalid:
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(AppError):
                    TestRepository(path)
