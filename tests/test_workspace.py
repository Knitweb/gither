from pathlib import Path

from forge.workspace import discover_workspace


def test_discover_workspace_finds_git_dirs(tmp_path: Path) -> None:
    repo = tmp_path / "alpha"
    repo.mkdir()
    (repo / ".git").mkdir()
    nested = repo / "ignored"
    nested.mkdir()
    (nested / ".git").mkdir()

    workspace = discover_workspace(tmp_path, name="test")

    assert [item.name for item in workspace.repos] == ["alpha"]
