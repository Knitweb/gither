# Gither Peer-to-Peer Protocol

Gither is positioned as a peer-to-peer duplicate of GitHub (see
[`P2P_GITHUB_DUPLICATE.md`](P2P_GITHUB_DUPLICATE.md)). To duplicate GitHub *without a
central server*, the forge state — repository identity, change proposals, review state,
release manifests — must be portable and verifiable between untrusted peers.

This document describes the P2P layer, modeled on [Radicle](https://radicle.xyz)'s
**Heartwood** protocol (a production, open-source, peer-to-peer git network written in
Rust). Gither re-implements the same primitives in **pure Python** (standard library
only — no binary crypto dependency), matching the Knitweb pure-Python ethos.

## Why model on Radicle

Radicle solved the hard problem already: collaborate on git repositories across a
gossip network where no peer is trusted and no server is authoritative. Its design rests
on four primitives, each of which Gither ports:

| Radicle (Heartwood) | Gither | Status |
| --- | --- | --- |
| Node ID = Ed25519 public key, encoded as `did:key` | `gither.peer` | **shipped** |
| Repository ID (RID) = content-addressed identity hash | `gither.identity` | planned |
| Signed refs (`rad/sigrefs`) — every peer signs its refs | `gither.sigrefs` | planned |
| Gossip: inventory + ref announcements between nodes | `gither.gossip` | planned |

## 1. Peer identity (shipped — `gither.peer`)

Every node has a long-lived **Ed25519 keypair**. The public key is the node's stable
identity across the network; the private seed never leaves the node.

- **Node ID** — the public key encoded as a `did:key` multibase string, e.g.
  `z6Mkw61NL4LKSXkFtU3FjKofgCCcdKT4DzMYMDARenQxq8u8`. This is exactly Radicle's Node ID
  format (multicodec `0xed01` for Ed25519 + base58btc multibase `z`).
- **DID** — the same value with the `did:key:` prefix, a W3C-standard decentralized
  identifier that any DID-aware system can resolve to the verifying key.
- **Signing** — the node signs control-plane records (identity documents, ref
  announcements, release receipts) so peers can verify authorship and integrity without
  a server or a certificate authority.

The Ed25519 implementation (`gither/peer.py`) is the compact RFC 8032 reference
construction over edwards25519, using only `hashlib`. It is **verification-grade, not
performance-grade**: gither signs small forge records, not bulk data. Correctness is
pinned by `tests/test_peer.py`, whose vectors were cross-validated to be **byte-identical
to libsodium** across 200 random keys in both signing directions, and whose `did:key`
value is the canonical example from the W3C did:key specification. Byte-level parity with
libsodium means a Gither identity is interoperable with real Radicle / `ed25519-dalek`
nodes.

```console
$ gither peer            # create on first use, then print the stable identity
created peer identity at ./.gither/identity/node.key
did:      did:key:z6Mkgjqe3XpXkRvdtWcv45kAhJGRatq227hfWC4SvY7NYrGD
node id:  z6Mkgjqe3XpXkRvdtWcv45kAhJGRatq227hfWC4SvY7NYrGD
```

The private seed is written to `.gither/identity/node.key` with `0600` permissions and is
git-ignored — it must never be committed or mirrored.

## 2. Repository ID (planned — `gither.identity`)

A repository's identity is a signed document — name, description, **delegates** (the
DIDs allowed to update the canonical identity), and a signing **threshold**. The
**Repository ID (RID)** is the content address of that initial document (a hash, encoded
like the Node ID). Because it is content-addressed, the RID is stable, globally unique,
and independent of any hosting location — the property that lets a repo move between
peers, static sites, and mirrors while keeping one identity.

## 3. Signed refs (planned — `gither.sigrefs`)

Each peer publishes its refs under its own namespace
(`refs/namespaces/<node-id>/…`) and signs the `{refname: oid}` set it claims to hold.
A receiving peer verifies the signature against the publisher's Node ID before trusting
any ref, so a malicious relay cannot forge or roll back another peer's branches. The
canonical branch head is the one the repository's delegates agree on (per the identity
document threshold).

## 4. Gossip (planned — `gither.gossip`)

Nodes announce two things to peers: their **inventory** (which RIDs they seed) and
**ref announcements** (per-repo, per-namespace: the signed-refs head plus a timestamp and
signature). Peers interested in a repo fetch the refs from any node announcing them.
Availability comes from **seeding** — nodes that choose to replicate and serve a repo.

## Implementation order

1. **Peer identity** ✅ — the cryptographic root everything else is anchored to.
2. **Repository identity + RID** — content-addressed repos with delegate signing.
3. **Signed refs** — per-peer, verifiable ref publication.
4. **Gossip + seeding** — inventory and ref announcements over a transport.

Each layer is independently testable and ships as its own pull request, keeping the
review gate green at every step.
