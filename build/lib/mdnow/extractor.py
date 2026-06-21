"""HTML bytes -> clean markdown + metadata via trafilatura.

trafilatura has no native "drop image, keep alt-text" mode, so we extract
with images included, then regex the markdown image syntax down to its alt text.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

import trafilatura

# ![alt](src)  ->  alt   (keep alt-text as plain text, drop the image)
_IMG_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")

# Content types trafilatura can extract from. Empty/missing is treated as OK.
_HTML_CTYPES = ("html", "xml", "text", "markdown")


def is_html(content_type: str) -> bool:
    """True if the content type looks extractable (or is unspecified)."""
    ct = (content_type or "").lower()
    return not ct or any(t in ct for t in _HTML_CTYPES)


@dataclass
class Extracted:
    markdown: str
    title: str | None
    published_date: str | None

    @property
    def word_count(self) -> int:
        return len(self.markdown.split())


def _strip_images(md: str) -> str:
    return _IMG_RE.sub(r"\1", md)


def extract(html: bytes, url: str | None = None) -> Extracted:
    """Extract main content as markdown. Raises ValueError if nothing usable."""
    md = trafilatura.extract(
        html,
        output_format="markdown",
        include_images=True,   # included so we can convert them to alt-text
        include_links=True,
        url=url,
    )
    if not md or not md.strip():
        raise ValueError("No main content extracted")
    md = _strip_images(md).strip()

    meta = trafilatura.extract_metadata(html)
    title = getattr(meta, "title", None) if meta else None
    published = getattr(meta, "date", None) if meta else None
    return Extracted(markdown=md, title=title, published_date=published)
