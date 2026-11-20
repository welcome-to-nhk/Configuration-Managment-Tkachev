"""Автономно продемонстрировать пять этапов и три Cargo-пакета."""

import contextlib
import functools
import http.server
import io
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ["crc32fast", "miniz_oxide", "itoa"]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Не засорять протокол демонстрации HTTP-логами."""

    def log_message(self, *args):
        """Отключить служебные сообщения HTTP-сервера."""


@contextlib.contextmanager
def sparse_server():
    """Временный loopback HTTP-сервер, автоматически закрывающийся."""
    handler = functools.partial(QuietHandler,
                                directory=str(ROOT / "examples/sparse"))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def execute(arguments, log, expected=0):
    """Запустить реальный CLI и проверить ожидаемый exit code."""
    command = [sys.executable, "-m", "src", *arguments]
    result = subprocess.run(command, cwd=ROOT, text=True,
                            capture_output=True, timeout=30)
    text = result.stdout + result.stderr
    log.write("$ python -m src " + " ".join(arguments) + "\n")
    log.write(text + f"exit_code={result.returncode}\n\n")
    print(text, end="")
    if result.returncode != expected:
        raise RuntimeError(f"Ожидался код {expected}, получен "
                           f"{result.returncode}")


def letter_examples(log):
    """Показать все пять этапов, фильтр, цикл и отдельную вершину."""
    base = ["--package", "A", "--test", "--repository", "examples/diamond.json"]
    for stage in range(1, 6):
        execute(base + ["--stage", str(stage)], log)
    for name in ["chain", "cycle", "self", "isolated", "filter"]:
        args = ["--package", "A", "--test", "--repository",
                f"examples/{name}.json"]
        execute(args + ["--stage", "3"], log)
        execute(args + ["--stage", "4"], log,
                expected=1 if name in {"cycle", "self"} else 0)
        execute(args + ["--output", f"out/{name}.svg"], log)
    execute(["--package", "A", "--test", "--repository",
             "examples/filter.json", "--filter", "X", "--stage", "3"], log)


def main():
    """Создать SVG/PlantUML и проверяемый журнал реальных запусков."""
    (ROOT / "out").mkdir(exist_ok=True)
    log = io.StringIO()
    letter_examples(log)
    with sparse_server() as url:
        for package in PACKAGES:
            base = ["--package", package, "--repository", url]
            execute(base + ["--stage", "2"], log)
            execute(base + ["--stage", "4"], log)
            execute(base + ["--output", f"out/{package}.svg"], log)
    path = ROOT / "out/demo-log.txt"
    path.write_text(log.getvalue(), encoding="utf-8")
    print(f"Готово. Протокол: {path}")


if __name__ == "__main__":
    main()
