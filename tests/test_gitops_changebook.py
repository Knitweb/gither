import json
import subprocess
from pathlib import Path

from gither.changebook import write_change_note
from gither.gitops import snapshot_repo


def test_snapshot_repo_reports_dirty_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    (repo / "code.py").write_text("print('changed')\n")

    snapshot = snapshot_repo(repo)

    assert snapshot.name == "repo"
    assert snapshot.branch in {"main", "master"}
    assert snapshot.dirty is True
    assert snapshot.changed_files == ("code.py",)


def test_write_change_note_records_context(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    (repo / "README.md").write_text("# Repo\n\nChanged.\n")

    note = write_change_note(
        repo_path=repo,
        summary="record code context",
        why="Gither changes must carry programmer background",
        tests=("python -m pytest -q",),
        programmer_notes="The note is versioned with the repository.",
    )
    payload = json.loads(note.read_text())

    assert note.parent == repo / ".gither" / "changes"
    assert payload["summary"] == "record code context"
    assert payload["review_gate"]["requires_python_audit"] is True
    assert payload["diff_name_status"] == ["M\tREADME.md"]


def test_write_change_note_records_untracked_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    (repo / "new.py").write_text("VALUE = 1\n")

    note = write_change_note(
        repo_path=repo,
        summary="record untracked files",
        why="New source files must appear in review context",
        tests=(),
        programmer_notes="Untracked files are treated as additions.",
    )
    payload = json.loads(note.read_text())

    assert "A\tnew.py" in payload["diff_name_status"]
