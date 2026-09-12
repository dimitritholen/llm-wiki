"""Record that a raw file has been compiled into the wiki.

Writes the file's sha256, the timestamp and the pages touched to
.wiki/state.json. Run this as the last step of an ingest, after cite.py and
lint.py pass.

Usage:
    python mark_compiled.py raw/articles/foo.md --pages wiki/sources/foo.md wiki/entities/bar.md
    python mark_compiled.py raw/articles/foo.md --forget     # drop the entry
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as W  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("raw", help="path to the raw file, relative to the vault or absolute")
    ap.add_argument("--pages", nargs="*", default=[], help="wiki pages created or updated")
    ap.add_argument("--forget", action="store_true", help="remove the entry instead")
    args = ap.parse_args(argv)

    vault = W.find_vault()
    cfg = W.load_config(vault)
    raw_path = (Path.cwd() / args.raw).resolve() if not Path(args.raw).is_absolute() else Path(args.raw)
    if not raw_path.is_file():
        raw_path = (vault / args.raw).resolve()
    if not raw_path.is_file():
        print(f"raw file not found: {args.raw}", file=sys.stderr)
        return 1
    relpath = W.rel(vault, raw_path)
    if not relpath.startswith(cfg["raw_dir"].rstrip("/") + "/"):
        print(f"not under {cfg['raw_dir']}/: {relpath}", file=sys.stderr)
        return 1

    state = W.load_state(vault, cfg)
    if args.forget:
        state.pop(relpath, None)
        W.save_state(vault, cfg, state)
        print(f"forgot {relpath}")
        return 0

    pages = []
    for p in args.pages:
        pp = Path(p)
        if not pp.is_absolute():
            pp = (Path.cwd() / p).resolve()
            if not pp.is_file():
                pp = (vault / p).resolve()
        if not pp.is_file():
            print(f"page not found: {p}", file=sys.stderr)
            return 1
        pages.append(W.rel(vault, pp))

    state[relpath] = {"sha256": W.file_sha256(raw_path), "compiled_at": W.now_iso(), "pages": sorted(set(pages))}
    W.save_state(vault, cfg, state)
    print(f"marked {relpath} compiled ({len(pages)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
