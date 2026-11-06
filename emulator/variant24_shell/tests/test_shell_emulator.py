"""Тесты этапов 1–3."""

import io
import tempfile
import unittest
from pathlib import Path

from src.shell_emulator import Config, ShellEmulator, ShellError, parse_command


class ParserTests(unittest.TestCase):
    def test_quoted_argument(self):
        self.assertEqual(parse_command('ls "two words"'), ["ls", "two words"])

    def test_single_quotes(self):
        self.assertEqual(parse_command("cd 'my folder'"), ["cd", "my folder"])

    def test_unclosed_quote(self):
        with self.assertRaises(ShellError):
            parse_command('ls "unfinished')


class EmulatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "docs" / "deep").mkdir(parents=True)
        (self.root / "hello.txt").write_text("hello", encoding="utf-8")
        (self.root / "docs" / "deep" / "note.txt").write_text(
            "note", encoding="utf-8"
        )
        self.output = io.StringIO()
        self.emulator = ShellEmulator(
            Config(self.root, None), io.StringIO(), self.output
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_stub_command(self):
        self.emulator.execute('ls "folder with spaces"')
        self.assertIn("folder with spaces", self.output.getvalue())

    def test_unknown_command(self):
        self.emulator.execute("not-a-command")
        self.assertIn("неизвестная команда", self.output.getvalue())

    def test_exit_with_argument_is_error(self):
        self.emulator.execute("exit now")
        self.assertTrue(self.emulator.running)
        self.assertIn("ожидалось аргументов: 0", self.output.getvalue())

    def test_exit(self):
        self.assertFalse(self.emulator.execute("exit"))
        self.assertFalse(self.emulator.running)

    def test_vfs_loaded_recursively(self):
        self.assertEqual(self.emulator.vfs.summary(), (3, 2))

    def test_missing_vfs(self):
        with self.assertRaises(ShellError):
            self.emulator.vfs.load(self.root / "missing")

    def test_script_stops_on_error(self):
        script = self.root / "commands.txt"
        script.write_text("echo first\nls\nexit\n", encoding="utf-8")
        with self.assertRaises(ShellError):
            self.emulator.run_script(script)


if __name__ == "__main__":
    unittest.main()
