# Code Knowledge Graph (Phase 1)

Gither needs to reason about *code*, not just about repositories. This phase
introduces a content-addressed code knowledge graph and seeds it from a clean,
human-crafted multilingual corpus.

## Why Rosetta Code as the first corpus

Phase 1 is deliberately small and clean. We start from
[Rosetta Code](https://rosettacode.org) because every task there is:

- a single self-contained functional unit;
- solved in many languages (one task can have hundreds of language solutions);
- tagged with semantic metadata (`task feature`, `Category`) that classifies
  the task — the over-arching topic layer we need to group code across tasks;
- human-written reference code, not AI output.

That gives us a reliable multilingual bridge (same task, many languages) before
we go anywhere near deep, messy production code.

## What Phase 1 does

- Import tasks from `Category:Solutions_by_Programming_Task` via the MediaWiki
  API (`src/gither/codegraph/rosetta.py`).
- Parse each task into three content-addressed record kinds:

  | kind          | meaning                                              |
  | ------------- | ---------------------------------------------------- |
  | `task_concept`| the task, its description and classifying metadata   |
  | `code_chunk`  | one `<syntaxhighlight>` block in one language        |
  | `lang_bridge` | derived edge: which languages solve a given task     |

- Hash identity is `sha256` over canonical bytes (trailing whitespace stripped),
  matching the canonical-layer rule in `docs/HASHGRAPH_NAVIGATION.md`.
- Zero runtime dependencies — only the standard library. HTTP goes through a
  swappable `http_get` callable (default backend: `curl`, because this macOS
  framework Python lacks CA certs for `urllib`).
- Query layer (`src/gither/codegraph/query.py` + `gither rosetta-query`) answers:
  stats, languages-for-task, chunks (optionally one language), tasks-by-feature,
  **tasks-by-category** (the real classification layer), free-text search, and
  top-tasks-by-language-count.

### CLI

```bash
gither rosetta-import --limit 20 --output-dir artifacts/codegraph --pause 0.5
gither rosetta-query  --dir artifacts/codegraph --action stats
gither rosetta-query  --dir artifacts/codegraph --action category --category Geometry
gither rosetta-query  --dir artifacts/codegraph --action chunks --task "100 doors" --language Python
```

Writes `tasks.jsonl`, `chunks.jsonl`, `bridges.jsonl` (one JSON record per line,
stable key order, so the output is diff-friendly).

## Classification metadata: Category vs task feature

Rosetta offers two semantic layers; we extract both but they are **not** equal:

- `[[task feature::...]]` is rare in practice (~0.3% of tasks).
- `[[Category:...]]` is the real classification layer (~28% of tasks, 85+
  distinct categories: Geometry, Puzzles, String manipulation, ...).

Use `rosetta-query --action category` for topic grouping.

## What Phase 1 does NOT do (on purpose)

These are deferred to later phases and called out here so expectations stay
honest:

- **No tree-sitter / deep call-edges in Phase 1.** Per-chunk dependency
  resolution is Phase 2 (`src/gither/codegraph/analyze.py`, optional dependency).
- **No float embeddings.** Per `HASHGRAPH_NAVIGATION.md`, embeddings are not
  canonical identity. They may anchor *outside* the canonical layer later.
- **Description text is cleaned** (HTML tags stripped, entities unescaped) but a
  handful of edge-case entities may survive (~1/686 tasks in the full corpus).

## Phase 2: tree-sitter depth (`src/gither/codegraph/analyze.py`)

Adds intra-repo **call-edges**, **definitions** and **imports** for real
repositories. tree-sitter is an **optional** dependency
(`pip install -e .[analyze]`); the core package stays `dependencies = []` and
the analyzer raises a clear error if the packages are missing. The incremental
snapshot layer in `src/gither/codegraph/store.py` reuses unchanged files by
checking `mtime_ns`, size and content hash before re-running tree-sitter.

```bash
gither analyze-python --root /path/to/repo/src
gither analyze-python --root /path/to/repo/src --snapshot-file .gither/codegraph.snapshot.json
```

Verified on `psf/requests` (19 files -> 320 definitions, 985 call-edges, 130
imports, 36.5% intra-repo call resolution) and on gither itself. The same
content-addressed record style means Phase-1 and Phase-2 records compose into
one graph.

## Phases (status)

1. **Rosetta kernel** - DONE. Multilingual bridge + task classification, full
   corpus import (686 tasks / ~44k chunks).
2. **Top open-source corpora** - PARTIAL. Python via tree-sitter works
   (`analyze-python`); Rust/Java/Go/C++ grammars and per-language metadata
   extraction still TODO. postgres / spark / dbt / polars are the targets.
3. **Our own code** - planned. Same pipeline plus links to the existing Gither
   workspace, license records, and Knitweb dependency records.

## Tests

`tests/test_codegraph.py` covers the pure parser on synthetic wikitext fixtures
(no network), including display-alias normalization (`C sharp|C#`), multi-block
language sections, `task feature` and `works with` extraction, and content-hash
stability.
