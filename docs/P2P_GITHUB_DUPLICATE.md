# P2P GitHub Duplicate

Gither should first be sold as a peer-to-peer duplicate of GitHub.

That framing is deliberately direct.
Developers already understand GitHub.
Gither starts by preserving that mental model while removing the platform as the final
authority.

## Promise

Gither is a portable code forge for Web3 and serverless development.

It duplicates the useful parts of GitHub:

- repository identity;
- source browsing;
- change proposals;
- review state;
- CI receipts;
- release manifests;
- ownership records;
- mirror publication.

It then changes the authority model:

```text
GitHub host -> optional mirror
Gither records -> portable source of authority
Knitweb graph -> dependency and provenance layer
Pulse receipts -> usage and activity layer
```

## Why Not GitLab

GitLab is not a sufficient alternative to GitHub for this goal.

It can reduce dependency on Microsoft-owned GitHub, but it still assumes servers,
operators, hosted instances, backups, account systems, and platform availability.

That means it is still a forge platform.
It is not a serverless, peer-to-peer, portable authority layer.

For Gither, GitLab can be a mirror or migration bridge.
It should not be positioned as the end state.

## Microsoft Lockout Risk

GitHub is owned by Microsoft.
That creates a strategic lockout risk for software projects that depend on GitHub as
their only forge, CI history, release surface, issue memory, and social graph.

Gither should not exaggerate this risk into a claim that GitHub is unusable.
The point is narrower and stronger:

```text
critical open-source infrastructure should be portable before a lockout happens
```

The p2p duplicate gives developers a familiar escape path before they need it.

## Web3 And Serverless Portability

The target is not just another hosted forge.

Gither should make repository state portable across:

- local developer machines;
- static websites;
- p2p storage;
- Git mirrors;
- signed Knitweb records;
- Pulse usage receipts;
- DApp-compatible settlement systems.

This is why Gither keeps Git compatibility while moving review state, CI receipts,
ownership, and release policy into portable records.

## Site Target

The preferred public identity is:

```text
https://gither.github.io/
```

That is risky because GitHub Pages user sites require control of the GitHub account or
organization named `gither`.
If that account is not controlled, the fallback remains:

```text
https://knitweb.github.io/gither/
```

The product message should still point toward an independent Gither identity, because
the project is meant to become portable beyond Knitweb and beyond GitHub.
