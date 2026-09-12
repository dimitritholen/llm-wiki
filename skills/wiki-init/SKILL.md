---
name: wiki-init
description: Scaffold a new LLM wiki vault (raw/, wiki/, schema, scripts, templates) in a directory, or add the wiki files to an existing Obsidian vault. Use when the user wants to start a knowledge base, "set up the wiki", or "make this folder a vault".
argument-hint: "[target directory]"
disable-model-invocation: true
allowed-tools: Bash(python:*) Bash(git:*) Read Glob
---

# wiki-init

Turn a directory into a vault that the other skills can operate on.

## Steps

1. Decide the target directory. If the user named one, use it. Otherwise ask
   for one; default to the current directory only when it is empty or already
   an Obsidian vault.
2. Locate `init.py`. In Claude Code with the plugin installed it is at
   `${CLAUDE_PLUGIN_ROOT}/scripts/init.py`. Otherwise it is
   `scripts/init.py` inside a checkout of the llm-wiki repository; ask for
   the path if you cannot find it.
3. Run it:

   ```
   python "<path>/scripts/init.py" "<target>"
   ```

   Add `--force` only if the user explicitly wants existing schema files
   replaced. Add `--no-git` if the target is already inside a repository.
4. Read the generated `WIKI.md` back to the user in three lines: raw/ is
   immutable, citations are footnotes with verbatim anchors, `## My take` is
   theirs.
5. Tell them how sources get in: the Obsidian Web Clipper pointed at `raw/`,
   or any file copied there by hand. Then point them at `wiki-ingest`.

## Do not

- Do not create example pages. An empty wiki with an honest overview beats a
  fake one.
- Do not edit `WIKI.md` to add domain rules yet. That happens after the first
  few ingests, when the domain's conventions are visible.
