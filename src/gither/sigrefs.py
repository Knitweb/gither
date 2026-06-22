"""Signed refs — verifiable per-peer ref publication for gither's P2P forge.

This is layer 3 of the Radicle-inspired protocol (see ``docs/P2P_PROTOCOL.md``), building on
:mod:`gither.peer` and :mod:`gither.identity`.

In a server-free network you cannot trust a relay to tell you the truth about another
peer's branches — it could forge a ref, roll one back, or reattribute it. Radicle solves
this by having every peer publish its refs under its own namespace
(``refs/namespaces/<node-id>/…``) and **sign the exact ``{refname: oid}`` set it claims to
hold** (its ``rad/sigrefs``). A receiver verifies that signature against the publisher's
Node ID before trusting any ref.

This module ports that: :class:`SignedRefs` binds a node's Node ID, its ref set, and an
Ed25519 signature over the canonical bytes of *both*, so the set is tamper-evident and
cannot be reattributed to another peer's namespace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .gitops import run_git
from .peer import PeerIdentity, verify

_NAMESPACE_PREFIX = "refs/namespaces/"


def namespaced_ref(node_id: str, refname: str) -> str:
    """Return a ref placed under a peer's namespace (``refs/namespaces/<node-id>/…``)."""
    return f"{_NAMESPACE_PREFIX}{node_id}/{refname}"


def read_git_refs(repo: Path, pattern: str = "refs/heads/") -> dict[str, str]:
    """Read ``{refname: oid}`` from a git repository via ``git for-each-ref``."""
    out = run_git(repo, ["for-each-ref", "--format=%(refname) %(objectname)", pattern])
    refs: dict[str, str] = {}
    for line in out.splitlines():
        if not line.strip():
            continue
        refname, _, oid = line.partition(" ")
        refs[refname] = oid
    return refs


def canonical_refs_bytes(node_id: str, refs: dict[str, str]) -> bytes:
    """Serialize (node_id, refs) to canonical JSON bytes for signing/verification.

    Refs are sorted by name so the bytes are reproducible regardless of input order, and
    the node_id is bound in so a signature cannot be replayed under another namespace.
    """
    payload = {"node_id": node_id, "refs": dict(sorted(refs.items()))}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True)
class SignedRefs:
    """A peer's signed ``{refname: oid}`` set (its ``rad/sigrefs`` equivalent)."""

    node_id: str
    refs: tuple[tuple[str, str], ...]
    signature: str  # hex Ed25519 signature over canonical_refs_bytes

    def as_dict(self) -> dict[str, str]:
        """Return the ref set as an ordinary ``{refname: oid}`` dictionary."""
        return dict(self.refs)

    def is_verified(self) -> bool:
        """Return True iff the signature verifies against this peer's Node ID."""
        body = canonical_refs_bytes(self.node_id, self.as_dict())
        try:
            signature = bytes.fromhex(self.signature)
        except ValueError:
            return False
        return verify(self.node_id, body, signature)

    def namespaced(self) -> dict[str, str]:
        """Return the ref set with each name placed under this peer's namespace."""
        return {namespaced_ref(self.node_id, name): oid for name, oid in self.refs}

    def to_json(self) -> dict[str, object]:
        """Serialize the signed refs to plain JSON data."""
        return {
            "node_id": self.node_id,
            "refs": dict(self.refs),
            "signature": self.signature,
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "SignedRefs":
        """Build signed refs from plain JSON data."""
        refs = {str(k): str(v) for k, v in dict(value.get("refs", {})).items()}
        return cls(
            node_id=str(value["node_id"]),
            refs=tuple(sorted(refs.items())),
            signature=str(value["signature"]),
        )


def sign_refs(refs: dict[str, str], signer: PeerIdentity) -> SignedRefs:
    """Sign a ``{refname: oid}`` set with a peer identity, returning :class:`SignedRefs`."""
    node_id = signer.node_id()
    signature = signer.sign(canonical_refs_bytes(node_id, refs)).hex()
    return SignedRefs(node_id=node_id, refs=tuple(sorted(refs.items())), signature=signature)


def sign_repo_refs(repo: Path, signer: PeerIdentity, pattern: str = "refs/heads/") -> SignedRefs:
    """Read a repository's refs and return a signed ref set for the given peer."""
    return sign_refs(read_git_refs(repo, pattern), signer)
