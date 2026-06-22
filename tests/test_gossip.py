"""Tests for gither.gossip (signed announcements + freshness-based merge)."""

from __future__ import annotations

from gither import gossip
from gither.peer import PeerIdentity
from gither.sigrefs import sign_refs

_RID = "rad:zExampleRepoId000000000000000000000000000"
_REFS = {"refs/heads/main": "a" * 40}


def _signed(node: PeerIdentity):
    """Return a signed-ref set for the given node."""
    return sign_refs(_REFS, node)


def test_refs_announcement_sign_and_verify() -> None:
    """A ref announcement verifies against the announcing node."""
    alice = PeerIdentity.generate()
    ann = gossip.announce_refs(_signed(alice), _RID, alice, timestamp=100)
    assert ann.node_id == alice.node_id()
    assert ann.is_verified()


def test_refs_announcement_tamper_fails() -> None:
    """Editing the timestamp or refs_root after signing breaks verification."""
    alice = PeerIdentity.generate()
    ann = gossip.announce_refs(_signed(alice), _RID, alice, timestamp=100)
    bumped = gossip.RefsAnnouncement(ann.node_id, ann.rid, ann.refs_root, 999, ann.signature)
    assert not bumped.is_verified()
    rerooted = gossip.RefsAnnouncement(ann.node_id, ann.rid, "deadbeef", ann.timestamp, ann.signature)
    assert not rerooted.is_verified()


def test_inventory_announcement_sign_and_verify() -> None:
    """An inventory announcement verifies and lists the seeded RIDs."""
    alice = PeerIdentity.generate()
    ann = gossip.announce_inventory((_RID,), alice, timestamp=5)
    assert ann.is_verified()
    assert _RID in ann.rids


def test_refs_root_is_stable_and_content_sensitive() -> None:
    """Equal signed-ref sets share a root; different sets differ."""
    alice, bob = PeerIdentity.generate(), PeerIdentity.generate()
    assert gossip.refs_root(_signed(alice)) == gossip.refs_root(_signed(alice))
    assert gossip.refs_root(sign_refs(_REFS, alice)) != gossip.refs_root(sign_refs({"refs/heads/main": "b" * 40}, alice))


def test_gossip_state_keeps_freshest_refs() -> None:
    """Only a strictly newer, verified ref announcement replaces the stored one."""
    alice = PeerIdentity.generate()
    state = gossip.GossipState()
    old = gossip.announce_refs(_signed(alice), _RID, alice, timestamp=10)
    new = gossip.announce_refs(_signed(alice), _RID, alice, timestamp=20)
    assert state.ingest_refs(old)
    assert state.ingest_refs(new)
    assert not state.ingest_refs(old)  # stale replay rejected
    assert state.refs[(alice.node_id(), _RID)].timestamp == 20


def test_gossip_state_rejects_invalid_announcement() -> None:
    """A forged signature is never ingested."""
    alice = PeerIdentity.generate()
    ann = gossip.announce_refs(_signed(alice), _RID, alice, timestamp=10)
    forged = gossip.RefsAnnouncement(ann.node_id, ann.rid, ann.refs_root, ann.timestamp, "00" * 64)
    state = gossip.GossipState()
    assert not state.ingest_refs(forged)
    assert (alice.node_id(), _RID) not in state.refs


def test_seeders_lists_nodes_advertising_a_repo() -> None:
    """seeders() returns every node whose freshest inventory includes the RID."""
    alice, bob, carol = (PeerIdentity.generate() for _ in range(3))
    state = gossip.GossipState()
    state.ingest_inventory(gossip.announce_inventory((_RID,), alice, timestamp=1))
    state.ingest_inventory(gossip.announce_inventory((_RID, "rad:zOther"), bob, timestamp=1))
    state.ingest_inventory(gossip.announce_inventory(("rad:zOther",), carol, timestamp=1))
    assert state.seeders(_RID) == tuple(sorted((alice.node_id(), bob.node_id())))


def test_inventory_freshness_replaces_older() -> None:
    """A newer inventory replaces an older one for the same node."""
    alice = PeerIdentity.generate()
    state = gossip.GossipState()
    state.ingest_inventory(gossip.announce_inventory((_RID,), alice, timestamp=1))
    assert state.ingest_inventory(gossip.announce_inventory((), alice, timestamp=2))
    assert state.seeders(_RID) == ()


def test_announcement_json_round_trips() -> None:
    """Both announcement types survive JSON serialization and still verify."""
    alice = PeerIdentity.generate()
    refs_ann = gossip.announce_refs(_signed(alice), _RID, alice, timestamp=7)
    inv_ann = gossip.announce_inventory((_RID,), alice, timestamp=7)
    assert gossip.RefsAnnouncement.from_json(refs_ann.to_json()).is_verified()
    assert gossip.InventoryAnnouncement.from_json(inv_ann.to_json()).is_verified()
