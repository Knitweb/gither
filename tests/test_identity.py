"""Tests for gither.identity (content-addressed RIDs + delegate threshold signing)."""

from __future__ import annotations

from gither import identity
from gither.peer import PeerIdentity


def _doc(delegates: tuple[str, ...], threshold: int = 1) -> identity.IdentityDoc:
    """Build a sample identity document for the given delegates and threshold."""
    return identity.IdentityDoc(
        name="gither",
        description="serverless p2p code forge",
        delegates=delegates,
        threshold=threshold,
    )


def test_rid_is_deterministic_and_well_formed() -> None:
    """The same document always yields the same rad:z… RID."""
    alice = PeerIdentity.generate().did()
    doc1 = _doc((alice,))
    doc2 = _doc((alice,))
    assert doc1.rid() == doc2.rid()
    assert doc1.rid().startswith("rad:z")


def test_rid_changes_with_content() -> None:
    """Any change to the document content changes the content-addressed RID."""
    alice = PeerIdentity.generate().did()
    base = _doc((alice,)).rid()
    renamed = identity.IdentityDoc("other", "serverless p2p code forge", (alice,)).rid()
    assert base != renamed


def test_canonical_bytes_are_stable_regardless_of_field_order() -> None:
    """Canonical serialization is independent of how the doc was constructed."""
    alice = PeerIdentity.generate().did()
    doc = _doc((alice,))
    assert doc.canonical_bytes() == identity.IdentityDoc.from_json(doc.to_json()).canonical_bytes()


def test_single_delegate_sign_and_verify() -> None:
    """A threshold-1 identity verifies once its sole delegate signs."""
    alice = PeerIdentity.generate()
    doc = _doc((alice.did(),))
    signed = identity.collect_signatures(doc, (alice,))
    assert signed.is_verified()
    assert signed.valid_signature_count() == 1


def test_threshold_requires_enough_delegates() -> None:
    """A 2-of-3 identity is unverified with one signature, verified with two."""
    alice, bob, carol = (PeerIdentity.generate() for _ in range(3))
    dids = (alice.did(), bob.did(), carol.did())
    doc = _doc(dids, threshold=2)
    one = identity.collect_signatures(doc, (alice,))
    assert not one.is_verified()
    two = identity.collect_signatures(doc, (alice, bob))
    assert two.is_verified()
    assert two.valid_signature_count() == 2


def test_non_delegate_cannot_sign() -> None:
    """Signing raises if the signer is not listed as a delegate."""
    alice = PeerIdentity.generate()
    stranger = PeerIdentity.generate()
    doc = _doc((alice.did(),))
    try:
        identity.sign_identity(doc, stranger)
    except ValueError:
        return
    raise AssertionError("expected ValueError for non-delegate signer")


def test_tampered_document_fails_verification() -> None:
    """A signature over the original doc does not verify against a modified doc."""
    alice = PeerIdentity.generate()
    doc = _doc((alice.did(),))
    sig = identity.sign_identity(doc, alice)
    forged = identity.SignedIdentity(
        doc=identity.IdentityDoc("evil-fork", doc.description, doc.delegates),
        signatures=(sig,),
    )
    assert not forged.is_verified()


def test_duplicate_delegate_signature_counts_once() -> None:
    """Two signatures from the same delegate count as one toward the threshold."""
    alice, bob, carol = (PeerIdentity.generate() for _ in range(3))
    doc = _doc((alice.did(), bob.did(), carol.did()), threshold=2)
    sig = identity.sign_identity(doc, alice)
    doubled = identity.SignedIdentity(doc=doc, signatures=(sig, sig))
    assert doubled.valid_signature_count() == 1
    assert not doubled.is_verified()


def test_signed_identity_json_round_trip() -> None:
    """A signed identity survives a JSON serialization round trip."""
    alice, bob = PeerIdentity.generate(), PeerIdentity.generate()
    doc = _doc((alice.did(), bob.did()), threshold=2)
    signed = identity.collect_signatures(doc, (alice, bob))
    restored = identity.SignedIdentity.from_json(signed.to_json())
    assert restored.is_verified()
    assert restored.doc.rid() == doc.rid()


def test_identity_validation_rules() -> None:
    """Construction rejects empty names, no delegates, dups, and bad thresholds."""
    alice = PeerIdentity.generate().did()
    for args in (
        ("", "d", (alice,), 1),
        ("n", "d", (), 1),
        ("n", "d", (alice, alice), 1),
        ("n", "d", (alice,), 2),
        ("n", "d", (alice,), 0),
    ):
        try:
            identity.IdentityDoc(*args)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {args!r}")


def test_is_valid_did() -> None:
    """is_valid_did accepts real DIDs and rejects junk."""
    assert identity.is_valid_did(PeerIdentity.generate().did())
    assert not identity.is_valid_did("did:key:Qnope")
