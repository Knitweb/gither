import json
import subprocess
from pathlib import Path

from gither.cli import main
from gither.models import RepoSpec, Workspace
from gither.p2p import build_p2p_manifest, verify_p2p_manifest


def _init_repo(path: Path) -> str:
    path.mkdir()
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    (path / "README.md").write_text("# Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, check=True, stdout=subprocess.DEVNULL)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def test_build_p2p_manifest_records_repo_identity_refs_and_ids(tmp_path: Path) -> None:
    repo = tmp_path / "alpha"
    head = _init_repo(repo)
    workspace = Workspace(
        name="test",
        repos=(
            RepoSpec(
                name="alpha",
                path=str(repo),
                remote="git@example.invalid:alpha.git",
                roles=("code forge",),
                keywords=("alpha", "p2p"),
            ),
        ),
    )

    manifest = build_p2p_manifest(workspace, generated_at="2026-07-01T00:00:00Z")
    report = verify_p2p_manifest(manifest)

    assert report.ok
    assert manifest["schema"] == "gither.p2p.repo-manifest.v1"
    assert manifest["manifestId"].startswith("sha256:")
    record = manifest["records"][0]
    assert record["identity"]["remote"] == "git@example.invalid:alpha.git"
    assert record["state"]["available"] is True
    assert record["state"]["head"] == head
    assert {"kind": "head", "name": record["state"]["branch"], "oid": head} in record["state"]["refs"]
    assert record["recordId"].startswith("sha256:")
    assert record["repoId"].startswith("sha256:")
    assert record["stateId"].startswith("sha256:")


def test_p2p_manifest_includes_missing_repos_as_catalog_records(tmp_path: Path) -> None:
    workspace = Workspace(
        name="test",
        repos=(RepoSpec(name="missing", path=str(tmp_path / "missing"), optional=True),),
    )

    manifest = build_p2p_manifest(workspace, generated_at="2026-07-01T00:00:00Z")
    record = manifest["records"][0]

    assert verify_p2p_manifest(manifest).ok
    assert record["state"]["available"] is False
    assert record["state"]["reason"] == "path does not exist"


def test_p2p_manifest_verification_detects_tampering(tmp_path: Path) -> None:
    repo = tmp_path / "alpha"
    _init_repo(repo)
    manifest = build_p2p_manifest(
        Workspace(name="test", repos=(RepoSpec(name="alpha", path=str(repo)),)),
        generated_at="2026-07-01T00:00:00Z",
    )

    manifest["records"][0]["state"]["head"] = "0" * 40

    report = verify_p2p_manifest(manifest)
    assert not report.ok
    assert any("stateId mismatch" in error for error in report.errors)
    assert any("recordId mismatch" in error for error in report.errors)
    assert any("manifestId does not match" in error for error in report.errors)


def test_p2p_manifest_cli_export_and_verify(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "alpha"
    _init_repo(repo)
    workspace = tmp_path / "workspace.json"
    output = tmp_path / "manifest.json"
    workspace.write_text(json.dumps({
        "workspace": "test",
        "repos": [{"name": "alpha", "path": str(repo)}],
    }))

    assert main(["p2p-manifest", "--workspace", str(workspace), "--output", str(output)]) == 0
    summary = capsys.readouterr().out
    assert "1 repos" in summary
    assert output.exists()

    assert main(["p2p-verify", "--manifest", str(output), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True
    assert report["record_count"] == 1
