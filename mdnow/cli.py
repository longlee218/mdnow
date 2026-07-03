"""mdnow CLI — convert a website URL or a file to clean, AI-friendly markdown.

Auto-routes by input type: a local file or a non-HTML/YouTube URL goes to
markitdown (convert.py); a normal web page goes through the fetch/extract
funnel. Flags (--crawl, --render, --no-llms, --allow-remote) tune the run.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import subprocess
from urllib.parse import urlparse

import typer

from . import auth, commands, doctor, ui
from .crawler import crawl_site
from .discovery import discover
from .inputs import is_local_file, is_youtube
from .runner import _convert_file, _convert_single, _convert_youtube, _write_extracted
from .slugs import slug
from .writer import write


def main(
    url: str = typer.Argument("", help="Website URL or file to convert"),
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
    header: list[str] = typer.Option(
        None, "--header", "-H",
        help='Extra request header "Name: Value" for private sites (repeatable)',
    ),
    cookie_file: Path = typer.Option(
        None, "--cookie-file",
        help="Cookies for private sites: Netscape cookies.txt or JSON list",
    ),
    install_skill: bool = typer.Option(
        False, "--install-skill", help="Install the bundled Claude skill and exit"
    ),
    skill_dir: Path = typer.Option(
        None, "--skill-dir", help="Destination dir for --install-skill (default: ~/.claude/skills/mdnow)"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing --install-skill destination"),
    run_doctor: bool = typer.Option(False, "--doctor", help="Report installed/missing extras and exit"),
    fetch_browser: bool = typer.Option(
        False, "--fetch-browser", help="Download the Camoufox browser for --render and exit"
    ),
    update: bool = typer.Option(
        False, "--update", help="Upgrade mdnow to the latest version from git and exit"
    ),
) -> None:
    """Fetch URL → clean markdown. Single page, or --crawl for a whole-site tree."""
    if run_doctor:
        ui.doctor_report(doctor.run_checks())
        return

    if update:
        try:
            commands.self_update()
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            ui.error(str(exc))
            raise typer.Exit(1) from exc
        return

    if fetch_browser:
        try:
            commands.fetch_browser()
        except (RuntimeError, FileNotFoundError) as exc:
            ui.error(str(exc))
            raise typer.Exit(1) from exc
        ui.success("downloaded", "Camoufox browser", "ready for --render")
        return

    if install_skill:
        try:
            dest = commands.install_skill(skill_dir, force)
        except (FileNotFoundError, FileExistsError) as exc:
            ui.error(str(exc))
            raise typer.Exit(1) from exc
        ui.success("installed", f"skill to {dest}", "usable by Claude")
        return

    if not url:
        ui.error("URL or file path is required.")
        raise typer.Exit(1)

    # Auth material for private/internal sites. Parsed once; values are secrets
    # and must never be echoed or written to any output.
    try:
        headers = auth.parse_headers(header or [])
        cookies = auth.load_cookies(cookie_file) if cookie_file else None
    except (ValueError, OSError) as exc:
        ui.error(str(exc))
        raise typer.Exit(1) from exc

    # Input-type fork: a local file path is converted directly (markitdown),
    # skipping the whole URL funnel (discovery/fetch/crawl don't apply to files).
    if is_local_file(url):
        if crawl:
            ui.error("--crawl is not valid for a local file (single file only).")
            raise typer.Exit(1)
        _convert_file(Path(url), out, allow_remote)
        return

    # YouTube URLs go to markitdown's transcript converter (network egress).
    if is_youtube(url):
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
                name = f"{slug(found.title, found.source_url)}.md"
            outcome = write(
                path=out / name,
                source_url=found.source_url,
                title=found.title,
                published_date=None,
                fetched_date=date.today().isoformat(),
                body=found.content,
            )
            ui.success(
                f"discovery: {outcome.status}", str(outcome.path),
                f"v{outcome.version}, from {found.source_url}",
            )
            ui.hint(f"Read it: {outcome.path}")
            return

    if crawl:
        out.mkdir(parents=True, exist_ok=True)
        from .fetcher import CamoufoxFetcher, StaticFetcher
        # renderer is created unconditionally: CamoufoxFetcher() is free until its
        # first fetch (lazy browser launch), and crawl auto-escalates SPA pages to it.
        if render:
            primary = renderer = CamoufoxFetcher(headers=headers, cookies=cookies)
        else:
            primary = StaticFetcher(headers=headers, cookies=cookies)
            renderer = CamoufoxFetcher(headers=headers, cookies=cookies)
        try:
            ui.step("Crawling", url)
            with ui.progress_bar() as advance:
                ok, failed = crawl_site(
                    url, out, max_pages, crawl_all, primary, ui.note,
                    render=render, renderer=renderer, progress=advance,
                )
        finally:
            for f in {primary, renderer}:  # set() dedupes the --render case
                getattr(f, "close", lambda: None)()
        ui.crawl_summary(ok, failed, str(out))
        ui.hint(f"Start with {out / 'manifest.json'} (index), then open the pages you need")
        return

    _convert_single(url, out, render, allow_remote, headers=headers, cookies=cookies)


def run() -> None:
    typer.run(main)


if __name__ == "__main__":
    run()
