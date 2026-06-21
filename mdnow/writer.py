"""Write markdown files with content-hash versioning.

On re-write: compare the new body hash against the existing file's frontmatter.
  - unchanged -> skip (no-op), keep version
  - changed   -> bump version, rewrite
  - new       -> version 1
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from . import frontmatter


@dataclass
class WriteOutcome:
    path: Path
    version: int
    status: str  # "created" | "updated" | "unchanged"


def _read_existing_meta(path: Path) -> dict | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return meta if isinstance(meta, dict) else None


def write(
    path: Path,
    source_url: str,
    title: str | None,
    published_date: str | None,
    fetched_date: str,
    body: str,
) -> WriteOutcome:
    new_hash = frontmatter.content_hash(body)
    existing = _read_existing_meta(path)

    if existing and existing.get("content_hash") == new_hash:
        return WriteOutcome(path, int(existing.get("version", 1)), "unchanged")

    if existing:
        version = int(existing.get("version", 1)) + 1
        status = "updated"
    else:
        version = 1
        status = "created"

    meta = frontmatter.build(source_url, title, published_date, fetched_date, version, body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(frontmatter.render(meta, body), encoding="utf-8")
    return WriteOutcome(path, version, status)
