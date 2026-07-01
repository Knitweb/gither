import subprocess
from pathlib import Path

from gither.changebook import write_change_note
from gither.review import build_review_pack, review_pack_markdown


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "src").mkdir()
    (repo / "src" / "example.py").write_text(
        '"""Example module."""\n\n'
        "def add(left: int, right: int) -> int:\n"
        '    """Add two integers."""\n'
        "    return left + right\n"
    )
    (repo / "README.md").write_text("# Repo\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, stdout=subprocess.DEVNULL)


def test_review_pack_blocks_dirty_repo_without_change_note(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "README.md").write_text("# Repo\n\nChanged.\n")

    pack = build_review_pack(repo)

    assert pack.ok is False
    assert "dirty repository needs a current Gither change note" in pack.blockers
    assert pack.python_audit.ok is True
    assert pack.to_json()["repo"]["changed_files"] == ["README.md"]


def test_review_pack_accepts_dirty_repo_with_change_note(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "README.md").write_text("# Repo\n\nChanged.\n")
    write_change_note(
        repo_path=repo,
        summary="document review packet",
        why="Gither review state needs portable context",
        tests=("python -m pytest -q",),
        programmer_notes="Review packet composes existing local state.",
    )

    pack = build_review_pack(repo)
    rendered = review_pack_markdown(pack)

    assert pack.ok is True
    assert pack.change_notes[0].summary == "document review packet"
    assert "run recorded test: python -m pytest -q" in pack.suggested_actions
    assert "review: ready" in rendered
    assert "document review packet" in rendered
