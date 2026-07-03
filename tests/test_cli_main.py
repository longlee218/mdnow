import mdnow.convert as convert
import mdnow.runner as run
import typer
from typer.testing import CliRunner

import mdnow.cli as cli
from mdnow.extractor import Extracted
from mdnow.fetcher import FetchResult
from mdnow.llmstxt import Discovered

runner = CliRunner()


def _app():
    app = typer.Typer()
    app.command()(cli.main)
    return app


def test_discovery_short_circuit_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "discover", lambda url, crawl: Discovered("# Docs\nbody", "https://s.com/llms.txt", "Docs"))
    res = runner.invoke(_app(), ["https://s.com/", "-o", str(tmp_path)])
    assert res.exit_code == 0 and "discovery" in res.stdout
    assert (tmp_path / "docs.md").exists()


def test_no_llms_skips_discovery(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("discover must not be called with --no-llms")
    monkeypatch.setattr(cli, "discover", boom)
    monkeypatch.setattr(run, "_acquire", lambda url, render, allow_remote, **kw: (
        FetchResult("https://s.com/p", b"x", "text/html"),
        Extracted("words " * 60, "Page", None),
    ))
    res = runner.invoke(_app(), ["https://s.com/p", "--no-llms", "-o", str(tmp_path)])
    assert res.exit_code == 0 and "created" in res.stdout


def test_single_mode_writes_via_acquire(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "discover", lambda url, crawl: None)
    monkeypatch.setattr(run, "_acquire", lambda url, render, allow_remote, **kw: (
        FetchResult("https://s.com/p", b"x", "text/html"),
        Extracted("words " * 60, "My Page", None),
    ))
    res = runner.invoke(_app(), ["https://s.com/p", "-o", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "my-page.md").exists()


def test_crawl_mode_invokes_crawl_site(tmp_path, monkeypatch):
    called = {}
    monkeypatch.setattr(cli, "discover", lambda url, crawl: None)

    def fake_crawl(url, out, max_pages, crawl_all, fetcher, echo, **kwargs):
        called["max_pages"] = max_pages
        return (3, 1)

    monkeypatch.setattr(cli, "crawl_site", fake_crawl)
    res = runner.invoke(_app(), ["https://s.com/", "--crawl", "--max-pages", "7", "-o", str(tmp_path)])
    assert res.exit_code == 0 and "3 page(s) written, 1 failed" in res.stdout
    assert called["max_pages"] == 7


def test_fetch_error_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "discover", lambda url, crawl: None)

    def boom(url, render, allow_remote):
        raise RuntimeError("blocked")
    monkeypatch.setattr(run, "_acquire", boom)
    res = runner.invoke(_app(), ["https://s.com/p", "-o", str(tmp_path)])
    assert res.exit_code == 1   # error reported (to stderr), nonzero exit


# --- Phase 2: non-HTML responses must route to markitdown, not the render tier ---


def _static_returns(monkeypatch, content_type, content=b"data"):
    monkeypatch.setattr(
        run.StaticFetcher, "fetch",
        lambda self, url: FetchResult(url, content, content_type),
    )


def test_acquire_nonhtml_routes_to_markitdown_not_render(monkeypatch):
    """A PDF (non-HTML) response is converted by markitdown — render is NOT called."""
    _static_returns(monkeypatch, "application/pdf", b"%PDF-1.4 ...")

    def no_render(url, *a):
        raise AssertionError("render must not be called for a non-HTML document")
    monkeypatch.setattr(run, "_render", no_render)
    monkeypatch.setattr(
        convert, "from_bytes",
        lambda data, url, ct, *, allow_remote: Extracted("PDF text", "Doc", None),
    )

    result, extracted = run._acquire("https://s.com/f.pdf", render=False, allow_remote=False)
    assert extracted.markdown == "PDF text"
    assert result.content_type == "application/pdf"


def test_acquire_nonhtml_falls_back_to_render_when_markitdown_missing(monkeypatch):
    """Without the [docs] extra, a non-HTML response falls back to the render tier.

    Exercises the REAL convert.from_bytes path (markitdown import wrapped to
    RuntimeError via _markitdown) rather than stubbing from_bytes — this is the
    regression that guards H1 (a bare ImportError would escape the fallback).
    """
    _static_returns(monkeypatch, "application/pdf")

    def no_markitdown():
        raise RuntimeError("markitdown not installed. Run: pip install 'mdnow[docs]'")
    monkeypatch.setattr(convert, "_markitdown", no_markitdown)
    sentinel = (FetchResult("https://s.com/f.pdf", b"<html>", "text/html"),
                Extracted("rendered", "R", None))
    monkeypatch.setattr(run, "_render", lambda url, *a: sentinel)

    _, extracted = run._acquire("https://s.com/f.pdf", render=False, allow_remote=False)
    assert extracted.markdown == "rendered"  # fell back to render, didn't crash


def test_from_bytes_blocks_extensionless_audio_by_mimetype(monkeypatch):
    """M1: audio/* content-type with no path extension is still refused (no silent egress)."""
    import pytest

    def no_markitdown():
        raise AssertionError("markitdown must not be touched — guard fires first")
    monkeypatch.setattr(convert, "_markitdown", no_markitdown)

    with pytest.raises(convert.RemoteBlocked):
        convert.from_bytes(b"audio-bytes", "https://s.com/clip", "audio/mpeg", allow_remote=False)


# --- Phase 3: input-type routing (local file / YouTube) ---------------------


def _no_discover(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("discover must not be called for a file/YouTube input")
    monkeypatch.setattr(cli, "discover", boom)


def test_local_file_routes_to_convert(tmp_path, monkeypatch):
    f = tmp_path / "doc.csv"
    f.write_text("a,b\n1,2\n")
    _no_discover(monkeypatch)
    monkeypatch.setattr(
        convert, "from_path",
        lambda path, *, allow_remote=False: Extracted("converted body", "Doc", None),
    )
    res = runner.invoke(_app(), [str(f), "-o", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "doc.md").exists()


def test_local_file_with_crawl_errors(tmp_path):
    f = tmp_path / "doc.csv"
    f.write_text("a\n1\n")
    res = runner.invoke(_app(), [str(f), "--crawl", "-o", str(tmp_path)])
    assert res.exit_code == 1


def test_youtube_routes_to_from_url_with_allow_remote(tmp_path, monkeypatch):
    _no_discover(monkeypatch)
    monkeypatch.setattr(
        convert, "from_url",
        lambda url, *, allow_remote=False: Extracted("transcript text", "Vid", None),
    )
    res = runner.invoke(_app(), ["https://youtu.be/abc", "--allow-remote", "-o", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "vid.md").exists()


def test_youtube_refused_without_allow_remote(tmp_path):
    res = runner.invoke(_app(), ["https://youtu.be/abc", "-o", str(tmp_path)])
    assert res.exit_code == 1


def test_acquire_nonhtml_remoteblocked_surfaces(monkeypatch):
    """An egress refusal propagates (so the user sees it) rather than rendering."""
    import pytest
    _static_returns(monkeypatch, "audio/mpeg")

    def no_render(url, *a):
        raise AssertionError("render must not be called when egress is refused")
    monkeypatch.setattr(run, "_render", no_render)

    def blocked(data, url, ct, *, allow_remote):
        raise convert.RemoteBlocked("audio needs --allow-remote")
    monkeypatch.setattr(convert, "from_bytes", blocked)

    with pytest.raises(convert.RemoteBlocked):
        run._acquire("https://s.com/a.mp3", render=False, allow_remote=False)


def test_missing_url_errors():
    res = runner.invoke(_app(), [])
    assert res.exit_code == 1
    assert "URL or file path is required" in res.output
