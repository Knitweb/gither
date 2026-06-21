"""Python source audit for Gither review gates."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SymbolAudit:
    """Audit result for one Python module, class, or public function."""

    file: str
    kind: str
    name: str
    line: int
    has_docstring: bool
    missing_annotations: tuple[str, ...]
    body_lines: int

    @property
    def ok(self) -> bool:
        """Return whether this symbol satisfies the local quality gate."""
        return self.has_docstring and not self.missing_annotations and self.body_lines <= 80

    def to_json(self) -> dict[str, object]:
        """Serialize the symbol audit to plain JSON data."""
        return {
            "file": self.file,
            "kind": self.kind,
            "name": self.name,
            "line": self.line,
            "has_docstring": self.has_docstring,
            "missing_annotations": list(self.missing_annotations),
            "body_lines": self.body_lines,
            "ok": self.ok,
        }


@dataclass(frozen=True)
class PythonAudit:
    """Audit result for a Python source tree."""

    root: str
    files_checked: int
    symbols: tuple[SymbolAudit, ...]
    syntax_errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return whether the source tree passed all audit checks."""
        return not self.syntax_errors and all(symbol.ok for symbol in self.symbols)

    def to_json(self) -> dict[str, object]:
        """Serialize the source-tree audit to plain JSON data."""
        return {
            "root": self.root,
            "files_checked": self.files_checked,
            "ok": self.ok,
            "syntax_errors": list(self.syntax_errors),
            "symbols": [symbol.to_json() for symbol in self.symbols],
        }


def audit_python(root: Path) -> PythonAudit:
    """Audit Python source files under root."""
    base = root.resolve()
    symbols: list[SymbolAudit] = []
    syntax_errors: list[str] = []
    files = sorted(path for path in base.rglob("*.py") if _is_source_path(path))
    for path in files:
        rel = str(path.relative_to(base))
        try:
            tree = ast.parse(path.read_text(), filename=rel)
        except SyntaxError as exc:
            syntax_errors.append(f"{rel}:{exc.lineno}: {exc.msg}")
            continue
        symbols.extend(_audit_tree(rel, tree))
    return PythonAudit(
        root=str(base),
        files_checked=len(files),
        symbols=tuple(symbols),
        syntax_errors=tuple(syntax_errors),
    )


def _audit_tree(filename: str, tree: ast.AST) -> list[SymbolAudit]:
    found: list[SymbolAudit] = []
    if isinstance(tree, ast.Module):
        found.append(
            SymbolAudit(
                file=filename,
                kind="module",
                name=filename,
                line=1,
                has_docstring=bool(ast.get_docstring(tree)),
                missing_annotations=(),
                body_lines=_body_lines(tree),
            )
        )
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            found.append(
                SymbolAudit(
                    file=filename,
                    kind="class",
                    name=node.name,
                    line=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    missing_annotations=(),
                    body_lines=_body_lines(node),
                )
            )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            missing = _missing_function_annotations(node)
            found.append(
                SymbolAudit(
                    file=filename,
                    kind="function",
                    name=node.name,
                    line=node.lineno,
                    has_docstring=bool(ast.get_docstring(node)),
                    missing_annotations=missing,
                    body_lines=_body_lines(node),
                )
            )
    return found


def _missing_function_annotations(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    missing: list[str] = []
    args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    for arg in args:
        if arg.arg in {"self", "cls"}:
            continue
        if arg.annotation is None:
            missing.append(arg.arg)
    if node.args.vararg and node.args.vararg.annotation is None:
        missing.append(node.args.vararg.arg)
    if node.args.kwarg and node.args.kwarg.annotation is None:
        missing.append(node.args.kwarg.arg)
    if node.returns is None:
        missing.append("return")
    return tuple(missing)


def _body_lines(node: ast.AST) -> int:
    lineno = getattr(node, "lineno", 1)
    end_lineno = getattr(node, "end_lineno", lineno)
    return max(1, int(end_lineno) - int(lineno) + 1)


def _is_source_path(path: Path) -> bool:
    ignored = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist"}
    return not any(part in ignored for part in path.parts)
