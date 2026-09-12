---
title: LLM Wiki pattern
kind: concept
summary: Three-layer architecture (immutable raw sources, model-owned wiki, schema file) in which knowledge is compiled at ingest time instead of retrieved per query.
sources: [raw/articles/karpathy-llm-wiki-gist.md]
created: 2026-09-12
last_verified: 2026-09-12
confidence: high
---

# LLM Wiki pattern

## Definition

A knowledge base where the model incrementally builds and maintains a
persistent, interlinked markdown wiki between the reader and the raw
sources.[^1]

## How the sources treat it

- [[karpathy-llm-wiki-gist]] defines three layers: immutable raw sources, a
  model-owned wiki, and a schema document.[^2]
- The same source sets the scale of an ingest at 10 to 15 pages.[^3]

## Disputed

<!-- No disputes yet. -->

## Related

- [[andrej-karpathy]]

[^1]: raw/articles/karpathy-llm-wiki-gist.md | "the LLM incrementally builds and maintains a persistent wiki"
[^2]: raw/articles/karpathy-llm-wiki-gist.md | "There are three layers."
[^3]: raw/articles/karpathy-llm-wiki-gist.md | "A single source might touch 10-15 wiki pages."
