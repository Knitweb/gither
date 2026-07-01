"""Phase 2: tree-sitter backed code analysis.

Phase 1 gave us multilingual *bridges* (same task, many languages) from the
clean Rosetta corpus. Phase 2 adds *depth*: real call-edges, definitions and
imports within real repositories (postgres, spark, dbt, polars, ...).

Design constraints:

- tree-sitter is an **optional** dependency. The project keeps
  ``dependencies = []`` in ``pyproject.toml``. ``analyze_source`` imports
  tree-sitter lazily and raises a clear error if it is missing, so the core
  graph code never breaks for users who do not need Phase-2 depth.
- The analyzer emits the same content-addressed record style as Phase 1 so the
  two layers compose into one graph.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

from .models import content_hash


@dataclass(frozen=True)
class Definition:
    """A named entity defined in a source file."""

    name: str
    kind: str  # function | class
    file: str
    start_line: int
    end_line: int

    @property
    def id(self) -> str:
        """Content address for the definition record."""
        return content_hash(f"DEF\n{self.kind}:{self.file}:{self.name}:{self.start_line}")

    def to_json(self) -> dict[str, object]:
        """Serialize the definition to a content-addressed JSON record."""
        return {
            "id": self.id,
            "kind": "definition",
            "name": self.name,
            "entity_kind": self.kind,
            "file": self.file,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }


@dataclass(frozen=True)
class CallEdge:
    """An edge from a caller definition to a called name.

    ``resolved`` is True when the called name matches a Definition in the same
    analysis batch (intra-repo call). Unresolved calls are kept too: they may
    be stdlib, third-party, or cross-module calls Phase-3 will resolve.
    """

    caller: str
    callee: str
    file: str
    line: int
    resolved: bool = False

    @property
    def id(self) -> str:
        """Content address for the call-edge record."""
        return content_hash(f"CALL\n{self.file}:{self.line}:{self.caller}->{self.callee}")

    def to_json(self) -> dict[str, object]:
        """Serialize the call edge to a content-addressed JSON record."""
        return {
            "id": self.id,
            "kind": "call_edge",
            "caller": self.caller,
            "callee": self.callee,
            "file": self.file,
            "line": self.line,
            "resolved": self.resolved,
        }


@dataclass(frozen=True)
class ImportEdge:
    """An import / dependency edge."""

    module: str
    file: str
    line: int
    imported_names: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        """Content address for the import-edge record."""
        return content_hash(f"IMPORT\n{self.file}:{self.line}:{self.module}")

    def to_json(self) -> dict[str, object]:
        """Serialize the import edge to a content-addressed JSON record."""
        return {
            "id": self.id,
            "kind": "import_edge",
            "module": self.module,
            "file": self.file,
            "line": self.line,
            "imported_names": list(self.imported_names),
        }


@dataclass
class FileAnalysis:
    """All Phase-2 records extracted from one source file."""

    path: str
    definitions: list[Definition] = field(default_factory=list)
    calls: list[CallEdge] = field(default_factory=list)
    imports: list[ImportEdge] = field(default_factory=list)


@dataclass
class RepoAnalysis:
    """Aggregated Phase-2 analysis across a repository."""

    root: str
    files: list[FileAnalysis] = field(default_factory=list)

    def all_definitions(self) -> list[Definition]:
        """Flatten every file's definitions into one list."""
        out: list[Definition] = []
        for fa in self.files:
            out.extend(fa.definitions)
        return out

    def resolve_calls(self) -> None:
        """Mark calls whose callee matches a known definition as resolved."""
        names = {d.name for d in self.all_definitions()}
        for fa in self.files:
            for index, call in enumerate(fa.calls):
                if call.callee in names:
                    fa.calls[index] = CallEdge(
                        caller=call.caller,
                        callee=call.callee,
                        file=call.file,
                        line=call.line,
                        resolved=True,
                    )

    def stats(self) -> dict[str, object]:
        """Return aggregate definition, call, import, and resolution counts."""
        defs = self.all_definitions()
        calls = [c for fa in self.files for c in fa.calls]
        imports = [i for fa in self.files for i in fa.imports]
        resolved = sum(1 for c in calls if c.resolved)
        return {
            "files": len(self.files),
            "definitions": len(defs),
            "calls": len(calls),
            "imports": len(imports),
            "resolved_calls": resolved,
            "resolution_rate": round(resolved / len(calls), 3) if calls else 0.0,
        }


def _require_tree_sitter() -> tuple[object, object, object]:
    """Lazily import tree-sitter; raise a clear error if it is absent.

    Returns ``(parser, language, QueryCursor_factory)``. The QueryCursor is the
    0.25+ API; older bindings exposed ``Query.captures`` directly, which we do
    not target.
    """
    try:
        import tree_sitter as ts  # type: ignore
        from tree_sitter_python import language as py_language  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Phase-2 analysis needs the optional tree-sitter packages. "
            "Install them with: pip install tree-sitter tree-sitter-python"
        ) from exc
    language = ts.Language(py_language())
    parser = ts.Parser(language)
    return parser, language, ts


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _containing_function(node, source: bytes) -> str:
    """Walk up to find the enclosing function/method name, or ``<module>``."""
    cur = node.parent
    while cur is not None:
        if cur.type == "function_definition":
            for child in cur.children:
                if child.type == "identifier":
                    return _node_text(child, source)
        cur = cur.parent
    return "<module>"


def analyze_python_source(source: bytes, rel_path: str) -> FileAnalysis:
    """Analyze one Python source file into Phase-2 records."""
    parser, language, ts = _require_tree_sitter()
    tree = parser.parse(source)
    root = tree.root_node
    analysis = FileAnalysis(path=rel_path)

    # Definitions (functions and classes).
    q_def = ts.Query(
        language,
        "(function_definition name: (identifier) @fn.name)"
        "(class_definition name: (identifier) @cls.name)",
    )
    for _pattern, captures in ts.QueryCursor(q_def).matches(root):
        if "fn.name" in captures:
            node = captures["fn.name"][0]
            def_node = node.parent
            analysis.definitions.append(
                Definition(
                    name=_node_text(node, source),
                    kind="function",
                    file=rel_path,
                    start_line=def_node.start_point[0] + 1,
                    end_line=def_node.end_point[0] + 1,
                )
            )
        elif "cls.name" in captures:
            node = captures["cls.name"][0]
            def_node = node.parent
            analysis.definitions.append(
                Definition(
                    name=_node_text(node, source),
                    kind="class",
                    file=rel_path,
                    start_line=def_node.start_point[0] + 1,
                    end_line=def_node.end_point[0] + 1,
                )
            )

    # Calls (plain identifiers and attribute accesses).
    q_call = ts.Query(
        language,
        "(call function: (identifier) @call.name)"
        "(call function: (attribute attribute: (identifier) @call.attr))",
    )
    for _pattern, captures in ts.QueryCursor(q_call).matches(root):
        node = captures.get("call.name", captures.get("call.attr", [None]))[0]
        if node is None:
            continue
        callee = _node_text(node, source)
        caller = _containing_function(node, source)
        analysis.calls.append(
            CallEdge(
                caller=caller,
                callee=callee,
                file=rel_path,
                line=node.start_point[0] + 1,
            )
        )

    # Imports.
    q_import = ts.Query(
        language,
        "(import_statement name: (dotted_name) @imp.mod)"
        "(import_from_statement module_name: (dotted_name) @imp.mod)",
    )
    for _pattern, captures in ts.QueryCursor(q_import).matches(root):
        nodes = captures.get("imp.mod", [])
        for node in nodes:
            analysis.imports.append(
                ImportEdge(
                    module=_node_text(node, source),
                    file=rel_path,
                    line=node.start_point[0] + 1,
                )
            )
    return analysis


def analyze_python_repo(root: str, glob: str = "**/*.py") -> RepoAnalysis:
    """Walk a repository and analyze every Python file."""
    base = pathlib.Path(root)
    repo = RepoAnalysis(root=str(base))
    files = sorted(p for p in base.glob(glob) if p.is_file())
    for path in files:
        try:
            source = path.read_bytes()
        except OSError:
            continue
        rel = str(path.relative_to(base))
        repo.files.append(analyze_python_source(source, rel))
    repo.resolve_calls()
    return repo
