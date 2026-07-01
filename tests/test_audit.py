import ast

from gither.audit import SymbolAudit, _audit_tree


def test_symbol_audit_uses_kind_specific_line_limits() -> None:
    large_class = SymbolAudit(
        file="sample.py",
        kind="class",
        name="Client",
        line=1,
        has_docstring=True,
        missing_annotations=(),
        body_lines=120,
    )
    large_function = SymbolAudit(
        file="sample.py",
        kind="function",
        name="run",
        line=1,
        has_docstring=True,
        missing_annotations=(),
        body_lines=120,
    )

    assert large_class.ok is True
    assert large_function.ok is False


def test_audit_tree_keeps_public_method_docstrings_required() -> None:
    tree = ast.parse(
        '"""Module."""\n\n'
        "class Client:\n"
        '    """Client."""\n\n'
        "    def run(self) -> None:\n"
        "        pass\n"
    )

    symbols = _audit_tree("sample.py", tree)
    run = next(symbol for symbol in symbols if symbol.name == "run")

    assert run.has_docstring is False
    assert run.ok is False
