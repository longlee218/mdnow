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
    assert (tmp_path / "index.md").exists()
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
