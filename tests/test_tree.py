from dataclasses import dataclass

from mdnow.tree import build_index


@dataclass
class P:
    canon: str
    title: str | None


def test_build_index_links_and_nesting():
    pages = [P("https://s.com/home", "Home"), P("https://s.com/a/b", "B")]
    m = {"https://s.com/home": "home.md", "https://s.com/a/b": "a/b.md"}
    idx = build_index("s.com", pages, m)
    assert "# Site Index — s.com" in idx
    assert "- [Home](home.md)" in idx
    assert "  - [B](a/b.md)" in idx        # depth 1 → indented


def test_build_index_missing_title_falls_back_to_relpath():
    pages = [P("https://s.com/x", None)]
    idx = build_index("s.com", pages, {"https://s.com/x": "x.md"})
    assert "[x.md](x.md)" in idx
