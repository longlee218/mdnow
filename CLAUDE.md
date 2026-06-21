# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`mdnow` — a personal, fully-local Python CLI that converts a website URL to clean, AI-friendly markdown. Single page or full-site crawl. No API keys, no data egress. Built for one user, low volume (so: no queues, no anti-abuse, no distributed concerns — keep it that way).

## Source of truth (MANDATORY)

`README.md` is the source of truth for behavior, flags, install, and usage. After **any** change to CLI flags, features, dependencies, install steps, or module structure, re-sync `README.md` in the same change — a stale README is a bug. Prefer the `docs` skill / `docs-manager` agent to do the sync. Keep this file in sync when architecture or commands change.

## Commands

```bash
# Dev install (editable, into a local venv)
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# Run from the venv
.venv/bin/mdnow <url> [-o out/] [--crawl] [--render] [--no-llms] [--max-pages N] [--all]

# Tests (54 tests, ~86% coverage)
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pytest tests/test_linkrewrite.py -q          # one file
.venv/bin/python -m pytest tests/test_cli.py::test_slug_fallbacks   # one test
.venv/bin/python -m pytest tests/ --cov=mdnow --cov-report=term-missing

# Compile-check (fast syntax gate)
.venv/bin/python -m compileall -q mdnow

# Global install (pipx). MUST include the [render] extra or --render breaks.
pipx install "/abs/path/to/MDNow[render]" --force
$HOME/.local/pipx/venvs/mdnow/bin/python -m camoufox fetch   # one-time ~300MB browser
```

Notes: `.venv` is allowlisted in `.claude/.ckignore` so the interpreter is callable. Tests are network-free (httpx is monkeypatched, `CamoufoxFetcher` is not unit-tested — it needs a real browser and is integration-tested live).

## Architecture — the big picture

**Cheapest-path-first funnel.** A URL flows through tiers; each runs only if the prior didn't already yield clean markdown. This is the core design — preserve it.

1. **Discovery** (`discovery.py` → `llmstxt.py`): probe `/llms.txt`, `/llms-full.txt` (+ variants, + `<url>.md` twin). If a site already publishes clean markdown, return it and **skip everything else**.
2. **Static** (`fetcher.StaticFetcher` + `extractor.py`): `httpx` fetch → `trafilatura` → markdown. The fast default.
3. **Render** (`fetcher.CamoufoxFetcher`): stealth headless Firefox for JS-heavy / anti-bot pages. Opt-in via `--render`, or **auto-escalated** when static returns blocked/empty/thin content.

**The one abstraction that matters: `Fetcher` (Protocol in `fetcher.py`).** `StaticFetcher` and `CamoufoxFetcher` both implement `fetch(url) -> FetchResult`. Everything downstream (extractor, crawler) is fetcher-agnostic — that's why swapping in render is a one-line change. Don't leak fetch details past this seam.

**`discover()` is a runtime gate, not an afterthought.** `cli.main` calls `discover()` *before* any crawl/fetch; the crawler is only reached on a `None` return. New input strategies plug in here.

**Crawl is a two-pass over the whole page set** (`crawler.crawl_site`): fetch+extract every page first (with per-page error isolation — one bad page never aborts the run), *then* build the URL→local-path map, *then* rewrite links and write. The two passes are required because link rewriting needs the complete set of crawled URLs before it can know which links resolve locally.

**Provenance: `token_estimate` and `summary` are derived once at the frontmatter choke point** (`frontmatter.build`), not threaded through callers. `outline.py` provides pure helpers: `slugify_heading`, `headings` (code-fence-aware), `summary_of` (extractive, first paragraph), `token_estimate` (chars/4).

**Crawl artifacts** (`artifacts.py` in crawl mode only): emits `llms.txt` (llmstxt.org-shaped index), `llms-full.txt` (full concatenated markdown), and `manifest.json` (machine-readable metadata). These replace the old `tree.py` index-building role — keep artifact emission alongside per-page writes.

**`canonical()` (`urls.py`) is the single source of URL identity** — used by both dedup and the path map, so a URL always resolves identically everywhere. If you touch URL normalization, change it only here.

**Link rewriting contract** (`linkrewrite.py`): internal+crawled → relative local `.md`; internal-but-not-crawled → left absolute (never emit broken local links); external → untouched.

**Versioning** (`writer.py` + `frontmatter.py`): every page is written with a content-hash. Re-running only bumps `version` when the body actually changed (unchanged → skipped). This makes re-crawls idempotent.

**robots.txt single source of truth** (`guards.py`): the BFS branch uses `trafilatura.focused_crawler` which enforces robots itself; `RobotsChecker` is applied **only** to the sitemap branch. Don't double-check.

## Conventions specific to this repo

- Every module stays **< 200 lines**, one responsibility. Many small files > few large ones.
- New CLI capabilities are **flags on the single command** (`cli.main`), not subcommands — the command is `mdnow <url> [flags]`.
- `camoufox` is an **optional** dependency (`[render]` extra), imported lazily so static-only users never need it.
- Founding constraint: **fully local, no API keys.** Any feature needing an LLM/network service must be opt-in behind a flag, never the default.

## Project workflow

Plans live in `plans/`, docs in `docs/`. The completed build plan is `plans/260621-0714-website-to-markdown-cli/` (per-phase docs explain each module's intent and the decisions behind it — read these before reworking a subsystem). Do not create markdown outside `plans/` or `docs/` except `README.md` / `CLAUDE.md`.
