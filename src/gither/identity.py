"""Repository identity and content-addressed Repository IDs (RIDs) for gither.

This is layer 2 of the Radicle-inspired peer-to-peer forge (see ``docs/P2P_PROTOCOL.md``),
building on :mod:`gither.peer`.

A repository's identity is a small signed document — name, description, the **delegates**
(peer DIDs allowed to update the canonical identity) and a signing **threshold**. The
**Repository ID (RID)** is the content address of that document: ``rad:z…``, a multibase
base58btc-encoded SHA-256 of the canonical document bytes. Because it is derived from the
content (not a host or path), the RID is stable and globally unique, so a repository keeps
one identity as it moves between peers, mirrors, and static sites.

Radicle anchors its RID on a git object id; gither anchors on a SHA-256 of the canonical
JSON document. The property that matters is identical: content-addressed, location-free
repository identity. Updates to the identity require a threshold of valid delegate
signatures, so no single peer can unilaterally rewrite who controls a repository.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .peer import PeerIdentity, _b58encode, decode_did_key, verify

_RID_PREFIX = "rad:"
_MULTIBASE_BASE58BTC = "z"


@dataclass(frozen=True)
class IdentityDoc:
    """The canonical identity document for a repository.

    ``delegates`` are the peer DIDs allowed to sign identity updates; ``threshold`` is the
    number of distinct delegate signatures required for an update to be accepted.
    """

    name: str
    description: str
    delegates: tuple[str, ...]
    threshold: int = 1

    def __post_init__(self) -> None:
        """Validate the delegate set and threshold are internally consistent."""
        if not self.name:
            raise ValueError("identity name must not be empty")
        if not self.delegates:
            raise ValueError("identity must have at least one delegate")
        if len(set(self.delegates)) != len(self.delegates):
            raise ValueError("delegates must be unique")
        if not 1 <= self.threshold <= len(self.delegates):
            raise ValueError("threshold must be between 1 and the number of delegates")

    def canonical_bytes(self) -> bytes:
        """Serialize to canonical JSON bytes (sorted keys, tight separators, UTF-8).

        The same document always produces the same bytes, so the RID and any signatures
        over it are reproducible on every peer.
        """
        payload = {
            "name": self.name,
            "description": self.description,
            "delegates": list(self.delegates),
            "threshold": self.threshold,
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def rid(self) -> str:
        """Return the content-addressed Repository ID (``rad:z…``).

        The payload is the SHA-256 of the canonical document bytes, multibase base58btc
        encoded with the ``z`` prefix — the same ``rad:z<base58>`` shape Radicle uses.
        """
        digest = hashlib.sha256(self.canonical_bytes()).digest()
        return _RID_PREFIX + _MULTIBASE_BASE58BTC + _b58encode(digest)

    def to_json(self) -> dict[str, object]:
        """Serialize the document to plain JSON data (for display / storage)."""
        return {
            "name": self.name,
            "description": self.description,
            "delegates": list(self.delegates),
            "threshold": self.threshold,
            "rid": self.rid(),
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "IdentityDoc":
        """Build an identity document from plain JSON data."""
        return cls(
            name=str(value["name"]),
            description=str(value.get("description", "")),
            delegates=tuple(str(item) for item in value.get("delegates", ())),
            threshold=int(value.get("threshold", 1)),
        )


@dataclass(frozen=True)
class SignedIdentity:
    """An identity document together with delegate signatures over its canonical bytes."""

    doc: IdentityDoc
    signatures: tuple[tuple[str, str], ...]  # (delegate DID, hex signature)

    def to_json(self) -> dict[str, object]:
        """Serialize the signed identity to plain JSON data."""
        return {
            "doc": self.doc.to_json(),
            "signatures": [{"did": did, "sig": sig} for did, sig in self.signatures],
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "SignedIdentity":
        """Build a signed identity from plain JSON data."""
        sigs = tuple((str(item["did"]), str(item["sig"])) for item in value.get("signatures", ()))
        return cls(doc=IdentityDoc.from_json(dict(value["doc"])), signatures=sigs)

    def valid_signature_count(self) -> int:
        """Count distinct delegates whose signature over the document verifies."""
        delegates = set(self.doc.delegates)
        seen: set[str] = set()
        body = self.doc.canonical_bytes()
        for did, sig_hex in self.signatures:
            if did not in delegates or did in seen:
                continue
            try:
                signature = bytes.fromhex(sig_hex)
            except ValueError:
                continue
            if verify(did, body, signature):
                seen.add(did)
        return len(seen)

    def is_verified(self) -> bool:
        """Return True iff enough distinct delegates signed to meet the threshold."""
        return self.valid_signature_count() >= self.doc.threshold


def sign_identity(doc: IdentityDoc, signer: PeerIdentity) -> tuple[str, str]:
    """Sign an identity document, returning the signer's ``(DID, hex signature)`` pair.

    Raises ``ValueError`` if the signer is not one of the document's delegates.
    """
    did = signer.did()
    if did not in doc.delegates:
        raise ValueError("signer is not a delegate of this identity")
    return did, signer.sign(doc.canonical_bytes()).hex()


def collect_signatures(doc: IdentityDoc, signers: tuple[PeerIdentity, ...]) -> SignedIdentity:
    """Sign a document with several delegate identities and bundle the signatures."""
    return SignedIdentity(doc=doc, signatures=tuple(sign_identity(doc, s) for s in signers))


def is_valid_did(did: str) -> bool:
    """Return True iff a string is a decodable did:key / Node ID."""
    try:
        decode_did_key(did)
    except ValueError:
        return False
    return True
