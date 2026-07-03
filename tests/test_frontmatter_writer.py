from mdnow import frontmatter
from mdnow.writer import write


def test_content_hash_ignores_surrounding_whitespace():
    assert frontmatter.content_hash("body") == frontmatter.content_hash("  body  ")


def test_render_is_yaml_safe_for_colon_titles():
    meta = frontmatter.build("https://x.com", "Title: with colon", None, "2026-06-21", 1, "body")
    doc = frontmatter.render(meta, "body")
    assert doc.startswith("---\n") and "\n---\n\n" in doc and doc.rstrip().endswith("body")


def test_build_includes_token_estimate_and_summary():
    body = "# T\n\nThis is a meaningful paragraph long enough to be captured as the page summary text."
    meta = frontmatter.build("https://x.com", "T", None, "2026-06-21", 1, body)
    assert meta["token_estimate"] > 0
    assert meta["summary"].startswith("This is a meaningful paragraph")


def test_writer_versioning_created_unchanged_updated(tmp_path):
    p = tmp_path / "x.md"
    o1 = write(p, "https://x.com", "T", None, "2026-06-21", "hello world")
    assert o1.status == "created" and o1.version == 1

    o2 = write(p, "https://x.com", "T", None, "2026-06-22", "hello world")
    assert o2.status == "unchanged" and o2.version == 1   # same body → no bump

    o3 = write(p, "https://x.com", "T", None, "2026-06-22", "hello world changed")
    assert o3.status == "updated" and o3.version == 2     # changed → bump


def test_build_includes_outline_of_headings():
    from mdnow.frontmatter import build
    meta = build("https://s.com/p", "T", None, "2026-07-03", 1, "# A\n\ntext\n\n## B\n\nmore\n")
    assert meta["outline"] == ["# A", "## B"]
