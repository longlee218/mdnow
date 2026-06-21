import mdnow.llmstxt as llmstxt
from mdnow.llmstxt import _looks_markdown, probe_page, probe_site

from conftest import FakeResp, router


def test_validator_accepts_markdown_rejects_html_and_json():
    assert _looks_markdown("# Title\n[x](/a)", "text/plain")
    assert not _looks_markdown("<!DOCTYPE html><html>..", "text/html")
    assert not _looks_markdown("<html>spa</html>", "text/html; charset=utf-8")
    assert not _looks_markdown('{"e":"' + "x" * 300 + '"}', "application/json")
    assert not _looks_markdown("plain text no markers " * 20, "text/plain")  # no marker → reject


def test_probe_site_prefers_llms_full(monkeypatch):
    routes = {
        "/llms-full.txt": FakeResp(200, "# Full\n[a](/a)", url="https://s.com/llms-full.txt"),
        "/llms.txt": FakeResp(200, "# Index\n[a](/a)", url="https://s.com/llms.txt"),
    }
    monkeypatch.setattr(llmstxt.httpx, "get", router(routes))
    d = probe_site("https://s.com/")
    assert d and d.source_url.endswith("/llms-full.txt") and d.title == "Full"


def test_probe_site_none_when_absent(monkeypatch):
    monkeypatch.setattr(llmstxt.httpx, "get", router({}))  # everything 404
    assert probe_site("https://s.com/") is None


def test_probe_site_rejects_oversized(monkeypatch):
    big = FakeResp(200, content_type="text/plain", content=b"#" * (llmstxt.MAX_DISCOVERY_BYTES + 1))
    monkeypatch.setattr(llmstxt.httpx, "get", router({"/llms.txt": big, "/llms-full.txt": big}))
    assert probe_site("https://s.com/") is None


def test_probe_page_md_twin(monkeypatch):
    routes = {"/guide.md": FakeResp(200, "# Guide\n[x](/y)", url="https://s.com/guide.md")}
    monkeypatch.setattr(llmstxt.httpx, "get", router(routes))
    d = probe_page("https://s.com/guide")
    assert d and d.source_url.endswith("/guide.md")
