"""Extraction-quality heuristics: decide when static extraction is junk.

Two failure modes trigger render escalation:
  1. thin  — too few words (JS-only page returned an empty shell)
  2. boilerplate — enough words, but nearly all of them inside links
     (nav/footer link-farm extracted instead of the article)

Past LINK_DENSE_MAX_WORDS we keep link-heavy pages: big genuine index pages
(sitemaps, tables of contents) are legitimately link-dense.
"""
from __future__ import annotations

import re

THIN_WORDS = 50            # below this, extraction is likely JS-blocked
LINK_DENSE_RATIO = 0.7     # above this share of link words → boilerplate…
LINK_DENSE_MAX_WORDS = 200  # …unless the page is big enough to be a real index

_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def _text_words(md: str) -> int:
    """Word count with link targets stripped (a URL is not a word)."""
    return len(_LINK_RE.sub(r"\1", md).split())


def link_density(md: str) -> float:
    """Share of words that live inside markdown link text (0.0–1.0)."""
    total = _text_words(md)
    if not total:
        return 0.0
    linked = sum(len(t.split()) for t in _LINK_RE.findall(md))
    return linked / total


def is_thin(md: str) -> bool:
    """True when extraction looks like junk → caller should try the render tier."""
    words = _text_words(md)
    if words < THIN_WORDS:
        return True
    return words < LINK_DENSE_MAX_WORDS and link_density(md) > LINK_DENSE_RATIO
