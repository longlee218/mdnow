# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`mdnow` — a personal, fully-local Python CLI that converts a website URL or local/remote file to clean, AI-friendly markdown. Single page, multi-page crawl, or any-file conversion (PDF, Office, images, audio, YouTube). No API keys, no data egress by default. Built for one user, low volume (so: no queues, no anti-abuse, no distributed concerns — keep it that way).

## Source of truth (MANDATORY)

`README.md` is the source of truth for behavior, flags, install, and usage. After **any** change to CLI flags, features, dependencies, install steps, or module structure, re-sync `README.md` in the same change — a stale README is a bug. Prefer the `docs` skill / `docs-manager` agent to do the sync. Keep this file in sync when architecture or commands change.

## Commands

```bash
# Dev install (editable, into a local venv; include [docs] to enable file conversion)
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,docs]"

# Run from the venv (auto-detects input type: URL, local file, or YouTube)
.venv/bin/mdnow <url|file> [-o out/] [--crawl] [--render] [--no-llms] [--allow-remote] [--max-pages N] [--all]

# Tests (72 tests, ~86% coverage)
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pytest tests/test_linkrewrite.py -q          # one file
.venv/bin/python -m pytest tests/test_cli.py::test_slug_fallbacks   # one test
.venv/bin/python -m pytest tests/ --cov=mdnow --cov-report=term-missing

# Compile-check (fast syntax gate)
.venv/bin/python -m compileall -q mdnow

# Global install (pipx). MUST include [render] and [docs] extras for full features.
pipx install "/abs/path/to/MDNow[render,docs]" --force
$HOME/.local/pipx/venvs/mdnow/bin/python -m camoufox fetch   # one-time ~300MB browser
```

Notes: `.venv` is allowlisted in `.claude/.ckignore` so the interpreter is callable. Tests are network-free (httpx is monkeypatched, `CamoufoxFetcher` is not unit-tested — it needs a real browser and is integration-tested live).

## Architecture — the big picture

**Input-type fork at CLI entry.** `cli.main` branches first:
- **Local file** → `convert.from_path()` (markitdown), skipping the entire URL funnel.
- **YouTube URL** → `convert.from_url()` (markitdown transcript, requires `--allow-remote`).
- **Other URL** → cheapest-path-first website funnel (below).

**Cheapest-path-first funnel** for web URLs. Each tier runs only if the prior didn't yield clean markdown:

1. **Discovery** (`discovery.py` → `llmstxt.py`): probe `/llms.txt`, `/llms-full.txt` (+ variants, + `<url>.md` twin). If a site already publishes clean markdown, return it and **skip everything else**.
2. **Static** (`fetcher.StaticFetcher` + `extractor.py`): `httpx` fetch → `trafilatura` → markdown. The fast default. **Content-type fork:** non-HTML → `convert.from_bytes()` (markitdown), with render as fallback if markitdown fails or isn't installed.
3. **Render** (`fetcher.CamoufoxFetcher`): stealth headless Firefox for JS-heavy / anti-bot pages. Opt-in via `--render`, or **auto-escalated** when static returns blocked/empty/thin content.

**The one abstraction that matters: `Fetcher` (Protocol in `fetcher.py`).** `StaticFetcher` and `CamoufoxFetcher` both implement `fetch(url) -> FetchResult`. Everything downstream (extractor, crawler) is fetcher-agnostic — that's why swapping in render is a one-line change. Don't leak fetch details past this seam.

**File conversion layer** (`convert.py`): lazy markitdown import (mirrors `CamoufoxFetcher` for optional dependencies). Raises `RemoteBlocked` if audio/video/YouTube and `--allow-remote` is off. Returns `Extracted` (reuses existing writer/frontmatter path). No LLM/Azure plugins.

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
- New CLI capabilities are **flags on the single command** (`cli.main`), not subcommands — the command is `mdnow <url|file> [flags]`.
- `camoufox` and `markitdown` are **optional** dependencies (`[render]` and `[docs]` extras), imported lazily so base-install users never need them.
- Founding constraint: **fully local, no API keys, no data egress by default.** Audio/video transcription and YouTube egress are opt-in via `--allow-remote`. Never use LLM/Azure client keys.

## Project workflow

Plans live in `plans/`, docs in `docs/`. The completed build plan is `plans/260621-0714-website-to-markdown-cli/` (per-phase docs explain each module's intent and the decisions behind it — read these before reworking a subsystem). Do not create markdown outside `plans/` or `docs/` except `README.md` / `CLAUDE.md`.
