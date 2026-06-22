"""Git-backed repository operations used by Gither."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoSnapshot:
    """Point-in-time repository state used by review gates."""

    path: str
    name: str
    branch: str
    head: str
    dirty: bool
    changed_files: tuple[str, ...]
    remotes: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        """Serialize the snapshot to plain JSON data."""
        return {
            "path": self.path,
            "name": self.name,
            "branch": self.branch,
            "head": self.head,
            "dirty": self.dirty,
            "changed_files": list(self.changed_files),
            "remotes": list(self.remotes),
        }


def snapshot_repo(path: Path) -> RepoSnapshot:
    """Create a reviewable snapshot of a Git repository."""
    repo = path.resolve()
    ensure_git_repo(repo)
    changed_files = tuple(path for _, path in _status_entries(repo))
    return RepoSnapshot(
        path=str(repo),
        name=repo.name,
        branch=run_git(repo, ["branch", "--show-current"]) or "detached",
        head=run_git(repo, ["rev-parse", "HEAD"]),
        dirty=bool(changed_files),
        changed_files=changed_files,
        remotes=tuple(line for line in run_git(repo, ["remote", "-v"]).splitlines() if line),
    )


def diff_name_status(path: Path) -> tuple[str, ...]:
    """Return name-status rows for tracked and untracked changes."""
    repo = path.resolve()
    ensure_git_repo(repo)
    return tuple(_status_name_row(code, path) for code, path in _status_entries(repo))


def ensure_git_repo(path: Path) -> None:
    """Raise a ValueError when path is not inside a Git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"{path} is not a Git repository")


def run_git(path: Path, args: list[str]) -> str:
    """Run a Git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.rstrip("\n")


def _status_entries(repo: Path) -> tuple[tuple[str, str], ...]:
    """Parse ``git status --porcelain -z`` into ``(code, path)`` pairs.

    The ``-z`` format is NUL-separated and does NOT quote paths with spaces (unlike the default
    newline porcelain). For a rename/copy the record is ``XY <dest>\\0<orig>\\0``, so we take the
    destination and consume the paired original field — fixing the prior ``line[3:]`` which returned
    the literal ``"old -> new"`` for renames and embedded quotes for spaced paths.
    """
    raw = run_git(repo, ["status", "--porcelain", "-z"])
    fields = raw.split("\0")
    entries: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        rec = fields[i]
        if not rec:
            i += 1
            continue
        code, path = rec[:2], rec[3:]
        if ("R" in code or "C" in code) and i + 1 < len(fields):
            i += 2  # the next field is the original path; `path` is the destination
        else:
            i += 1
        entries.append((code, path))
    return tuple(entries)


def _status_name_row(code: str, path: str) -> str:
    if code == "??":
        return f"A\t{path}"
    if "D" in code:
        return f"D\t{path}"
    if "R" in code:
        return f"R\t{path}"
    if "C" in code:
        return f"C\t{path}"
    if "A" in code:
        return f"A\t{path}"
    return f"M\t{path}"
