"""Append one entry to wiki/log.md in the fixed format

    ## [YYYY-MM-DD] operation | title
    optional note lines

so that `grep "^## \\[" wiki/log.md` lists every operation.

Usage:
    python log.py ingest "Karpathy: LLM Wiki gist" --note "touched 6 pages"
    python log.py query "Does RAG scale better than a wiki?"
    python log.py lint "monthly" --note "0 errors, 3 warnings"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as W  # noqa: E402

OPERATIONS = ("init", "ingest", "query", "lint", "note")


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("operation", choices=OPERATIONS)
    ap.add_argument("title")
    ap.add_argument("--note", action="append", default=[], help="extra line(s) under the heading")
    ap.add_argument("--print-only", action="store_true", help="print the entry, do not write")
    args = ap.parse_args(argv)

    vault = W.find_vault()
    cfg = W.load_config(vault)
    log_path = vault / cfg["wiki_dir"] / "log.md"

    title = " ".join(args.title.split())
    entry = f"## [{W.today()}] {args.operation} | {title}\n"
    for note in args.note:
        entry += f"{note.strip()}\n"
    entry += "\n"

    if args.print_only:
        print(entry, end="")
        return 0
    if not log_path.is_file():
        W.write_text(log_path, "# Log\n\n")
    with log_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(entry)
    print(entry.split("\n")[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
