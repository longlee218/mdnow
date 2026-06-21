import httpx
import pytest

import mdnow.fetcher as fetcher
from mdnow.fetcher import StaticFetcher

from conftest import FakeResp


def test_static_fetch_success(monkeypatch):
    monkeypatch.setattr(
        fetcher.httpx, "get",
        lambda *a, **k: FakeResp(200, "<html>ok</html>", "text/html", url="https://x.com/p"),
    )
    r = StaticFetcher().fetch("https://x.com/p")
    assert r.url == "https://x.com/p" and r.content == b"<html>ok</html>"
    assert "text/html" in r.content_type


def test_static_4xx_fails_fast_no_retry(monkeypatch):
    calls = {"n": 0}

    def get(*a, **k):
        calls["n"] += 1
        return FakeResp(403, url="https://x.com/p")

    monkeypatch.setattr(fetcher.httpx, "get", get)
    with pytest.raises(RuntimeError):
        StaticFetcher().fetch("https://x.com/p")
    assert calls["n"] == 1          # 403 → no retry


def test_static_transport_error_retries_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def get(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectTimeout("boom")
        return FakeResp(200, "ok", "text/html")

    monkeypatch.setattr(fetcher.httpx, "get", get)
    r = StaticFetcher().fetch("https://x.com/p")
    assert calls["n"] == 2 and r.content == b"ok"   # retried once
