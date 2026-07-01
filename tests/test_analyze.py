"""Tests for the Phase-2 tree-sitter analyzer.

These exercise the real tree-sitter bindings on small source fixtures so they
fail loudly if the analyzer drifts. They are skipped automatically when the
optional tree-sitter packages are not installed, so the core suite stays green
in a dependency-free environment (the project ships ``dependencies = []``).
"""

import importlib.util

import pytest

from gither.codegraph.analyze import analyze_python_repo, analyze_python_source


def _has_tree_sitter() -> bool:
    return importlib.util.find_spec("tree_sitter") is not None and (
        importlib.util.find_spec("tree_sitter_python") is not None
    )


needs_tree_sitter = pytest.mark.skipif(
    not _has_tree_sitter(), reason="optional tree-sitter packages not installed"
)


SAMPLE = b"""\
import os
from collections import defaultdict


def add(a, b):
    return a + b


class Calculator:
    def run(self):
        return add(1, 2)


def main():
    add(1, 2)
    os.getcwd()
    print(add)
"""


@needs_tree_sitter
def test_definitions_split_functions_and_classes() -> None:
    analysis = analyze_python_source(SAMPLE, "sample.py")
    kinds = {d.name: d.kind for d in analysis.definitions}
    assert kinds["add"] == "function"
    assert kinds["Calculator"] == "class"
    assert kinds["run"] == "function"
    assert kinds["main"] == "function"


@needs_tree_sitter
def test_calls_carry_caller_context() -> None:
    analysis = analyze_python_source(SAMPLE, "sample.py")
    edges = {(c.caller, c.callee) for c in analysis.calls}
    assert ("run", "add") in edges
    assert ("main", "add") in edges
    assert ("<module>", "add") not in edges  # add is always inside a function


@needs_tree_sitter
def test_imports_captured_without_fromimport_bodies() -> None:
    analysis = analyze_python_source(SAMPLE, "sample.py")
    modules = {i.module for i in analysis.imports}
    assert "os" in modules
    assert "collections" in modules  # from collections import ... -> top package


@needs_tree_sitter
def test_resolution_marks_intra_repo_calls(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "a.py").write_bytes(SAMPLE)
    repo = analyze_python_repo(str(repo_root))
    stats = repo.stats()
    assert stats["definitions"] == 4
    assert stats["calls"] >= 4
    # 'add' is defined in the same batch, so calls to it must resolve.
    resolved_add = [
        c for fa in repo.files for c in fa.calls if c.callee == "add" and c.resolved
    ]
    assert resolved_add, "intra-repo call to add() should resolve"


def test_missing_tree_sitter_raises_clear_error(monkeypatch) -> None:
    if not _has_tree_sitter():
        pytest.skip("only meaningful when tree-sitter is present to mask")
    import sys

    # Make both optional modules unimportable for this test.
    monkeypatch.setitem(sys.modules, "tree_sitter", None)
    monkeypatch.setitem(sys.modules, "tree_sitter_python", None)
    real_find = importlib.util.find_spec

    def fake_find(name, *args, **kwargs):
        if name in ("tree_sitter", "tree_sitter_python"):
            raise ModuleNotFoundError(name)
        return real_find(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find)
    with pytest.raises(RuntimeError, match="optional tree-sitter"):
        analyze_python_source(b"x = 1", "x.py")
