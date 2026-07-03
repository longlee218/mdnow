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


def _mask_fences(markdown: str) -> str:
    """Blank out fenced code (keeping length + newlines) so `# x` inside code
    is never a heading, while match positions still index the original text."""
    return _FENCE_RE.sub(lambda m: re.sub(r"[^\n]", "\x00", m.group(0)), markdown)


def _heading_matches(markdown: str) -> list[tuple[re.Match, str, str]]:
    """(match, text, deduped-slug) triples — shared by headings() and sections()."""
    out: list[tuple[re.Match, str, str]] = []
    seen: dict[str, int] = {}
    for m in _HEADING_RE.finditer(_mask_fences(markdown)):
        text = m.group(2).strip()
        if not text:
            continue
        slug = slugify_heading(text) or "section"
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 0
        out.append((m, text, slug))
    return out


def headings(markdown: str) -> list[dict]:
    """Outline as [{level, text, slug}] with de-duplicated slugs."""
    return [
        {"level": len(m.group(1)), "text": text, "slug": slug}
        for m, text, slug in _heading_matches(markdown)
    ]


def sections(markdown: str) -> list[dict]:
    """Heading-delimited chunks with size metadata, for agent-side retrieval.

    Each section runs from its heading to the next heading (any level).
    Prose before the first heading becomes slug `_intro` (level 0).
    Slugs match headings() exactly, so both can be joined on slug.
    """
    matches = _heading_matches(markdown)
    out: list[dict] = []

    def _entry(slug: str, heading: str, level: int, body: str) -> dict:
        body = body.strip()
        return {"slug": slug, "heading": heading, "level": level,
                "word_count": len(body.split()),
                "token_estimate": token_estimate(body)}

    intro = markdown[: matches[0][0].start()] if matches else markdown
    if intro.strip():
        out.append(_entry("_intro", "", 0, intro))
    for i, (m, text, slug) in enumerate(matches):
        end = matches[i + 1][0].start() if i + 1 < len(matches) else len(markdown)
        out.append(_entry(slug, text, len(m.group(1)), markdown[m.end():end]))
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
