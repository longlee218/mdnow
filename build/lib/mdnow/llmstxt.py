"""Detect site-published AI markdown (llms.txt family) so we can skip crawling.

Probe tiers in priority order; a lower tier is only tried after higher tiers
miss. Every hit is validated as real markdown (a 200 HTML/SPA shell is rejected).
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlsplit, urlunsplit

import httpx

from .fetcher import DEFAULT_UA

PROBE_TIMEOUT = 4.0  # "does this file exist" — keep short so a slow host can't stall
MAX_DISCOVERY_BYTES = 20 * 1024 * 1024  # safety bound on a discovered file

# Root-level candidates, highest-confidence first.
_ROOT_TIERS = (
    ("/llms-full.txt", "/llms.txt"),       # llmstxt.org standard
    ("/llms-full.md", "/llms.md"),         # markdown-extension variants
    ("/llm.txt", "/llm.md"),               # singular variants
    ("/.well-known/llms.txt",),            # emerging well-known location
)


@dataclass
class Discovered:
    content: str
    source_url: str
    title: str | None


def _get(url: str, accept: str | None = None) -> httpx.Response | None:
    headers = {"User-Agent": DEFAULT_UA}
    if accept:
        headers["Accept"] = accept
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=PROBE_TIMEOUT, headers=headers)
    except httpx.HTTPError:
        return None
    if resp.status_code != 200 or len(resp.content) > MAX_DISCOVERY_BYTES:
        return None
    return resp


def _looks_markdown(text: str, content_type: str) -> bool:
    """Reject HTML/SPA/JSON 200s; require a real markdown marker."""
    ct = (content_type or "").lower()
    head = text.lstrip()[:256].lower()
    if head.startswith(("<!doctype", "<html", "<?xml")):
        return False
    if "text/html" in ct or "json" in ct:
        return False
    return "# " in text or "](" in text


def _title(text: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _as_discovered(resp: httpx.Response) -> Discovered | None:
    text = resp.text
    if _looks_markdown(text, resp.headers.get("content-type", "")):
        return Discovered(text, str(resp.url), _title(text))
    return None


def _root(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc, "", "", ""))


def probe_site(start_url: str) -> Discovered | None:
    """Crawl mode: prefer a whole-site markdown dump / index at the root."""
    root = _root(start_url)
    for tier in _ROOT_TIERS:
        for name in tier:
            resp = _get(root + name)
            if resp:
                found = _as_discovered(resp)
                if found:
                    return found
    return None


def probe_page(url: str) -> Discovered | None:
    """Single mode: try the page's own markdown twin before falling back."""
    p = urlsplit(url)
    if p.path and not p.path.endswith("/"):
        md_url = urlunsplit((p.scheme, p.netloc, p.path + ".md", "", ""))
        resp = _get(md_url)
        if resp:
            found = _as_discovered(resp)
            if found:
                return found
    # Content negotiation: only trust it if the server truly returns markdown.
    resp = _get(url, accept="text/markdown")
    if resp and "markdown" in resp.headers.get("content-type", "").lower():
        return _as_discovered(resp)
    return None
