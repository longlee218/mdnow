"""Auth material for private/internal sites: --header strings + cookie files.

Header/cookie VALUES are secrets: never echo, log, or write them to any
output file. Error messages name the offending header, never its value.

Cookie files: Netscape cookies.txt (browser-extension export) or a JSON list
of {name, value[, domain, path]}. Both normalize to the same dict shape,
consumed by StaticFetcher (httpx jar) and CamoufoxFetcher (context cookies).
"""
from __future__ import annotations

import json
from pathlib import Path

_NETSCAPE_FIELDS = 7  # domain, include_subdomains, path, secure, expiry, name, value


def parse_headers(pairs: list[str]) -> dict[str, str]:
    """Parse repeatable --header 'Name: Value' strings. Raises ValueError."""
    out: dict[str, str] = {}
    for raw in pairs:
        name, sep, value = raw.partition(":")
        if not sep:
            # no colon → we can't tell name from value, so echo NOTHING of the
            # argument: it may be entirely secret (e.g. "Authorization=Bearer x")
            raise ValueError("Invalid header (missing ':'): expected 'Name: Value'")
        if not name.strip() or not value.strip():
            # the part before ':' is a header NAME — safe to echo; never the value
            raise ValueError(
                f"Invalid header {name.strip() or '(no name)'!r}: expected 'Name: Value'"
            )
        out[name.strip()] = value.strip()
    return out


def _cookie(name: str, value: str, domain: str = "", path: str = "/") -> dict:
    return {"name": name, "value": value, "domain": domain, "path": path or "/"}


def _from_json(text: str, source: Path) -> list[dict]:
    try:
        entries = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Cookie file {source} is not valid JSON: {exc}") from exc
    if not isinstance(entries, list):
        raise ValueError(f"Cookie file {source}: expected a JSON list of cookies")
    out = []
    for e in entries:
        if not isinstance(e, dict) or not e.get("name") or "value" not in e:
            raise ValueError(f"Cookie file {source}: every entry needs 'name' and 'value'")
        out.append(_cookie(e["name"], e["value"], e.get("domain", ""), e.get("path", "/")))
    return out


def _from_netscape(text: str, source: Path) -> list[dict]:
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        # "#HttpOnly_" is a real cookie flag, not a comment
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_"):]
        elif not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != _NETSCAPE_FIELDS:
            raise ValueError(
                f"Cookie file {source}, line {lineno}: expected {_NETSCAPE_FIELDS} "
                "tab-separated fields (Netscape cookies.txt format)"
            )
        domain, _, path, _, _, name, value = fields
        out.append(_cookie(name, value, domain, path))
    return out


def load_cookies(path: Path) -> list[dict]:
    """Load cookies from a Netscape cookies.txt or JSON-list file."""
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        return _from_json(text, path)
    return _from_netscape(text, path)
