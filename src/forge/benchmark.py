from __future__ import annotations


BENCHMARK_MARKDOWN = """# Forge Benchmark Plan

Forge should compare Knitweb/Lens against LightRAG-style baselines on the dimensions
that matter for the product claim.

## Systems

- Knitweb graph plus Lens reasoning layer.
- LightRAG or another local RAG baseline.
- Plain text search baseline.

## Required Shared Corpus

Use a scrubbed public corpus before any private material is loaded.
Good first corpus: selected public README files, docs, issues, and source snippets from
Knitweb repositories.

## Metrics

1. Compile time
   - cold import from raw documents;
   - incremental update after one small document change;
   - graph rebuild cost.

2. Query time
   - exact fact lookup;
   - cross-repo relation lookup;
   - "which repo should change" routing query;
   - code-navigation query.

3. Query output
   - answer correctness;
   - source citation quality;
   - relation provenance;
   - hallucination rate.

4. Model weight
   - no model needed;
   - small local model;
   - frontier model;
   - embedding-only model.

5. Privacy and reproducibility
   - can the system run without uploading data;
   - can the output be reproduced from deterministic graph records;
   - can the result be verified without trusting a server.

## Product Claim To Test

No LLM is needed at compile time when the graph is already knitted.
Only changed records should need deterministic relation updates.

If this holds, Forge can market Knitweb as lower-cost and more provenance-rich than
RAG systems that repeatedly reprocess the same corpus with model tokens.
"""


def benchmark_plan() -> str:
    return BENCHMARK_MARKDOWN
