import mdnow.crawler as crawler
from mdnow.fetcher import FetchResult


def _page_html(url: str) -> bytes:
    paras = "".join(
        f"<p>Paragraph {i} with enough genuine words for the extractor heuristics "
        f"to treat this as real article content worth keeping.</p>"
        for i in range(6)
    )
    link = '<p>Please read the <a href="/about">about</a> page for more.</p>' if url.endswith("/") else ""
    return (
        f"<html><head><title>{url}</title></head><body>"
        f"<article><h1>Page</h1>{paras}{link}</article></body></html>"
    ).encode()


class _FakeFetcher:
    def fetch(self, url: str) -> FetchResult:
        return FetchResult(url, _page_html(url), "text/html")


def test_crawl_site_writes_pages_tree_and_rewrites_links(tmp_path, monkeypatch):
    monkeypatch.setattr(crawler, "CRAWL_DELAY", 0.0)  # speed up test
    monkeypatch.setattr(
        crawler, "discover_urls",
        lambda *a, **k: ["https://s.com/", "https://s.com/about"],
    )
    ok, failed = crawler.crawl_site("https://s.com/", tmp_path, 10, False, _FakeFetcher(), lambda m: None)

    assert ok == 2 and failed == 0
    assert not (tmp_path / "index.md").exists()           # superseded by llms.txt
    for f in ("llms.txt", "llms-full.txt", "manifest.json"):
        assert (tmp_path / f).exists()
    assert (tmp_path / "home.md").exists() and (tmp_path / "about.md").exists()
    # internal crawled link rewritten to a relative local path
    assert "about.md" in (tmp_path / "home.md").read_text()


def test_crawl_site_isolates_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(crawler, "CRAWL_DELAY", 0.0)
    monkeypatch.setattr(
        crawler, "discover_urls",
        lambda *a, **k: ["https://s.com/", "https://s.com/bad"],
    )

    class Flaky:
        def fetch(self, url):
            if url.endswith("/bad"):
                raise RuntimeError("boom")
            return FetchResult(url, _page_html(url), "text/html")

    ok, failed = crawler.crawl_site("https://s.com/", tmp_path, 10, False, Flaky(), lambda m: None)
    assert ok == 1 and failed == 1      # one bad page does not abort the run


# ---- render-aware discovery (Phase 1) ----

_SPA_LINKS_HTML = (
    "<html><body>"
    '<a href="/controllers">Controllers</a>'
    '<a href="/providers">Providers</a>'
    '<a href="/faq/global-prefix#anchor">FAQ</a>'      # fragment stripped
    '<a href="/assets/favicon.ico">icon</a>'           # asset dropped
    '<a href="https://external.com/x">ext</a>'          # off-host dropped
    "</body></html>"
).encode()


class _SpaRenderer:
    """Static discovery finds nothing; this renderer exposes the nav links."""
    def fetch(self, url):
        return FetchResult("https://s.com/", _SPA_LINKS_HTML, "text/html")


def test_discover_urls_renders_when_static_empty(monkeypatch):
    monkeypatch.setattr(crawler, "sitemap_search", lambda *a, **k: [])
    monkeypatch.setattr(crawler, "focused_crawler", lambda *a, **k: ([], {"https://s.com/"}))

    urls = crawler.discover_urls("https://s.com/", 100, False, renderer=_SpaRenderer())

    assert "https://s.com/controllers" in urls
    assert "https://s.com/providers" in urls
    assert "https://s.com/faq/global-prefix" in urls   # fragment stripped
    assert not any("favicon" in u for u in urls)        # asset dropped
    assert not any("external.com" in u for u in urls)   # off-host dropped
    assert urls[0] == "https://s.com/"                   # start URL first


def test_discover_urls_static_hit_skips_render(monkeypatch):
    monkeypatch.setattr(crawler, "sitemap_search", lambda *a, **k: [])
    monkeypatch.setattr(
        crawler, "focused_crawler",
        lambda *a, **k: ([], {"https://s.com/", "https://s.com/a", "https://s.com/b"}),
    )

    class _Boom:
        def fetch(self, url):
            raise AssertionError("renderer must not be called when static discovery is rich")

    urls = crawler.discover_urls("https://s.com/", 100, False, renderer=_Boom())
    assert set(urls) == {"https://s.com/", "https://s.com/a", "https://s.com/b"}


# ---- fetch-loop escalation (Phase 2) ----

def test_crawl_escalates_thin_page_to_renderer(tmp_path, monkeypatch):
    monkeypatch.setattr(crawler, "CRAWL_DELAY", 0.0)
    monkeypatch.setattr(crawler, "discover_urls", lambda *a, **k: ["https://s.com/thin"])

    class _ThinPrimary:
        def fetch(self, url):
            return FetchResult(url, b"<html><body><p>too short</p></body></html>", "text/html")

    class _FullRenderer:
        def fetch(self, url):
            return FetchResult(url, _page_html(url), "text/html")

    ok, failed = crawler.crawl_site(
        "https://s.com/thin", tmp_path, 10, False, _ThinPrimary(), lambda m: None,
        renderer=_FullRenderer(),
    )
    assert ok == 1 and failed == 0
    assert (tmp_path / "thin.md").exists()


def test_crawl_no_renderer_skips_unextractable(tmp_path, monkeypatch):
    monkeypatch.setattr(crawler, "CRAWL_DELAY", 0.0)
    monkeypatch.setattr(crawler, "discover_urls", lambda *a, **k: ["https://s.com/empty"])

    class _EmptyPrimary:
        def fetch(self, url):
            return FetchResult(url, b"<html><body></body></html>", "text/html")

    ok, failed = crawler.crawl_site(
        "https://s.com/empty", tmp_path, 10, False, _EmptyPrimary(), lambda m: None,
        renderer=None,
    )
    assert ok == 0 and failed == 1      # today's behavior preserved when no renderer


def test_crawl_render_flag_no_double_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr(crawler, "CRAWL_DELAY", 0.0)
    monkeypatch.setattr(crawler, "discover_urls", lambda *a, **k: ["https://s.com/p"])
    calls = {"n": 0}

    class _CountingRenderer:
        def fetch(self, url):
            calls["n"] += 1
            return FetchResult(url, _page_html(url), "text/html")

    fetcher = _CountingRenderer()
    # primary IS the renderer (--render) → escalation guard off, no re-fetch
    ok, failed = crawler.crawl_site(
        "https://s.com/p", tmp_path, 10, False, fetcher, lambda m: None,
        render=True, renderer=fetcher,
    )
    assert ok == 1 and failed == 0 and calls["n"] == 1
