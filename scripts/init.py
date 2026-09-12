"""Scaffold a new vault, or add the llm-wiki files to an existing directory.

Creates:
    WIKI.md, CLAUDE.md, AGENTS.md, wiki.json
    raw/  wiki/{sources,entities,concepts,analyses}/  output/
    wiki/overview.md  wiki/log.md  and the generated indexes
    .wiki/scripts/    a copy of these scripts, so any agent can run them
    .wiki/skills/     a copy of the SKILL.md workflows, for agents without plugins
    .wiki/templates/  page templates

Existing files are left alone unless --force is given. Run it from the
llm-wiki checkout or from the installed plugin; it locates templates relative
to its own location, or from --plugin-root.

Usage:
    python init.py ~/vaults/research
    python init.py . --force
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib as W  # noqa: E402


def plugin_root(explicit: str | None) -> Path:
    if explicit:
        root = Path(explicit).resolve()
    else:
        root = Path(__file__).resolve().parent.parent
    if not (root / "templates" / "WIKI.md").is_file():
        raise SystemExit(f"templates/ not found under {root}; pass --plugin-root <path to llm-wiki checkout>")
    return root


def copy_file(src: Path, dst: Path, force: bool, created: list[str]) -> None:
    if dst.exists() and not force:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    created.append(dst.as_posix())


def main(argv: list[str] | None = None) -> int:
    W.configure_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="directory to turn into a vault (created if missing)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    ap.add_argument("--plugin-root", help="path to the llm-wiki checkout (default: derived from this script)")
    ap.add_argument("--no-git", action="store_true", help="do not run git init")
    args = ap.parse_args(argv)

    root = plugin_root(args.plugin_root)
    vault = Path(args.target).resolve()
    vault.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    t = root / "templates"

    for name in ("WIKI.md", "CLAUDE.md", "AGENTS.md", "wiki.json"):
        copy_file(t / name, vault / name, args.force, created)

    cfg = W.load_config(vault)
    for d in (cfg["raw_dir"], cfg["output_dir"], cfg["wiki_dir"], *[f"{cfg['wiki_dir']}/{x}" for x in cfg["page_dirs"]]):
        (vault / d).mkdir(parents=True, exist_ok=True)
    copy_file(t / "pages" / "overview.md", vault / cfg["wiki_dir"] / "overview.md", args.force, created)
    copy_file(t / "pages" / "log.md", vault / cfg["wiki_dir"] / "log.md", args.force, created)
    gitignore = vault / ".gitignore"
    if not gitignore.exists():
        W.write_text(gitignore, "__pycache__/\n.obsidian/workspace*.json\n")
        created.append(".gitignore")

    state_dir = vault / cfg["state_dir"]
    for script in sorted((root / "scripts").glob("*.py")):
        copy_file(script, state_dir / "scripts" / script.name, True, created)
    for tpl in sorted((t / "pages").glob("*.md")):
        copy_file(tpl, state_dir / "templates" / tpl.name, True, created)
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        copy_file(skill_md, state_dir / "skills" / skill_md.parent.name / "SKILL.md", True, created)

    # Generated files and the first log line.
    subprocess.run([sys.executable, str(state_dir / "scripts" / "build_index.py")], cwd=vault, check=True)
    subprocess.run([sys.executable, str(state_dir / "scripts" / "log.py"), "init", "vault created", "--note", f"scaffolded by init.py from {root.as_posix()}"], cwd=vault, check=True)

    if not args.no_git and not (vault / ".git").exists() and shutil.which("git"):
        inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=vault, capture_output=True, text=True)
        if inside.returncode != 0:
            subprocess.run(["git", "init", "-q"], cwd=vault, check=True)
            created.append(".git/")

    print(f"vault ready at {vault.as_posix()}")
    print(f"{len(created)} file(s) written")
    print("next: drop a source into raw/ and run the wiki-ingest skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
