"""PreToolUse hook: keep raw/ immutable and generated files untouched.

Reads the hook payload on stdin. Denies Write and Edit calls whose target is
inside a vault's raw/ directory, or is one of the generated navigation files
(wiki/index.md, wiki/*/index.md, wiki/disputes.md). Allows everything else,
including all writes in directories that are not a vault (no wiki.json above
the target), so the plugin never interferes with other projects.

Only Write and Edit are covered. A shell redirect in Bash bypasses this guard;
the schema text is the second line of defence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONFIG_NAME = "wiki.json"


def find_vault(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    return None


def load_cfg(vault: Path) -> dict:
    cfg = {"raw_dir": "raw", "wiki_dir": "wiki", "page_dirs": {"sources": 1, "entities": 1, "concepts": 1, "analyses": 1}}
    try:
        cfg.update(json.loads((vault / CONFIG_NAME).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def deny(reason: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if payload.get("tool_name") not in ("Write", "Edit"):
        return 0
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("path")
    if not target:
        return 0
    path = Path(target)
    if not path.is_absolute():
        path = Path(payload.get("cwd") or Path.cwd()) / path
    path = path.resolve()
    vault = find_vault(path.parent)
    if vault is None:
        return 0
    cfg = load_cfg(vault)
    try:
        relparts = path.relative_to(vault).parts
    except ValueError:
        return 0
    if not relparts:
        return 0
    if relparts[0] == cfg["raw_dir"]:
        return deny(f"{cfg['raw_dir']}/ is immutable: sources are read only. Add a new file through the clipper or the shell, never edit one.")
    wiki = cfg["wiki_dir"]
    generated = {(wiki, "index.md"), (wiki, "disputes.md")} | {(wiki, d, "index.md") for d in cfg["page_dirs"]}
    if tuple(relparts) in generated:
        return deny(f"{'/'.join(relparts)} is generated. Run python .wiki/scripts/build_index.py instead of editing it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
