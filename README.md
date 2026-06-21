# mdnow

Convert any website URL to clean, AI-friendly markdown. Strips ads/nav/footer, keeps image alt-text, and builds a context tree when crawling. Fully local — no API keys, no data leaves your machine.

## How it works

A cheapest-path-first funnel — each tier only runs if the one above didn't already produce clean markdown:

1. **Discovery** — if the site publishes `/llms.txt`, `/llms-full.txt` (or variants, or a `<url>.md` twin), use it directly and skip everything else.
2. **Static fetch** — `httpx` + `trafilatura` extraction. Fast default.
3. **Render** — Camoufox stealth browser for JS-heavy / anti-bot sites (opt-in or auto-escalated).

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e .

# Only needed for the --render tier (downloads a Firefox build, ~300MB, one time):
.venv/bin/python -m camoufox fetch
```

## Usage

```bash
# Single page → one .md with frontmatter
mdnow https://example.com/article -o out/

# Whole site → folder of per-page .md + index.md context tree
mdnow https://example.com --crawl --max-pages 100 -o out/
mdnow https://example.com --crawl --all -o out/        # no page cap

# JS-heavy / anti-bot site → stealth render
mdnow https://example.com/spa --render -o out/

# Force the manual pipeline (skip llms.txt discovery)
mdnow https://example.com --crawl --no-llms -o out/
```

### Flags

| Flag | Meaning |
|------|---------|
| `-o, --out` | Output directory (default `.`) |
| `--crawl` | Crawl the whole site into a tree |
| `--max-pages N` | Max pages to crawl (default 100) |
| `--all` | Crawl all pages (ignore `--max-pages`) |
| `--render` | Use the Camoufox stealth browser |
| `--no-llms` | Skip llms.txt discovery; force fetch/crawl |

## Output

Each page is written with YAML frontmatter and content-hash **versioning** — re-running only bumps `version` when the content actually changed:

```yaml
---
source_url: https://example.com/article
title: Example Article
published_date: 2026-01-01
fetched_date: 2026-06-21
version: 1
content_hash: <sha256>
word_count: 1234
---
```

Crawl mode also writes `index.md` — a hierarchical context tree linking every page, with internal links rewritten to relative local paths (external/uncrawled links left absolute).

## Behavior notes

- **Images** are dropped but their alt-text is kept inline.
- **Crawl** discovers via `sitemap.xml` first, falls back to a same-domain BFS; respects `robots.txt`, rate-limits, and isolates per-page failures.
- **Cloudflare / anti-bot** bypass via `--render` is best-effort.

## Develop

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest          # 44 tests, ~84% coverage
```

## Architecture

Plan & phase docs: `plans/260621-0714-website-to-markdown-cli/`. Modules (each <200 lines): `cli`, `discovery`/`llmstxt`, `fetcher` (`StaticFetcher`/`CamoufoxFetcher` behind one `Fetcher` interface), `extractor`, `crawler`, `urls`, `linkrewrite`, `tree`, `guards`, `frontmatter`, `writer`.
