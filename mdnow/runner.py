"""CLI action helpers — fetch/extract/convert and write outcomes.

Kept separate from cli.py so the orchestration module stays under 200 lines.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import typer

from . import convert, outline, quality, ui
from .extractor import Extracted, extract, is_html
from .fetcher import CamoufoxFetcher, FetchResult, StaticFetcher
from .slugs import file_slug, slug
from .writer import write

THIN_WORDS = quality.THIN_WORDS  # re-export; heuristics live in quality.py


def _render(url: str, headers: dict | None = None, cookies: list[dict] | None = None) -> tuple[FetchResult, Extracted]:
    """Fetch via Camoufox and extract. Caller owns error handling."""
    fetcher = CamoufoxFetcher(headers=headers, cookies=cookies)
    try:
        result = fetcher.fetch(url)
        return result, extract(result.content, url=result.url)
    finally:
        fetcher.close()


def _acquire(
    url: str,
    render: bool,
    allow_remote: bool,
    headers: dict | None = None,
    cookies: list[dict] | None = None,
) -> tuple[FetchResult, Extracted]:
    """Get (result, extracted), escalating to the render tier when needed.

    --render forces Camoufox. Otherwise: static first; a non-HTML response goes
    to markitdown (PDF/Office/…), then a one-shot render retry if the page is
    empty or yields suspiciously thin content. headers/cookies carry auth
    material for private sites (both tiers).
    """
    if render:
        return _render(url, headers, cookies)

    try:
        result = StaticFetcher(headers=headers, cookies=cookies).fetch(url)
    except RuntimeError:
        return _render(url, headers, cookies)  # blocked (e.g. 403) → let the stealth browser try
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
            return _render(url, headers, cookies)
    try:
        extracted = extract(result.content, url=result.url)
    except ValueError:
        return _render(url, headers, cookies)  # nothing extracted → JS-only page, escalate

    if quality.is_thin(extracted.markdown):
        try:
            # thin or link-farm boilerplate → likely JS-blocked; one-shot escalate
            return _render(url, headers, cookies)
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
    ui.success(
        outcome.status, str(outcome.path),
        f"v{outcome.version}, {extracted.word_count} words, "
        f"~{outline.token_estimate(extracted.markdown)} tokens",
    )
    if outcome.status != "unchanged":
        ui.hint(f"Read it: {outcome.path}")


def _convert_single(
    url: str,
    out: Path,
    render: bool,
    allow_remote: bool,
    headers: dict | None = None,
    cookies: list[dict] | None = None,
) -> None:
    action = "Rendering" if render else "Fetching"
    ui.step(action, url)
    try:
        with ui.status(f"{action} {url}"):
            result, extracted = _acquire(url, render, allow_remote, headers=headers, cookies=cookies)
    except (RuntimeError, ValueError) as exc:
        ui.error(str(exc))
        raise typer.Exit(1)
    _write_extracted(out, slug(extracted.title, result.url), result.url, extracted)


def _convert_file_to_extracted(path: Path, allow_remote: bool) -> Extracted:
    """Convert a local file to markdown without writing to disk."""
    return convert.from_path(path, allow_remote=allow_remote)


def _convert_file(path: Path, out: Path, allow_remote: bool) -> None:
    """Convert a local file to markdown via markitdown, then write it."""
    ui.step("Converting", str(path))
    try:
        extracted = _convert_file_to_extracted(path, allow_remote)
    except (RuntimeError, ValueError) as exc:
        ui.error(str(exc))
        raise typer.Exit(1)
    _write_extracted(out, file_slug(path), str(path), extracted)


def _convert_youtube(url: str, out: Path, allow_remote: bool) -> None:
    """Convert a YouTube URL (transcript) via markitdown, then write it."""
    ui.step("Converting (YouTube)", url)
    try:
        with ui.status(f"Transcribing {url}"):
            extracted = convert.from_url(url, allow_remote=allow_remote)
    except (RuntimeError, ValueError) as exc:
        ui.error(str(exc))
        raise typer.Exit(1)
    _write_extracted(out, slug(extracted.title, url), url, extracted)
