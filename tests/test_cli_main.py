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
    monkeypatch.setattr(cli, "_acquire", lambda url, render: (
        FetchResult("https://s.com/p", b"x", "text/html"),
        Extracted("words " * 60, "Page", None),
    ))
    res = runner.invoke(_app(), ["https://s.com/p", "--no-llms", "-o", str(tmp_path)])
    assert res.exit_code == 0 and "created" in res.stdout


def test_single_mode_writes_via_acquire(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "discover", lambda url, crawl: None)
    monkeypatch.setattr(cli, "_acquire", lambda url, render: (
        FetchResult("https://s.com/p", b"x", "text/html"),
        Extracted("words " * 60, "My Page", None),
    ))
    res = runner.invoke(_app(), ["https://s.com/p", "-o", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "my-page.md").exists()


def test_crawl_mode_invokes_crawl_site(tmp_path, monkeypatch):
    called = {}
    monkeypatch.setattr(cli, "discover", lambda url, crawl: None)

    def fake_crawl(url, out, max_pages, crawl_all, fetcher, echo):
        called["max_pages"] = max_pages
        return (3, 1)

    monkeypatch.setattr(cli, "crawl_site", fake_crawl)
    res = runner.invoke(_app(), ["https://s.com/", "--crawl", "--max-pages", "7", "-o", str(tmp_path)])
    assert res.exit_code == 0 and "3 page(s) written, 1 failed" in res.stdout
    assert called["max_pages"] == 7


def test_fetch_error_exits_nonzero(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "discover", lambda url, crawl: None)

    def boom(url, render):
        raise RuntimeError("blocked")
    monkeypatch.setattr(cli, "_acquire", boom)
    res = runner.invoke(_app(), ["https://s.com/p", "-o", str(tmp_path)])
    assert res.exit_code == 1   # error reported (to stderr), nonzero exit
