# Plan: Fix `--crawl` on JS-rendered SPA sites (render-aware discovery + fetch escalation)

**Status:** pending
**Created:** 2026-06-30
**Trigger bug:** `mdnow https://docs.nestjs.com --crawl --max-pages 100 -o out/` → every page `skipped: No main content extracted`. Single-page mode works.

## Root cause (debugged, confirmed)

docs.nestjs.com is an **Angular SPA with no server-side rendering**. Static HTML at every path is the same 15,607-byte app shell. This breaks crawl in two independent places:

1. **Discovery** (`discover_urls`): `sitemap_search` → 0 (the "sitemap.xml" is the SPA catch-all serving `index.html`, not XML). `focused_crawler` → 1 URL (static shell has **0 doc-nav links** — all rendered client-side; the only internal hrefs are favicons/manifest). Crawl enumerates just the start URL.
2. **Extraction** (`crawl_site` loop): that 1 URL → 15KB shell → trafilatura `No main content extracted`. Crawl has **no escalation** to the render tier (single-page `_acquire` has it — that's why single-page works).

**Proof rendering fixes both:** rendered homepage = 167KB, exposes **139 doc-route links**, extracts to 465 words.

## Design decisions (confirmed with user)

- **Discovery trigger:** auto-fallback — static discovery first; if it yields ≤1 URL (or `--render` set), render the start page and harvest DOM links. No new flag.
- **Fetch escalation:** reuse single-page logic — escalate a page to the renderer on `extract()` failure OR `word_count < THIN_WORDS` (import `THIN_WORDS` from `runner`, DRY).
- **Renderer lifecycle:** `CamoufoxFetcher()` construction is free (browser launches lazily on first `fetch()`); `close()` is a no-op if never launched. So cli always passes a renderer when not `--render`; it costs nothing unless actually used.
- **Camoufox-missing:** escalation/fallback `fetch()` raises `RuntimeError` → catch, log one-time hint (`install mdnow[render]`), disable further render attempts, fall back to today's skip behavior.

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Render-aware discovery (Part B) | pending | [phase-01](phase-01-render-aware-discovery.md) |
| 2 | Fetch-loop escalation (Part A) | pending | [phase-02](phase-02-fetch-loop-escalation.md) |
| 3 | Tests + README/CLAUDE sync | pending | [phase-03](phase-03-tests-and-readme-sync.md) |

## Key files

- `mdnow/crawler.py` — `discover_urls` (Part B), `crawl_site` loop (Part A)
- `mdnow/cli.py` — wire `renderer` + `render` flag into `crawl_site`
- `mdnow/runner.py` — source of `THIN_WORDS` (import, don't redefine)
- `tests/test_crawler.py` — new cases for fallback discovery + escalation

## Out of scope (verified OK)

- `llms.txt` discovery seam already correctly rejected the nestjs SPA shell (else the user would not have reached the crawler). No change to `llmstxt.py`.
- No new CLI flag. No subcommands. Modules stay <200 lines.

## Success criteria

- `mdnow https://docs.nestjs.com --crawl --max-pages 100 -o out/` writes ~100 pages, 0 `No main content` skips, with no `--render` flag.
- Existing crawl tests pass unchanged in spirit; new tests are network-free (fake renderer injected).
- README reflects the new auto-escalation crawl behavior.
