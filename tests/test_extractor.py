import pytest

from mdnow.extractor import extract, is_html


def _article(extra: str = "") -> bytes:
    paras = "".join(
        f"<p>Paragraph {i} with plenty of real words so the extractor heuristics "
        f"engage and treat this as genuine article content.</p>"
        for i in range(8)
    )
    return (
        f"<html><head><title>Guide</title></head><body>"
        f"<nav>Home About ADSENSE</nav><article><h1>Guide</h1>{paras}{extra}</article>"
        f"<footer>COOKIEBANNER privacy</footer></body></html>"
    ).encode()


def test_extract_strips_boilerplate_and_keeps_heading():
    e = extract(_article())
    assert e.title == "Guide"
    assert "# Guide" in e.markdown
    assert "ADSENSE" not in e.markdown and "COOKIEBANNER" not in e.markdown


def test_image_becomes_alt_text():
    html = _article('<figure><img src="https://cdn/x.png" alt="a diagram"></figure>')
    e = extract(html)
    assert "![" not in e.markdown          # no image syntax
    assert "a diagram" in e.markdown        # alt text kept


def test_empty_content_raises():
    with pytest.raises(ValueError):
        extract(b"<html><body></body></html>")


def test_is_html():
    assert is_html("text/html; charset=utf-8") and is_html("")
    assert not is_html("application/pdf") and not is_html("image/png")
