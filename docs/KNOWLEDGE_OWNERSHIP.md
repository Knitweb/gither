# Knowledge Ownership

Gither stores ownership of knowledge.

```text
Git stores code.
Ethereum stores value.
Gither stores ownership of knowledge.
```

The name is intentionally compact:

- Git is visible because Gither stays compatible with the open-source Git object and transport layer.
- Ether is visible as a playful reference to DApp settlement.
- Gither also sounds like gather: collecting code, context, usage, and ownership in one system.

## Marketplace For Living Software

GitHub is a repository.
Gither is a marketplace for living software.

GitHub tracks commits.
Gither tracks value.

The first commercial message should be simpler:

```text
Gither is a peer-to-peer duplicate of GitHub,
portable to Web3 and serverless development.
```

That does not mean GitHub compatibility disappears.
It means GitHub becomes a mirror instead of the authority.

GitLab is not a good final alternative because it is also server-based.
It can reduce Microsoft GitHub dependence, but it still requires hosted instances,
operators, accounts, backups, and platform uptime.
Gither is meant to make the forge state portable before any Microsoft lockout or
hosted-platform failure matters.

That value must not be inferred from line count, commit count, or pull-request volume.
Those metrics are too easy to farm.
They also become worse when AI can generate unlimited plausible code noise.

## Royalty Rule

Code earns only when it is actually used.

The intended flow is:

```text
code committed to Gither
-> ownership accepted by review gate
-> Knitweb records dependency relationships
-> Pulse records real usage
-> revenue is attributed across dependencies
-> royalties settle to owners of used components
```

This is closer to software royalties than commit rewards.

## Ecosystem Roles

Knitweb owns the relationship layer.
It records which modules, services, protocols, releases, and communities depend on each other.

Pulse owns the live usage layer.
It records the realtime receipts that prove software was exercised.

Gither owns the software economy layer.
It records repository identity, reviewed changes, ownership state, release gates, royalty policy, and future settlement hooks.

## Anti-Farming Requirements

An economic claim should require all of these:

- accepted review state;
- a deployable release or artifact;
- dependency records in Knitweb;
- usage receipts from Pulse;
- revenue or settlement input;
- reproducible split rules.

Commits alone do not earn.
Lines alone do not earn.
AI-generated volume alone does not earn.

## Settlement Direction

Gither does not need to start as an Ethereum-only protocol.
Ether belongs in the name as a strong signal of DApp-compatible settlement, not as a premature implementation lock.

The first implementation can remain ledger-neutral while preserving the path to Ethereum, rollups, account abstraction, or another compatible settlement rail.

## Semi-Commune Ownership

Software ownership in Gither should not collapse to one maintainer just because one person
opened the repo first.

Many repositories are genuinely co-built.
In those cases, the right model is a semi-commune:

- the repository has a shared ownership pool;
- individual developers hold explicit shares inside that pool;
- some share belongs to the repository commons itself for future maintainers, fixes, and
  long-tail upkeep;
- dependency components can receive an allocated share when their code is actually used.

This avoids two failures:

1. fake individual ownership over obviously collective work;
2. total collectivization with no attributable economic share.

The shared pool should be review-governed, not commit-count-governed.

## Multi-Developer Split Rules

The intended split should come from records, not from folklore.

At minimum Gither should record:

- founding maintainer shares;
- accepted contributor shares;
- repository commons share;
- dependency royalty share;
- dispute or override decisions;
- vesting or dilution rules when the team changes.

That means a repo can say, for example:

```text
40% founding maintainers
25% active contributors
20% repository commons
15% upstream dependencies
```

The exact percentages are governance decisions.
The important point is that they are explicit, reviewable, and portable.

## Issuer And Registrar Path

If ownership or release authority needs stronger accountability, Gither should support an
issuer-registrar path:

- an issuer verifies a natural person or service role;
- a registrar records whether that issuer is accepted for a repository, team, or network;
- Vank can issue the resulting agent attestation;
- Gither can require that attestation for sensitive actions such as release signing,
  treasury control, or ownership disputes.

This keeps ordinary coding open while letting high-risk actions move onto a stronger trust
rail.
