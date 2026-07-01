"""Slug helpers for stable, filesystem-safe output names."""
from __future__ import annotations

from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse


def _slugify(text: str) -> str:
    """ASCII slug: transliterate accents, drop other non-ascii. May return ''."""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")


def slug(title: str | None, url: str) -> str:
    """Stable filename slug. Tries title, then URL path, then host."""
    parsed = urlparse(url)
    for candidate in (title or "", parsed.path, parsed.netloc):
        s = _slugify(candidate)
        if s:
            return s[:80]
    return "page"


def file_slug(path: Path) -> str:
    """Filename slug for a local file — its stem, slugified."""
    return _slugify(path.stem)[:80] or "file"
