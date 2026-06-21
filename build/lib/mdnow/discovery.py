"""Discovery seam — gates the crawler.

When a site already publishes clean markdown (llms.txt family, or a per-page
`.md` twin), `discover()` returns it and the crawler/extractor never runs.
"""
from __future__ import annotations

from . import llmstxt
from .llmstxt import Discovered


def discover(url: str, *, crawl: bool) -> Discovered | None:
    """Return ready-made markdown for `url`, or None to fall through."""
    return llmstxt.probe_site(url) if crawl else llmstxt.probe_page(url)
