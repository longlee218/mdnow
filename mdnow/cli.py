"""mdnow CLI — convert a website URL to clean, AI-friendly markdown.

Phase 1: single-page static conversion. Later phases add flags
(--crawl, --render, --no-llms) to this same command.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse

import typer

from .crawler import crawl_site
from .discovery import discover
from .extractor import Extracted, extract, is_html
from .fetcher import CamoufoxFetcher, FetchResult, StaticFetcher
from .writer import write

THIN_WORDS = 50  # below this, static extraction is likely JS-blocked → try render


def _slugify(text: str) -> str:
    """ASCII slug: transliterate accents, drop other non-ascii. May return ''."""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", norm.lower()).strip("-")


def _slug(title: str | None, url: str) -> str:
    """Stable filename slug. Tries title, then URL path, then host."""
    parsed = urlparse(url)
    for candidate in (title or "", parsed.path, parsed.netloc):
        slug = _slugify(candidate)
        if slug:
            return slug[:80]
    return "page"


def main(
    url: str = typer.Argument(..., help="Website URL to convert"),
    out: Path = typer.Option(Path("."), "--out", "-o", help="Output directory"),
    crawl: bool = typer.Option(False, "--crawl", help="Crawl the whole site into a tree"),
    max_pages: int = typer.Option(100, "--max-pages", help="Max pages to crawl"),
    crawl_all: bool = typer.Option(False, "--all", help="Crawl all pages (ignore --max-pages)"),
    no_llms: bool = typer.Option(False, "--no-llms", help="Skip llms.txt discovery; force fetch/crawl"),
    render: bool = typer.Option(False, "--render", help="Use the Camoufox stealth browser (JS/anti-bot sites)"),
) -> None:
    """Fetch URL → clean markdown. Single page, or --crawl for a whole-site tree."""
    # Discovery seam: a site may already publish ready-made markdown (llms.txt).
    if not no_llms:
        found = discover(url, crawl=crawl)
        if found is not None:
            out.mkdir(parents=True, exist_ok=True)
            if crawl:
                # name after the source file (llms-full.txt → llms-full.md)
                stem = urlparse(found.source_url).path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                name = f"{stem or 'llms'}.md"
            else:
                name = f"{_slug(found.title, found.source_url)}.md"
            outcome = write(
                path=out / name,
                source_url=found.source_url,
                title=found.title,
                published_date=None,
                fetched_date=date.today().isoformat(),
                body=found.content,
            )
            typer.echo(
                f"discovery: {outcome.status} {outcome.path} "
                f"(v{outcome.version}, from {found.source_url})"
            )
            return

    if crawl:
        out.mkdir(parents=True, exist_ok=True)
        fetcher = CamoufoxFetcher() if render else StaticFetcher()
        try:
            typer.echo(f"Crawling {url} ...")
            ok, failed = crawl_site(url, out, max_pages, crawl_all, fetcher, typer.echo)
        finally:
            getattr(fetcher, "close", lambda: None)()
        typer.echo(f"Done: {ok} page(s) written, {failed} failed → {out}")
        return

    _convert_single(url, out, render)


def _render(url: str) -> tuple[FetchResult, Extracted]:
    """Fetch via Camoufox and extract. Caller owns error handling."""
    fetcher = CamoufoxFetcher()
    try:
        result = fetcher.fetch(url)
        return result, extract(result.content, url=result.url)
    finally:
        fetcher.close()


def _acquire(url: str, render: bool) -> tuple[FetchResult, Extracted]:
    """Get (result, extracted), escalating to the render tier when needed.

    --render forces Camoufox. Otherwise: static first, then a one-shot render
    retry if the page is non-HTML, empty, or yields suspiciously thin content.
    """
    if render:
        return _render(url)

    try:
        result = StaticFetcher().fetch(url)
    except RuntimeError:
        return _render(url)  # blocked (e.g. 403) → let the stealth browser try
    if not is_html(result.content_type):
        return _render(url)  # binary/SPA → let the browser try
    try:
        extracted = extract(result.content, url=result.url)
    except ValueError:
        return _render(url)  # nothing extracted → JS-only page, escalate

    if extracted.word_count < THIN_WORDS:
        try:
            return _render(url)  # thin → likely JS-blocked; one-shot escalate
        except (RuntimeError, ValueError):
            pass  # render unavailable / failed / empty → keep the thin static result
    return result, extracted


def _convert_single(url: str, out: Path, render: bool) -> None:
    typer.echo(f"{'Rendering' if render else 'Fetching'} {url} ...")
    try:
        result, extracted = _acquire(url, render)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{_slug(extracted.title, result.url)}.md"

    outcome = write(
        path=path,
        source_url=result.url,
        title=extracted.title,
        published_date=extracted.published_date,
        fetched_date=date.today().isoformat(),
        body=extracted.markdown,
    )
    typer.echo(
        f"{outcome.status}: {outcome.path} "
        f"(v{outcome.version}, {extracted.word_count} words)"
    )


def run() -> None:
    typer.run(main)


if __name__ == "__main__":
    run()
