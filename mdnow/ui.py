"""Console UI: one Rich Console + styled, markup-safe helpers.

Rich auto-degrades on a non-tty / NO_COLOR terminal (plain text, no ANSI), so
output stays scriptable and the informational substrings stay intact. All
dynamic content is rendered via rich.text.Text (never markup parsing), so a
title or path containing '[' can't break formatting or inject styles.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

_THEME = Theme({
    "ok": "bold green", "err": "bold red", "warn": "yellow",
    "hint": "cyan", "muted": "dim", "head": "bold",
})
_out = Console(theme=_THEME, highlight=False)
_err = Console(theme=_THEME, stderr=True, highlight=False)


def _line(console: Console, text: Text) -> None:
    """Print one status line without wrapping. soft_wrap stops Rich from
    hard-wrapping at the (80-col) non-tty default, which would split a long
    file path mid-string and break scripts that parse the emitted path."""
    console.print(text, soft_wrap=True)


def info(msg: str) -> None:
    _line(_out, Text(msg, style="muted"))


def step(action: str, subject: str) -> None:
    """A work-in-progress line, e.g. 'Fetching  https://… …'."""
    _line(_out, Text.assemble((f"{action} ", "muted"), subject, (" …", "muted")))


def success(status: str, path: str, detail: str) -> None:
    """A written-file outcome. Keeps status ('created'/'updated'/'unchanged')
    and detail as plain substrings for scripts and tests."""
    _line(_out, Text.assemble(("✓ ", "ok"), f"{status}: {path} ", (f"({detail})", "muted")))


def note(msg: str) -> None:
    _line(_out, Text.assemble(("  • ", "muted"), (msg, "muted")))


def hint(msg: str) -> None:
    """An actionable next step / suggestion."""
    _line(_out, Text.assemble(("→ ", "hint"), (msg, "hint")))


def error(msg: str) -> None:
    _line(_err, Text.assemble(("Error: ", "err"), msg))


def crawl_summary(ok: int, failed: int, out: str) -> None:
    mark, style = ("✓", "ok") if failed == 0 else ("!", "warn")
    _line(_out, Text.assemble(
        (f"{mark} Done: ", style), f"{ok} page(s) written, {failed} failed ",
        ("→ ", "muted"), (out, "muted"),
    ))


def doctor_report(checks: list) -> None:
    """Render doctor checks as a colored table. Falls back to plain rows on a
    non-tty. `checks` are doctor.Check objects (name, ok, detail, fix)."""
    table = Table(title="mdnow doctor", title_style="head", show_edge=False, pad_edge=False)
    table.add_column("", no_wrap=True)
    table.add_column("Check", style="head", no_wrap=True)
    table.add_column("Detail")
    for c in checks:
        mark = Text("✓", style="ok") if c.ok else Text("✗", style="err")
        detail = Text(c.detail)
        if not c.ok and c.fix:
            detail.append(f"\n→ {c.fix}", style="hint")
        # Text() so a name/detail containing '[...]' (e.g. '[docs] extra') is
        # never parsed as Rich markup.
        table.add_row(mark, Text(c.name), detail)
    _out.print(table)


@contextmanager
def status(message: str) -> Iterator[None]:
    """Spinner while a single fetch/convert runs. No-op visual on a non-tty."""
    with _out.status(Text(message, style="muted"), spinner="dots"):
        yield


@contextmanager
def progress_bar() -> Iterator[Callable[[int, int, str], None]]:
    """Crawl progress. Yields advance(done, total, label); the task is created
    lazily on the first call so the total (known only after discovery) is set
    correctly. Renders nothing extra on a non-tty."""
    prog = Progress(
        TextColumn("[muted]crawling[/muted]"),
        BarColumn(),
        MofNCompleteColumn(),
        # markup=False: the description is a URL path (e.g. '/docs/[slug]');
        # with the default markup=True, '[slug]' is eaten as a style tag and a
        # path like '[/]' raises MarkupError on the final Live refresh — after
        # pages are written — making a successful crawl look like a crash.
        TextColumn("{task.description}", markup=False),
        console=_out,
        transient=True,
    )
    task_id = {"id": None}

    def advance(done: int, total: int, label: str) -> None:
        if task_id["id"] is None:
            task_id["id"] = prog.add_task("", total=total)
        prog.update(task_id["id"], completed=done, description=label)

    with prog:
        yield advance
