# Hashgraph Navigation

Forge is a step toward a code navigation mechanism for AI-built systems.

The idea from the chat:

```text
Hash the top open-source AI tools and search over their relationships.
```

This is not Git replacement.
Git stores history and source.
Knitweb can store deterministic relationships between source, docs, tasks, agents,
and outcomes.

## What Gets Hashed

The source layer should hash canonical deterministic bytes:

- code chunks;
- documentation chunks;
- relationships;
- task records;
- review records;
- benchmark records.

Those hashes become content-addressed nodes or relations.

## What Does Not Get Hashed Directly

Do not hash raw float embeddings as canonical source identity.

Float encodings can differ across machines and runtimes.
That breaks deterministic content addressing.

Instead:

- anchor full-precision vectors outside the canonical layer; or
- quantize vectors into fixed-point integer representations before they enter the
  deterministic layer.

## Query Goal

A vibe coder should be able to ask:

```text
Which existing open-source tool has solved the same workflow problem?
```

The system should return:

- related projects;
- useful implementation atoms;
- source references;
- what worked in prior contexts;
- what failed in prior contexts.

That feedback loop matters more than search alone.
Search tells you what matched.
Forge should eventually tell you what worked.
