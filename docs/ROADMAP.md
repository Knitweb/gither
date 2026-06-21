# Forge Roadmap

## Phase 1: Current Build

- Workspace manifest.
- Repo discovery.
- Request routing.
- Test-plan output.
- Repo graph export.
- Benchmark plan.
- Documentation site.

## Phase 2: Knitweb Integration

- Emit canonical Knitweb records for repos, docs, commands, and routes.
- Add content-addressed graph export.
- Track which routes were correct after human review.
- Feed accepted routing decisions into Lens.

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

## Phase 5: Distribution Resilience

- Mirror Forge outside GitHub.
- Publish source bundles.
- Add Radicle repository identity.
- Archive releases with Software Heritage.
- Export manifests for offline recovery.
