"""Gossip announcements — what peers tell each other in gither's P2P forge.

Layer 4a of the Radicle-inspired protocol (see ``docs/P2P_PROTOCOL.md``), building on
:mod:`gither.peer`, :mod:`gither.identity`, and :mod:`gither.sigrefs`.

Radicle nodes gossip two kinds of message:

* **inventory** — the set of repository IDs (RIDs) a node currently seeds;
* **ref announcements** — per repository, the head of the node's signed refs plus a
  timestamp, so peers know whose branches advanced and can fetch the new objects.

Both are signed by the announcing node so a relay cannot forge or alter them, and both
carry a monotonically increasing **timestamp** that lets receivers keep only the freshest
announcement per (node, repo) and ignore stale replays.

This module implements the *message layer* — construction, signing, verification, and the
freshness-based merge a receiver applies (:class:`GossipState`). It is pure and fully
testable; the raw socket transport that carries these messages between hosts (layer 4b) is
deliberately separate and is the only part that needs real multi-node networking.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .peer import PeerIdentity, verify
from .sigrefs import SignedRefs


def _canonical(payload: dict[str, object]) -> bytes:
    """Serialize a payload to canonical JSON bytes (sorted keys, tight separators)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def refs_root(signed: SignedRefs) -> str:
    """Return a stable digest identifying a peer's signed-ref set (its 'head').

    Two peers holding the identical signed-ref set produce the same root, so a ref
    announcement can advertise *which* set the node has without shipping all the refs.
    """
    body = _canonical({"node_id": signed.node_id, "refs": signed.as_dict()})
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True)
class RefsAnnouncement:
    """A signed statement: "node N holds signed-ref set R for repo RID at time T"."""

    node_id: str
    rid: str
    refs_root: str
    timestamp: int
    signature: str

    def _body(self) -> bytes:
        """Canonical signed bytes binding node, repo, ref-root, and timestamp."""
        return _canonical({
            "kind": "refs",
            "node_id": self.node_id,
            "rid": self.rid,
            "refs_root": self.refs_root,
            "timestamp": self.timestamp,
        })

    def is_verified(self) -> bool:
        """Return True iff the announcement's signature verifies against its node."""
        try:
            signature = bytes.fromhex(self.signature)
        except ValueError:
            return False
        return verify(self.node_id, self._body(), signature)

    def to_json(self) -> dict[str, object]:
        """Serialize the announcement to plain JSON data."""
        return {
            "kind": "refs",
            "node_id": self.node_id,
            "rid": self.rid,
            "refs_root": self.refs_root,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "RefsAnnouncement":
        """Build a refs announcement from plain JSON data."""
        return cls(
            node_id=str(value["node_id"]),
            rid=str(value["rid"]),
            refs_root=str(value["refs_root"]),
            timestamp=int(value["timestamp"]),
            signature=str(value["signature"]),
        )


@dataclass(frozen=True)
class InventoryAnnouncement:
    """A signed statement: "node N seeds these RIDs as of time T"."""

    node_id: str
    rids: tuple[str, ...]
    timestamp: int
    signature: str

    def _body(self) -> bytes:
        """Canonical signed bytes binding node, sorted RID set, and timestamp."""
        return _canonical({
            "kind": "inventory",
            "node_id": self.node_id,
            "rids": sorted(self.rids),
            "timestamp": self.timestamp,
        })

    def is_verified(self) -> bool:
        """Return True iff the announcement's signature verifies against its node."""
        try:
            signature = bytes.fromhex(self.signature)
        except ValueError:
            return False
        return verify(self.node_id, self._body(), signature)

    def to_json(self) -> dict[str, object]:
        """Serialize the announcement to plain JSON data."""
        return {
            "kind": "inventory",
            "node_id": self.node_id,
            "rids": list(self.rids),
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "InventoryAnnouncement":
        """Build an inventory announcement from plain JSON data."""
        return cls(
            node_id=str(value["node_id"]),
            rids=tuple(str(item) for item in value.get("rids", ())),
            timestamp=int(value["timestamp"]),
            signature=str(value["signature"]),
        )


def announce_refs(signed: SignedRefs, rid: str, signer: PeerIdentity, timestamp: int) -> RefsAnnouncement:
    """Build a signed ref announcement for the node's signed-ref set of a repository."""
    ann = RefsAnnouncement(
        node_id=signer.node_id(),
        rid=rid,
        refs_root=refs_root(signed),
        timestamp=int(timestamp),
        signature="",
    )
    return RefsAnnouncement(ann.node_id, ann.rid, ann.refs_root, ann.timestamp, signer.sign(ann._body()).hex())


def announce_inventory(rids: tuple[str, ...], signer: PeerIdentity, timestamp: int) -> InventoryAnnouncement:
    """Build a signed inventory announcement for the RIDs a node seeds."""
    ann = InventoryAnnouncement(signer.node_id(), tuple(rids), int(timestamp), "")
    return InventoryAnnouncement(ann.node_id, ann.rids, ann.timestamp, signer.sign(ann._body()).hex())


@dataclass
class GossipState:
    """A receiver's view of the freshest *verified* announcement per (node, repo).

    Ingesting an announcement keeps it only if it verifies and is newer than what is
    already stored for that key, which is how a gossip network converges while ignoring
    forged or replayed (stale) messages.
    """

    refs: dict[tuple[str, str], RefsAnnouncement] = field(default_factory=dict)
    inventory: dict[str, InventoryAnnouncement] = field(default_factory=dict)

    def ingest_refs(self, ann: RefsAnnouncement) -> bool:
        """Ingest a ref announcement; return True iff it was accepted as fresher."""
        if not ann.is_verified():
            return False
        key = (ann.node_id, ann.rid)
        current = self.refs.get(key)
        if current is not None and ann.timestamp <= current.timestamp:
            return False
        self.refs[key] = ann
        return True

    def ingest_inventory(self, ann: InventoryAnnouncement) -> bool:
        """Ingest an inventory announcement; return True iff it was accepted as fresher."""
        if not ann.is_verified():
            return False
        current = self.inventory.get(ann.node_id)
        if current is not None and ann.timestamp <= current.timestamp:
            return False
        self.inventory[ann.node_id] = ann
        return True

    def seeders(self, rid: str) -> tuple[str, ...]:
        """Return the node IDs currently advertising that they seed a given RID."""
        return tuple(sorted(node for node, ann in self.inventory.items() if rid in ann.rids))
