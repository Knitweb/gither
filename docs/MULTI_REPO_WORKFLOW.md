# Multi-Repo Agent Workflow

This document answers the practical question from the chat:

```text
How does an agent know where a change must be placed, and how do you test the whole thing?
```

## Rule 1: Keep Repos Separate

Separate repos prevent accidental spaghetti when the domains are genuinely different.

For Knitweb, the domains are different:

- graph fabric;
- token/live state;
- reasoning layer;
- monitoring layer;
- governance/time-series layer;
- DEX layer;
- game/deployment layer.

That separation is useful.
The missing piece is a map.

## Rule 2: Use Forge As The Map

Forge keeps a workspace manifest with one entry per repo.

Each entry declares:

- what the repo is for;
- which words route work there;
- where docs live;
- which tests prove the repo still works;
- whether the repo is optional or required locally.

## Normal Change Flow

1. Capture the user request.
2. Run `forge route "<request>"`.
3. Read the top repo docs.
4. Make the smallest coherent change in that repo.
5. Run that repo's tests.
6. If contracts changed, run `forge test-plan`.
7. Export the updated repo graph when topology changed.

## Example

Request:

```text
Benchmark Lens against LightRAG and compare query output.
```

Command:

```bash
forge route "Benchmark Lens against LightRAG and compare query output"
```

Expected first target:

```text
lens
```

Related repos:

```text
knitweb
forge
knitweb-monitor
```

Reason:

Lens owns reasoning and queries.
Knitweb owns the graph records.
Forge owns benchmark orchestration.
Monitor can later observe repository activity.

## Testing The Whole System

Repo-local tests prove local correctness.
Cross-repo tests prove contract compatibility.

Forge does not invent those tests.
It records and prints the test commands so they are visible in one place.

Command:

```bash
forge test-plan --workspace examples/knitweb.workspace.json
```

## Why This Beats Nine Manual Sessions

Nine open sessions can work for a founder, but it does not scale.

Forge makes the routing explicit.
An agent can enter one repo with intent, run that repo's checks, and only widen scope
when the manifest says the change touches multiple domains.
