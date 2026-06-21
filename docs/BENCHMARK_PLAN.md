# Benchmark Plan

Gither should benchmark Knitweb/Lens against LightRAG-style systems only after the
corpus is privacy-safe.

The benchmark must not use private WhatsApp, personal notes, or unpublished business
data.

## Fair Comparison

Use the same corpus for every system.

Good first corpus:

- public README files;
- public docs;
- selected public source snippets;
- public issues or PR descriptions;
- synthetic questions with known answers.

## Metrics

### Compile Time

Measure:

- cold import from raw docs;
- incremental update after one changed document;
- graph rebuild cost;
- token usage if an LLM is used.

### Query Time

Measure:

- exact fact lookup;
- cross-repo relation query;
- "which repo should change" routing query;
- source-backed answer generation.

### Query Output

Score:

- correctness;
- source citation quality;
- provenance clarity;
- hallucination rate;
- ability to say "unknown".

### Model Weight

Classify each step:

- no model needed;
- embedding model;
- small local LLM;
- frontier LLM.

The marketing claim is strongest when compile and routing work without an LLM.

## Expected Knitweb Advantage

Knitweb's hard advantage is verifiability and provenance.

The potential advantage to measure is lower incremental cost:

```text
small corpus change -> deterministic relation update -> no full LLM graph rebuild
```

Do not claim lower latency or better answers until the benchmark proves it.
