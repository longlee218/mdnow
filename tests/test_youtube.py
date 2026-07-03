"""youtube.py — timestamped transcript conversion. Network-free.

The transcript API and oEmbed title fetch are monkeypatched; no real egress.
"""
from dataclasses import dataclass

import pytest

from mdnow import youtube
from mdnow.convert import RemoteBlocked


@dataclass
class _Snip:
    text: str
    start: float
    duration: float = 2.0


def _snips(*pairs):
    return [_Snip(text, start) for start, text in pairs]


# --- video id parsing --------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://www.youtube.com/watch?v=abc123DEF45", "abc123DEF45"),
    ("https://youtu.be/abc123DEF45", "abc123DEF45"),
    ("https://youtu.be/abc123DEF45?t=30", "abc123DEF45"),
    ("https://www.youtube.com/shorts/abc123DEF45", "abc123DEF45"),
    ("https://www.youtube.com/embed/abc123DEF45", "abc123DEF45"),
    ("https://music.youtube.com/watch?v=abc123DEF45", "abc123DEF45"),
    ("https://www.youtube.com/", None),
])
def test_video_id(url, expected):
    assert youtube._video_id(url) == expected


# --- timestamp + bucketing ---------------------------------------------------

def test_timestamp_formats_hours_only_when_needed():
    assert youtube._timestamp(5) == "00:05"
    assert youtube._timestamp(65) == "01:05"
    assert youtube._timestamp(3661) == "1:01:01"


def test_paragraphs_bucket_by_time():
    # 45s bucket: 0s & 10s share para 1; 50s opens para 2, 60s joins it.
    snips = _snips((0, "a"), (10, "b"), (50, "c"), (60, "d"))
    paras = list(youtube._paragraphs(snips))
    assert paras == [(0, "a b"), (50, "c d")]


def test_paragraphs_skips_empty_snippets():
    paras = list(youtube._paragraphs(_snips((0, " "), (1, "hello"))))
    assert paras == [(0, "hello")]


# --- rendering ---------------------------------------------------------------

def test_render_emits_timestamp_markers_and_deeplinks():
    md = youtube._render("My Video", "vid123", _snips((0, "hello"), (50, "world")))
    assert "## My Video" in md
    assert "### Transcript" in md
    assert "**[00:00](https://www.youtube.com/watch?v=vid123&t=0s)** hello" in md
    assert "**[00:50](https://www.youtube.com/watch?v=vid123&t=50s)** world" in md


# --- convert() gating + error normalization ----------------------------------

def test_convert_refused_without_allow_remote():
    with pytest.raises(RemoteBlocked):
        youtube.convert("https://youtu.be/abc123DEF45")


def test_convert_bad_url_raises_valueerror():
    with pytest.raises(ValueError):
        youtube.convert("https://www.youtube.com/", allow_remote=True)


def test_convert_happy_path(monkeypatch):
    monkeypatch.setattr(youtube, "_fetch_snippets", lambda vid: _snips((0, "hi"), (1, "there")))
    monkeypatch.setattr(youtube, "_title", lambda url: "Cool Video")
    ext = youtube.convert("https://youtu.be/abc123DEF45", allow_remote=True)
    assert ext.title == "Cool Video"
    assert "hi there" in ext.markdown


def _patch_api(monkeypatch, fetch_impl, list_impl=None):
    """Install a fake YouTubeTranscriptApi into the youtube_transcript_api module."""
    import youtube_transcript_api

    class _FakeApi:
        def fetch(self, video_id, languages=()):
            return fetch_impl()

        def list(self, video_id):
            return list_impl() if list_impl else iter([])

    monkeypatch.setattr(youtube_transcript_api, "YouTubeTranscriptApi", _FakeApi)


def test_fetch_snippets_request_blocked_gives_friendly_message(monkeypatch):
    from youtube_transcript_api._errors import RequestBlocked

    def boom():
        raise RequestBlocked("vid123")

    _patch_api(monkeypatch, boom)
    with pytest.raises(ValueError) as exc:
        youtube._fetch_snippets("vid123")
    assert "rate-limiting or blocking" in str(exc.value)
    # The library's 40-line proxy essay must NOT leak through.
    assert "Webshare" not in str(exc.value)


def test_fetch_snippets_no_transcript_falls_back_to_first_track(monkeypatch):
    from youtube_transcript_api._errors import NoTranscriptFound

    class _Track:
        def fetch(self):
            return _snips((0, "fallback"))

    def boom():
        raise NoTranscriptFound("vid123", ["en"], {})

    _patch_api(monkeypatch, boom, list_impl=lambda: iter([_Track()]))
    snips = youtube._fetch_snippets("vid123")
    assert snips[0].text == "fallback"
