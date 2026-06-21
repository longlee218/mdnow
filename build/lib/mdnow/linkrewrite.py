"""Rewrite markdown links for a crawled page.

Contract:
  - internal + crawled  → relative local .md path (fragment preserved)
  - internal not-crawled → left absolute (never a broken local link)
  - external             → left absolute
Relative hrefs are resolved against the page's source URL first.
"""
from __future__ import annotations

import posixpath
import re
from urllib.parse import urljoin, urlsplit

from .urls import canonical

# [text](href) or [text](href "title"); (?<!\!) skips images (already stripped).
# href allows balanced single-level parens, e.g. /wiki/Mercury_(planet).
_LINK_RE = re.compile(
    r'(?<!\!)\[([^\]]*)\]\(\s*([^()\s]+(?:\([^()\s]*\)[^()\s]*)*)(\s+"[^"]*")?\s*\)'
)


def rewrite_links(md: str, page_url: str, page_relpath: str, url_map: dict[str, str]) -> str:
    page_dir = posixpath.dirname(page_relpath)

    def repl(m: re.Match) -> str:
        text, href, tail = m.group(1), m.group(2), m.group(3) or ""
        abs_href = urljoin(page_url, href)
        frag = urlsplit(abs_href).fragment
        canon = canonical(abs_href)
        if canon in url_map:
            rel = posixpath.relpath(url_map[canon], page_dir or ".")
            target = rel + (f"#{frag}" if frag else "")
            return f"[{text}]({target}{tail})"
        return f"[{text}]({abs_href}{tail})"

    return _LINK_RE.sub(repl, md)
