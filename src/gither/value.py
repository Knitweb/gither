"""Knowledge ownership and usage-royalty model for Gither."""

from __future__ import annotations

VALUE_MODEL_MARKDOWN = """# Gither Value Model

Gither stores ownership of knowledge.

Git stores code.
Ethereum stores value.
Gither connects code ownership to actual software usage.

## Position

GitHub is a repository.
Gither is a marketplace for living software.

GitHub tracks commits.
Gither tracks value.

The name Gither keeps Git visible and nods to Ether as the settlement direction,
but the core mechanism is not payment for every line of code.
That would invite spam commits, commit farming, and AI-generated noise.

## Rule

Code earns only when it is actually used.

The system path is:

1. Code is committed into Gither.
2. Gither records ownership and review state.
3. Knitweb records dependency relationships between modules, services, releases, and people.
4. Pulse records real usage as signed receipts.
5. Revenue is attributed across the dependency graph.
6. Settlement distributes royalties to the components that were actually used.

## Core Records

### Ownership Record

An ownership record binds a contributor, component, change, review gate, and release.
It does not claim that a line is valuable.
It only records who owns an accepted piece of software state.

### Dependency Record

A dependency record says which components rely on which other components.
This lets revenue flow to transitive dependencies instead of only the top-level app.

### Usage Receipt

A usage receipt is emitted by Pulse when software is actually exercised.
It can describe events, calls, runtime, seats, transactions, bandwidth, or another measured unit.

### Royalty Split

A royalty split is calculated from usage receipts and dependency records.
The split rewards living dependencies according to observed demand.

## Anti-Farming Design

Gither should reject economic claims that depend only on commit count, line count, or pull-request volume.

Valid economic claims require:

- accepted review state;
- a release or deployable artifact;
- dependency links recorded by Knitweb;
- usage receipts recorded by Pulse;
- revenue or settlement input;
- reproducible split rules.

## Knitweb And Pulse

Knitweb owns the relationship graph.
Pulse owns the live usage signal.
Gither owns software identity, review state, ownership state, and royalty policy.

Together they support serverless continuous development and continuous integration:

```text
code change -> review gate -> dependency graph -> usage receipt -> royalty split
```

## Settlement

Ether is the playful and practical settlement reference in the Gither name.
The first implementation can stay ledger-neutral.
Later versions can settle through Ethereum, rollups, account abstraction, or another DApp-compatible rail.
"""


def value_model() -> str:
    """Return the Gither knowledge ownership model as Markdown."""
    return VALUE_MODEL_MARKDOWN
