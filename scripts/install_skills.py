"""Copy (or symlink) the four wiki skills into an agent's user-level skills
directory, for agents that do not read the vault's .agents/skills/ folder or
when you want the skills available in every project.

    python install_skills.py hermes      -> ~/.hermes/skills/llm-wiki/<skill>/
    python install_skills.py codex       -> ~/.codex/skills/<skill>/
    python install_skills.py claude      -> ~/.claude/skills/<skill>/   (no raw/ guard; prefer the plugin)
    python install_skills.py agents      -> ~/.agents/skills/<skill>/   (Cline, Copilot, Gemini CLI, Amp)
    python install_skills.py hermes --dest /some/dir   (any directory)
    python install_skills.py codex --link             (symlink instead of copy)
    python install_skills.py codex --remove

The scripts the skills call still live inside each vault (.wiki/scripts/),
placed there by init.py. This installer only registers the workflows.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

TARGETS = {
    "hermes": Path.home() / ".hermes" / "skills" / "llm-wiki",
    "codex": Path.home() / ".codex" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("agent", choices=sorted(TARGETS))
    ap.add_argument("--dest", help="override the destination directory")
    ap.add_argument("--link", action="store_true", help="symlink the skill directories instead of copying")
    ap.add_argument("--remove", action="store_true", help="remove the installed skills")
    args = ap.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print(f"skills/ not found under {root}", file=sys.stderr)
        return 1
    dest = Path(args.dest).expanduser().resolve() if args.dest else TARGETS[args.agent]
    dest.mkdir(parents=True, exist_ok=True)

    done = []
    for skill in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").is_file()):
        target = dest / skill.name
        if target.is_symlink() or target.exists():
            if target.is_symlink() or target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
        if args.remove:
            done.append(f"removed {target}")
            continue
        if args.link:
            os.symlink(skill, target, target_is_directory=True)
            done.append(f"linked  {target} -> {skill}")
        else:
            shutil.copytree(skill, target)
            done.append(f"copied  {target}")
    for line in done:
        print(line)
    if not args.remove:
        print(f"\n{len(done)} skill(s) installed for {args.agent} in {dest}")
        print("start a new agent session to pick them up")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
