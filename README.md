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

## Requirements

- Python 3.10 or newer on `PATH` as `python`. The scripts use the standard
  library only.
- git, for the per-operation commits and for cloning this repo.
- One of the agents below. Obsidian is optional but the intended viewer.

Every install starts the same way: clone the repo, then scaffold a vault.

```
git clone https://github.com/dimitritholen/llm-wiki
python llm-wiki/scripts/init.py ~/vaults/research
```

`init.py` writes the schema files, creates `raw/`, `wiki/` and `output/`,
copies the scripts and templates into `.wiki/`, and copies the four skills
into `.agents/skills/`. The vault is self-contained after that; the clone is
only needed again to scaffold another vault or to update.

## Install for Claude Code

The plugin carries the four skills, the `wiki-auditor` agent and the
PreToolUse hook that makes `raw/` read only. Two ways to load it.

**From the GitHub repo**, inside Claude Code:

```
/plugin marketplace add dimitritholen/llm-wiki
/plugin install llm-wiki@llm-wiki
```

**From a local clone**, for development or when you prefer not to install:

```
claude --plugin-dir ./llm-wiki
```

Then open the vault:

```
cd ~/vaults/research
claude
/llm-wiki:wiki-ingest
```

The skills are `/llm-wiki:wiki-init`, `/llm-wiki:wiki-ingest`,
`/llm-wiki:wiki-query` and `/llm-wiki:wiki-lint`. `wiki-init` is hidden from
the model and only runs when you invoke it. Verify the hook once by asking
Claude to edit a file under `raw/`; the request must be denied with the
message "raw/ is immutable".

## Install for Codex

Codex reads project skills from `.agents/skills/` and `AGENTS.md` from the
vault root. `init.py` writes both, so nothing else is required:

```
cd ~/vaults/research
codex
```

Type `$` to see the skills; they are `$wiki-ingest`, `$wiki-query`,
`$wiki-lint` and `$wiki-init`. Codex also picks them implicitly when the
request matches the skill description. To have them in every project rather
than per vault:

```
python llm-wiki/scripts/install_skills.py codex
```

which copies them to `~/.codex/skills/`. Restart Codex after installing.
Codex has no equivalent of the raw/ guard hook; the `AGENTS.md` and `WIKI.md`
text is what keeps sources read only, and git history is the backstop.

## Install for Hermes

Hermes loads skills from `~/.hermes/skills/` and makes each one a slash
command. Install the four skills there:

```
python llm-wiki/scripts/install_skills.py hermes
```

They land in `~/.hermes/skills/llm-wiki/wiki-*/`. Start a new session, or
`/reset` in the current one, then:

```
cd ~/vaults/research
hermes
/wiki-ingest
```

Two alternatives. Point Hermes at the vault's own copy instead of installing
globally:

```
export HERMES_OPTIONAL_SKILLS_DIR=~/vaults/research/.agents/skills
```

Or, if you make the repo public, install straight from GitHub:

```
hermes skills install dimitritholen/llm-wiki/skills/wiki-ingest
```

Hermes reads the same `SKILL.md` files; the frontmatter carries a
`metadata.hermes` block with tags and category so they file correctly in
`/skills list`. Hermes has no PreToolUse hook, so `raw/` protection rests on
the schema text and git, as with Codex.

## Other agents

Gemini CLI, GitHub Copilot, Cline, Amp and Cursor read `.agents/skills/` in
the project, so a scaffolded vault works as is. For a user-level install:

```
python llm-wiki/scripts/install_skills.py agents      # ~/.agents/skills/
python llm-wiki/scripts/install_skills.py <agent> --link   # symlink instead of copy
python llm-wiki/scripts/install_skills.py <agent> --remove
```

The [`skills` CLI](https://github.com/vercel-labs/skills) also understands
this repo: `npx skills add dimitritholen/llm-wiki -a codex -a hermes-agent`.

## Quick start

```
cd ~/vaults/research
# drop a markdown file into raw/ (Obsidian Web Clipper works well)
python .wiki/scripts/status.py          # shows it as pending
```

Then, in your agent: "ingest the pending source". The agent reads it,
searches the wiki for related pages, shows a plan, writes the pages with
citations, verifies, logs and commits. Open the folder in Obsidian to browse.

Ask questions with the `wiki-query` skill. Run `wiki-lint` monthly, with
`--semantic` when you want the second-model audit.

## Updating

```
cd llm-wiki && git pull
python llm-wiki/scripts/init.py ~/vaults/research --force
```

`--force` replaces `WIKI.md`, `CLAUDE.md`, `AGENTS.md`, `wiki.json`, the
scripts, templates and skills in the vault. It never touches `raw/`,
`wiki/`, `output/` or `.wiki/state.json`. If you edited `WIKI.md` for your
domain, diff before forcing. Claude Code plugin users also run
`/plugin update llm-wiki`.

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
.agents/skills/    the four skills, discovered by Codex and others
.wiki/
  state.json       ingest state per raw file
  scripts/ templates/
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
| `init.py <dir> [--force]` | Scaffolds a vault, or refreshes its scripts, templates and skills. |
| `install_skills.py <hermes\|codex\|claude\|agents>` | Copies the skills into that agent's user-level skills directory. |

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
