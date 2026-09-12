---
title: LLM Wiki
source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
author: Andrej Karpathy
published: 2026-04-04
clipped: 2026-09-12
---

# LLM Wiki (excerpt)

Excerpt of the public gist, kept short for the example vault. The full text
is at the source URL above.

Most people's experience with LLMs and documents looks like RAG: you upload a
collection of files, the LLM retrieves relevant chunks at query time, and
generates an answer. This works, but the LLM is rediscovering knowledge from
scratch on every question. There's no accumulation.

Instead of just retrieving from raw documents at query time, the LLM
incrementally builds and maintains a persistent wiki — a structured,
interlinked collection of markdown files that sits between you and the raw
sources. The knowledge is compiled once and then kept current, not re-derived
on every query.

There are three layers. Raw sources — your curated collection of source
documents. These are immutable — the LLM reads from them but never modifies
them. The wiki — a directory of LLM-generated markdown files. The LLM owns
this layer entirely. The schema — a document (e.g. CLAUDE.md for Claude Code
or AGENTS.md for Codex) that tells the LLM how the wiki is structured.

A single source might touch 10-15 wiki pages.

Related post on X, 2 April 2026: "You rarely ever write or edit the wiki
manually, it's the domain of the LLM."
