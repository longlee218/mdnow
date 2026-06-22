"""mdnow CLI — convert a website URL or a file to clean, AI-friendly markdown.

Auto-routes by input type: a local file or a non-HTML/YouTube URL goes to
markitdown (convert.py); a normal web page goes through the fetch/extract
funnel. Flags (--crawl, --render, --no-llms, --allow-remote) tune the run.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse

import typer

from . import convert
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


def _file_slug(path: Path) -> str:
    """Filename slug for a local file — its stem, slugified."""
    return _slugify(path.stem)[:80] or "file"


def _is_local_file(arg: str) -> bool:
    """True if arg is a path to an existing local file (not an http(s) URL)."""
    try:
        scheme = urlparse(arg).scheme
    except ValueError:
        return False  # malformed input → let the URL branch report it cleanly
    return scheme not in ("http", "https") and Path(arg).is_file()


_YT_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def _is_youtube(arg: str) -> bool:
    """True if arg is a YouTube URL (handled by markitdown's transcript converter)."""
    try:
        return urlparse(arg).netloc.lower() in _YT_HOSTS
    except ValueError:
        return False


def main(
    url: str = typer.Argument(..., help="Website URL to convert"),
    out: Path = typer.Option(Path("."), "--out", "-o", help="Output directory"),
    crawl: bool = typer.Option(False, "--crawl", help="Crawl the whole site into a tree"),
    max_pages: int = typer.Option(100, "--max-pages", help="Max pages to crawl"),
    crawl_all: bool = typer.Option(False, "--all", help="Crawl all pages (ignore --max-pages)"),
    no_llms: bool = typer.Option(False, "--no-llms", help="Skip llms.txt discovery; force fetch/crawl"),
    render: bool = typer.Option(False, "--render", help="Use the Camoufox stealth browser (JS/anti-bot sites)"),
    allow_remote: bool = typer.Option(
        False, "--allow-remote",
        help="Allow converters that egress to cloud APIs (audio/video transcription, YouTube)",
    ),
) -> None:
    """Fetch URL → clean markdown. Single page, or --crawl for a whole-site tree."""
    # Input-type fork: a local file path is converted directly (markitdown),
    # skipping the whole URL funnel (discovery/fetch/crawl don't apply to files).
    if _is_local_file(url):
        if crawl:
            typer.secho(
                "Error: --crawl is not valid for a local file (single file only).",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(1)
        _convert_file(Path(url), out, allow_remote)
        return

    # YouTube URLs go to markitdown's transcript converter (network egress).
    if _is_youtube(url):
        _convert_youtube(url, out, allow_remote)
        return

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

    _convert_single(url, out, render, allow_remote)


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


def _write_extracted(out: Path, slug: str, source_url: str, extracted: Extracted) -> None:
    """Write an Extracted to out/<slug>.md with versioned frontmatter."""
    out.mkdir(parents=True, exist_ok=True)
    outcome = write(
        path=out / f"{slug}.md",
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
    _write_extracted(out, _slug(extracted.title, result.url), result.url, extracted)


def _convert_file(path: Path, out: Path, allow_remote: bool) -> None:
    """Convert a local file to markdown via markitdown, then write it."""
    typer.echo(f"Converting {path} ...")
    try:
        extracted = convert.from_path(path, allow_remote=allow_remote)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    _write_extracted(out, _file_slug(path), str(path), extracted)


def _convert_youtube(url: str, out: Path, allow_remote: bool) -> None:
    """Convert a YouTube URL (transcript) via markitdown, then write it."""
    typer.echo(f"Converting (YouTube) {url} ...")
    try:
        extracted = convert.from_url(url, allow_remote=allow_remote)
    except (RuntimeError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    _write_extracted(out, _slug(extracted.title, url), url, extracted)


def run() -> None:
    typer.run(main)


if __name__ == "__main__":
    run()
