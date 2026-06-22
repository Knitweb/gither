# Gither Roadmap

## Phase 1: Current Build

- Workspace manifest.
- Repo discovery.
- Request routing.
- Test-plan output.
- Repo graph export.
- Benchmark plan.
- Repository snapshot command.
- Python source audit.
- Local review gate.
- Versioned change notes.
- Knowledge ownership model.
- P2P GitHub-duplicate positioning.
- License-aware mirror protocol.

## Phase 2: Knitweb Integration

- Emit canonical Knitweb records for repos, docs, commands, and routes.
- Add content-addressed graph export.
- Track which routes were correct after human review.
- Feed accepted routing decisions into Lens.
- Sign change notes and CI receipts.
- Emit ownership records for accepted software state.
- Add issuer registry and registrar records for trusted identity and service providers.
- Link releases to Knitweb dependency records.
- Emit license, clause, notice, consent, and mirror-manifest records.
- Move review state out of hosted forges.
- Publish independent `gither.github.io` site when the GitHub identity is controlled.

## Phase 3: Benchmark Harness

- Build scrubbed public corpus.
- Compile corpus into Knitweb/Lens.
- Compile same corpus into LightRAG baseline.
- Measure compile time, query time, model weight, and output quality.
- Publish reproducible benchmark fixtures.

## Phase 4: Agent Orchestration

- Add task graph records.
- Add critical-change classification.
- Add mixture-of-experts review slots.
- Add final review checklist.
- Add CI adapters for repo-local and cross-repo tests.
- Add serverless CI receipt exchange between developer nodes.
- Add DApp-ready release acceptance records.
- Add signed deployment receipts and rollback receipts.
- Add environment attestation records for continuous deployment.
- Add Pulse usage receipt ingestion.
- Add usage-based royalty split calculation.
- Add semi-commune ownership records for multi-developer repositories.
- Add repository commons share rules, contributor-share rules, and dependency-share rules.
- Add ownership dispute and arbitration records.

## Phase 5: Distribution Resilience

- Mirror Gither outside GitHub and GitLab.
- Publish source bundles.
- Add Radicle repository identity.
- Add p2p forge-state exchange.
- Add serverless issue and review-state replication.
- Add license-aware p2p mirror negotiation.
- Add encrypted evidence-envelope references for optional vBank-backed agent identity.
- Add hybrid secp256k1 + post-quantum signature policy for critical records.
- Add `sha256.fail` frontier-risk ingestion and crypto-policy gates.
- Archive releases with Software Heritage.
- Export manifests for offline recovery.
