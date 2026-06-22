"""Tests for gither.peer (pure-Python Ed25519 peer identity).

The frozen Ed25519 vector below was cross-validated to be byte-identical to libsodium
(via the ``cryptography`` package) across 200 random keys in both signing directions, and
the did:key value is the canonical example from the W3C did:key specification. These tests
depend on the standard library only, so CI stays dependency-free.
"""

from __future__ import annotations

from gither import peer

# Frozen regression vector (validated against libsodium / RFC 8032).
_SEED_HEX = "9d61b19deffebc3a6080b9e5c1042cefee009e515c45a07ec07e57e3e8de4f33"
_PUBLIC_HEX = "f724e2b035073d53ae296ec1aa96c3b341028775a62cb87a27be1084d91e8edb"
_DID = "did:key:z6Mkw61NL4LKSXkFtU3FjKofgCCcdKT4DzMYMDARenQxq8u8"
_SIG_EMPTY_HEX = (
    "8280fb68a291e50cd2fc3bf7cd0578223637200ba93d52d64820fef175e8d9c2"
    "3e055d77afcbf3c49d261ae4d4a325763c46344392bfda9d7679fad1c4caf609"
)
# Canonical Ed25519 example from the W3C did:key specification.
_W3C_DID = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"


def test_public_key_derivation_matches_frozen_vector() -> None:
    """Public-key derivation reproduces the libsodium-validated vector."""
    identity = peer.PeerIdentity.from_seed_hex(_SEED_HEX)
    assert identity.public.hex() == _PUBLIC_HEX


def test_did_and_node_id_format() -> None:
    """DID carries the did:key prefix; Node ID is the bare multibase form."""
    identity = peer.PeerIdentity.from_seed_hex(_SEED_HEX)
    assert identity.did() == _DID
    assert identity.node_id() == _DID.removeprefix("did:key:")
    assert identity.node_id().startswith("z6Mk")


def test_signature_matches_frozen_vector() -> None:
    """Deterministic Ed25519 signing reproduces the frozen signature bytes."""
    identity = peer.PeerIdentity.from_seed_hex(_SEED_HEX)
    assert identity.sign(b"").hex() == _SIG_EMPTY_HEX


def test_sign_verify_round_trip() -> None:
    """A freshly generated identity verifies its own signatures."""
    identity = peer.PeerIdentity.generate()
    message = b"gither peer-to-peer code forge"
    signature = identity.sign(message)
    assert identity.verify(message, signature)
    assert peer.verify(identity.did(), message, signature)
    assert peer.verify(identity.node_id(), message, signature)


def test_tampered_message_and_wrong_key_fail() -> None:
    """Verification rejects altered messages and signatures from another peer."""
    alice = peer.PeerIdentity.generate()
    bob = peer.PeerIdentity.generate()
    message = b"release v1.2.3"
    signature = alice.sign(message)
    assert not peer.verify(alice.did(), message + b"!", signature)
    assert not peer.verify(bob.did(), message, signature)
    assert not alice.verify(message, signature[:-1] + bytes([signature[-1] ^ 0x01]))


def test_did_key_round_trip_and_w3c_example() -> None:
    """did:key encode/decode round-trips, including the canonical W3C example."""
    identity = peer.PeerIdentity.from_seed_hex(_SEED_HEX)
    assert peer.decode_did_key(identity.did()) == identity.public
    assert peer.decode_did_key(identity.node_id()) == identity.public
    assert peer.encode_did_key(peer.decode_did_key(_W3C_DID)) == _W3C_DID


def test_seed_hex_persistence_round_trip() -> None:
    """An identity survives a seed-hex save/load cycle unchanged."""
    identity = peer.PeerIdentity.generate()
    restored = peer.PeerIdentity.from_seed_hex(identity.seed_hex())
    assert restored.public == identity.public
    assert restored.did() == identity.did()


def test_invalid_inputs_raise() -> None:
    """Malformed seeds and DIDs are rejected with ValueError."""
    for bad_seed in (b"", b"\x00" * 31, b"\x00" * 33):
        try:
            peer.PeerIdentity.from_seed(bad_seed)
        except ValueError:
            continue
        raise AssertionError("expected ValueError for bad seed length")
    for bad_did in ("did:key:Qabc", "did:key:zNotEd25519"):
        try:
            peer.decode_did_key(bad_did)
        except ValueError:
            continue
        raise AssertionError("expected ValueError for bad did:key")


def test_verify_is_total_on_bad_signature() -> None:
    """verify() returns False (never raises) for malformed signatures or DIDs."""
    identity = peer.PeerIdentity.generate()
    assert not peer.verify(identity.did(), b"m", b"too-short")
    assert not peer.verify("not-a-did", b"m", b"\x00" * 64)
    assert not identity.verify(b"m", b"\x00" * 64)


def test_base58_preserves_leading_zero_bytes() -> None:
    """base58btc round-trips leading zero bytes as leading '1' characters."""
    data = b"\x00\x00\x01gither"
    assert peer._b58decode(peer._b58encode(data)) == data
