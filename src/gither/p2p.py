"""Peer-to-peer repository manifests for Gither.

The manifest is intentionally transport-neutral: it can be copied as a file,
served from a static site, pinned in a p2p store, or carried by a gossip layer.
Git remains the object store; Gither makes the repo catalog, refs, and review
metadata content-addressable so GitHub/GitLab are mirrors, not authorities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .gitops import snapshot_repo
from .models import RepoSpec, Workspace

REPO_RECORD_SCHEMA = "gither.p2p.repo-record.v1"
MANIFEST_SCHEMA = "gither.p2p.repo-manifest.v1"


@dataclass(frozen=True)
class P2PManifestReport:
    """Verification result for a p2p repo manifest."""

    ok: bool
    manifest_id: str | None
    record_count: int
    errors: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        """Serialize the verification report to JSON."""

        return {
            "ok": self.ok,
            "manifest_id": self.manifest_id,
            "record_count": self.record_count,
            "errors": list(self.errors),
        }


def canonical_bytes(value: Any) -> bytes:
    """Return deterministic JSON bytes for manifest hashing."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def content_id(value: Any) -> str:
    """Return a stable Gither content id for a JSON-compatible value."""

    return f"sha256:{hashlib.sha256(canonical_bytes(value)).hexdigest()}"


def now_utc() -> str:
    """Return a compact UTC timestamp for generated manifests."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_repo_record(repo: RepoSpec) -> dict[str, Any]:
    """Build a p2p repository record from a workspace repository entry."""

    identity = {
        "name": repo.name,
        "remote": repo.remote,
        "roles": list(repo.roles),
        "keywords": list(repo.keywords),
        "docs": list(repo.docs),
        "optional": repo.optional,
    }
    repo_id = content_id({"schema": "gither.p2p.repo-identity.v1", **identity})
    path = Path(repo.path)
    if path.exists():
        try:
            snapshot = snapshot_repo(path)
            state = {
                "available": True,
                "path": snapshot.path,
                "branch": snapshot.branch,
                "head": snapshot.head,
                "dirty": snapshot.dirty,
                "changedFiles": list(snapshot.changed_files),
                "remotes": list(snapshot.remotes),
                "refs": _git_refs(path),
            }
        except Exception as exc:  # defensive: a catalog peer should keep partial state
            state = {
                "available": False,
                "path": str(path),
                "reason": str(exc),
                "refs": [],
            }
    else:
        state = {
            "available": False,
            "path": str(path),
            "reason": "path does not exist",
            "refs": [],
        }
    state_id = content_id({"schema": "gither.p2p.repo-state.v1", "repoId": repo_id, **state})
    body = {
        "schema": REPO_RECORD_SCHEMA,
        "repoId": repo_id,
        "identity": identity,
        "stateId": state_id,
        "state": state,
        "mirrorPolicy": {
            "authority": "gither",
            "git": "object-store-and-transport",
            "github": "optional-mirror",
            "p2p": "content-addressed-repo-state",
        },
    }
    return {**body, "recordId": content_id(body)}


def build_p2p_manifest(workspace: Workspace, *, generated_at: str | None = None) -> dict[str, Any]:
    """Build a content-addressed p2p manifest for every repo in ``workspace``."""

    records = [build_repo_record(repo) for repo in workspace.repos]
    body = {
        "schema": MANIFEST_SCHEMA,
        "workspace": workspace.name,
        "generatedAt": generated_at or now_utc(),
        "count": len(records),
        "records": records,
    }
    return {**body, "manifestId": content_id(body)}


def verify_p2p_manifest(manifest: dict[str, Any]) -> P2PManifestReport:
    """Verify manifest and record content ids without touching the network."""

    errors: list[str] = []
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest schema mismatch")
    records = manifest.get("records")
    if not isinstance(records, list):
        errors.append("records must be a list")
        records = []
    if manifest.get("count") != len(records):
        errors.append("count does not match records length")
    manifest_body = {key: value for key, value in manifest.items() if key != "manifestId"}
    expected_manifest_id = content_id(manifest_body)
    if manifest.get("manifestId") != expected_manifest_id:
        errors.append("manifestId does not match canonical content")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} is not an object")
            continue
        prefix = f"record {index} ({record.get('identity', {}).get('name', 'unknown')})"
        if record.get("schema") != REPO_RECORD_SCHEMA:
            errors.append(f"{prefix}: schema mismatch")
        record_body = {key: value for key, value in record.items() if key != "recordId"}
        if record.get("recordId") != content_id(record_body):
            errors.append(f"{prefix}: recordId mismatch")
        identity = record.get("identity")
        if not isinstance(identity, dict):
            errors.append(f"{prefix}: missing identity")
            continue
        expected_repo_id = content_id({"schema": "gither.p2p.repo-identity.v1", **identity})
        if record.get("repoId") != expected_repo_id:
            errors.append(f"{prefix}: repoId mismatch")
        state = record.get("state")
        if not isinstance(state, dict):
            errors.append(f"{prefix}: missing state")
            continue
        expected_state_id = content_id(
            {"schema": "gither.p2p.repo-state.v1", "repoId": record.get("repoId"), **state}
        )
        if record.get("stateId") != expected_state_id:
            errors.append(f"{prefix}: stateId mismatch")
        _validate_git_state(prefix, state, errors)
    return P2PManifestReport(
        ok=not errors,
        manifest_id=manifest.get("manifestId") if isinstance(manifest.get("manifestId"), str) else None,
        record_count=len(records),
        errors=tuple(errors),
    )


def write_p2p_manifest(path: Path, manifest: dict[str, Any]) -> Path:
    """Write a p2p manifest to disk as stable JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return path


def load_p2p_manifest(path: Path) -> dict[str, Any]:
    """Read a p2p manifest JSON file."""

    return json.loads(path.read_text())


def _git_refs(path: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "show-ref", "--heads", "--tags"],
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=5,
    )
    refs: list[dict[str, str]] = []
    if result.returncode not in {0, 1}:
        return refs
    for line in result.stdout.splitlines():
        oid, ref = line.split(" ", 1)
        if ref.startswith("refs/heads/"):
            kind = "head"
            name = ref.removeprefix("refs/heads/")
        elif ref.startswith("refs/tags/"):
            kind = "tag"
            name = ref.removeprefix("refs/tags/")
        else:
            kind = "ref"
            name = ref
        refs.append({"kind": kind, "name": name, "oid": oid})
    return sorted(refs, key=lambda item: (item["kind"], item["name"], item["oid"]))


def _validate_git_state(prefix: str, state: dict[str, Any], errors: list[str]) -> None:
    if not isinstance(state.get("available"), bool):
        errors.append(f"{prefix}: state.available must be boolean")
    head = state.get("head")
    if state.get("available") and not _is_git_oid(head):
        errors.append(f"{prefix}: head is not a Git object id")
    refs = state.get("refs")
    if not isinstance(refs, list):
        errors.append(f"{prefix}: refs must be a list")
        return
    for ref_index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            errors.append(f"{prefix}: ref {ref_index} is not an object")
            continue
        if ref.get("kind") not in {"head", "tag", "ref"}:
            errors.append(f"{prefix}: ref {ref_index} has invalid kind")
        if not isinstance(ref.get("name"), str) or not ref.get("name"):
            errors.append(f"{prefix}: ref {ref_index} has invalid name")
        if not _is_git_oid(ref.get("oid")):
            errors.append(f"{prefix}: ref {ref_index} oid is not a Git object id")


def _is_git_oid(value: Any) -> bool:
    return isinstance(value, str) and len(value) in {40, 64} and all(ch in "0123456789abcdef" for ch in value)
