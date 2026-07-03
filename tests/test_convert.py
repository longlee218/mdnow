"""convert.py — file → markdown via markitdown. Network-free.

Real conversions use tiny text-based formats (csv/json) that markitdown handles
locally with no egress. The cloud-egress converters (audio/YouTube) are tested
only at the guard boundary — they are never actually invoked.
"""
import pytest

from mdnow import convert


# --- real local conversions (markitdown runs, fully local) -----------------

def test_from_path_csv_to_table(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("name,role\nAda,engineer\nGrace,admiral\n")
    extracted = convert.from_path(p)
    assert "Ada" in extracted.markdown and "engineer" in extracted.markdown
    assert extracted.published_date is None  # files carry no publish date

def test_from_path_empty_raises_valueerror(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("")
    with pytest.raises(ValueError):
        convert.from_path(p)

def test_from_bytes_json(tmp_path):
    extracted = convert.from_bytes(b'{"a": 1}', "https://s.com/d.json", "application/json")
    assert "a" in extracted.markdown


# --- _ext_from sniffing ------------------------------------------------------

def test_ext_from_prefers_url_extension():
    assert convert._ext_from("https://s.com/a/file.PDF", "application/octet-stream") == ".pdf"

def test_ext_from_falls_back_to_content_type():
    assert convert._ext_from("https://s.com/download", "application/pdf") == ".pdf"

def test_ext_from_unknown_returns_empty():
    assert convert._ext_from("https://s.com/x", "application/octet-stream") == ""


# --- network-egress gate (audio) ---------------------------------------------

def test_from_path_audio_refused_without_allow_remote(tmp_path):
    p = tmp_path / "clip.mp3"
    p.write_bytes(b"not really audio")
    with pytest.raises(convert.RemoteBlocked):
        convert.from_path(p)

def test_from_bytes_audio_mimetype_refused_without_allow_remote():
    # Extensionless URL but audio/* content-type → still refused (no silent egress).
    with pytest.raises(convert.RemoteBlocked):
        convert.from_bytes(b"x", "https://s.com/clip", "audio/mpeg")

def test_from_bytes_conversion_failure_normalized_to_valueerror(monkeypatch):
    # A markitdown MarkItDownException must surface as ValueError (clean error),
    # not a raw traceback that escapes the caller's (RuntimeError, ValueError).
    from markitdown import MarkItDownException

    class _FakeMd:
        def convert_stream(self, *a, **k):
            raise MarkItDownException("boom")

    monkeypatch.setattr(convert, "_markitdown", lambda: _FakeMd())
    with pytest.raises(ValueError):
        convert.from_bytes(b"data", "https://s.com/f.pdf", "application/pdf")

def test_non_audio_not_blocked():
    # A pdf ext must NOT be treated as audio.
    assert convert._is_audio(".pdf", "application/pdf") is False
    assert convert._is_audio(".mp3", "") is True
    assert convert._is_audio("", "audio/wav") is True


def test_mp4_and_video_mimetype_treated_as_audio_egress():
    # markitdown's AudioConverter transcribes .mp4 / video/mp4 too → must be gated.
    assert convert._is_audio(".mp4", "") is True
    assert convert._is_audio("", "video/mp4") is True


def test_from_bytes_video_mp4_refused_without_allow_remote():
    with pytest.raises(convert.RemoteBlocked):
        convert.from_bytes(b"x", "https://s.com/clip", "video/mp4")
