from mdnow.outline import headings, slugify_heading, summary_of, token_estimate


def test_token_estimate_is_ceil_chars_over_4():
    assert token_estimate("") == 0
    assert token_estimate("a" * 40) == 10
    assert token_estimate("a" * 41) == 11


def test_slugify_heading():
    assert slugify_heading("Hello, World!") == "hello-world"
    assert slugify_heading("  Multiple   Spaces  ") == "multiple-spaces"
    assert slugify_heading("!!!") == ""               # all punctuation
    assert slugify_heading("Café Münü") == "café-münü"  # unicode preserved


def test_headings_levels_and_slug_dedup():
    hs = headings("# A\n\n## B\n\n## B\n")
    assert [h["level"] for h in hs] == [1, 2, 2]
    assert [h["slug"] for h in hs] == ["a", "b", "b-1"]


def test_headings_ignore_code_fences():
    md = "# Real\n\n```\n# fake\n## fake2\n```\n\n## Second\n"
    assert [h["text"] for h in headings(md)] == ["Real", "Second"]


def test_summary_first_meaningful_paragraph():
    md = "# Title\n\n- bullet\n\nThis is a genuine paragraph long enough to qualify as a summary sentence.\n"
    assert summary_of(md).startswith("This is a genuine paragraph")


def test_summary_empty_when_no_prose_and_respects_cap():
    assert summary_of("# Only heading\n\n- a\n- b") == ""
    assert len(summary_of("\n\n" + "x" * 500, max_chars=100)) == 100
