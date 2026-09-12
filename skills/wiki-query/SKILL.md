---
name: wiki-query
description: Answer a question from the wiki, with citations to wiki pages and their raw anchors, and file the answer back so it compounds. Use when the user asks a question about the material in the vault, says "ask the wiki", "what do my sources say about", or "query".
argument-hint: "[question] [--file]"
allowed-tools: Bash(python:*) Bash(git:*) Read Write Glob Grep
---

# wiki-query

Answer from the compiled wiki, not from your training data and not from
raw/ directly. Say so when the wiki does not cover the question.

If `.wiki/scripts/search.py` does not exist in the vault root, run the
`wiki-init` skill on this directory first.

## Steps

1. **Search.** Run `python .wiki/scripts/search.py "<question terms>" -k 10`.
   Rephrase once with synonyms if the top hits look weak. Read
   `wiki/index.md` when the question is broad.
2. **Read.** Open every relevant hit in full, plus the pages they link to
   when the question spans them. Check `wiki/disputes.md` for the topic; a
   disputed claim is reported as disputed, not picked silently.
3. **Verify the claims you will lean on.** For any sentence that decides the
   answer, open the cited raw anchor and confirm it says what the page says.
   If it does not, say so in the answer and note the page for wiki-lint.
4. **Answer.** Lead with the answer. Cite as `[[Page Name]]` after each claim.
   Where a raw anchor was checked, add the footnote id from that page in
   parentheses so a reader can trace it. Distinguish three things plainly:
   what the sources say, what the wiki's synthesis pages infer, and what you
   are inferring now. State what the wiki does not cover.
5. **File back.** Always write the answer to
   `output/YYYY-MM-DD-<slug>.md` with the question, the answer, and the list
   of pages read. If the answer is reusable knowledge (a comparison, a
   resolved question, a gap analysis) or the user passed `--file`, also
   create `wiki/analyses/<slug>.md` from the analysis template with
   `kind: analysis` (or `synthesis` when it is mostly inference), citing the
   raw anchors you verified, then run:

   ```
   python .wiki/scripts/cite.py wiki/analyses/<slug>.md
   python .wiki/scripts/build_index.py
   python .wiki/scripts/lint.py
   ```

6. **Log and commit.**

   ```
   python .wiki/scripts/log.py query "<question>" --note "filed to output/...; analysis page: yes|no"
   git add -A && git commit -q -m "query | <question>"
   ```

## Do not

- Do not answer from raw/ when a wiki page exists; if the wiki is thin on the
  topic, say that the source should be ingested and offer to do it.
- Do not resolve a dispute in the answer. Present both sides with citations.
- Do not touch `## My take` sections.
