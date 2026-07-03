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


def test_sections_split_at_headings_with_intro():
    md = "Intro paragraph before any heading with several words.\n\n# A\n\nBody of A here.\n\n## B\n\nBody of B.\n"
    from mdnow.outline import sections
    secs = sections(md)
    assert [s["slug"] for s in secs] == ["_intro", "a", "b"]
    assert secs[0]["level"] == 0 and secs[0]["heading"] == ""
    assert secs[1]["heading"] == "A" and secs[1]["level"] == 1
    assert secs[1]["word_count"] == 4          # "Body of A here."
    assert secs[2]["token_estimate"] > 0


def test_sections_no_intro_when_document_starts_with_heading():
    from mdnow.outline import sections
    secs = sections("# Top\n\ntext here\n")
    assert [s["slug"] for s in secs] == ["top"]


def test_sections_ignore_headings_inside_code_fences():
    from mdnow.outline import sections
    md = "# Real\n\n```\n# fake\n```\n\nafter code\n"
    secs = sections(md)
    assert len(secs) == 1
    # the fenced block's words still belong to the section's content
    assert secs[0]["word_count"] >= 3


def test_sections_slugs_match_headings_dedup():
    from mdnow.outline import headings, sections
    md = "# X\n\na\n\n# X\n\nb\n"
    assert [s["slug"] for s in sections(md)] == [h["slug"] for h in headings(md)]
