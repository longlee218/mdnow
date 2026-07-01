"""CLI action helpers — fetch/extract/convert and write outcomes.

Kept separate from cli.py so the orchestration module stays under 200 lines.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import typer

from . import convert
from .extractor import Extracted, extract, is_html
from .fetcher import CamoufoxFetcher, FetchResult, StaticFetcher
from .slugs import file_slug, slug
from .writer import write

THIN_WORDS = 50  # below this, static extraction is likely JS-blocked → try render


def _render(url: str) -> tuple[FetchResult, Extracted]:
    """Fetch via Camoufox and extract. Caller owns error handling."""
    fetcher = CamoufoxFetcher()
    try:
        result = fetcher.fetch(url)
        return result, extract(result.content, url=result.url)
    finally:
        fetcher.close()


def _acquire(url: str, render: bool, allow_remote: bool) -> tuple[FetchResult, Extracted]:
    """Get (result, extracted), escalating to the render tier when needed.

    --render forces Camoufox. Otherwise: static first; a non-HTML response goes
    to markitdown (PDF/Office/…), then a one-shot render retry if the page is
    empty or yields suspiciously thin content.
    """
    if render:
        return _render(url)

    try:
        result = StaticFetcher().fetch(url)
    except RuntimeError:
        return _render(url)  # blocked (e.g. 403) → let the stealth browser try
    if not is_html(result.content_type):
        # Non-HTML (PDF/Office/…) → convert the bytes with markitdown. If it's
        # not installed, fall back to render (preserves prior behavior); an
        # egress refusal (RemoteBlocked) surfaces to the user instead.
        try:
            return result, convert.from_bytes(
                result.content, result.url, result.content_type, allow_remote=allow_remote
            )
        except convert.RemoteBlocked:
            raise
        except RuntimeError:
            return _render(url)
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


def _write_extracted(out: Path, page_slug: str, source_url: str, extracted: Extracted) -> None:
    """Write an Extracted to out/<slug>.md with versioned frontmatter."""
    out.mkdir(parents=True, exist_ok=True)
    outcome = write(
        path=out / f"{page_slug}.md",
        source_url=source_url,
        title=extracted.title,
        published_date=extracted.published_date,
        fetched_date=date.today().isoformat(),
        body=extracted.markdown,
    )
    typer.echo(
        f"{outcome.status}: {outcome.path} "
        f"(v{outcome.version}, {extracted.word_count} words)"
    )


def _convert_single(url: str, out: Path, render: bool, allow_remote: bool) -> None:
    typer.echo(f"{'Rendering' if render else 'Fetching'} {url} ...")
    try:
        result, extracted = _acquire(url, render, allow_remote)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    _write_extracted(out, slug(extracted.title, result.url), result.url, extracted)


def _convert_file_to_extracted(path: Path, allow_remote: bool) -> Extracted:
    """Convert a local file to markdown without writing to disk."""
    return convert.from_path(path, allow_remote=allow_remote)


def _convert_file(path: Path, out: Path, allow_remote: bool) -> None:
    """Convert a local file to markdown via markitdown, then write it."""
    typer.echo(f"Converting {path} ...")
    try:
        extracted = _convert_file_to_extracted(path, allow_remote)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    _write_extracted(out, file_slug(path), str(path), extracted)


def _convert_youtube(url: str, out: Path, allow_remote: bool) -> None:
    """Convert a YouTube URL (transcript) via markitdown, then write it."""
    typer.echo(f"Converting (YouTube) {url} ...")
    try:
        extracted = convert.from_url(url, allow_remote=allow_remote)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    _write_extracted(out, slug(extracted.title, url), url, extracted)
