"""BM25 search over the wiki pages. Standard library only, no index file;
the whole wiki is scanned per query, which is fine up to a few thousand pages.
Beyond that, point the agent at a hybrid search tool such as qmd.

Title and summary tokens count three times so a page about the query term
outranks a page that merely mentions it.

Usage:
    python search.py "contradiction resolution" [-k 8] [--kind concept] [--json]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as W  # noqa: E402

TOKEN_RE = re.compile(r"[a-z0-9]+")
K1 = 1.5
B = 0.75


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_docs(pages: list[W.Page], cfg: dict, kind: str | None) -> list[tuple[W.Page, list[str]]]:
    docs = []
    for p in pages:
        if W.is_special(p, cfg):
            continue
        if kind and p.kind != kind:
            continue
        head = f"{p.frontmatter.get('title', '')} {p.frontmatter.get('summary', '')} {p.name.replace('-', ' ')}"
        docs.append((p, tokens(head) * 3 + tokens(p.body)))
    return docs


def bm25(query: list[str], docs: list[tuple[W.Page, list[str]]]) -> list[tuple[float, W.Page]]:
    n = len(docs)
    if n == 0:
        return []
    avgdl = sum(len(t) for _, t in docs) / n
    df: Counter = Counter()
    tfs = []
    for _, toks in docs:
        tf = Counter(toks)
        tfs.append(tf)
        for term in set(toks):
            df[term] += 1
    scored = []
    for (page, toks), tf in zip(docs, tfs):
        dl = len(toks)
        score = 0.0
        for term in query:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            freq = tf[term]
            score += idf * (freq * (K1 + 1)) / (freq + K1 * (1 - B + B * dl / avgdl))
        if score > 0:
            scored.append((score, page))
    scored.sort(key=lambda x: (-x[0], x[1].relpath))
    return scored


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query")
    ap.add_argument("-k", type=int, default=10, help="number of results")
    ap.add_argument("--kind", help="restrict to one kind (source, entity, concept, analysis, synthesis)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    vault = W.find_vault()
    cfg = W.load_config(vault)
    pages = W.iter_wiki_pages(vault, cfg)
    q = tokens(args.query)
    results = bm25(q, build_docs(pages, cfg, args.kind))[: args.k]

    if args.json:
        print(json.dumps([{"score": round(s, 3), "path": p.relpath, "title": p.frontmatter.get("title", p.name), "kind": p.kind, "summary": p.frontmatter.get("summary", "")} for s, p in results], indent=2))
        return 0
    if not results:
        print("no matches")
        return 0
    for rank, (score, p) in enumerate(results, 1):
        title = p.frontmatter.get("title", p.name)
        summary = str(p.frontmatter.get("summary", "")).strip()
        print(f"{rank:2}. {score:6.2f}  {p.relpath}  [{p.kind or '?'}] {title}")
        if summary:
            print(f"            {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
