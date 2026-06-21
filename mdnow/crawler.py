"""Full-site crawl: discover URLs → fetch/extract each → write tree.

Discovery prefers sitemap.xml (cheap), falls back to a focused BFS crawl.
Per-page fetches are isolated: one bad page never aborts the run.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

from trafilatura.sitemaps import sitemap_search
from trafilatura.spider import focused_crawler

from .extractor import extract, is_html
from .fetcher import Fetcher
from .guards import RateLimiter, RobotsChecker
from .linkrewrite import rewrite_links
from .tree import build_index
from .urls import build_path_map, canonical, same_host
from .writer import write

CRAWL_DELAY = 0.5  # polite minimal delay; full rate-limit = Phase 4
_BIG = 100_000     # effective "no cap" for --all


@dataclass
class Page:
    canon: str
    source_url: str
    body: str
    title: str | None
    published: str | None


def discover_urls(start_url: str, max_pages: int, crawl_all: bool) -> list[str]:
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


def crawl_site(
    start_url: str,
    out: Path,
    max_pages: int,
    crawl_all: bool,
    fetcher: Fetcher,
    echo: Callable[[str], None],
) -> tuple[int, int]:
    urls = discover_urls(start_url, max_pages, crawl_all)
    echo(f"Discovered {len(urls)} page(s). Fetching...")

    limiter = RateLimiter(CRAWL_DELAY)
    pages: dict[str, Page] = {}
    failures: list[tuple[str, str]] = []
    for u in urls:
        limiter.wait()
        try:
            r = fetcher.fetch(u)
            if not is_html(r.content_type):
                failures.append((u, f"non-HTML content ({r.content_type})"))
                continue
            e = extract(r.content, url=r.url)
            c = canonical(r.url)
            pages.setdefault(c, Page(c, r.url, e.markdown, e.title, e.published_date))
        except (RuntimeError, ValueError) as exc:
            failures.append((u, str(exc)))

    page_list = list(pages.values())
    url_map = build_path_map([p.canon for p in page_list])
    today = date.today().isoformat()
    for p in page_list:
        body = rewrite_links(p.body, p.source_url, url_map[p.canon], url_map)
        write(out / url_map[p.canon], p.source_url, p.title, p.published, today, body)

    host = urlsplit(start_url).netloc.lower()
    (out / "index.md").write_text(build_index(host, page_list, url_map), encoding="utf-8")

    for u, err in failures:
        echo(f"  skipped {u}: {err}")
    return len(page_list), len(failures)
