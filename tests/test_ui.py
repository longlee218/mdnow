"""Console UI helpers: markup-safety, informational substrings, progress."""
import mdnow.ui as ui
from mdnow.doctor import Check


def _capture(monkeypatch, width=200):
    """Force Rich to render plain text into a buffer (simulate a non-tty)."""
    from io import StringIO
    from rich.console import Console

    buf = StringIO()
    console = Console(file=buf, theme=ui._THEME, force_terminal=False, width=width, highlight=False)
    monkeypatch.setattr(ui, "_out", console)
    return buf


def test_success_keeps_status_and_detail_substrings(monkeypatch):
    buf = _capture(monkeypatch)
    ui.success("created", "out/page.md", "v1, 40 words")
    out = buf.getvalue()
    assert "created" in out and "out/page.md" in out and "40 words" in out


def test_folder_summary_substrings(monkeypatch):
    buf = _capture(monkeypatch)
    ui.folder_summary(4, 1, "out/")
    out = buf.getvalue()
    assert "file(s) converted" in out and "4" in out and "1 failed" in out and "out/" in out


def test_folder_summary_clean_run_mark(monkeypatch):
    buf = _capture(monkeypatch)
    ui.folder_summary(3, 0, "out/")
    assert "✓" in buf.getvalue()


def test_crawl_summary_still_says_pages(monkeypatch):
    buf = _capture(monkeypatch)
    ui.crawl_summary(2, 0, "out/")
    assert "page(s) written" in buf.getvalue()


def test_progress_bar_accepts_verb(monkeypatch):
    _capture(monkeypatch)
    with ui.progress_bar("converting") as advance:
        advance(1, 2, "a.pdf")
        advance(2, 2, "b.pdf")


def test_hint_and_note_render(monkeypatch):
    buf = _capture(monkeypatch)
    ui.hint("Read it: out/page.md")
    ui.note("Discovered 4 page(s).")
    out = buf.getvalue()
    assert "Read it: out/page.md" in out and "Discovered 4" in out


def test_doctor_report_preserves_bracketed_names(monkeypatch):
    # regression: a name like "[docs] extra" must not be eaten as Rich markup
    buf = _capture(monkeypatch)
    ui.doctor_report([
        Check("[docs] extra", True, "installed"),
        Check("[render] extra", False, "not installed", fix="uv tool install ..."),
    ])
    out = buf.getvalue()
    assert "[docs] extra" in out and "[render] extra" in out
    assert "uv tool install" in out          # fix hint shown for the failing check


def test_crawl_summary_marks_failure(monkeypatch):
    buf = _capture(monkeypatch)
    ui.crawl_summary(3, 1, "out/")
    ui.crawl_summary(4, 0, "out/")
    out = buf.getvalue()
    assert "3 page(s) written, 1 failed" in out
    assert "4 page(s) written, 0 failed" in out


def test_progress_bar_advances_lazily(monkeypatch):
    _capture(monkeypatch)
    with ui.progress_bar() as advance:
        advance(1, 3, "/a")   # creates the task on first call
        advance(3, 3, "/c")   # updates it — must not raise


def test_progress_label_with_brackets_does_not_crash(monkeypatch):
    # regression: URL paths like '/docs/[slug]' or '[/]' must not be parsed as
    # Rich markup (would eat the segment or raise MarkupError on Live refresh)
    _capture(monkeypatch)
    with ui.progress_bar() as advance:
        advance(1, 2, "/docs/[slug]")
        advance(2, 2, "/weird/[/]/path")   # malformed markup — must not raise


def test_long_path_not_hard_wrapped_on_narrow_nontty(monkeypatch):
    # regression: at the 80-col non-tty default, a long path must stay on one
    # line so scripts parsing the emitted path don't get a broken string
    buf = _capture(monkeypatch, width=80)
    long_path = "out/" + "a" * 120 + "/very-long-page-name.md"
    ui.success("created", long_path, "v1, 40 words")
    assert long_path in buf.getvalue()   # intact, not split by a newline
