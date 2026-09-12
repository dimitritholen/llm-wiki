"""Verify citations.

Every footnote definition of the form

    [^id]: raw/path.md | "verbatim anchor"

must point at an existing file under raw/ and the anchor must occur in that
file after whitespace and quote normalisation. Source pages must carry at
least one citation. Footnote references without a definition, and definitions
without a reference, are reported.

Usage:
    python cite.py                 # every page under wiki/
    python cite.py wiki/sources/x.md [more pages]
    python cite.py --json
Exit code 1 when any error is found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as W  # noqa: E402


def check_page(vault: Path, cfg: dict, page: W.Page, raw_cache: dict) -> list[W.Finding]:
    out: list[W.Finding] = []
    refs = set(page.footnote_refs)
    defs = page.footnote_defs

    for fid in sorted(refs - set(defs)):
        out.append(W.Finding("error", "cite-undefined", page.relpath, f"[^{fid}] is referenced but never defined"))
    for fid in sorted(set(defs) - refs):
        out.append(W.Finding("warning", "cite-unused", page.relpath, f"[^{fid}] is defined but never referenced"))

    raw_prefix = cfg["raw_dir"].rstrip("/") + "/"
    for fid, (raw_rel, anchor) in defs.items():
        if not raw_rel.startswith(raw_prefix):
            out.append(W.Finding("error", "cite-not-raw", page.relpath, f"[^{fid}] points outside {raw_prefix}: {raw_rel}"))
            continue
        raw_path = vault / raw_rel
        if not raw_path.is_file():
            out.append(W.Finding("error", "cite-missing-file", page.relpath, f"[^{fid}] file not found: {raw_rel}"))
            continue
        if not anchor.strip():
            out.append(W.Finding("error", "cite-empty-anchor", page.relpath, f"[^{fid}] has an empty anchor"))
            continue
        if raw_rel not in raw_cache:
            try:
                raw_cache[raw_rel] = W.read_text(raw_path)
            except UnicodeDecodeError:
                raw_cache[raw_rel] = None
        raw_text = raw_cache[raw_rel]
        if raw_text is None:
            out.append(W.Finding("warning", "cite-binary", page.relpath, f"[^{fid}] points at a non-text file; anchor not checked"))
            continue
        if not W.anchor_found(anchor, raw_text):
            out.append(W.Finding("error", "cite-anchor", page.relpath, f'[^{fid}] anchor not found in {raw_rel}: "{anchor[:60]}"'))

    if page.kind == "source" and not defs:
        out.append(W.Finding("error", "cite-none", page.relpath, "source page has no citations"))
    return out


def run(vault: Path, cfg: dict, pages: list[W.Page]) -> list[W.Finding]:
    findings: list[W.Finding] = []
    raw_cache: dict = {}
    for page in pages:
        if W.is_special(page, cfg):
            continue
        findings.extend(check_page(vault, cfg, page, raw_cache))
    return findings


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="*", help="pages to check (default: all under wiki/)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    vault = W.find_vault()
    cfg = W.load_config(vault)
    if args.pages:
        pages = [W.load_page(vault, (Path.cwd() / p).resolve()) for p in args.pages]
    else:
        pages = W.iter_wiki_pages(vault, cfg)
    findings = run(vault, cfg, pages)
    W.print_findings(findings, args.json)
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
