---
status: completed
created: 2026-06-21
slug: website-to-markdown-cli
---

# MDNow — Website→Markdown CLI

Personal local CLI: convert any URL → clean, AI-friendly markdown. Strip ads/nav/footer/images (keep alt-text). Two modes: single page + full-site crawl with context tree. Python. Fully local, no API keys.

Source brainstorm: `plans/reports/brainstorm-260621-0714-website-to-markdown-cli.md`

## Locked Stack

- **Python** CLI (`typer`)
- **trafilatura** — extraction + markdown + sitemap + spider crawl
- **httpx** — static fetch (default fast path)
- **Camoufox** — stealth render/anti-bot tier (replaces Firecrawl)
- **Fetcher** swappable interface (StaticFetcher ↔ CamoufoxFetcher)

## Phases

| # | Phase | Status | Depends |
|---|-------|--------|---------|
| 0 | [Camoufox HTML spike](phase-00-camoufox-html-spike.md) | done | — |
| 1 | [Static single-page MVP](phase-01-static-single-page-mvp.md) | done | — |
| 2 | [Full-site crawl + tree](phase-02-full-site-crawl-tree.md) | done | 1 |
| 3 | [Camoufox render tier](phase-03-camoufox-render-tier.md) | done | 0,1 |
| 4 | [Guards, polish, tests](phase-04-guards-polish-tests.md) | done | 2,3 |
| 5 | [llms.txt discovery short-circuit](phase-05-llms-txt-discovery.md) | done | 1, 2 (seam) |

**ALL PHASES COMPLETE.** 44 tests pass, 84% coverage. `mdnow <url>` (single), `--crawl` (site tree), `--render` (Camoufox stealth), llms.txt short-circuit, content-hash versioning. Fully local, no API keys.

**Build order: 0 → 1 → 5 → 2 → 3 → 4.** Phase 2 stubs a `discover()` dispatch seam; Phase 5 fills it (llms.txt must gate the crawler architecturally, not be retrofitted). Phase 0 (spike) is independent — can run anytime before Phase 3. Phase 1 delivers usable value alone.

## Key Decisions

- **Images:** extract `include_images=True` then regex `![alt](src)`→`alt` (keep alt-text, drop image). Not native in trafilatura.
- **Encoding:** feed bytes (`resp.content`) to trafilatura, not text.
- **Frontmatter + versioning:** `source_url, title, published_date, fetched_date, version, content_hash, word_count`. Re-crawl: hash changed → bump version + update fetched_date; unchanged → skip rewrite. YAML-safe dumper.
- **Crawl limit:** `--max-pages` default 100 + `--all` to uncap. No `--depth` (lib is count-based). Cap applies to sitemap AND BFS branches.
- **Canonical URL (shared dedup+path-map):** lowercase host, strip `#fragment` + `?query`, collapse trailing slash, resolve relative→absolute.
- **Links:** internal-crawled → relative local; internal-not-crawled → leave absolute; external → untouched.
- **Auto-detect** thin static extraction → one-shot render retry. Crawl+render sequential.
- **robots.txt single source:** focused_crawler covers BFS; add robotparser only for sitemap + llms probes.
- **llms.txt short-circuit** (Phase 5, gates crawler via `discover()` seam): tiered probes — standard `/llms-full.txt`,`/llms.txt` → variants `/llms-full.md`,`/llms.md`,`/llm.txt`,`/llm.md` → `/.well-known/llms.txt`; single mode prefers `<url>.md`/`Accept: text/markdown`. Validate real markdown (reject `<!doctype` 200s). On by default, `--no-llms` to disable.

## Success Criteria

- `mdnow <url>` → clean `.md` + versioned frontmatter; images→alt-text; re-run unchanged → version stays, no rewrite
- `mdnow <url> --crawl [--max-pages N|--all]` → per-page `.md` + `index.md` tree; internal-crawled links resolve locally, not-crawled/external stay absolute; no `<url>` vs `<url>/` dupes
- Site with llms.txt/variant → used directly, crawler skipped; non-llms site falls back cleanly
- JS site succeeds with `--render`; Cloudflare bypass = best-effort (not a gate)
- 100% local, no API keys, no data egress
- Files <200 lines; KISS/YAGNI/DRY
