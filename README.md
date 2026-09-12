# llm-wiki

An LLM-maintained markdown wiki for Claude Code, Codex, OpenCode and any
other agent that can read a SKILL.md and run Python. It implements Andrej
Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
pattern and closes the failure modes the pattern leaves open.

The agent compiles your raw sources into linked pages and keeps them
current. You collect sources, ask questions, and write one section per page
that the agent may not touch.

## What is different from the gist

| Problem in the plain pattern | What this plugin does |
|---|---|
| Citations are optional, so a hallucinated claim becomes a normal wiki line | Every claim on a source page is a footnote `[^n]: raw/file.md \| "verbatim anchor"`. `cite.py` proves the anchor exists in the raw file. |
| Web clips are untrusted text that the agent reads and then acts on | Schema declares sources as data. A PreToolUse hook denies every Write or Edit under `raw/`. |
| The model lints its own output | `lint.py` does the mechanical checks with no model at all. The semantic pass runs as a separate agent on a different model. |
| New facts silently overwrite old ones | Contradictions go in a `## Disputed` section, aggregated into `disputes.md`. Superseded claims stay in the text, marked. One git commit per operation. |
| One `index.md` becomes the whole context budget | Per-directory indexes generated from frontmatter, a root index of indexes, and a BM25 `search.py`. |
| Re-ingesting a source produces different pages each time | `.wiki/state.json` records the hash and the pages touched per raw file. `status.py` shows what is pending or changed. Ingest shows its plan before writing. |
| Old facts read the same as new ones | `last_verified` on every page; lint flags pages older than `stale_days`. |
| You stop understanding your own material | Every source page has a `## My take` section reserved for the human. Lint reminds you when it is empty. |
| The schema file grows into a manual | `WIKI.md` holds layout and invariants only. Workflows live in four skills. |

## Install

### Claude Code

```
git clone https://github.com/dimitritholen/llm-wiki
claude --plugin-dir ./llm-wiki
```

The skills appear as `/llm-wiki:wiki-init`, `/llm-wiki:wiki-ingest`,
`/llm-wiki:wiki-query` and `/llm-wiki:wiki-lint`. The `wiki-auditor` agent
and the raw/ guard hook load with the plugin.

### Codex, OpenCode, other agents

```
git clone https://github.com/dimitritholen/llm-wiki
python llm-wiki/scripts/init.py ~/vaults/research
```

`init.py` copies the scripts, the templates and the four SKILL.md files into
`.wiki/` inside the vault and writes an `AGENTS.md` that points at them. The
vault is self-contained; no plugin runtime is needed. The write guard is a
Claude Code hook only; other agents rely on the schema text.

## Quick start

```
python llm-wiki/scripts/init.py ~/vaults/research
cd ~/vaults/research
# drop a markdown file into raw/ (Obsidian Web Clipper works well)
python .wiki/scripts/status.py          # shows it as pending
```

Then, in your agent: "ingest the pending source". The agent reads it,
searches the wiki for related pages, shows a plan, writes the pages with
citations, verifies, logs and commits. Open the folder in Obsidian to browse.

Ask questions with the `wiki-query` skill. Run `wiki-lint` monthly, with
`--semantic` when you want the second-model audit.

## Vault layout

```
WIKI.md            schema: layout and invariants (read this)
CLAUDE.md          thin pointer for Claude Code
AGENTS.md          thin pointer for other agents
wiki.json          configuration for the scripts
raw/               immutable sources
wiki/
  index.md         generated
  log.md           append only
  overview.md      agent-written orientation
  disputes.md      generated from every "## Disputed" section
  sources/ entities/ concepts/ analyses/   each with a generated index.md
output/            query answers
.wiki/
  state.json       ingest state per raw file
  scripts/ skills/ templates/
```

## Scripts

All standard library, Python 3.10 or newer, UTF-8 everywhere. Run them from
anywhere inside the vault.

| Script | Does |
|---|---|
| `lint.py [--json] [--strict]` | All mechanical checks. Exit 1 on errors; warnings need `--strict` to fail. |
| `cite.py [pages]` | Footnote citations: file exists, anchor found verbatim, refs and defs match, source pages cite at least once. |
| `build_index.py [--check]` | Regenerates the directory indexes, the root index and `disputes.md` from frontmatter. |
| `status.py [--pending] [--json]` | Which raw files are pending, changed or compiled. |
| `mark_compiled.py <raw> --pages ...` | Records hash, time and pages touched after an ingest. |
| `search.py "<query>" [-k N] [--kind K]` | BM25 over the wiki pages, title and summary weighted. |
| `log.py <op> "<title>" [--note ...]` | Appends `## [date] op \| title` to `wiki/log.md`. |
| `init.py <dir>` | Scaffolds a vault. |

Lint codes: errors are `link-broken`, `link-ambiguous`, `fm-missing`,
`fm-kind`, `human-missing`, `cite-*`, `raw-changed`, `raw-gone`. Warnings
are `human-empty`, `stale`, `orphan`, `raw-uncompiled`, `index-drift`,
`cite-unused`.

## Page conventions

Frontmatter on every page under `sources/`, `entities/`, `concepts/`,
`analyses/`:

```
---
title: Page title
kind: source | entity | concept | analysis | synthesis
summary: One line; becomes the index entry.
sources: [raw/articles/foo.md]
created: 2026-09-12
last_verified: 2026-09-12
confidence: high | medium | low
---
```

Citations:

```
Karpathy ingests one source at a time.[^1]

[^1]: raw/articles/foo.md | "I prefer to ingest sources one at a time"
```

The anchor is compared after folding curly quotes and dashes and collapsing
whitespace. Case matters.

## Limits

- One user, one machine. No access control, no concurrency. That is the
  pattern's scope, not an oversight.
- The write guard covers the Write and Edit tools. A shell redirect can still
  write into `raw/`; git history is the backstop.
- The guard hook runs `python` from PATH. Claude Code blocks a tool call when
  its hook command cannot run, so with no Python interpreter on PATH the
  plugin blocks every Write and Edit until it is disabled or Python is
  installed.
- BM25 with no index file. Fine to a few thousand pages. Past that, point the
  skills at a hybrid search tool such as qmd.
- No tests beyond the example vault. `python scripts/lint.py` run from
  `example/vault` should report zero errors and one `human-empty` warning.

## Credits

Pattern: Andrej Karpathy, "LLM Wiki", April 2026. Vannevar Bush's Memex
before that. The adjustments come from the criticism the pattern attracted in
its first months: hallucination contamination, self-linting, overwrite drift,
index scaling and injection through sources.

License: MIT.
