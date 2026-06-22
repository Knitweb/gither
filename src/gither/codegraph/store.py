"""Incremental repository snapshots for the Gither code graph.

The tree-sitter analyzer is deterministic, but a full rescan on every commit is
still wasteful. This module keeps a small JSON snapshot with per-file
fingerprints so unchanged files can be reused without re-analysis.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass, field

from .analyze import CallEdge, Definition, FileAnalysis, ImportEdge, RepoAnalysis, analyze_python_source


@dataclass(frozen=True)
class FileSnapshot:
    """One file's fingerprint and cached analysis."""

    path: str
    mtime_ns: int
    size: int
    content_sha: str
    analysis: FileAnalysis

    @property
    def id(self) -> str:
        """Stable record identifier for the file snapshot."""
        return self.content_sha

    def to_json(self) -> dict[str, object]:
        """Serialize the file snapshot to plain JSON."""
        return {
            "id": self.id,
            "kind": "file_snapshot",
            "path": self.path,
            "mtime_ns": self.mtime_ns,
            "size": self.size,
            "content_sha": self.content_sha,
            "analysis": file_analysis_to_json(self.analysis),
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "FileSnapshot":
        """Rebuild a file snapshot from JSON."""
        return cls(
            path=str(value["path"]),
            mtime_ns=int(value["mtime_ns"]),
            size=int(value["size"]),
            content_sha=str(value["content_sha"]),
            analysis=file_analysis_from_json(value["analysis"]),
        )


@dataclass
class RepoSnapshot:
    """Incremental codegraph snapshot for one repository."""

    root: str
    files: list[FileSnapshot] = field(default_factory=list)
    reused_paths: tuple[str, ...] = ()
    reanalyzed_paths: tuple[str, ...] = ()

    def analysis(self) -> RepoAnalysis:
        """Return the aggregated repo analysis for this snapshot."""
        repo = RepoAnalysis(root=self.root)
        repo.files = [file.analysis for file in self.files]
        repo.resolve_calls()
        return repo

    def stats(self) -> dict[str, object]:
        """Return aggregate counts for the current snapshot."""
        stats = self.analysis().stats()
        stats.update(
            {
                "snapshot_files": len(self.files),
                "reused_files": len(self.reused_paths),
                "reanalyzed_files": len(self.reanalyzed_paths),
            }
        )
        return stats

    def to_json(self) -> dict[str, object]:
        """Serialize the snapshot to JSON."""
        return {
            "kind": "repo_snapshot",
            "root": self.root,
            "files": [file.to_json() for file in self.files],
            "reused_paths": list(self.reused_paths),
            "reanalyzed_paths": list(self.reanalyzed_paths),
            "stats": self.stats(),
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "RepoSnapshot":
        """Rebuild a repository snapshot from JSON."""
        files = [FileSnapshot.from_json(item) for item in value.get("files", [])]
        return cls(
            root=str(value["root"]),
            files=files,
            reused_paths=tuple(str(item) for item in value.get("reused_paths", ())),
            reanalyzed_paths=tuple(str(item) for item in value.get("reanalyzed_paths", ())),
        )


def load_repo_snapshot(path: pathlib.Path) -> RepoSnapshot:
    """Load a snapshot from a JSON file."""
    return RepoSnapshot.from_json(json.loads(path.read_text()))


def save_repo_snapshot(snapshot: RepoSnapshot, path: pathlib.Path) -> None:
    """Write a snapshot to disk as stable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_json(), indent=2, sort_keys=True) + "\n")


def build_repo_snapshot(root: str, glob: str = "**/*.py", previous: RepoSnapshot | None = None) -> RepoSnapshot:
    """Analyze a repository incrementally and return the new snapshot."""
    base = pathlib.Path(root)
    previous_index = {item.path: item for item in previous.files} if previous else {}
    files: list[FileSnapshot] = []
    reused_paths: list[str] = []
    reanalyzed_paths: list[str] = []

    for path in sorted((p for p in base.glob(glob) if p.is_file()), key=lambda item: str(item.relative_to(base))):
        rel = str(path.relative_to(base))
        stat = path.stat()
        content = path.read_bytes()
        content_sha = hashlib.sha256(content).hexdigest()
        previous_file = previous_index.get(rel)
        if (
            previous_file
            and previous_file.mtime_ns == stat.st_mtime_ns
            and previous_file.size == stat.st_size
            and previous_file.content_sha == content_sha
        ):
            analysis = file_analysis_from_json(file_analysis_to_json(previous_file.analysis))
            reused_paths.append(rel)
        else:
            analysis = analyze_python_source(content, rel)
            reanalyzed_paths.append(rel)
        files.append(
            FileSnapshot(
                path=rel,
                mtime_ns=stat.st_mtime_ns,
                size=stat.st_size,
                content_sha=content_sha,
                analysis=analysis,
            )
        )

    return RepoSnapshot(
        root=str(base.resolve()),
        files=files,
        reused_paths=tuple(reused_paths),
        reanalyzed_paths=tuple(reanalyzed_paths),
    )


def file_analysis_to_json(analysis: FileAnalysis) -> dict[str, object]:
    """Serialize a file analysis to JSON-compatible data."""
    return {
        "path": analysis.path,
        "definitions": [definition.to_json() for definition in analysis.definitions],
        "calls": [call.to_json() for call in analysis.calls],
        "imports": [item.to_json() for item in analysis.imports],
    }


def file_analysis_from_json(value: dict[str, object]) -> FileAnalysis:
    """Rebuild a file analysis from JSON-compatible data."""
    return FileAnalysis(
        path=str(value["path"]),
        definitions=[definition_from_json(item) for item in value.get("definitions", [])],
        calls=[call_from_json(item) for item in value.get("calls", [])],
        imports=[import_from_json(item) for item in value.get("imports", [])],
    )


def definition_from_json(value: dict[str, object]) -> Definition:
    """Rebuild a definition record from JSON-compatible data."""
    return Definition(
        name=str(value["name"]),
        kind=str(value["entity_kind"]),
        file=str(value["file"]),
        start_line=int(value["start_line"]),
        end_line=int(value["end_line"]),
    )


def call_from_json(value: dict[str, object]) -> CallEdge:
    """Rebuild a call edge from JSON-compatible data."""
    return CallEdge(
        caller=str(value["caller"]),
        callee=str(value["callee"]),
        file=str(value["file"]),
        line=int(value["line"]),
        resolved=bool(value.get("resolved", False)),
    )


def import_from_json(value: dict[str, object]) -> ImportEdge:
    """Rebuild an import edge from JSON-compatible data."""
    return ImportEdge(
        module=str(value["module"]),
        file=str(value["file"]),
        line=int(value["line"]),
        imported_names=tuple(str(item) for item in value.get("imported_names", ())),
    )
