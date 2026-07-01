import importlib.util

import pytest

from gither.codegraph.analyze import FileAnalysis
from gither.codegraph import store


needs_tree_sitter = pytest.mark.skipif(
    not (
        importlib.util.find_spec("tree_sitter") is not None
        and importlib.util.find_spec("tree_sitter_python") is not None
    ),
    reason="optional tree-sitter packages not installed",
)


@needs_tree_sitter
def test_incremental_snapshot_reuses_unchanged_files(tmp_path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "a.py").write_text(
        "def first():\n"
        "    return 1\n"
    )
    (repo_root / "b.py").write_text(
        "def second():\n"
        "    return 2\n"
    )

    calls: list[str] = []
    real = store.analyze_python_source

    def counting(source: bytes, rel_path: str):
        calls.append(rel_path)
        return real(source, rel_path)

    monkeypatch.setattr(store, "analyze_python_source", counting)

    initial = store.build_repo_snapshot(str(repo_root))
    assert calls == ["a.py", "b.py"]
    assert initial.reanalyzed_paths == ("a.py", "b.py")

    calls.clear()
    (repo_root / "a.py").write_text(
        "def first():\n"
        "    return 1\n\n"
        "def extra():\n"
        "    return 3\n"
    )

    snapshot_path = tmp_path / "snapshot.json"
    store.save_repo_snapshot(initial, snapshot_path)
    previous = store.load_repo_snapshot(snapshot_path)
    updated = store.build_repo_snapshot(str(repo_root), previous=previous)

    assert calls == ["a.py"]
    assert updated.reused_paths == ("b.py",)
    assert updated.reanalyzed_paths == ("a.py",)
    assert updated.stats()["snapshot_files"] == 2


def test_snapshot_roundtrip_is_stable(tmp_path) -> None:
    snapshot = store.RepoSnapshot(
        root=str(tmp_path),
        files=[
            store.FileSnapshot(
                path="main.py",
                mtime_ns=123,
                size=9,
                content_sha="sha256:abc",
                analysis=FileAnalysis(path="main.py"),
            )
        ],
        reused_paths=("main.py",),
        reanalyzed_paths=(),
    )
    snapshot_path = tmp_path / "snapshot.json"
    store.save_repo_snapshot(snapshot, snapshot_path)

    loaded = store.load_repo_snapshot(snapshot_path)
    assert loaded.to_json() == snapshot.to_json()
