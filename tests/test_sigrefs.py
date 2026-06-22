"""Tests for gither.sigrefs (verifiable per-peer signed ref sets)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from gither import sigrefs
from gither.peer import PeerIdentity

_REFS = {"refs/heads/main": "a" * 40, "refs/heads/dev": "b" * 40}


def test_sign_and_verify_round_trip() -> None:
    """A peer's signed ref set verifies against its own Node ID."""
    alice = PeerIdentity.generate()
    signed = sigrefs.sign_refs(_REFS, alice)
    assert signed.node_id == alice.node_id()
    assert signed.is_verified()
    assert signed.as_dict() == _REFS


def test_tampered_oid_fails_verification() -> None:
    """Changing any oid after signing breaks verification."""
    alice = PeerIdentity.generate()
    signed = sigrefs.sign_refs(_REFS, alice)
    tampered = sigrefs.SignedRefs(
        node_id=signed.node_id,
        refs=(("refs/heads/main", "c" * 40), ("refs/heads/dev", "b" * 40)),
        signature=signed.signature,
    )
    assert not tampered.is_verified()


def test_cannot_reattribute_to_another_peer() -> None:
    """A signature over one peer's refs does not verify under another Node ID."""
    alice, bob = PeerIdentity.generate(), PeerIdentity.generate()
    signed = sigrefs.sign_refs(_REFS, alice)
    reattributed = sigrefs.SignedRefs(
        node_id=bob.node_id(),
        refs=signed.refs,
        signature=signed.signature,
    )
    assert not reattributed.is_verified()


def test_canonical_bytes_are_order_independent() -> None:
    """Canonical serialization does not depend on dict insertion order."""
    a = sigrefs.canonical_refs_bytes("n", {"refs/heads/main": "1", "refs/heads/dev": "2"})
    b = sigrefs.canonical_refs_bytes("n", {"refs/heads/dev": "2", "refs/heads/main": "1"})
    assert a == b


def test_namespaced_ref_layout() -> None:
    """Each ref is placed under refs/namespaces/<node-id>/…."""
    alice = PeerIdentity.generate()
    signed = sigrefs.sign_refs({"refs/heads/main": "a" * 40}, alice)
    key = f"refs/namespaces/{alice.node_id()}/refs/heads/main"
    assert signed.namespaced() == {key: "a" * 40}


def test_json_round_trip() -> None:
    """Signed refs survive a JSON serialization round trip."""
    alice = PeerIdentity.generate()
    signed = sigrefs.sign_refs(_REFS, alice)
    restored = sigrefs.SignedRefs.from_json(signed.to_json())
    assert restored.is_verified()
    assert restored.as_dict() == _REFS


def test_bad_signature_hex_is_not_verified() -> None:
    """A malformed signature string fails verification without raising."""
    alice = PeerIdentity.generate()
    signed = sigrefs.sign_refs(_REFS, alice)
    broken = sigrefs.SignedRefs(node_id=signed.node_id, refs=signed.refs, signature="zz")
    assert not broken.is_verified()


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_sign_real_repo_refs(tmp_path: Path) -> None:
    """sign_repo_refs reads a real repo's heads and produces a verified set."""
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    for args in (["init", "-q", "-b", "main"], ["commit", "-q", "--allow-empty", "-m", "first"]):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, env={"PATH": __import__("os").environ["PATH"], **env})
    refs = sigrefs.read_git_refs(tmp_path)
    assert "refs/heads/main" in refs
    alice = PeerIdentity.generate()
    signed = sigrefs.sign_repo_refs(tmp_path, alice)
    assert signed.is_verified()
    assert signed.as_dict()["refs/heads/main"] == refs["refs/heads/main"]
