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
    changed_files = tuple(_status_path(line) for line in _status_lines(repo))
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
    return tuple(_status_name_row(line) for line in _status_lines(repo))


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


def _status_lines(repo: Path) -> tuple[str, ...]:
    return tuple(line for line in run_git(repo, ["status", "--porcelain"]).splitlines() if line)


def _status_path(line: str) -> str:
    return line[3:]


def _status_name_row(line: str) -> str:
    code = line[:2]
    path = _status_path(line)
    if code == "??":
        return f"A\t{path}"
    if "D" in code:
        return f"D\t{path}"
    if "R" in code:
        return f"R\t{path}"
    if "A" in code:
        return f"A\t{path}"
    return f"M\t{path}"
