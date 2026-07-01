"""mcp_server.py — MCP tool handlers. Network-free.

These tests are skipped if the `[mcp]` extra is not installed.
"""
import asyncio
import json
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mdnow.extractor import Extracted
from mdnow.fetcher import FetchResult
from mdnow.mcp_server import (
    CHARACTER_LIMIT,
    ConvertFileInput,
    CrawlSiteInput,
    FetchUrlInput,
    _format_result,
    _truncate,
    convert_file,
    crawl_site,
    fetch_url,
)


def _run(coro):
    return asyncio.run(coro)


def test_fetch_url_success(monkeypatch):
    monkeypatch.setattr(
        "mdnow.runner._acquire",
        lambda url, render, allow_remote: (
            FetchResult("https://s.com/p", b"x", "text/html"),
            Extracted("# Hello\n\nworld", "Hello", None),
        ),
    )
    result = _run(fetch_url(FetchUrlInput(url="https://s.com/p")))
    data = json.loads(result)
    assert data["title"] == "Hello"
    assert "# Hello" in data["markdown"]
    assert data["word_count"] == 3


def test_fetch_url_truncation(monkeypatch):
    long_md = "word " * 10_000  # > 25_000 chars
    monkeypatch.setattr(
        "mdnow.runner._acquire",
        lambda url, render, allow_remote: (
            FetchResult("https://s.com/p", b"", "text/html"),
            Extracted(long_md, "Long", None),
        ),
    )
    result = _run(fetch_url(FetchUrlInput(url="https://s.com/p")))
    data = json.loads(result)  # must remain valid JSON after truncation
    assert "truncated" in data["markdown"]
    assert len(result) <= CHARACTER_LIMIT + 500


def test_fetch_url_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("blocked")
    monkeypatch.setattr("mdnow.runner._acquire", boom)
    result = _run(fetch_url(FetchUrlInput(url="https://s.com/p")))
    data = json.loads(result)
    assert "error" in data


def test_crawl_site_success(monkeypatch, tmp_path):
    def fake_crawl(url, out, max_pages, crawl_all, fetcher, echo, **kwargs):
        # Simulate crawler output
        (out / "manifest.json").write_text(
            json.dumps({
                "pages": [
                    {"source_url": "https://s.com/", "local_path": "index.md", "title": "Home"},
                    {"source_url": "https://s.com/a", "local_path": "a.md", "title": "A"},
                ]
            }),
            encoding="utf-8",
        )
        return (2, 0)
    monkeypatch.setattr("mdnow.crawler.crawl_site", fake_crawl)

    result = _run(crawl_site(CrawlSiteInput(url="https://s.com/")))
    data = json.loads(result)
    assert data["pages_crawled"] == 2
    assert data["pages_failed"] == 0
    assert len(data["pages"]) == 2


def test_convert_file_local_success(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "mdnow.runner._convert_file_to_extracted",
        lambda path, allow_remote: Extracted("# File", "File", None),
    )
    monkeypatch.setattr("mdnow.inputs.is_local_file", lambda p: True)
    result = _run(convert_file(ConvertFileInput(path="/tmp/report.pdf")))
    data = json.loads(result)
    assert data["title"] == "File"
    assert "# File" in data["markdown"]


def test_convert_file_remote_success(monkeypatch):
    monkeypatch.setattr("mdnow.inputs.is_local_file", lambda p: False)
    monkeypatch.setattr("mdnow.runner._acquire",
        lambda url, render, allow_remote: (
            FetchResult("https://s.com/report.pdf", b"PDF", "application/pdf"),
            Extracted("# Remote File", "Remote", None),
        ),
    )
    result = _run(convert_file(ConvertFileInput(path="https://s.com/report.pdf")))
    data = json.loads(result)
    assert data["title"] == "Remote"
    assert data["source_url"] == "https://s.com/report.pdf"


def test_truncate_under_limit():
    assert _truncate("short") == "short"


def test_truncate_over_limit():
    long = "a" * (CHARACTER_LIMIT + 100)
    result = _truncate(long)
    assert result.endswith("chars omitted]")
    assert len(result) <= CHARACTER_LIMIT + 100


def test_format_result_structure():
    extracted = Extracted("hello world", "T", None)
    result = _format_result(extracted, "https://s.com/p")
    data = json.loads(result)
    assert set(data.keys()) == {"source_url", "title", "word_count", "token_estimate", "summary", "markdown"}
    assert data["source_url"] == "https://s.com/p"
    assert data["title"] == "T"
    assert data["word_count"] == 2
