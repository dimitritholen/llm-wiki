"""Mechanical health check for the wiki. No model involved.

Errors (exit 1):
    link-broken          [[wikilink]] to a page that does not exist
    link-ambiguous       two pages share a filename, so wikilinks cannot resolve
    fm-missing           required frontmatter key absent
    fm-kind              kind does not match the directory
    human-missing        source page lacks the human section
    cite-*               citation problems (see cite.py)
    raw-changed          raw file changed after it was compiled
    raw-gone             state entry for a raw file that no longer exists

Warnings (exit 0, or 1 with --strict):
    human-empty          human section still empty
    stale                last_verified older than stale_days
    orphan               no other page links here
    raw-uncompiled       raw file never ingested
    index-drift          generated indexes are out of date
    cite-unused          footnote defined but never referenced

Usage:
    python lint.py [--json] [--strict]
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index  # noqa: E402
import cite  # noqa: E402
import wikilib as W  # noqa: E402


def run(vault: Path, cfg: dict) -> list[W.Finding]:
    findings: list[W.Finding] = []
    pages = W.iter_wiki_pages(vault, cfg)
    raw_files = W.iter_raw_files(vault, cfg)
    state = W.load_state(vault, cfg)
    human = cfg["human_section"]
    required = cfg["required_frontmatter"]
    stale_days = int(cfg["stale_days"])

    # Link targets: every markdown file under wiki/ and raw/, by lowercase stem.
    targets: dict[str, list[str]] = defaultdict(list)
    for p in pages:
        targets[p.name.lower()].append(p.relpath)
    for rf in raw_files:
        if rf.suffix.lower() == ".md":
            targets[rf.stem.lower()].append(W.rel(vault, rf))
    special_stems = {Path(s).stem.lower() for s in cfg["special_pages"]}
    for name, paths in sorted(targets.items()):
        if name in special_stems:
            continue  # one index.md per directory is by design
        wiki_paths = [x for x in paths if x.startswith(cfg["wiki_dir"] + "/")]
        if len(wiki_paths) > 1:
            findings.append(W.Finding("error", "link-ambiguous", wiki_paths[0], f"filename '{name}.md' also used by: {', '.join(wiki_paths[1:])}"))

    inbound: dict[str, int] = defaultdict(int)
    content_pages = [p for p in pages if not W.is_special(p, cfg)]
    linking_pages = [p for p in pages if p.path.name not in ("index.md", "disputes.md", "log.md")]
    for p in linking_pages:
        for target in p.links:
            # Obsidian may emit path-style links ([[sources/foo]] or [[foo.md]]);
            # resolve on the last segment without the extension.
            key = target.strip().replace("\\", "/").rsplit("/", 1)[-1].lower()
            if key.endswith(".md"):
                key = key[:-3]
            if key in targets:
                if key != p.name.lower():
                    inbound[key] += 1
            else:
                findings.append(W.Finding("error", "link-broken", p.relpath, f"[[{target}]] does not resolve"))

    today = date.today()
    for p in content_pages:
        expected_kind = W.page_dir_kind(p, vault, cfg)
        if expected_kind is None:
            continue  # a page outside the known directories is not checked for frontmatter
        for key in required:
            if not str(p.frontmatter.get(key, "")).strip():
                findings.append(W.Finding("error", "fm-missing", p.relpath, f"frontmatter '{key}' missing or empty"))
        if p.kind and p.kind not in (expected_kind, "synthesis"):
            findings.append(W.Finding("error", "fm-kind", p.relpath, f"kind '{p.kind}' in directory for '{expected_kind}'"))
        if expected_kind == "source":
            if human not in p.sections:
                findings.append(W.Finding("error", "human-missing", p.relpath, f"no '## {human}' section"))
            elif W.section_is_empty(p.sections[human]):
                findings.append(W.Finding("warning", "human-empty", p.relpath, f"'## {human}' is still empty"))
        verified = W.parse_date(p.frontmatter.get("last_verified"))
        if verified and (today - verified).days > stale_days:
            findings.append(W.Finding("warning", "stale", p.relpath, f"last_verified {verified.isoformat()} is older than {stale_days} days"))
        if inbound[p.name.lower()] == 0:
            findings.append(W.Finding("warning", "orphan", p.relpath, "no other page links here"))

    findings.extend(cite.run(vault, cfg, pages))

    for rf in raw_files:
        relpath = W.rel(vault, rf)
        entry = state.get(relpath)
        if entry is None:
            findings.append(W.Finding("warning", "raw-uncompiled", relpath, "never ingested"))
        elif entry.get("sha256") != W.file_sha256(rf):
            findings.append(W.Finding("error", "raw-changed", relpath, "changed since it was compiled; re-ingest or run mark_compiled.py --forget"))
    for relpath in state:
        if not (vault / relpath).is_file():
            findings.append(W.Finding("error", "raw-gone", relpath, "in state.json but the file is missing"))

    stale_indexes = build_index.drift(vault, build_index.render(vault, cfg, pages))
    for relpath in stale_indexes:
        findings.append(W.Finding("warning", "index-drift", relpath, "out of date; run build_index.py"))

    order = {"error": 0, "warning": 1}
    findings.sort(key=lambda f: (order[f.severity], f.path, f.code))
    return findings


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    args = ap.parse_args(argv)

    vault = W.find_vault()
    cfg = W.load_config(vault)
    findings = run(vault, cfg)
    W.print_findings(findings, args.json)
    has_error = any(f.severity == "error" for f in findings)
    has_warning = any(f.severity == "warning" for f in findings)
    return 1 if has_error or (args.strict and has_warning) else 0


if __name__ == "__main__":
    raise SystemExit(main())
