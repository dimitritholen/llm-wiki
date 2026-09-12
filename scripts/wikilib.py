"""Shared helpers for the llm-wiki scripts.

Standard library only. Works on Windows, macOS and Linux. Every file is read
and written as UTF-8 regardless of the platform default.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

CONFIG_NAME = "wiki.json"
SCHEMA_NAME = "WIKI.md"

DEFAULT_CONFIG = {
    "version": 1,
    "raw_dir": "raw",
    "wiki_dir": "wiki",
    "output_dir": "output",
    "state_dir": ".wiki",
    "stale_days": 90,
    "page_dirs": {
        "sources": "source",
        "entities": "entity",
        "concepts": "concept",
        "analyses": "analysis",
    },
    "special_pages": ["index.md", "log.md", "overview.md", "disputes.md"],
    "required_frontmatter": ["title", "kind", "summary", "created", "last_verified"],
    "human_section": "My take",
    "dispute_section": "Disputed",
}

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]")
FOOTNOTE_DEF_RE = re.compile(r'^\[\^([^\]]+)\]:\s*(\S+)\s*\|\s*"(.*)"\s*$')
FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\](?!:)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def configure_stdout() -> None:
    """Force UTF-8 on stdout so non-ASCII titles do not crash on cp1252."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def find_vault(start: Path | None = None) -> Path:
    """Walk up from start (default cwd) until a directory holds wiki.json."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    raise SystemExit(
        f"No {CONFIG_NAME} found in {here} or any parent. Run this from inside a vault."
    )


def load_config(vault: Path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    data = json.loads(read_text(vault / CONFIG_NAME))
    cfg.update(data)
    return cfg


def rel(vault: Path, path: Path) -> str:
    return path.resolve().relative_to(vault.resolve()).as_posix()


# --- frontmatter -----------------------------------------------------------


def _parse_scalar(raw: str):
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(item.strip()) for item in inner.split(",")]
    return _strip_quotes(value)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body). Supports the YAML subset the templates use:
    `key: scalar`, `key: [a, b]`, and block lists with `- item` lines."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    body = text[end + 4 :]
    if body.startswith("\n"):
        body = body[1:]
    data: dict = {}
    current_key: str | None = None
    for line in block.split("\n"):
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and current_key is not None:
            data.setdefault(current_key, [])
            if not isinstance(data[current_key], list):
                data[current_key] = []
            data[current_key].append(_strip_quotes(line.lstrip()[2:].strip()))
            continue
        if ":" in line and not line.startswith(" "):
            key, _, raw = line.partition(":")
            current_key = key.strip()
            data[current_key] = _parse_scalar(raw) if raw.strip() else ""
    return data, body


# --- pages -----------------------------------------------------------------


@dataclass
class Page:
    path: Path
    relpath: str
    name: str  # filename without .md, used for wikilink resolution
    frontmatter: dict
    body: str
    text: str
    kind: str = ""
    links: list[str] = field(default_factory=list)
    footnote_refs: list[str] = field(default_factory=list)
    footnote_defs: dict = field(default_factory=dict)  # id -> (raw_relpath, anchor)
    sections: dict = field(default_factory=dict)  # heading text -> section body


def load_page(vault: Path, path: Path) -> Page:
    text = read_text(path)
    fm, body = parse_frontmatter(text)
    page = Page(
        path=path,
        relpath=rel(vault, path),
        name=path.stem,
        frontmatter=fm,
        body=body,
        text=text,
        kind=str(fm.get("kind", "")),
    )
    page.links = [m.group(1).strip() for m in WIKILINK_RE.finditer(body)]
    defs: dict = {}
    for line in body.split("\n"):
        m = FOOTNOTE_DEF_RE.match(line.strip())
        if m:
            defs[m.group(1)] = (m.group(2), m.group(3))
    page.footnote_defs = defs
    body_without_defs = "\n".join(
        line for line in body.split("\n") if not FOOTNOTE_DEF_RE.match(line.strip())
    )
    page.footnote_refs = [m.group(1) for m in FOOTNOTE_REF_RE.finditer(body_without_defs)]
    # Footnote definitions sit at the end of the file, inside whatever section
    # comes last. Split on the body without them so "My take" and "Disputed"
    # are judged on their own content.
    page.sections = split_sections(body_without_defs)
    return page


def split_sections(body: str) -> dict:
    """Map each heading (any level) to the text until the next heading."""
    sections: dict = {}
    current = None
    buf: list[str] = []
    for line in body.split("\n"):
        m = HEADING_RE.match(line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(2).strip()
            buf = []
        else:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def section_is_empty(text: str) -> bool:
    """True when a section holds nothing but comments, placeholders or whitespace."""
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    if not stripped:
        return True
    placeholders = {"todo", "tbd", "pending", "_(pending)_", "(pending)", "..."}
    return stripped.lower().strip("_* ") in placeholders


def iter_wiki_pages(vault: Path, cfg: dict) -> list[Page]:
    wiki = vault / cfg["wiki_dir"]
    pages: list[Page] = []
    if not wiki.is_dir():
        return pages
    for path in sorted(wiki.rglob("*.md")):
        pages.append(load_page(vault, path))
    return pages


def is_special(page: Page, cfg: dict) -> bool:
    return page.path.name in set(cfg["special_pages"])


def page_dir_kind(page: Page, vault: Path, cfg: dict) -> str | None:
    """Return the expected kind for a page based on its directory, or None."""
    wiki = (vault / cfg["wiki_dir"]).resolve()
    try:
        first = page.path.resolve().relative_to(wiki).parts[0]
    except (ValueError, IndexError):
        return None
    return cfg["page_dirs"].get(first)


def iter_raw_files(vault: Path, cfg: dict) -> list[Path]:
    raw = vault / cfg["raw_dir"]
    if not raw.is_dir():
        return []
    return sorted(p for p in raw.rglob("*") if p.is_file() and not p.name.startswith("."))


# --- state -----------------------------------------------------------------


def state_path(vault: Path, cfg: dict) -> Path:
    return vault / cfg["state_dir"] / "state.json"


def load_state(vault: Path, cfg: dict) -> dict:
    path = state_path(vault, cfg)
    if not path.is_file():
        return {}
    return json.loads(read_text(path))


def save_state(vault: Path, cfg: dict, state: dict) -> None:
    write_text(state_path(vault, cfg), json.dumps(state, indent=2, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# --- citations -------------------------------------------------------------

_QUOTE_MAP = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        " ": " ",
    }
)


def normalize(text: str) -> str:
    """Fold curly quotes and dashes, collapse whitespace. Case is preserved."""
    text = text.translate(_QUOTE_MAP)
    text = re.sub(r"[*_`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def anchor_found(anchor: str, raw_text: str) -> bool:
    return normalize(anchor) in normalize(raw_text)


# --- dates -----------------------------------------------------------------


def today() -> str:
    return date.today().isoformat()


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


# --- output ----------------------------------------------------------------


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    code: str
    path: str
    message: str

    def line(self) -> str:
        return f"{self.severity.upper():7} {self.code:18} {self.path}: {self.message}"


def print_findings(findings: list[Finding], as_json: bool) -> None:
    if as_json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
        return
    for f in findings:
        print(f.line())
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    print(f"\n{errors} error(s), {warnings} warning(s)")
