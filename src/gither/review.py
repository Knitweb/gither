"""Portable review packets for Gither-managed code changes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .audit import PythonAudit, audit_python
from .gitops import RepoSnapshot, snapshot_repo


@dataclass(frozen=True)
class ChangeNoteSummary:
    """Small, review-facing projection of a Gither change note."""

    path: str
    summary: str
    why: str
    created_at: str
    tests: tuple[str, ...]
    diff_name_status: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        """Serialize the summary to JSON-compatible data."""
        return {
            "path": self.path,
            "summary": self.summary,
            "why": self.why,
            "created_at": self.created_at,
            "tests": list(self.tests),
            "diff_name_status": list(self.diff_name_status),
        }


@dataclass(frozen=True)
class ReviewPack:
    """Complete local review context for a repository state."""

    repo: RepoSnapshot
    python_audit: PythonAudit
    change_notes: tuple[ChangeNoteSummary, ...]
    blockers: tuple[str, ...]
    suggested_actions: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return whether the packet is ready for human review."""
        return not self.blockers

    def to_json(self) -> dict[str, object]:
        """Serialize the review packet to plain JSON."""
        return {
            "kind": "gither_review_pack",
            "ok": self.ok,
            "repo": self.repo.to_json(),
            "python_audit": self.python_audit.to_json(),
            "change_notes": [note.to_json() for note in self.change_notes],
            "blockers": list(self.blockers),
            "suggested_actions": list(self.suggested_actions),
        }


def build_review_pack(
    repo_path: Path,
    python_root: str = "src",
    max_change_notes: int = 5,
) -> ReviewPack:
    """Build a portable review packet from Git state, audit state, and notes."""
    repo = repo_path.resolve()
    snapshot = snapshot_repo(repo)
    audit_root = repo / python_root
    audit = audit_python(audit_root if audit_root.exists() else repo)
    change_notes = load_change_note_summaries(repo, limit=max_change_notes)
    blockers = _review_blockers(snapshot, audit, change_notes)
    return ReviewPack(
        repo=snapshot,
        python_audit=audit,
        change_notes=change_notes,
        blockers=blockers,
        suggested_actions=_suggested_actions(snapshot, audit, change_notes, blockers),
    )


def load_change_note_summaries(repo_path: Path, limit: int = 5) -> tuple[ChangeNoteSummary, ...]:
    """Load the newest Gither change notes as compact review summaries."""
    notes_dir = repo_path.resolve() / ".gither" / "changes"
    if not notes_dir.exists():
        return ()
    summaries: list[ChangeNoteSummary] = []
    for path in sorted(notes_dir.glob("*.json"), reverse=True):
        if len(summaries) >= limit:
            break
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        summaries.append(
            ChangeNoteSummary(
                path=str(path.relative_to(repo_path.resolve())),
                summary=str(payload.get("summary", "")),
                why=str(payload.get("why", "")),
                created_at=str(payload.get("created_at", "")),
                tests=tuple(str(item) for item in payload.get("tests", ())),
                diff_name_status=tuple(str(item) for item in payload.get("diff_name_status", ())),
            )
        )
    return tuple(summaries)


def review_pack_markdown(pack: ReviewPack) -> str:
    """Render a review packet as concise Markdown for a PR or handoff."""
    repo = pack.repo
    lines = [
        "# Gither Review Pack",
        "",
        f"repo: {repo.name}",
        f"path: {repo.path}",
        f"branch: {repo.branch}",
        f"head: {repo.head[:12]}",
        f"dirty: {str(repo.dirty).lower()}",
        f"python audit: {'ok' if pack.python_audit.ok else 'issues'}",
        f"review: {'ready' if pack.ok else 'blocked'}",
        "",
        "## Changed Files",
    ]
    lines.extend(_list_lines(repo.changed_files))
    lines.extend(["", "## Blockers"])
    lines.extend(_list_lines(pack.blockers))
    lines.extend(["", "## Latest Change Notes"])
    if pack.change_notes:
        for note in pack.change_notes:
            tests = ", ".join(note.tests) if note.tests else "none"
            lines.append(f"- {note.created_at or 'undated'}: {note.summary} ({tests})")
    else:
        lines.append("- none")
    lines.extend(["", "## Suggested Actions"])
    lines.extend(_list_lines(pack.suggested_actions))
    lines.append("")
    return "\n".join(lines)


def _review_blockers(
    snapshot: RepoSnapshot,
    audit: PythonAudit,
    change_notes: tuple[ChangeNoteSummary, ...],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if audit.syntax_errors:
        blockers.append("python syntax errors must be fixed")
    if not audit.ok:
        blockers.append("python audit must pass")
    if snapshot.dirty and not _change_notes_cover_dirty_state(snapshot, change_notes):
        blockers.append("dirty repository needs a current Gither change note")
    return tuple(dict.fromkeys(blockers))


def _suggested_actions(
    snapshot: RepoSnapshot,
    audit: PythonAudit,
    change_notes: tuple[ChangeNoteSummary, ...],
    blockers: tuple[str, ...],
) -> tuple[str, ...]:
    actions: list[str] = []
    if snapshot.dirty and not _change_notes_cover_dirty_state(snapshot, change_notes):
        actions.append("run gither change-note with summary, reason, tests, and programmer notes")
    if not audit.ok:
        actions.append("fix Python audit issues or narrow --python-root to the changed source tree")
    if change_notes:
        tests = sorted({test for note in change_notes for test in note.tests})
        actions.extend(f"run recorded test: {test}" for test in tests)
    if not blockers:
        actions.append("attach this review pack to the human review or PR")
    return tuple(actions)


def _change_notes_cover_dirty_state(
    snapshot: RepoSnapshot,
    change_notes: tuple[ChangeNoteSummary, ...],
) -> bool:
    reviewable_changes = {
        path for path in snapshot.changed_files if not path.startswith(".gither/")
    }
    if not reviewable_changes:
        return True
    noted_changes = {
        _path_from_name_status(row)
        for note in change_notes
        for row in note.diff_name_status
    }
    return reviewable_changes.issubset(noted_changes)


def _path_from_name_status(row: str) -> str:
    if "\t" not in row:
        return row
    return row.split("\t", 1)[1]


def _list_lines(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]
