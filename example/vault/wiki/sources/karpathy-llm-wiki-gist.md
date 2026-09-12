---
title: Karpathy — LLM Wiki gist
kind: source
summary: Karpathy's April 2026 gist describing an LLM-maintained markdown wiki as an alternative to RAG, with three layers and three operations.
sources: [raw/articles/karpathy-llm-wiki-gist.md]
created: 2026-09-12
last_verified: 2026-09-12
confidence: high
---

# Karpathy — LLM Wiki gist

**Source:** `raw/articles/karpathy-llm-wiki-gist.md` · Andrej Karpathy · 2026-04-04

## Summary

The gist contrasts RAG, where the model re-derives an answer from raw chunks
on every question, with a wiki the model builds and keeps current.[^1] The
wiki is a persistent, interlinked set of markdown files between the reader
and the sources.[^2] Knowledge is compiled once and maintained rather than
recomputed per query.[^3]

## Key claims

- RAG has no accumulation; each question starts from scratch.[^1]
- Raw sources are immutable; the model reads them and never edits them.[^4]
- The wiki layer is owned entirely by the model.[^5]
- A schema file such as CLAUDE.md or AGENTS.md tells the model how the wiki is structured.[^6]
- One ingested source typically touches 10 to 15 pages.[^7]

## Related

- [[andrej-karpathy]] — author
- [[llm-wiki-pattern]] — the pattern this source defines

## My take

<!-- Reserved for the human. The agent leaves this empty. -->

[^1]: raw/articles/karpathy-llm-wiki-gist.md | "the LLM is rediscovering knowledge from scratch on every question. There's no accumulation."
[^2]: raw/articles/karpathy-llm-wiki-gist.md | "a structured, interlinked collection of markdown files that sits between you and the raw sources"
[^3]: raw/articles/karpathy-llm-wiki-gist.md | "The knowledge is compiled once and then kept current, not re-derived on every query."
[^4]: raw/articles/karpathy-llm-wiki-gist.md | "These are immutable - the LLM reads from them but never modifies them."
[^5]: raw/articles/karpathy-llm-wiki-gist.md | "The LLM owns this layer entirely."
[^6]: raw/articles/karpathy-llm-wiki-gist.md | "a document (e.g. CLAUDE.md for Claude Code or AGENTS.md for Codex) that tells the LLM how the wiki is structured"
[^7]: raw/articles/karpathy-llm-wiki-gist.md | "A single source might touch 10-15 wiki pages."
