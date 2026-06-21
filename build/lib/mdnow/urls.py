"""URL canonicalization + URL→local-path mapping.

`canonical()` is the single source of truth used by BOTH dedup and the path
map, so the same URL always resolves identically everywhere (DRY).
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit


def canonical(url: str) -> str:
    """Lowercase scheme/host, strip default port, drop query+fragment, collapse slash."""
    p = urlsplit(url)
    scheme = p.scheme.lower()
    netloc = p.netloc.lower()
    if (scheme == "http" and netloc.endswith(":80")):
        netloc = netloc[:-3]
    elif (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc[:-4]
    path = p.path or "/"
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, "", ""))


def same_host(url: str, host: str) -> bool:
    return urlsplit(url).netloc.lower() == host.lower()


def _short(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:6]


def _relpath_for(url: str) -> str:
    """Mirror the URL path as a local .md path. Root → home.md."""
    path = urlsplit(url).path.strip("/")
    if not path:
        return "home.md"
    segs = []
    for seg in path.split("/"):
        norm = unicodedata.normalize("NFKD", seg).encode("ascii", "ignore").decode()
        norm = re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")
        segs.append(norm or "x")
    return "/".join(segs) + ".md"


def build_path_map(canon_urls: list[str]) -> dict[str, str]:
    """Map each canonical URL to a unique local .md path (stable across runs).

    Collisions and the reserved tree name `index.md` get a deterministic
    sha1 suffix so distinct URLs never overwrite each other.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for u in canon_urls:
        rel = _relpath_for(u)
        if rel in used or rel == "index.md":
            rel = f"{rel[:-3]}-{_short(u)}.md"
        used.add(rel)
        mapping[u] = rel
    return mapping
