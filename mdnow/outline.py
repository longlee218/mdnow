"""Content-derived metadata helpers (pure, stdlib-only).

Heading outline + slugs, extractive summary, approximate token count.
Shared by frontmatter (per-page) and artifacts (manifest). All deterministic
so re-runs over unchanged content produce identical metadata.
"""
from __future__ import annotations

import math
import re

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$", re.MULTILINE)
_FENCE_RE = re.compile(r"(?ms)^```.*?^```")          # fenced code blocks
_SLUG_DROP = re.compile(r"[^\w\- ]+", re.UNICODE)    # keep word chars, hyphen, space


def token_estimate(text: str) -> int:
    """Approximate token count (~4 chars/token). Zero-dependency heuristic."""
    return math.ceil(len(text) / 4)


def slugify_heading(text: str) -> str:
    """GitHub-style heading slug: lowercase, drop punctuation, spaces→hyphens."""
    s = _SLUG_DROP.sub("", text.strip().lower())
    s = re.sub(r"\s+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def headings(markdown: str) -> list[dict]:
    """Outline as [{level, text, slug}] with de-duplicated slugs."""
    out: list[dict] = []
    seen: dict[str, int] = {}
    stripped = _FENCE_RE.sub("", markdown)   # don't treat `# x` inside code as a heading
    for m in _HEADING_RE.finditer(stripped):
        text = m.group(2).strip()
        if not text:
            continue
        slug = slugify_heading(text) or "section"
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 0
        out.append({"level": len(m.group(1)), "text": text, "slug": slug})
    return out


def summary_of(markdown: str, max_chars: int = 300) -> str:
    """First meaningful paragraph — skips headings, quotes, lists, code, short lines."""
    for block in re.split(r"\n\s*\n", markdown):
        first = block.strip().splitlines()[0].strip() if block.strip() else ""
        if not first or first.startswith(("#", ">", "-", "*", "|", "```", "    ")):
            continue
        text = re.sub(r"\s+", " ", block.strip())
        if len(text) < 40:
            continue
        return text[:max_chars].rstrip()
    return ""
