from mdnow.linkrewrite import rewrite_links

UMAP = {"https://s.com/guides/auth": "guides/auth.md", "https://s.com/home": "home.md"}


def test_crawled_link_becomes_relative():
    out = rewrite_links("[a](/guides/auth)", "https://s.com/home", "home.md", UMAP)
    assert out == "[a](guides/auth.md)"


def test_not_crawled_and_external_left_absolute():
    out = rewrite_links("[a](/nope) [b](https://x.com/y)", "https://s.com/home", "home.md", UMAP)
    assert "(https://s.com/nope)" in out and "(https://x.com/y)" in out


def test_fragment_preserved():
    out = rewrite_links("[a](/guides/auth#sec)", "https://s.com/home", "home.md", UMAP)
    assert out == "[a](guides/auth.md#sec)"


def test_relative_from_nested_page():
    out = rewrite_links("[h](/home)", "https://s.com/guides/auth", "guides/auth.md", UMAP)
    assert out == "[h](../home.md)"


def test_paren_in_url_not_truncated():
    # crawled paren URL -> relative
    um = {"https://s.com/wiki/Mercury_(planet)": "wiki/mercury.md"}
    assert rewrite_links("[Hg](/wiki/Mercury_(planet))", "https://s.com/x", "x.md", um) == "[Hg](wiki/mercury.md)"
    # not-crawled paren URL -> absolute, intact
    assert rewrite_links("[x](/a_(b))", "https://s.com/x", "x.md", {}) == "[x](https://s.com/a_(b))"


def test_title_preserved():
    out = rewrite_links('[x](/a "T")', "https://s.com/x", "x.md", {})
    assert '"T"' in out
