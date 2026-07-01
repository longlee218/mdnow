"""Input-type detection for the CLI (URL vs local file vs YouTube)."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

_YT_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def is_local_file(arg: str) -> bool:
    """True if arg is a path to an existing local file (not an http(s) URL)."""
    try:
        scheme = urlparse(arg).scheme
    except ValueError:
        return False  # malformed input → let the URL branch report it cleanly
    return scheme not in ("http", "https") and Path(arg).is_file()


def is_youtube(arg: str) -> bool:
    """True if arg is a YouTube URL (handled by markitdown's transcript converter)."""
    try:
        return urlparse(arg).netloc.lower() in _YT_HOSTS
    except ValueError:
        return False
