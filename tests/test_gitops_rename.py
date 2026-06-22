"""Regression: git-status parsing must handle renames and paths with spaces.

The old `line[3:]` newline-porcelain parse returned the literal "old -> new" for a rename and
git-quoted paths with spaces. The `--porcelain -z` parse returns the destination path, unquoted.
"""

import subprocess
from pathlib import Path

from gither.gitops import diff_name_status, snapshot_repo


def _init(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=repo, check=True)


def _commit(repo: Path, msg: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=repo, check=True, stdout=subprocess.DEVNULL)


def test_rename_reports_destination_path_not_arrow(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init(repo)
    (repo / "old.py").write_text("x = 1\n")
    _commit(repo, "initial")
    subprocess.run(["git", "mv", "old.py", "new.py"], cwd=repo, check=True)

    snap = snapshot_repo(repo)
    assert snap.changed_files == ("new.py",), snap.changed_files          # destination, no " -> "
    assert all(" -> " not in f for f in snap.changed_files)
    assert diff_name_status(repo) == ("R\tnew.py",)


def test_path_with_spaces_is_unquoted(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init(repo)
    (repo / "seed.py").write_text("x = 0\n")
    _commit(repo, "initial")  # need a HEAD for snapshot_repo's rev-parse
    (repo / "a file.py").write_text("x = 1\n")  # space in the name → git would quote in newline mode

    snap = snapshot_repo(repo)
    assert snap.changed_files == ("a file.py",), snap.changed_files       # unquoted, exact
    assert diff_name_status(repo) == ("A\ta file.py",)
