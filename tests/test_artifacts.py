import json

from mdnow.artifacts import build_llms_full, build_llms_txt, build_manifest

PAGES = [
    {"title": "Home", "source_url": "https://s.com/", "local_path": "home.md",
     "body": "# Home\n\nWelcome to the documentation site, with enough prose here to summarize nicely."},
    {"title": "Auth", "source_url": "https://s.com/auth", "local_path": "auth.md",
     "body": "# Auth\n\n## Tokens\n\nHow authentication tokens work in this system, explained at some length."},
]


def test_llms_txt_shape():
    out = build_llms_txt("s.com", "Site summary here", PAGES)
    assert out.startswith("# s.com\n")
    assert "> Site summary here" in out and "## Pages" in out
    assert "- [Home](home.md):" in out and "- [Auth](auth.md):" in out


def test_llms_full_includes_every_page_body_and_source():
    out = build_llms_full("s.com", "sum", PAGES)
    assert out.count("## ") >= 2
    assert "Source: https://s.com/" in out and "Source: https://s.com/auth" in out
    assert "How authentication tokens work" in out


def test_manifest_structure_and_headings():
    d = json.loads(build_manifest("s.com", "https://s.com/", PAGES))
    assert d["host"] == "s.com" and d["page_count"] == 2
    p = d["pages"][1]
    assert set(p) == {"source_url", "local_path", "title", "content_hash",
                      "token_estimate", "word_count", "summary", "headings"}
    assert any(h["slug"] == "tokens" for h in p["headings"])


def test_llms_txt_title_injection_sanitized():
    bad = [{"title": "Evil](http://x)\nrow", "source_url": "https://s.com/p", "local_path": "p.md",
            "body": "# H\n\nbody long enough to qualify as a summary sentence right here indeed."}]
    out = build_llms_txt("s.com", "s", bad)
    assert "](http://x)" not in out
    assert out.count("- [") == 1          # no injected second entry


def test_builders_handle_empty_crawl():
    assert "# s.com" in build_llms_txt("s.com", "s", [])
    assert json.loads(build_manifest("s.com", "https://s.com/", []))["page_count"] == 0
