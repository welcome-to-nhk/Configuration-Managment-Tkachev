"""Независимая проверка этапов 4/5 реальным Cargo, не источник анализатора."""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.errors import AppError
from src.graph import build_graph
from src.order import loading_order
from src.repositories import CargoRepository, index_path

TREE_LINE = re.compile(r"(\d+)([A-Za-z0-9_-]+) v([^ ]+)")


def parse_tree(text):
    """Преобразовать cargo tree --prefix depth --no-dedupe в ребра."""
    edges = {}
    stack = []
    for line in text.splitlines():
        match = TREE_LINE.fullmatch(line.strip())
        if not match:
            raise AppError(f"Непонятная строка cargo tree: {line}")
        depth, name, version = match.groups()
        depth = int(depth)
        node = f"{name}@{version}"
        edges.setdefault(node, set())
        if depth:
            if depth > len(stack):
                raise AppError("Неверная глубина cargo tree")
            edges[stack[depth - 1]].add(node)
        stack[depth:] = [node]
    edges.pop("v24-comparison@0.1.0", None)
    return edges


def edge_set(edges):
    """Набор пар для точного сравнения ребер, включая версии."""
    return {(node, dep) for node, deps in edges.items() for dep in deps}


def prepare_project(directory, name, version):
    """Создать отдельный Cargo-проект для сверки, не меняя исходники."""
    (directory / "src").mkdir(parents=True, exist_ok=True)
    manifest = ('[package]\nname = "v24-comparison"\n'
                'version = "0.1.0"\nedition = "2021"\n'
                f'[dependencies]\n{name} = "={version}"\n')
    (directory / "Cargo.toml").write_text(manifest, encoding="utf-8")
    (directory / "src/main.rs").write_text("fn main() {}\n")
    (directory / "Cargo.lock").unlink(missing_ok=True)


def compare(package, destination, repository):
    """Выполнить cargo tree и сопоставить вершины, ребра и порядок."""
    root = repository.root(package)
    graph = build_graph(repository, root)
    directory = destination / package
    prepare_project(directory, package, root.split("@", 1)[1])
    command = ["cargo", "tree", "--prefix", "depth", "--format", "{p}",
               "--no-dedupe", "--edges", "normal,build", "--target", "all"]
    result = subprocess.run(command, cwd=directory, capture_output=True,
                            text=True, timeout=180, check=True)
    (directory / "cargo-tree.txt").write_text(result.stdout, encoding="utf-8")
    native = parse_tree(result.stdout)
    order = loading_order(graph)
    only_ours = sorted(edge_set(graph.edges) - edge_set(native))
    only_cargo = sorted(edge_set(native) - edge_set(graph.edges))
    violations = [(a, b) for a, b in edge_set(native)
                  if a in order and b in order
                  and order.index(b) >= order.index(a)]
    report = dict(root=root, cargo_only_nodes=sorted(set(native)
                  - set(graph.edges)), analyzer_only_nodes=sorted(
                  set(graph.edges) - set(native)), cargo_only_edges=only_cargo,
                  analyzer_only_edges=only_ours, loading_order=order,
                  order_violations=violations, cargo_command=command)
    target = directory / "comparison.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"Сравнение сохранено: {target}")


def main():
    """Cargo требуется только здесь; основной программе он не нужен."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    parser.add_argument("--repository", default="https://index.crates.io")
    parser.add_argument("--destination", default="out/comparison")
    args = parser.parse_args()
    index_path(args.package)
    if not shutil.which("cargo"):
        raise AppError("Cargo не найден: установите Rust и повторите сверку")
    compare(args.package, Path(args.destination).resolve(),
            CargoRepository(args.repository))


if __name__ == "__main__":
    try:
        main()
    except (AppError, OSError, subprocess.SubprocessError) as error:
        print(f"Ошибка сравнения: {error}", file=sys.stderr)
        sys.exit(1)
