"""Versioned change note writer for Gither-managed repositories."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from .gitops import diff_name_status, snapshot_repo

SLUG_RE = re.compile(r"[^a-z0-9]+")


def write_change_note(
    repo_path: Path,
    summary: str,
    why: str,
    tests: tuple[str, ...],
    programmer_notes: str,
) -> Path:
    """Write a versioned change note that belongs in the repository."""
    snapshot = snapshot_repo(repo_path)
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    slug = SLUG_RE.sub("-", summary.lower()).strip("-")[:60] or "change"
    note_dir = repo_path.resolve() / ".gither" / "changes"
    note_dir.mkdir(parents=True, exist_ok=True)
    note_path = note_dir / f"{timestamp}-{slug}.json"
    payload = {
        "summary": summary,
        "why": why,
        "programmer_notes": programmer_notes,
        "tests": list(tests),
        "created_at": timestamp,
        "repo": snapshot.to_json(),
        "diff_name_status": list(diff_name_status(repo_path)),
        "review_gate": {
            "requires_code_context": True,
            "requires_tests": True,
            "requires_python_audit": True,
            "requires_human_review_for_public_release": True,
        },
    }
    note_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return note_path
