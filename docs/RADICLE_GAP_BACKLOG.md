# Radicle Gap Backlog

## Why this doc exists

Radicle is a real competitor in sovereign forge infrastructure.
It already ships a peer-to-peer Git forge, patches, issues, node replication, and a mature
local-first story.

Gither should not hand-wave that away.
It should beat Radicle on the parts Radicle does not yet try to own:

- portable review gates;
- deploy receipts;
- dependency-linked ownership;
- optional identity-backed authority;
- usage-linked royalties;
- Web3-ready mirror and settlement policy.

## Verified Radicle baseline

From Radicle's current public docs:

- Radicle is a sovereign code forge built on Git.
- Repositories are replicated across peers in a decentralized manner.
- Social artifacts are stored in Git and signed.
- The stack includes code, issues, and patches.
- Users run their own nodes.
- Identity is currently device-scoped; the user guide warns against sharing one identity
  across devices and says linked-device support is still being designed.

Those are substantial strengths.

## Where Gither can win

### 1. Repository state should be richer than Git plus social objects

Gither should make the forge state itself portable:

- review gates;
- CI receipts;
- release manifests;
- dependency proofs;
- license mirror policy;
- ownership state.

### 2. Continuous deployment should be first-class

Radicle talks about collaboration and CI integration.
Gither should go one step further and make deployments portable:

- reviewed change;
- deterministic test receipt;
- environment receipt;
- release acceptance record;
- mirrored deploy receipt;
- rollback receipt.

That is the shortest path to "serverless continuous development and continuous integration"
as an actual system claim.

### 3. Identity-backed authority should be optional but real

Radicle's public model is strong on self-sovereign device identity.
Gither should add a higher-assurance mode:

- optional vBank-issued agent identity;
- issuer and registrar trust records;
- encrypted evidence vaults;
- public records that stay PII-free;
- release or governance actions that can require stronger accountability.

### 4. Ownership should be usage-linked, not commit-linked

Radicle does not position itself around software royalties.
Gither can.

But it should do so with discipline:

- no commit farming;
- no line-count rewards;
- no AI-noise incentives;
- only reviewed, deployed, used software enters the split model.

### 5. Dependency-aware value flow is the real differentiator

Knitweb plus Pulse gives Gither something Radicle does not claim:

- dependency graph structure;
- live usage receipts;
- attribution across components;
- software royalty policy.

That is a different category from patch exchange alone.

## Backlog

## Phase A: Match Radicle's practical floor

- Add peer-to-peer forge-state exchange for issues, patches, and reviews.
- Add multi-device repository authority records.
- Add offline-first local review queues.
- Add canonical repository identity replication.
- Add seedless recovery/export bundles for cold-start peers.

## Phase B: Surpass on release authority

- Add signed CI receipts.
- Add signed deployment receipts.
- Add release acceptance and rollback records.
- Add environment and artifact attestations.
- Add mirror freshness and liveness proofs.

## Phase C: Surpass on identity and governance

- Add issuer registry records.
- Add registrar records for approved service providers.
- Add encrypted evidence envelope records.
- Add revocation and suspension flows for agent attestations.
- Add optional strong-identity requirements for maintainer, deployer, and signer roles.

## Phase D: Surpass on code ownership

- Add semi-commune ownership records for teams.
- Add maintainer-share and contributor-share rules.
- Add dependency royalty splits.
- Add dispute and arbitration records.
- Add vesting, decay, and inactivity rules for long-lived shared codebases.

## Phase E: Surpass on crypto resilience

- Add hybrid secp256k1 + ML-DSA signatures for critical records.
- Add ML-KEM-wrapped evidence vault receipts.
- Add frontier-signal ingestion from `sha256.fail`.
- Add crypto-policy gates that tighten as frontier risk moves.
- Add legacy verification windows and forced re-signing flows.

## Product message

Radicle is a sovereign forge built on Git.
Gither should become the sovereign forge that also knows:

- what was reviewed;
- what was deployed;
- what was used;
- who can be held accountable;
- who owns the resulting value.

That is the backlog worth shipping.
