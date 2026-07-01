# Agent Identity Issuance for Gither and Vang

## Abstract

Gither and Vang need two different protections that should not be collapsed into one
mechanism.

- Gither needs strong code authority so propaganda, mirror tampering, or forged release
  state cannot silently rewrite software history.
- Vang needs strong accountability for agents and people, but it must not publish raw
  identity evidence or KYC payloads into the replicated fabric.

This paper proposes a practical first architecture:

1. keep public voting and forge records minimal and content-addressed;
2. move raw identity evidence into an encrypted evidence vault;
3. let Vang issue traceable agent identity attestations only after a regulated or
   contractually trusted identity service has verified the underlying person;
4. make the cryptographic stack crypto-agile, with a migration path from
   secp256k1/SHA-256 toward post-quantum signatures and KEM-based evidence encryption;
5. let Gither miners finance identity issuance and renewal as a protocol cost, recorded
   as portable receipts.

The conclusion is conservative:

- use **ML-DSA** as the primary post-quantum signature target;
- use **SLH-DSA** as the backup signature family;
- use **ML-KEM** for the encrypted evidence vault;
- treat `sha256.fail` as a **frontier signal source**, not yet as an autonomous switch;
- keep raw ID copies and provider certificates **off-fabric** at all times.

## Repo-grounded constraints

The current codebase already locks in several useful boundaries.

### Pulse / Knitweb today

`pulse/src/knitweb/core/crypto.py` currently uses:

- secp256k1 ECDSA for signatures;
- SHA-256 for hashing and Merkle roots;
- versioned `pls1` addresses with a reserved scheme byte for future post-quantum schemes.

That scheme byte is important. It means the system already anticipates a soft-fork path for
future signature schemes instead of forcing one irreversible address rewrite.

### Vang today

`vang` currently consumes personhood tickets and scope nullifiers, and its ballot record
deliberately carries no raw identity. In the personhood foundation branch of Pulse:

- `personhood-anchor` is PII-free;
- revocation is pointer-based, not nullifier-based;
- pairwise addresses are per-scope;
- the verifier backend is intentionally replaceable;
- current pairwise and nullifier derivation still depend on secp256k1/SHA-256.

This is the correct privacy direction. It should be extended, not undone.

### sha256.fail today

`sha256.fail` is currently a scaffold benchmark for reversible SHA-256 compression. It does
not yet provide a production runtime, wallet, or key-management layer. Therefore it cannot
yet be the component that directly switches live application cryptography. What it can do is
publish a benchmarked **risk frontier** that downstream systems normalize into policy.

### Gither today

Gither already positions itself as the authority layer above hosted forges. That makes it
the right place to record:

- miner receipts;
- issuer registry entries;
- crypto-policy updates;
- release gates that refuse weak signature suites once risk passes a threshold.

## Problem statement

The user requirement is stricter than normal pseudonymous voting:

- every relevant agent must remain traceable to a real identified person;
- that trace must rest on a copy of an identity document and a trustworthy service-provider
  process;
- but public ledgers and public forge records must not expose those raw artifacts;
- miners may pay for the identity work, and miners themselves are paid via Gither.

That rules out two bad extremes:

1. **Pure pseudonymity only**: good privacy, insufficient accountability.
2. **Raw KYC on-chain or on-fabric**: strong accountability, unacceptable exposure and
   retention risk.

The viable design is a split model:

- public records hold only minimal attestable facts and revocation handles;
- encrypted evidence stays off-fabric but remains audit-addressable;
- payment and governance receipts remain on-fabric.

## Threat model

### Gither threats

- hosted mirror tampering;
- propaganda injected into code mirrors or release metadata;
- signature replay across record types;
- key compromise of visible secp256k1 identities;
- future Shor-style break against revealed ECC public keys.

### Vang threats

- disclosure of ID copies, liveness checks, or provider transcripts;
- correlation of a person across scopes or elections;
- forged or stale revocation status;
- provider lock-in or regulatory dependence on a single issuer;
- future decryption of archived identity evidence.

### Quantum transition threats

- `sha256.fail` shows the resource frontier for Grover-style SHA-256 attacks moving down;
- secp256k1 is structurally vulnerable to Shor once a sufficiently capable quantum computer
  exists;
- an abrupt one-shot migration will fail operationally;
- an unguided migration will fragment identity and code authority.

## Survey of existing digital services

The current market already splits into distinct service classes. No single provider should
own the whole stack.

### 1. Public or regulated digital identity frameworks

The revised European digital identity framework requires Member States to provide a digital
wallet, keep it voluntary, and let it link national identity with other electronic
attestations. The Council text also emphasizes user control and free issuance, use, and
revocation for natural persons.

Implication for Gither/Vang:

- public or regulated wallet ecosystems are the best upstream source for high-assurance
  personhood;
- they should be treated as issuer roots or trust anchors, not as the storage layer for
  Gither or Vang.

### 2. Privacy-first selective-disclosure wallet layer

Yivi is relevant because it is:

- open source;
- explicit about selective disclosure;
- explicit that data is stored on the user’s phone;
- already oriented toward login, signing, and voting scenarios.

Implication:

- Yivi-like flows fit the presentation layer well;
- they are strong for privacy and user control;
- they do not eliminate the need for a regulated issuer or external evidence process when
  legal traceability to a real person is required.

### 3. Commercial KYC / trust orchestration platforms

#### Signicat

Signicat presents a broad European digital identity platform:

- identity proofing;
- authentication;
- electronic signing;
- trust orchestration;
- EU Digital Identity Wallet support;
- 240+ identity methods via one integration surface.

This is strong for multi-market orchestration and issuer integration.

#### IDnow

IDnow presents a modular identity and trust platform with:

- identity verification;
- risk/fraud layers;
- EUDI wallet support;
- trust services;
- SES, AES, QES, and QSeals.

This is strong where qualified signatures and trust-service style evidence matter.

#### Veriff

Veriff is strong as a high-volume KYC/KYB and fraud-screening layer:

- document verification;
- proof of address;
- AML screening;
- biometric verification;
- liveness;
- broad country and document coverage.

This is useful as an operational fallback or onboarding rail, but it should not become the
sole root of trust for agent identity.

## Recommended service split

The best first architecture is multi-layered.

### Root issuer layer

Preferred sources:

- EUDI / eIDAS wallet issuers and associated trust anchors;
- regulated trust-service providers where qualified signatures or seals matter.

Role:

- establish that a natural person exists and is verified;
- establish that a provider operated under a recognized compliance process;
- mint or support revocable, auditable attestations.

### Presentation layer

Preferred sources:

- Yivi-style selective disclosure wallets;
- EUDI wallet presentation flows;
- pairwise per-scope identifiers.

Role:

- authenticate to applications with minimum disclosure;
- present age, role, or service entitlements without exposing raw identity.

### High-volume verification / fallback layer

Preferred sources:

- Signicat;
- IDnow;
- Veriff;
- similar KYC platforms under explicit contractual controls.

Role:

- onboarding throughput;
- document and liveness checks;
- recovery or fallback where wallet-native issuance is not yet available.

## Proposed Vang architecture

Vang should become an issuer of **agent identity attestations**, but not a warehouse of raw
identity artifacts.

### Public fabric payload

Public records should contain only:

- pairwise or agent-specific public identifier;
- issuer trust anchor hash;
- provider class;
- credential class;
- validity window;
- revocation pointer;
- proof digest;
- key scheme;
- evidence envelope CID or digest;
- attestation signatures.

### Encrypted evidence vault

Raw artifacts stay off-fabric:

- ID copy or passport scan;
- provider KYC transcript;
- liveness evidence;
- service-provider certificate or qualification evidence;
- internal case review notes;
- revocation rationale where sensitive.

That vault should be encrypted per envelope, not per database.

Recommended first target:

- envelope key establishment with **ML-KEM-768**;
- optional hybrid wrapping during transition;
- object-addressable encrypted blobs with hash receipts stored in public records.

### Traceability rule

The public chain should not identify the person directly. Instead it should prove that:

1. a valid encrypted evidence envelope exists;
2. the envelope was created or countersigned by an accepted issuer/provider;
3. the provider can, under due process, map the envelope back to a real identified person.

This satisfies the “herleidbaar tot een persoon” requirement without turning the public
fabric into a PII archive.

## Proposed Gither architecture

Gither should not verify passports or selfies itself. Its role is economic and governance
control.

Gither should store:

- issuer registry entries;
- service-provider trust classes;
- miner-funded identity issuance receipts;
- crypto-policy records;
- release gates requiring stronger schemes as risk rises;
- dispute and revocation records for compromised agents or maintainers.

This directly addresses the propaganda concern: authority moves from a mutable hosted forge
page into signed, portable records with explicit issuer and scheme metadata.

## Post-quantum migration policy

### Why ML-DSA

NIST finalized **FIPS 204** as the primary post-quantum digital signature standard. For the
Gither/Vang problem, that makes ML-DSA the correct primary target for:

- code-authority signatures;
- issuer attestations;
- agent identity attestations;
- miner payment receipts.

### Why SLH-DSA

NIST finalized **FIPS 205** as a backup signature family based on a different mathematical
approach. That makes SLH-DSA the right contingency suite for:

- long-lived root attestations;
- emergency fallback if a lattice-based weakness appears;
- high-value archive re-signing.

### Why ML-KEM

NIST finalized **FIPS 203** as the primary post-quantum KEM. That makes ML-KEM the right
choice for:

- encrypted evidence envelopes;
- provider-to-Vang secure handoff;
- key rotation for archived raw identity evidence.

### Migration phases

#### Phase 0: current

- secp256k1 ECDSA + SHA-256 remains accepted;
- public addresses keep their existing scheme byte;
- no raw identity data on fabric.

#### Phase 1: hybrid

Triggered when Gither governance and the frontier signal agree risk is material.

- every critical attestation is dual-signed:
  - current secp256k1 path;
  - ML-DSA path.
- new evidence envelopes use ML-KEM wrapping.
- roots may additionally carry SLH-DSA backup signatures.

#### Phase 2: PQ-first

Triggered when the normalized hash-risk signal crosses the hard protocol threshold, such as
the user-specified “effective SHA-256 break frontier under 512 qubits,” plus governance
confirmation.

- new Gither authority records require ML-DSA;
- Vang issuer attestations require ML-DSA;
- archived sensitive evidence must be rewrapped with ML-KEM;
- secp256k1 becomes legacy-verify-only or fully disallowed, depending on record class.

## How `sha256.fail` should be used

`sha256.fail` should not directly flip production cryptography today. It should publish a
machine-readable frontier signal, for example:

- current best reversible SHA-256 score;
- estimated logical qubits;
- estimated Toffoli cost;
- normalized risk percentile;
- last-updated and quorum metadata.

Gither can then convert that into a policy signal:

- `risk_percent`;
- `phase`;
- `required_signature_schemes`;
- `required_evidence_kem`;
- `legacy_acceptance_window`.

That keeps the scientific benchmark separate from governance.

## Miner-funded payment model

Identity issuance and maintenance should be protocol-paid, but not blindly.

### Payment events

- enrollment completed;
- renewal completed;
- revocation processed;
- challenge or recovery completed;
- provider evidence envelope accepted;
- dispute resolved.

### Suggested payment path

1. Miner completes protocol work and receives Gither reward.
2. A defined fraction flows into an identity-operations pool.
3. Vang or Gither releases provider receipts when issuer work is validated.
4. Payment receipts are public; raw identity evidence remains encrypted and off-fabric.

This makes identity a funded infrastructure cost instead of an unfunded compliance burden.

## Recommended first implementation

1. Keep Vang public records PII-free.
2. Add an encrypted evidence-vault concept instead of storing ID copies in the fabric.
3. Register issuer/provider trust anchors in Gither.
4. Introduce hybrid-signature policy records in Gither before changing every primitive.
5. Let `sha256.fail` emit a frontier/risk JSON artifact instead of pretending it is already
   an application-side switch.
6. Add Vang support for traceable agent identity attestations backed by provider-issued
   evidence envelopes.

## Decision

For the current repos, the best first move is:

- **not** to replace secp256k1 everywhere immediately;
- **not** to store identity documents in public or replicated records;
- **not** to let one commercial KYC provider become the only trust root.

Instead:

- Gither becomes the portable policy and payment authority;
- Vang becomes the issuer of traceable agent identity attestations;
- regulated issuers and digital identity services feed encrypted evidence into that system;
- ML-DSA, SLH-DSA, and ML-KEM define the post-quantum destination;
- `sha256.fail` supplies a risk frontier that helps time the migration.

## Sources

- Pulse current crypto boundary: local repo `pulse/src/knitweb/core/crypto.py`
- Pulse personhood foundation branch: local repo `origin/feat/personhood-foundation`
- Vang current architecture: local repo `vang/docs/ARCHITECTURE.md`
- Gither current authority model: local repo `gither/README.md`
- EU Council, *European digital identity (eID): Council adopts legal framework on a secure and trustworthy digital wallet for all Europeans*: https://www.consilium.europa.eu/en/press/press-releases/2024/03/26/european-digital-identity-eid-council-adopts-legal-framework-on-a-secure-and-trustworthy-digital-wallet-for-all-europeans/
- NIST FIPS 203, *Module-Lattice-Based Key-Encapsulation Mechanism Standard*: https://csrc.nist.gov/pubs/fips/203/final
- NIST FIPS 204, *Module-Lattice-Based Digital Signature Standard*: https://csrc.nist.gov/pubs/fips/204/final
- NIST FIPS 205, *Stateless Hash-Based Digital Signature Standard*: https://csrc.nist.gov/pubs/fips/205/final
- NIST, *NIST Releases First 3 Finalized Post-Quantum Encryption Standards*: https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards
- Yivi official site: https://yivi.app/en/
- Veriff official site: https://www.veriff.com/
- IDnow official site: https://idnow.io/
- Signicat official site: https://www.signicat.com/
- Sitouah, Esposito, Bruschi (2026), *Self-Sovereign Identity and eIDAS 2.0: An Analysis of Control, Privacy, and Legal Implications*: https://arxiv.org/abs/2601.19837
