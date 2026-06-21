# Forge

Forge is the Knitweb multi-repo build and navigation layer.
It does not replace Git.
It tells an agent, developer, or reviewer which repository should change, which tests
prove the change, and how the resulting knowledge can be connected back into the
Knitweb graph.

The first goal is practical:

- stop manual project switching from becoming chaos;
- keep separate repositories without losing the whole-system view;
- route a request to the right repo from plain language;
- generate a repo relation graph;
- produce a test plan across the portfolio;
- document benchmark criteria for Knitweb/Lens versus LightRAG-style systems.

The product idea is simple: **no LLM at compile time when the graph is already
knitted**.
Small changes should update deterministic relations and metadata instead of forcing
an expensive full graph rebuild.

## Why Forge

Knitweb is becoming a portfolio:

- `knitweb` is the relation fabric and content-addressed graph layer.
- `pulse` is the token and live-state layer.
- `lens` is the reasoning and query layer.
- `monitor` observes repository and network activity.
- `vbank` handles governance and time-series signals.
- `bt` is the basket-trust DEX.
- `molgang` is the game and P2P deployment surface.

Separate repos reduce spaghetti code, but they create a coordination problem.
Forge is the coordination layer.

## Install

```bash
python -m pip install -e .
```

## Commands

Discover local repositories:

```bash
forge discover --root /Users/develuse/repo --output forge.workspace.json
```

Route a task:

```bash
forge route "benchmark Lens against LightRAG and expose graph query results"
```

Print a cross-repo test plan:

```bash
forge test-plan --workspace examples/knitweb.workspace.json
```

Export a repo graph:

```bash
forge graph --workspace examples/knitweb.workspace.json --output forge-graph.json
```

Show the benchmark plan:

```bash
forge benchmark-plan
```

## How The Agent Knows Where To Change Code

Forge uses a workspace manifest.
Each repo has roles, keywords, paths, docs, and test commands.
The router scores a user request against that manifest and returns the most likely
target repositories with reasons.

This is deliberately boring and deterministic.
The LLM can propose a plan, but Forge gives the agent a stable map before code is
touched.

## Current Status

This is a first build:

- Python CLI works.
- Workspace discovery works.
- Task routing works.
- Graph export works.
- Test-plan generation works.
- Docs are included for GitHub Pages.

It is not yet a live Knitweb indexer, Radicle mirror manager, or CI orchestrator.
Those are roadmap items.
