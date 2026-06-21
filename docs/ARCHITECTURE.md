# Gither Architecture

Gither has one primary job: own the code forge layer for Knitweb.

It should replace GitHub and GitLab as the trusted application layer for repository
state, change review, CI receipts, and releases.

The first external positioning is intentionally simple: Gither is a peer-to-peer
duplicate of GitHub.
It preserves the familiar forge workflow while moving authority into portable records
that can survive GitHub, GitLab, hosted CI, and server lockout.

It is not a replacement for Git at the object-storage level yet.
Git remains the open-source, de-facto interoperable substrate while Gither builds the
serverless forge layer above it.

GitLab is not the final alternative because it still relies on servers, operators,
accounts, backups, and platform uptime.
Gither can mirror to GitLab, but it should not depend on GitLab as the authority.

## Components

### Repository Registry

The registry lists repositories, paths, roles, keywords, remotes, and test commands.

This gives the agent a stable map before it edits code.

### Repository Snapshot

The snapshot command records branch, head commit, dirty state, changed files, and
remotes.

This is the minimum codebase state required before a review can mean anything.

### Router

The router scores a plain-language request against the workspace manifest.

It intentionally starts simple:

- repo name match;
- keyword match;
- role overlap;
- documentation reference.

The first version is deterministic and inspectable.
Later versions can add Knitweb graph records and Lens reasoning on top.

### Changebook

The changebook writes `.gither/changes/*.json` records.

Each record stores the change reason, programmer background notes, tests, repository
state, and current diff names.

### Review Gate

The local gate combines repository state and source audit.

The first implementation audits Python syntax, annotations, docstrings, and symbol
size.

### Test Planner

The test planner prints the test commands attached to each repo.

This answers the practical question: when a change crosses repo boundaries, what must
be checked?

### Graph Export

The graph exporter produces a JSON relation graph from shared repo keywords.

This is not the final Knitweb graph.
It is a bootstrap graph that can be loaded by Lens, Monitor, or the 3D Molgang graph.

### Benchmark Plan

The benchmark plan defines how to compare Knitweb/Lens against LightRAG-style systems.

The core claim to test is:

```text
No LLM is needed at compile time when the graph is already knitted.
```

## Data Flow

```text
request -> workspace manifest -> router -> target repos -> repo tests -> graph export
```

The agent can still use a frontier model for reasoning, but Gither owns the code
state and review gate first.

## Boundaries

Gither does not:

- run untrusted code automatically;
- merge pull requests;
- replace repository-specific tests;
- claim benchmark wins before data exists;
- upload private corpus data.
- treat GitHub or GitLab as the authority.

Gither does:

- map repos;
- route tasks;
- record repository state;
- write versioned change notes;
- audit Python code discipline;
- gate local review;
- expose test plans;
- export graph metadata;
- document benchmark criteria.
