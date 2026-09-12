"""Show ingest state of every raw file.

    pending   never compiled
    changed   compiled, but the raw file changed since (hash mismatch)
    compiled  up to date

Usage:
    python status.py            # human readable
    python status.py --json
    python status.py --pending  # only pending and changed, one path per line
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as W  # noqa: E402


def collect(vault: Path, cfg: dict) -> list[dict]:
    state = W.load_state(vault, cfg)
    rows = []
    for path in W.iter_raw_files(vault, cfg):
        relpath = W.rel(vault, path)
        entry = state.get(relpath)
        if entry is None:
            status = "pending"
        elif entry.get("sha256") != W.file_sha256(path):
            status = "changed"
        else:
            status = "compiled"
        rows.append(
            {
                "path": relpath,
                "status": status,
                "compiled_at": (entry or {}).get("compiled_at"),
                "pages": (entry or {}).get("pages", []),
            }
        )
    for relpath, entry in state.items():
        if not (vault / relpath).is_file():
            rows.append({"path": relpath, "status": "missing", "compiled_at": entry.get("compiled_at"), "pages": entry.get("pages", [])})
    return rows


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--pending", action="store_true", help="print only pending/changed paths")
    args = ap.parse_args(argv)

    vault = W.find_vault()
    cfg = W.load_config(vault)
    rows = collect(vault, cfg)

    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if args.pending:
        for r in rows:
            if r["status"] in ("pending", "changed"):
                print(r["path"])
        return 0
    counts = {"pending": 0, "changed": 0, "compiled": 0, "missing": 0}
    for r in rows:
        counts[r["status"]] += 1
        extra = f"  ({len(r['pages'])} pages, {r['compiled_at']})" if r["status"] == "compiled" else ""
        print(f"{r['status']:9} {r['path']}{extra}")
    print(f"\n{counts['compiled']} compiled, {counts['pending']} pending, {counts['changed']} changed, {counts['missing']} missing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
