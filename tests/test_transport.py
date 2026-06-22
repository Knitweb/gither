"""Tests for gither.transport (loopback gossip exchange + bundle ingest)."""

from __future__ import annotations

from gither import gossip, transport
from gither.peer import PeerIdentity
from gither.sigrefs import sign_refs

_RID = "rad:zExampleRepoId000000000000000000000000000"


def _peer_bundle(node: PeerIdentity, oid: str, ts: int) -> dict[str, object]:
    """Build a wire bundle of one ref + one inventory announcement for a node."""
    signed = sign_refs({"refs/heads/main": oid}, node)
    refs = gossip.announce_refs(signed, _RID, node, timestamp=ts)
    inv = gossip.announce_inventory((_RID,), node, timestamp=ts)
    return transport.make_bundle((refs,), (inv,))


def test_two_node_loopback_exchange() -> None:
    """Two peers swap bundles over loopback and each ends up with the other's refs."""
    alice, bob = PeerIdentity.generate(), PeerIdentity.generate()
    server = transport.GossipPeer(state=gossip.GossipState(), local_bundle=_peer_bundle(bob, "b" * 40, 1), timeout=5.0)
    client = transport.GossipPeer(state=gossip.GossipState(), local_bundle=_peer_bundle(alice, "a" * 40, 1), timeout=5.0)

    thread, port = server.serve_once()
    accepted_from_server = client.exchange_with(port)
    thread.join(timeout=5.0)
    assert not thread.is_alive()

    # client ingested bob's announcement; server ingested alice's
    assert accepted_from_server >= 1
    assert (bob.node_id(), _RID) in client.state.refs
    assert (alice.node_id(), _RID) in server.state.refs
    assert bob.node_id() in client.state.seeders(_RID)
    assert alice.node_id() in server.state.seeders(_RID)


def test_ingest_bundle_skips_malformed_entries() -> None:
    """A bundle with junk entries ingests the good ones and ignores the rest."""
    alice = PeerIdentity.generate()
    good = _peer_bundle(alice, "a" * 40, 1)
    good["refs"].append({"not": "an announcement"})
    good["inventory"].append("garbage")
    state = gossip.GossipState()
    accepted = transport.ingest_bundle(state, good)
    assert accepted == 2  # one valid refs + one valid inventory
    assert (alice.node_id(), _RID) in state.refs


def test_forged_announcement_in_bundle_is_rejected() -> None:
    """A tampered announcement carried over the wire is not accepted."""
    alice = PeerIdentity.generate()
    bundle = _peer_bundle(alice, "a" * 40, 1)
    bundle["refs"][0]["refs_root"] = "deadbeef"  # invalidates the signature
    state = gossip.GossipState()
    accepted = transport.ingest_bundle(state, bundle)
    assert accepted == 1  # only the inventory announcement survives
    assert (alice.node_id(), _RID) not in state.refs


def test_make_bundle_shape() -> None:
    """make_bundle produces JSON-serializable refs/inventory lists."""
    alice = PeerIdentity.generate()
    bundle = _peer_bundle(alice, "a" * 40, 1)
    assert set(bundle) == {"refs", "inventory"}
    assert bundle["refs"][0]["kind"] == "refs"
    assert bundle["inventory"][0]["kind"] == "inventory"
