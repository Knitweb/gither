# Gither

Gither is the ownership layer of the knowledge economy.

Git stores code.
Ethereum stores value.
Gither stores ownership of knowledge.

It is the Knitweb code forge for serverless continuous development and continuous
integration.

It is meant to replace GitHub and GitLab as the trusted application layer for code
ownership, change review, release gating, and repository collaboration.
Git can still be used underneath as the open-source, de-facto interoperable object and
transport layer.
GitHub and GitLab are optional mirrors, not the authority.

GitHub is a repository.
Gither is a marketplace for living software.

GitHub tracks commits.
Gither tracks value.

Gither should first be sold as a peer-to-peer duplicate of GitHub: familiar enough
for developers to adopt, but portable enough to move toward Web3 and serverless
development.
The strategic risk is Microsoft lockout through GitHub dependence.
The practical answer is not "move to GitLab."
GitLab still depends on servers, operators, hosted instances, and platform uptime.
For Gither, GitLab can be a mirror or migration bridge, not the end state.

Documentation is not the goal.
Documentation is a consequence of disciplined code changes:

- every code change has versioned context;
- the programmer records why the change exists;
- Python code is audited for annotations, docstrings, and manageable symbol size;
- tests and review gates are attached to the repository state;
- releases are accepted by Gither before they are mirrored outward.

Gither does not reward every "valuable line of code."
That framing creates the wrong incentives: spam commits, commit farming, and
AI-generated noise.
The stronger rule is:

```text
code earns only when it is actually used
```

Knitweb records dependency relationships.
Pulse records real usage.
Gither records reviewed ownership and royalty policy.
Revenue can then be distributed across the components that were actually used.

## Why Gither

Git is open source, but not a formally ratified open standard.
There is no ISO Git and no IETF RFC that defines Git as a vendor-neutral standard.
In practice, Git behaves like a strong de-facto standard because its formats and
protocols are openly documented and independently reimplemented by libraries such as
libgit2, JGit, go-git, gitoxide, Dulwich, and isomorphic-git.

Gither keeps the useful Git object model while moving the forge layer away from
central platforms.
The long-term target is a serverless developer network where code, changes, reviews,
tests, releases, and CI receipts can be verified through Knitweb records instead of
trusted through one hosted service.

## Current Build

Gither already provides:

- repository discovery;
- task routing across Knitweb repos;
- repo graph export;
- cross-repo test plan output;
- Git repository snapshots;
- Python code discipline audit;
- versioned change notes in `.gither/changes`;
- a local review gate for source state and Python quality.
- a knowledge ownership model;
- a license-aware mirror protocol;
- p2p GitHub-duplicate positioning for Web3/serverless portability.

This is still early.
It is not yet a full GitHub/GitLab replacement, but the codebase now points in that
direction.

## Install

```bash
python -m pip install -e .
```

## Code Forge Commands

Inspect repository state:

```bash
gither repo-snapshot --repo .
```

Audit Python code discipline:

```bash
gither python-audit --root src
```

Write a versioned change note:

```bash
gither change-note \
  --summary "add deterministic review gate" \
  --why "Gither must own code quality before mirroring to external forges" \
  --test "python -m pytest -q" \
  --programmer-notes "Uses Git state for now; Knitweb signed records come next."
```

Run the local review gate:

```bash
gither gate --repo . --python-root src
```

Print the knowledge ownership model:

```bash
gither value-model
```

Print the license mirror protocol:

```bash
gither license-protocol
gither license-protocol --json
```

## Portfolio Commands

Discover local repositories:

```bash
gither discover --root /Users/develuse/repo --output gither.workspace.json
```

Route a task:

```bash
gither route "benchmark Lens against LightRAG and expose graph query results"
```

Print a cross-repo test plan:

```bash
gither test-plan --workspace examples/knitweb.workspace.json
```

Export a repo graph:

```bash
gither graph --workspace examples/knitweb.workspace.json --output gither-graph.json
```

## Authority Model

Gither should become the authority for:

- repository identity;
- signed code changes;
- review state;
- CI receipts;
- release manifests;
- license records;
- ownership records;
- usage-based royalty policy;
- mirror publication.

GitHub and GitLab should become distribution endpoints only.
If they disappear, the Gither state and Knitweb-backed records should still be enough
to continue development.

## Public Site

The desired independent site is:

```text
https://gither.github.io/
```

That requires control of the GitHub account or organization named `gither`.
Until that identity is controlled, the public fallback is:

```text
https://knitweb.github.io/gither/
```
