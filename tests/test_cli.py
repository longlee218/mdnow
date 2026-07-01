import mdnow.runner as runner
import mdnow.slugs as slugs
from mdnow.extractor import Extracted
from mdnow.fetcher import FetchResult


def test_slug_fallbacks():
    assert slugs.slug("My Post: A Guide", "https://x.com/p") == "my-post-a-guide"
    assert slugs.slug("Café Crème", "https://x.com/c") == "cafe-creme"
    assert slugs.slug("日本語", "https://x.com/guide/intro") == "guide-intro"   # non-ascii → url path
    assert slugs.slug("!!!", "https://x.com/docs/p7") == "docs-p7"             # symbols → url path
    assert slugs.slug("", "https://example.com/") == "example-com"             # empty → host


def _static(content=b"<html></html>", ctype="text/html"):
    return lambda: type("F", (), {"fetch": lambda self, u: FetchResult(u, content, ctype)})()


def test_acquire_render_flag_forces_render(monkeypatch):
    called = {}
    monkeypatch.setattr(runner, "_render", lambda u: (FetchResult(u, b"", "text/html"),
                                                   Extracted("rendered body words " * 20, "R", None)))
    res, ext = runner._acquire("https://x.com", render=True, allow_remote=False)
    assert ext.title == "R"


def test_acquire_escalates_on_static_403(monkeypatch):
    def boom_fetch(self, u): raise RuntimeError("403")
    monkeypatch.setattr(runner, "StaticFetcher", lambda: type("F", (), {"fetch": boom_fetch})())
    monkeypatch.setattr(runner, "_render", lambda u: (FetchResult(u, b"", "text/html"),
                                                   Extracted("words " * 100, "Rendered", None)))
    _, ext = runner._acquire("https://x.com", render=False, allow_remote=False)
    assert ext.title == "Rendered"


def test_acquire_thin_static_kept_when_render_fails(monkeypatch):
    monkeypatch.setattr(runner, "StaticFetcher", _static())
    monkeypatch.setattr(runner, "extract", lambda c, url=None: Extracted("ten words " * 5, "Thin", None))
    def render_fails(u): raise ValueError("rendered but empty")
    monkeypatch.setattr(runner, "_render", render_fails)
    _, ext = runner._acquire("https://x.com/p", render=False, allow_remote=False)
    assert ext.title == "Thin" and ext.word_count == 10   # kept, no crash


def test_acquire_returns_good_static_without_render(monkeypatch):
    monkeypatch.setattr(runner, "StaticFetcher", _static())
    monkeypatch.setattr(runner, "extract", lambda c, url=None: Extracted("plenty of words here " * 30, "OK", None))
    sentinel = {"rendered": False}
    monkeypatch.setattr(runner, "_render", lambda u: sentinel.__setitem__("rendered", True))
    _, ext = runner._acquire("https://x.com/p", render=False, allow_remote=False)
    assert ext.title == "OK" and sentinel["rendered"] is False   # render never called
