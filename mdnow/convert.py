"""Any-file → markdown via Microsoft markitdown.

markitdown is an OPTIONAL dependency (the `[docs]` extra), imported lazily so
static-only users never need it installed — mirrors fetcher.CamoufoxFetcher.
Its `(markdown, title)` result maps onto the existing Extracted dataclass, so
the whole writer/frontmatter path is reused unchanged.

Network egress: markitdown's audio-transcription and YouTube converters call
cloud APIs. Those are gated behind `allow_remote` — refused with RemoteBlocked
otherwise — so MDNow stays fully local by default.
"""
from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path
from urllib.parse import urlparse

from .doctor import missing_extra_message
from .extractor import Extracted

_INSTALL_HINT = missing_extra_message("docs")

# Formats markitdown's AudioConverter transcribes via a cloud speech API.
# Must stay a superset of that converter's accept-list (incl. .mp4 / video/mp4,
# which it transcribes the audio track of) — else those egress silently.
_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".mp4", ".flac", ".ogg", ".aac", ".aiff", ".aif"}

# Fallback ext lookup when a URL has no path extension (e.g. octet-stream PDF).
_CTYPE_EXT = {
    "application/pdf": ".pdf",
    "application/epub+zip": ".epub",
    "application/zip": ".zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.ms-powerpoint": ".ppt",
    "text/csv": ".csv",
    "application/json": ".json",
}


class RemoteBlocked(RuntimeError):
    """Raised when a converter would egress to the network and --allow-remote is off."""


def _markitdown():
    """Lazy MarkItDown factory. Plugins off; no LLM/Azure client (stays local)."""
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc
    return MarkItDown(enable_plugins=False)


def _ext_from(url: str, content_type: str) -> str:
    """Best-effort file extension: URL path ext first, then a content-type map."""
    try:
        ext = os.path.splitext(urlparse(url).path)[1].lower()
    except ValueError:
        ext = ""
    if ext:
        return ext
    ct = (content_type or "").split(";")[0].strip().lower()
    return _CTYPE_EXT.get(ct, "")


def _is_audio(ext: str, content_type: str) -> bool:
    """Audio/video by extension OR content-type (matches markitdown's accept-list)."""
    if ext in _AUDIO_EXT:
        return True
    ct = (content_type or "").split(";")[0].strip().lower()
    return ct.startswith("audio/") or ct == "video/mp4"


def _guard_audio(ext: str, content_type: str, allow_remote: bool) -> None:
    if _is_audio(ext, content_type) and not allow_remote:
        raise RemoteBlocked(
            "converting audio/video transcribes it via a cloud API. "
            "Re-run with --allow-remote to allow it."
        )


def _result_to_extracted(result, where: str) -> Extracted:
    md = (result.markdown or "").strip()
    if not md:
        raise ValueError(f"No content extracted from {where}")
    title = str(result.title).strip() if result.title else None
    return Extracted(markdown=md, title=title, published_date=None)


def from_path(path: Path, *, allow_remote: bool = False) -> Extracted:
    """Convert a local file to markdown. Raises ValueError if nothing usable."""
    _guard_audio(path.suffix.lower(), "", allow_remote)  # RemoteBlocked before markitdown
    md = _markitdown()  # RuntimeError if [docs] missing
    from markitdown import MarkItDownException  # safe: import above already succeeded

    try:
        result = md.convert(str(path))
    except MarkItDownException as exc:
        # UnsupportedFormat/FileConversion don't subclass RuntimeError/ValueError;
        # normalize so callers' (RuntimeError, ValueError) handling works — a
        # clean error for single files, a per-file skip in folder batch mode.
        raise ValueError(f"cannot convert {path.name}: {exc}") from exc
    return _result_to_extracted(result, str(path))


def from_bytes(data: bytes, url: str, content_type: str, *, allow_remote: bool = False) -> Extracted:
    """Convert already-fetched bytes (a remote non-HTML file) to markdown."""
    ext = _ext_from(url, content_type)
    _guard_audio(ext, content_type, allow_remote)  # refuse egress BEFORE touching markitdown
    md = _markitdown()  # raises RuntimeError(_INSTALL_HINT) if [docs] missing → render fallback
    from markitdown import StreamInfo  # safe: markitdown import already succeeded above

    stream_info = StreamInfo(extension=ext or None, mimetype=(content_type or None), url=url)
    return _result_to_extracted(md.convert_stream(BytesIO(data), stream_info=stream_info), url)


def from_url(url: str, *, allow_remote: bool = False) -> Extracted:
    """Convert a URL markitdown handles specially (YouTube). Always egresses.

    Contract: this is the ONLY place a raw URL is passed to markitdown.convert();
    _acquire always uses convert_stream(bytes), so already-fetched content never
    triggers a markitdown network fetch. Keep it that way.
    """
    if not allow_remote:
        raise RemoteBlocked(
            "YouTube conversion fetches transcripts over the network. "
            "Re-run with --allow-remote to allow it."
        )
    return _result_to_extracted(_markitdown().convert(url), url)
