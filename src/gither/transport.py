"""Gossip transport — the TCP wire that carries signed announcements between peers.

Layer 4b of the Radicle-inspired protocol (see ``docs/P2P_PROTOCOL.md``), the final piece,
building on :mod:`gither.gossip`. Layers 1-4a produce *verifiable* announcements; this layer
moves them between hosts.

The wire is intentionally minimal and pure-stdlib (``socket`` + ``threading``): each message
is a 4-byte big-endian length prefix followed by a UTF-8 JSON body. A connection carries one
**bundle** — ``{"inventory": [...], "refs": [...]}`` of announcement JSON objects. The exchange
is symmetric: each side sends its bundle and ingests the peer's, feeding every announcement
through :class:`gither.gossip.GossipState`, which already discards anything that fails
signature verification or is staler than what is held. So the transport never has to trust the
socket — authenticity and freshness are enforced by the message layer, exactly as in Radicle.

Because the message layer is transport-agnostic and self-verifying, the whole exchange is
testable over loopback (two nodes on 127.0.0.1 in one process); see ``tests/test_transport.py``.
"""

from __future__ import annotations

import json
import socket
import struct
import threading
from dataclasses import dataclass

from .gossip import GossipState, InventoryAnnouncement, RefsAnnouncement

_LEN = struct.Struct(">I")
_MAX_MESSAGE_BYTES = 8 * 1024 * 1024  # reject oversized frames to bound memory
_DEFAULT_TIMEOUT = 10.0


def _send_message(sock: socket.socket, payload: dict[str, object]) -> None:
    """Send one length-prefixed JSON message over a socket."""
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(body) > _MAX_MESSAGE_BYTES:
        raise ValueError("outgoing gossip message exceeds the size limit")
    sock.sendall(_LEN.pack(len(body)) + body)


def _recv_exactly(sock: socket.socket, count: int) -> bytes:
    """Read exactly count bytes from a socket or raise ConnectionError."""
    chunks: list[bytes] = []
    remaining = count
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("peer closed the connection mid-message")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_message(sock: socket.socket) -> dict[str, object]:
    """Receive one length-prefixed JSON message from a socket."""
    (length,) = _LEN.unpack(_recv_exactly(sock, _LEN.size))
    if length > _MAX_MESSAGE_BYTES:
        raise ValueError("incoming gossip message exceeds the size limit")
    payload = json.loads(_recv_exactly(sock, length).decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("incoming gossip message must be a JSON object")
    return payload


def make_bundle(refs: tuple[RefsAnnouncement, ...], inventory: tuple[InventoryAnnouncement, ...]) -> dict[str, object]:
    """Build a wire bundle from ref and inventory announcements."""
    return {
        "refs": [ann.to_json() for ann in refs],
        "inventory": [ann.to_json() for ann in inventory],
    }


def _bundle_items(bundle: dict[str, object], key: str) -> tuple[object, ...]:
    """Return a normalized list-like field from a received bundle."""
    value = bundle.get(key, [])
    if not isinstance(value, list):
        return ()
    return tuple(value)


def ingest_bundle(state: GossipState, bundle: dict[str, object]) -> int:
    """Feed every announcement in a received bundle through GossipState.

    Returns the number of announcements accepted (verified and fresh). Malformed entries
    are skipped, so a hostile peer cannot crash the receiver with bad data.
    """
    accepted = 0
    for item in _bundle_items(bundle, "refs"):
        try:
            if state.ingest_refs(RefsAnnouncement.from_json(dict(item))):
                accepted += 1
        except (KeyError, ValueError, TypeError):
            continue
    for item in _bundle_items(bundle, "inventory"):
        try:
            if state.ingest_inventory(InventoryAnnouncement.from_json(dict(item))):
                accepted += 1
        except (KeyError, ValueError, TypeError):
            continue
    return accepted


@dataclass
class GossipPeer:
    """A loopback-capable gossip endpoint: serves a bundle and ingests what peers send.

    ``state`` accumulates verified announcements received from peers; ``local_bundle`` is what
    this peer offers in return on each connection.
    """

    state: GossipState
    local_bundle: dict[str, object]
    host: str = "127.0.0.1"
    timeout: float = _DEFAULT_TIMEOUT

    def serve_once(self) -> tuple[threading.Thread, int]:
        """Start a one-shot server in a thread; return (thread, bound_port).

        The thread accepts a single connection, ingests the peer's bundle into ``state``,
        sends ``local_bundle`` back, then exits. Join the thread to await completion.
        """
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.host, 0))
        listener.listen(1)
        listener.settimeout(self.timeout)
        port = listener.getsockname()[1]

        def _run() -> None:
            with listener:
                try:
                    conn, _ = listener.accept()
                except (socket.timeout, OSError):
                    return
                with conn:
                    conn.settimeout(self.timeout)
                    ingest_bundle(self.state, _recv_message(conn))
                    _send_message(conn, self.local_bundle)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread, port

    def exchange_with(self, port: int) -> int:
        """Connect to a peer on (host, port), send our bundle, ingest theirs.

        Returns the number of announcements accepted from the peer.
        """
        with socket.create_connection((self.host, port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            _send_message(sock, self.local_bundle)
            return ingest_bundle(self.state, _recv_message(sock))
