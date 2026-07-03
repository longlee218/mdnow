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


def test_static_fetch_sends_custom_headers_and_cookies(monkeypatch):
    seen = {}

    def get(url, **kw):
        seen.update(kw)
        return FakeResp(200, "ok", "text/html")

    monkeypatch.setattr(fetcher.httpx, "get", get)
    StaticFetcher(
        headers={"Authorization": "Bearer tok"},
        cookies=[{"name": "session", "value": "abc", "domain": "x.com", "path": "/"}],
    ).fetch("https://x.com/p")
    assert seen["headers"]["Authorization"] == "Bearer tok"
    assert seen["headers"]["User-Agent"]            # UA still present
    jar = seen["cookies"]
    assert isinstance(jar, httpx.Cookies)


def test_static_fetch_header_can_override_user_agent(monkeypatch):
    seen = {}
    monkeypatch.setattr(fetcher.httpx, "get", lambda url, **kw: seen.update(kw) or FakeResp(200, "ok", "text/html"))
    StaticFetcher(headers={"User-Agent": "custom-ua"}).fetch("https://x.com/p")
    assert seen["headers"]["User-Agent"] == "custom-ua"


def test_cookie_jar_empty_is_none():
    assert fetcher._cookie_jar(None) is None
    assert fetcher._cookie_jar([]) is None


def test_camoufox_cookies_for_scopes_by_domain_or_url():
    f = fetcher.CamoufoxFetcher(cookies=[
        {"name": "a", "value": "1", "domain": ".x.com", "path": "/wiki"},
        {"name": "b", "value": "2"},   # no domain → scoped to the fetched url
    ])
    scoped = f._cookies_for("https://x.com/p")
    assert scoped[0] == {"name": "a", "value": "1", "domain": ".x.com", "path": "/wiki"}
    assert scoped[1] == {"name": "b", "value": "2", "url": "https://x.com/p"}


def test_domainless_cookie_scoped_to_request_host_not_global(monkeypatch):
    # regression: an empty-domain cookie would be sent to EVERY host,
    # leaking the session across a cross-host redirect
    seen = {}
    monkeypatch.setattr(fetcher.httpx, "get", lambda url, **kw: seen.update(kw) or FakeResp(200, "ok", "text/html"))
    StaticFetcher(cookies=[{"name": "session", "value": "abc"}]).fetch("https://internal.corp.com/p")
    domains = {c.domain for c in seen["cookies"].jar}
    assert domains == {"internal.corp.com"}
