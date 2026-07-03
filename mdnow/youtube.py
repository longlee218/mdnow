"""YouTube URL → timestamped transcript markdown.

Bypasses markitdown's YouTube converter, which merges the whole transcript into
one block and discards timing. Fetching the transcript ourselves lets us emit
coarse, deep-linkable timestamps AND own the error handling: youtube-transcript-
api scrapes YouTube's private endpoints with no API key, so it egresses (gated
behind allow_remote) and is often IP-blocked/rate-limited. Those failures are
normalized to a short ValueError here — never a raw traceback or the library's
40-line proxy essay.
"""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import httpx

from .convert import RemoteBlocked
from .doctor import missing_extra_message
from .extractor import Extracted

# Start a new timestamped paragraph roughly every this many seconds. Coarse on
# purpose: per-caption timestamps (~1-2s each) are noise for an LLM reader.
_BUCKET_SECONDS = 45
_PREFERRED_LANGS = ("en", "en-US", "en-GB")
_INSTALL_HINT = missing_extra_message("docs")

_BLOCKED_MSG = (
    "YouTube is rate-limiting or blocking this IP for transcript requests. "
    "Wait a few minutes and retry — cloud, VPN, and datacenter IPs are usually "
    "blocked by YouTube."
)


def _video_id(url: str) -> str | None:
    """Extract the video id from watch / youtu.be / shorts URLs (None if absent)."""
    try:
        p = urlparse(url)
    except ValueError:
        return None
    host = p.netloc.lower()
    if host == "youtu.be" or host.endswith(".youtu.be"):
        return p.path.lstrip("/").split("/")[0] or None
    parts = [seg for seg in p.path.split("/") if seg]
    if parts and parts[0] in ("shorts", "embed", "v"):
        return parts[1] if len(parts) > 1 else None
    return parse_qs(p.query).get("v", [None])[0]


def _timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _fetch_snippets(video_id: str) -> list:
    """Fetch transcript snippets; normalize youtube-transcript-api errors.

    Prefers English, falls back to the first available track. RequestBlocked /
    IpBlocked → the friendly rate-limit message; any other retrieval failure →
    a short 'no transcript available' message. ImportError (base install w/o
    [docs]) → RuntimeError with the install hint.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            CouldNotRetrieveTranscript,
            NoTranscriptFound,
            RequestBlocked,
        )
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc

    api = YouTubeTranscriptApi()
    try:
        try:
            return list(api.fetch(video_id, languages=_PREFERRED_LANGS))
        except NoTranscriptFound:
            # English track missing → take the first available language.
            return list(next(iter(api.list(video_id))).fetch())
    except RequestBlocked as exc:  # incl. IpBlocked subclass
        raise ValueError(_BLOCKED_MSG) from exc
    except (CouldNotRetrieveTranscript, StopIteration) as exc:
        raise ValueError(
            f"no transcript available for this video ({type(exc).__name__})."
        ) from exc


def _title(url: str) -> str | None:
    """Best-effort video title via YouTube's public oEmbed (no key, no scrape).

    Title is optional — the slug falls back to the URL — so any failure here
    returns None rather than aborting the conversion.
    """
    try:
        resp = httpx.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        title = resp.json().get("title")
        return title.strip() if title else None
    except (httpx.HTTPError, ValueError):
        return None


def _paragraphs(snippets: list):
    """Group caption snippets into ~_BUCKET_SECONDS paragraphs. Yields (start, text).

    A snippet whose start is >= _BUCKET_SECONDS past the current paragraph's
    start opens a new paragraph, so each paragraph's timestamp marks where its
    own content begins.
    """
    bucket_start: float | None = None
    parts: list[str] = []
    for snip in snippets:
        if bucket_start is not None and snip.start - bucket_start >= _BUCKET_SECONDS:
            yield bucket_start, " ".join(parts)
            bucket_start, parts = None, []
        if bucket_start is None:
            bucket_start = snip.start
        text = snip.text.strip()
        if text:
            parts.append(text)
    if parts:
        yield bucket_start or 0.0, " ".join(parts)


def _render(title: str | None, video_id: str, snippets: list) -> str:
    lines = ["# YouTube"]
    if title:
        lines.append(f"\n## {title}")
    lines.append("\n### Transcript\n")
    for start, text in _paragraphs(snippets):
        link = f"https://www.youtube.com/watch?v={video_id}&t={int(start)}s"
        lines.append(f"**[{_timestamp(start)}]({link})** {text}\n")
    return "\n".join(lines)


def convert(url: str, *, allow_remote: bool = False) -> Extracted:
    """Convert a YouTube URL to timestamped transcript markdown.

    Egresses to YouTube to scrape the transcript — gated behind allow_remote.
    """
    if not allow_remote:
        raise RemoteBlocked(
            "YouTube conversion fetches the transcript over the network. "
            "Re-run with --allow-remote to allow it."
        )
    video_id = _video_id(url)
    if not video_id:
        raise ValueError(f"could not find a YouTube video id in {url!r}.")
    snippets = _fetch_snippets(video_id)
    if not snippets:
        raise ValueError("the transcript was empty.")
    title = _title(url)
    return Extracted(
        markdown=_render(title, video_id, snippets), title=title, published_date=None
    )
