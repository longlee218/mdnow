"""Full-site crawl: discover URLs → fetch/extract each → write tree.

Discovery prefers sitemap.xml (cheap), falls back to a focused BFS crawl.
JS-rendered SPA sites (no server-side nav/content) defeat static discovery and
extraction alike, so both stages auto-escalate to the render tier: discovery
renders the start page to harvest nav links, and the per-page loop re-fetches
thin/empty pages through the renderer (mirrors single-page `runner._acquire`).
Per-page fetches are isolated: one bad page never aborts the run.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlsplit

from trafilatura.sitemaps import sitemap_search
from trafilatura.spider import focused_crawler

from . import artifacts, outline
from .extractor import extract, is_html
from .fetcher import Fetcher
from .guards import RateLimiter, RobotsChecker
from .linkrewrite import rewrite_links
from .runner import THIN_WORDS  # DRY: single source of the thin-content threshold
from .urls import build_path_map, canonical, same_host
from .writer import write

CRAWL_DELAY = 0.5  # polite minimal delay; full rate-limit = Phase 4
_BIG = 100_000     # effective "no cap" for --all

# href harvesting for render-aware discovery
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']')
_ASSET_RE = re.compile(r"\.(png|jpe?g|gif|svg|ico|webp|css|js|json|xml|pdf|zip|woff2?)$", re.I)


@dataclass
class Page:
    canon: str
    source_url: str
    body: str
    title: str | None
    published: str | None


def _render_discover(start_url: str, host: str, renderer: Fetcher) -> list[str]:
    """Render the start page and harvest same-host page links from the DOM.

    SPA nav links don't exist in static HTML — rendering exposes them. Returns
    [] if the renderer is unavailable (camoufox missing surfaces as RuntimeError
    on fetch), letting the caller keep whatever static discovery found.
    """
    try:
        r = renderer.fetch(start_url)
    except RuntimeError:
        return []
    html = r.content.decode("utf-8", "ignore")
    out: list[str] = []
    for href in _HREF_RE.findall(html):
        absu = urljoin(r.url, href.split("#")[0])  # resolve relative + drop fragment
        if not absu.startswith(("http://", "https://")):
            continue
        if same_host(absu, host) and not _ASSET_RE.search(urlsplit(absu).path):
            out.append(absu)
    return out


def discover_urls(
    start_url: str,
    max_pages: int,
    crawl_all: bool,
    *,
    render: bool = False,
    renderer: Fetcher | None = None,
) -> list[str]:
    host = urlsplit(start_url).netloc.lower()
    found = [u for u in (sitemap_search(start_url) or []) if same_host(u, host)]
    if found:
        # sitemap branch: enforce robots.txt ourselves (focused_crawler doesn't run)
        robots = RobotsChecker(start_url)
        found = [u for u in found if robots.allowed(u)]
    else:
        cap = _BIG if crawl_all else max_pages
        _, known = focused_crawler(start_url, max_seen_urls=cap, max_known_urls=cap)
        found = [u for u in known if same_host(u, host)]

    # SPA fallback: static discovery came up empty (≤1 URL = just the start page),
    # or --render forces it → render the start page to harvest nav links.
    if renderer is not None and (render or len(found) <= 1):
        found = found + _render_discover(start_url, host, renderer)

    # deterministic order across runs (BFS set iteration is otherwise random)
    found = sorted(found, key=canonical)

    # start URL first (explicitly requested → not robots-filtered), then dedup
    seen: set[str] = set()
    ordered: list[str] = []
    for u in [start_url, *found]:
        c = canonical(u)
        if c not in seen:
            seen.add(c)
            ordered.append(u)
    return ordered if crawl_all else ordered[:max_pages]


def _fetch_one(fetcher: Fetcher, url: str) -> Page:
    """Fetch + extract one URL into a Page. Raises RuntimeError/ValueError."""
    r = fetcher.fetch(url)
    if not is_html(r.content_type):
        raise ValueError(f"non-HTML content ({r.content_type})")
    e = extract(r.content, url=r.url)
    return Page(canonical(r.url), r.url, e.markdown, e.title, e.published_date)


def crawl_site(
    start_url: str,
    out: Path,
    max_pages: int,
    crawl_all: bool,
    fetcher: Fetcher,
    echo: Callable[[str], None],
    *,
    render: bool = False,
    renderer: Fetcher | None = None,
) -> tuple[int, int]:
    urls = discover_urls(start_url, max_pages, crawl_all, render=render, renderer=renderer)
    echo(f"Discovered {len(urls)} page(s). Fetching...")

    # escalate thin/empty pages to the renderer, unless the primary already renders
    can_escalate = renderer is not None and renderer is not fetcher

    limiter = RateLimiter(CRAWL_DELAY)
    pages: dict[str, Page] = {}
    failures: list[tuple[str, str]] = []
    escalated = 0
    render_dead = False  # set once if camoufox is unavailable → stop retrying
    for u in urls:
        limiter.wait()
        try:
            page = _fetch_one(fetcher, u)
            thin = len(page.body.split()) < THIN_WORDS
        except (RuntimeError, ValueError) as exc:
            page, thin, reason = None, True, str(exc)

        if thin and can_escalate and not render_dead:
            try:
                page = _fetch_one(renderer, u)  # browser launches lazily here
                escalated += 1
            except RuntimeError as exc:
                if "not installed" in str(exc).lower():
                    render_dead = True
                    echo("  note: install mdnow[render] to auto-recover JS-heavy pages")
            except ValueError:
                pass  # rendered but still no content → genuine empty page

        if page is None:
            failures.append((u, reason))
            continue
        pages.setdefault(page.canon, page)

    if escalated:
        echo(f"  rendered {escalated} page(s) that static fetch could not extract")

    page_list = list(pages.values())
    url_map = build_path_map([p.canon for p in page_list])
    today = date.today().isoformat()
    rendered: list[dict] = []  # final (link-rewritten) bodies — feeds the artifacts
    for p in page_list:
        rel = url_map[p.canon]
        body = rewrite_links(p.body, p.source_url, rel, url_map)
        write(out / rel, p.source_url, p.title, p.published, today, body)
        rendered.append({"title": p.title, "source_url": p.source_url, "local_path": rel, "body": body})

    host = urlsplit(start_url).netloc.lower()
    start_canon = canonical(start_url)
    # start page may redirect (/, locale, trailing slash) → fall back to first crawled page
    start_body = next((r["body"] for r in rendered if canonical(r["source_url"]) == start_canon),
                      rendered[0]["body"] if rendered else "")
    site_summary = outline.summary_of(start_body) or f"Documentation crawled from {host}"

    (out / "llms.txt").write_text(artifacts.build_llms_txt(host, site_summary, rendered), encoding="utf-8")
    (out / "llms-full.txt").write_text(artifacts.build_llms_full(host, site_summary, rendered), encoding="utf-8")
    (out / "manifest.json").write_text(artifacts.build_manifest(host, start_url, rendered), encoding="utf-8")

    for u, err in failures:
        echo(f"  skipped {u}: {err}")
    return len(page_list), len(failures)
