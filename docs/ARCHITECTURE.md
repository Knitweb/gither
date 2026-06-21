# Forge Architecture

Forge has one job: keep a multi-repo Knitweb system understandable and testable.

It is not a monorepo tool.
It is not a replacement for Git.
It is a deterministic control plane for agents and developers.

## Components

### Workspace Manifest

The workspace manifest lists repositories, paths, roles, keywords, docs, remotes, and
test commands.

This gives the agent a stable map before it edits code.

### Router

The router scores a plain-language request against the workspace manifest.

It intentionally starts simple:

- repo name match;
- keyword match;
- role overlap;
- documentation reference.

The first version is deterministic and inspectable.
Later versions can add Knitweb graph records and Lens reasoning on top.

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

The agent can still use a frontier model for reasoning, but Forge decides the boring
mechanical routing first.

## Boundaries

Forge does not:

- run untrusted code automatically;
- merge pull requests;
- replace repository-specific tests;
- claim benchmark wins before data exists;
- upload private corpus data.

Forge does:

- map repos;
- route tasks;
- expose test plans;
- export graph metadata;
- document benchmark criteria.
