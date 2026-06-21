# Gither Code Forge

Gither is for the codebase first.

Documentation is generated, maintained, or corrected only because a code change needs
clear background and reviewable context.

## Core Objects

### Repository

A repository has:

- local path;
- identity;
- current branch;
- head commit;
- dirty state;
- remotes;
- review rules.

### Change Note

A change note explains:

- what changed;
- why it changed;
- which tests prove it;
- what background a programmer must know;
- which files are in the current diff.

Gither stores these notes in:

```text
.gither/changes/
```

### Review Gate

A gate checks:

- repository state;
- Python syntax;
- type annotations;
- symbol docstrings;
- function size;
- configured tests.

The first implementation is local and Git-backed.
Later versions should write signed Knitweb records.

### CI Receipt

A CI receipt should eventually record:

- command;
- environment;
- result;
- output hash;
- timestamp;
- signer;
- related change note.

This makes continuous integration serverless-friendly because the receipt can travel
as a signed record instead of living only in one hosted CI service.

### Ownership Record

An ownership record binds accepted software state to its contributor, review gate,
release, and dependency position.

It is not a claim that a line of code is valuable.
Value is only measured later through actual use.

### Usage-Based Royalty

Gither should treat revenue distribution as a royalty problem, not a commit reward
problem.

Knitweb records the dependency graph.
Pulse records usage receipts.
Gither applies reproducible split rules to the components that were actually used.

## Serverless Direction

The long-term Gither model is:

```text
developer node -> signed change -> local tests -> signed CI receipt -> mirrored release
```

No hosted platform should be mandatory.
Hosted platforms can still help with discovery and redundancy.
