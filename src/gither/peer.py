"""Peer identity for Gither's peer-to-peer code forge.

Radicle (Heartwood) identifies every node by an Ed25519 public key — the *Node ID* —
and encodes it as a W3C ``did:key`` decentralized identifier (``did:key:z6Mk…``).
Repository identifiers, signed refs, and gossip announcements are all anchored to that
key. This module ports that foundation to Python.

To keep gither dependency-free (``dependencies = []`` in ``pyproject.toml``) and match the
Knitweb pure-Python ethos, Ed25519 (RFC 8032) is implemented here with only the standard
library (``hashlib`` for SHA-512). The signing primitives are deliberately the compact
reference construction; correctness is pinned by the official RFC 8032 test vectors in
``tests/test_peer.py``. This is verification-grade, not performance-grade — gither signs
small control-plane records (identity docs, ref announcements), not bulk data.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

# ── edwards25519 parameters (RFC 8032, §5.1) ────────────────────────────────────
_B_BITS = 256
_Q = 2 ** 255 - 19  # field prime
_L = 2 ** 252 + 27742317777372353535851937790883648493  # group order
_KEY_LEN = 32
_SIG_LEN = 64
# Multicodec prefix for an Ed25519 public key (unsigned varint 0xed) + multibase
# base58btc indicator "z"; together they yield the canonical did:key "z6Mk…" form.
_ED25519_MULTICODEC = b"\xed\x01"
_MULTIBASE_BASE58BTC = "z"
_DID_KEY_PREFIX = "did:key:"
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _inv(x: int) -> int:
    """Multiplicative inverse modulo the field prime."""
    return pow(x, _Q - 2, _Q)


_D = (-121665 * _inv(121666)) % _Q
_SQRT_M1 = pow(2, (_Q - 1) // 4, _Q)


def _x_recover(y: int) -> int:
    """Recover the x coordinate of a curve point from its y coordinate."""
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q != 0:
        x = (x * _SQRT_M1) % _Q
    if x % 2 != 0:
        x = _Q - x
    return x


_BY = (4 * _inv(5)) % _Q
_BX = _x_recover(_BY)
_BASE = (_BX % _Q, _BY % _Q)


def _edwards_add(p, q):
    """Add two points on the twisted Edwards curve."""
    x1, y1 = p
    x2, y2 = q
    denom = _inv(1 + _D * x1 * x2 * y1 * y2)
    x3 = (x1 * y2 + x2 * y1) * denom
    denom2 = _inv(1 - _D * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * denom2
    return (x3 % _Q, y3 % _Q)


def _scalar_mult(p, e: int):
    """Multiply a curve point by a scalar (double-and-add)."""
    result = (0, 1)
    addend = p
    while e > 0:
        if e & 1:
            result = _edwards_add(result, addend)
        addend = _edwards_add(addend, addend)
        e >>= 1
    return result


def _bit(data: bytes, i: int) -> int:
    """Return bit i (little-endian) of a byte string."""
    return (data[i // 8] >> (i % 8)) & 1


def _encode_int(y: int) -> bytes:
    """Encode an integer as a little-endian 32-byte string."""
    return y.to_bytes(_KEY_LEN, "little")


def _encode_point(point) -> bytes:
    """Encode a curve point in the 32-byte compressed Ed25519 form."""
    x, y = point
    return ((y & ((1 << 255) - 1)) | ((x & 1) << 255)).to_bytes(_KEY_LEN, "little")


def _decode_int(data: bytes) -> int:
    """Decode a little-endian integer from bytes."""
    return int.from_bytes(data, "little")


def _decode_point(data: bytes):
    """Decode a compressed 32-byte point back to (x, y), verifying it is on-curve."""
    y = _decode_int(data) & ((1 << 255) - 1)
    x = _x_recover(y)
    if (x & 1) != _bit(data, _B_BITS - 1):
        x = _Q - x
    point = (x, y)
    if (-x * x + y * y - 1 - _D * x * x * y * y) % _Q != 0:
        raise ValueError("decoded point is not on the edwards25519 curve")
    return point


def _hash_to_int(data: bytes) -> int:
    """SHA-512 a byte string and interpret the digest as a little-endian integer."""
    return int.from_bytes(hashlib.sha512(data).digest(), "little")


def _clamp_scalar(seed_hash: bytes) -> int:
    """Derive the clamped Ed25519 secret scalar from the seed hash (RFC 8032 §5.1.5)."""
    a = _decode_int(seed_hash[:_KEY_LEN])
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a


def _public_from_seed(seed: bytes) -> bytes:
    """Compute the 32-byte Ed25519 public key for a 32-byte seed."""
    a = _clamp_scalar(hashlib.sha512(seed).digest())
    return _encode_point(_scalar_mult(_BASE, a))


def _sign_raw(message: bytes, seed: bytes, public: bytes) -> bytes:
    """Produce a 64-byte Ed25519 signature over message (RFC 8032 §5.1.6)."""
    h = hashlib.sha512(seed).digest()
    a = _clamp_scalar(h)
    r = _hash_to_int(h[_KEY_LEN:] + message) % _L
    big_r = _encode_point(_scalar_mult(_BASE, r))
    k = _hash_to_int(big_r + public + message) % _L
    s = (r + k * a) % _L
    return big_r + _encode_int(s)


def _verify_raw(message: bytes, signature: bytes, public: bytes) -> bool:
    """Verify a 64-byte Ed25519 signature; return True iff valid."""
    if len(signature) != _SIG_LEN or len(public) != _KEY_LEN:
        return False
    try:
        big_r = _decode_point(signature[:_KEY_LEN])
        a_point = _decode_point(public)
    except ValueError:
        return False
    s = _decode_int(signature[_KEY_LEN:])
    if s >= _L:
        return False
    k = _hash_to_int(signature[:_KEY_LEN] + public + message) % _L
    left = _scalar_mult(_BASE, s)
    right = _edwards_add(big_r, _scalar_mult(a_point, k))
    return left == right


def _b58encode(data: bytes) -> str:
    """Encode bytes with the base58btc (Bitcoin) alphabet."""
    n = int.from_bytes(data, "big")
    chars: list[str] = []
    while n > 0:
        n, rem = divmod(n, 58)
        chars.append(_B58_ALPHABET[rem])
    pad = len(data) - len(data.lstrip(b"\x00"))
    return "1" * pad + "".join(reversed(chars))


def _b58decode(text: str) -> bytes:
    """Decode a base58btc string back to bytes."""
    n = 0
    for ch in text:
        n = n * 58 + _B58_ALPHABET.index(ch)
    pad = len(text) - len(text.lstrip("1"))
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n > 0 else b""
    return b"\x00" * pad + body


def encode_did_key(public: bytes) -> str:
    """Encode a 32-byte Ed25519 public key as a ``did:key`` DID (``did:key:z6Mk…``)."""
    if len(public) != _KEY_LEN:
        raise ValueError("ed25519 public key must be 32 bytes")
    multibase = _MULTIBASE_BASE58BTC + _b58encode(_ED25519_MULTICODEC + public)
    return _DID_KEY_PREFIX + multibase


def node_id_from_public(public: bytes) -> str:
    """Return the Radicle-style Node ID (the did:key multibase, e.g. ``z6Mk…``)."""
    return encode_did_key(public).removeprefix(_DID_KEY_PREFIX)


def decode_did_key(did: str) -> bytes:
    """Decode a ``did:key`` DID or bare Node ID back to its 32-byte public key."""
    multibase = did.removeprefix(_DID_KEY_PREFIX)
    if not multibase.startswith(_MULTIBASE_BASE58BTC):
        raise ValueError("expected a base58btc multibase ('z') did:key value")
    raw = _b58decode(multibase[1:])
    if not raw.startswith(_ED25519_MULTICODEC):
        raise ValueError("did:key is not an Ed25519 multicodec key")
    public = raw[len(_ED25519_MULTICODEC):]
    if len(public) != _KEY_LEN:
        raise ValueError("decoded Ed25519 public key has the wrong length")
    return public


@dataclass(frozen=True)
class PeerIdentity:
    """A node's Ed25519 keypair: its peer-to-peer identity in the gither network.

    ``seed`` is the 32-byte private key material; ``public`` is the derived 32-byte
    public key. The Node ID / DID are computed from ``public`` and are safe to share.
    """

    seed: bytes
    public: bytes

    @classmethod
    def generate(cls) -> "PeerIdentity":
        """Create a fresh identity from a cryptographically secure random seed."""
        return cls.from_seed(os.urandom(_KEY_LEN))

    @classmethod
    def from_seed(cls, seed: bytes) -> "PeerIdentity":
        """Build an identity deterministically from a 32-byte seed."""
        if len(seed) != _KEY_LEN:
            raise ValueError("ed25519 seed must be 32 bytes")
        return cls(seed=bytes(seed), public=_public_from_seed(bytes(seed)))

    @classmethod
    def from_seed_hex(cls, seed_hex: str) -> "PeerIdentity":
        """Build an identity from a 64-character hex seed (as stored on disk)."""
        return cls.from_seed(bytes.fromhex(seed_hex.strip()))

    def seed_hex(self) -> str:
        """Return the private seed as lowercase hex for persistence."""
        return self.seed.hex()

    def did(self) -> str:
        """Return the W3C ``did:key`` DID for this identity."""
        return encode_did_key(self.public)

    def node_id(self) -> str:
        """Return the Radicle-style Node ID (bare did:key multibase)."""
        return node_id_from_public(self.public)

    def sign(self, message: bytes) -> bytes:
        """Sign a message and return the 64-byte Ed25519 signature."""
        return _sign_raw(message, self.seed, self.public)

    def verify(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature against this identity's own public key."""
        return _verify_raw(message, signature, self.public)


def verify(did_or_node_id: str, message: bytes, signature: bytes) -> bool:
    """Verify a signature given a signer's DID / Node ID, the message, and the signature."""
    try:
        public = decode_did_key(did_or_node_id)
    except ValueError:
        return False
    return _verify_raw(message, signature, public)
