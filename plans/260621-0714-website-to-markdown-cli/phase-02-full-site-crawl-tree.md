# Phase 2 — Full-Site Crawl + Context Tree

**Priority:** High · **Status:** pending · **Effort:** ~2 day · **Depends:** Phase 1

## Overview
`mdnow <url> --crawl [--max-pages N] [--all] [-o out/]` → discover URLs → extract each → folder of per-page `.md` + `index.md` context tree. Internal links rewritten to relative local paths.

## Requirements
- **Discovery dispatch seam (gates Phase 5):** cli orchestration calls `discover(url)` FIRST (stub returns `None` here; Phase 5 fills it). If it returns content → use directly, NO crawl. Else → crawl. This seam MUST exist now so Phase 5 doesn't force a cli rewrite.
- URL discovery: sitemap.xml first (`trafilatura.sitemaps.sitemap_search`), fallback BFS same-domain (`trafilatura.spider.focused_crawler`).
- **Limit:** `--max-pages` default 100; `--all` removes the cap. **Cap applies to BOTH branches** (sitemap can return thousands).
- No `--depth` (focused_crawler is count-based, not depth-based — avoid implying a feature the lib lacks).
- Per-page extraction + versioned write reuse Phase 1 (extractor, frontmatter, writer).
- `index.md` = hierarchy (by URL path) with relative links → context tree.
- Minimal politeness: single fixed inter-request delay here (full robots/rate-limit = Phase 4).

## Canonical-URL contract (shared, define ONCE — used by dedup AND path-map)
- lowercase host, strip `#fragment`, **strip `?query`** (decision E), collapse trailing slash, resolve relative→absolute against page base.
- One function `canonical(url) -> str` in `crawler.py`; everything uses it (DRY).

## Link-rewrite contract (Phase 2's hardest surface — specify fully)
- Resolve each `href` against page base URL → canonical.
- Internal (in crawled set) → relative local `.md` path.
- Internal but NOT crawled (over cap / excluded) → **leave absolute** (decision D) — never emit broken local links.
- External → untouched.
- Drop/keep `#fragment` on output links: keep fragment appended to rewritten path.

## Architecture
```
crawler.py    → canonical(), discover (sitemap+BFS), dedup, cap (max-pages/--all)
tree.py       → build hierarchy from canonical URLs, render index.md
linkrewrite.py→ map canonical URL → local relative path, rewrite md links
```
Reuse fetcher.py + extractor.py + frontmatter.py + writer.py from Phase 1.

## Files to Create / Modify
- `mdnow/crawler.py`, `mdnow/tree.py`, `mdnow/linkrewrite.py`
- Extend `mdnow/cli.py`: `--crawl`, `--max-pages`, `--all`, the `discover()` seam.

## Implementation Steps
1. Add `discover()` seam in cli (stub → None) before any crawl logic.
2. `canonical()` + URL→local-path map (deterministic, collision-safe via hash suffix).
3. Discovery: sitemap → list (apply cap); if empty, BFS via focused_crawler (apply cap).
4. Extract each page (reuse extractor); versioned write (reuse writer).
5. Rewrite internal links per contract; leave not-crawled/external absolute.
6. Generate `index.md` tree from canonical hierarchy.

## Todo
- [ ] discover() dispatch seam in cli
- [ ] canonical() + URL→local-path map
- [ ] discovery (sitemap + BFS) with cap on both branches
- [ ] per-page extract + versioned write
- [ ] link rewriting per contract
- [ ] index.md tree generation

## Success Criteria
- Small docs site → folder of `.md`, `index.md` lists hierarchy, internal links open local files, not-crawled/external links stay absolute, no dup pages (`<url>` == `<url>/`), cap respected (and `--all` ignores it).

## Risks
- URL→path collisions → canonical + hash suffix on collision.
- Sitemap missing → BFS fallback must work.
- focused_crawler does its own robots/dedup — don't double it; Phase 4 reconciles single source of truth.

## Carryover from Phase 1 review (address here)
- **Slug collisions / silent overwrite (HIGH for crawl):** Phase 1 slug is title→URL-path→host. For crawl, derive path from FULL URL path (not title) so many pages in one dir can't collide on `page.md`; hash-suffix on residual collision.
- **Per-page error isolation:** crawl must wrap each URL in try/except — one bad page (403/timeout/empty) must NOT abort the whole run. Collect failures, report at end.
- **Connection pooling:** reuse a single `httpx.Client` across the crawl (StaticFetcher currently opens a new connection per `httpx.get`). Add a pooled variant behind the same Fetcher interface.
