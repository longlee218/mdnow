# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`mdnow` — a personal, fully-local Python CLI that converts a website URL or local/remote file to clean, AI-friendly markdown. Single page, multi-page crawl, or any-file conversion (PDF, Office, images, audio, YouTube). No API keys, no data egress by default. Built for one user, low volume (so: no queues, no anti-abuse, no distributed concerns — keep it that way).

## Source of truth (MANDATORY)

`README.md` (English) is the canonical source of truth for behavior, flags, install, and usage. After **any** change to CLI flags, features, dependencies, install steps, or module structure, re-sync both `README.md` **and** `README.vi.md` in the same change — a stale README is a bug. `README.vi.md` is a full Vietnamese mirror kept in sync with the English canonical; treat drifting translations as documentation debt.

Prefer the `docs` skill / `docs-manager` agent to do the sync. Keep this file in sync when architecture or commands change.

## Skill sync (MANDATORY)

The bundled skill at `mdnow/skill/` teaches *other AIs* how to drive the CLI — it is a public surface, not internal notes. Two rules:

1. **Any change to a feature, CLI flag, flag list, input type, or output schema MUST be synced into `mdnow/skill/` in the same change set** — alongside the README sync above. A skill that lists stale flags or a stale frontmatter/manifest schema misleads the agent using it; treat skill drift as a bug, exactly like README drift.
2. **When writing/editing the skill, always follow skill best practices** — invoke the `skill-creator` skill for its guidance and validate with `.venv/bin/python .claude/skills/skill-creator/scripts/quick_validate.py mdnow/skill`. Keep `SKILL.md` and each reference **< 150 lines**, use imperative instructions, avoid duplication between SKILL.md and references, and preserve the `## Scope` and `## Security` blocks (they carry the benchmark's security score).
   - **The `description` is the single most important field — it is the auto-activation trigger other AIs match against, so optimize it to get mdnow *chosen*, not for brevity.** Write it third-person ("Use this skill whenever…"), pack it with concrete *when-to-use* signals (single page, whole-site crawl, private/internal site behind auth, document/audio/YouTube conversion) and the input keywords an agent would phrase the request with. Hard limit is 1024 chars (skill-creator's "< 200" is a benchmark-conciseness heuristic, not a cap — prefer a strong, detailed trigger). No angle brackets (`<`/`>`) — the validator rejects them.

## Commands

```bash
# Dev install (editable, into a local venv; include [docs] for file conversion)
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,docs]"

# Run from the venv (auto-detects input type: URL, local file, local folder, or YouTube)
.venv/bin/mdnow <url|file|folder> [-o out/] [--crawl] [--render] [--no-llms] [--allow-remote] [--max-pages N] [--all]

# Private/internal sites: inject auth into both fetch tiers
.venv/bin/mdnow <url> -H "Authorization: Bearer $TOKEN" --cookie-file cookies.txt

# Utility flags
.venv/bin/mdnow --doctor                              # report installed/missing extras
.venv/bin/mdnow --fetch-browser                       # download Camoufox browser (one-time)
.venv/bin/mdnow --install-skill                       # install skill to ~/.claude/skills/mdnow
.venv/bin/mdnow --install-skill --skill-dir <path>    # install to custom location
.venv/bin/mdnow --install-skill --force               # overwrite existing skill
.venv/bin/mdnow --update                              # upgrade mdnow to the latest git version

# Tests (139 tests, ~88% coverage)
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pytest tests/test_linkrewrite.py -q          # one file
.venv/bin/python -m pytest tests/test_cli.py::test_slug_fallbacks   # one test
.venv/bin/python -m pytest tests/ --cov=mdnow --cov-report=term-missing

# Compile-check (fast syntax gate)
.venv/bin/python -m compileall -q mdnow

# Global install via uv from GitHub (recommended; distributed via git, NOT PyPI)
uv tool install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"

# Global install via pipx (Python-only)
pipx install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"

# One-liner install (macOS / Linux)
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --all

# One-liner install (Windows)
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 | iex
```

Notes: `.venv` is allowlisted in `.claude/.ckignore` so the interpreter is callable. Tests are network-free (httpx is monkeypatched, `CamoufoxFetcher` is not unit-tested — it needs a real browser and is integration-tested live).

## Architecture — the big picture

**Input-type fork at CLI entry.** `cli.main` branches first:
- **`--update`** → `commands.self_update()` (detects installed extras, runs `uv tool install --force` from git, or prints a manual-install hint if uv is missing).
- **Local folder** → `folder.convert_folder()` (recursively batch-converts files, mirrors `crawler.py` two-pass pattern: convert-all with per-file isolation → map paths → write + emit artifacts).
- **Local file** → `convert.from_path()` (markitdown), skipping the entire URL funnel.
- **YouTube URL** → `convert.from_url()` (markitdown transcript, requires `--allow-remote`).
- **Other URL** → cheapest-path-first website funnel (below).

**Cheapest-path-first funnel** for web URLs. Each tier runs only if the prior didn't yield clean markdown:

1. **Discovery** (`discovery.py` → `llmstxt.py`): probe `/llms.txt`, `/llms-full.txt` (+ variants, + `<url>.md` twin). If a site already publishes clean markdown, return it and **skip everything else**.
2. **Static** (`fetcher.StaticFetcher` + `extractor.py`): `httpx` fetch → `trafilatura` → markdown. The fast default. **Content-type fork:** non-HTML → `convert.from_bytes()` (markitdown), with render as fallback if markitdown fails or isn't installed.
3. **Render** (`fetcher.CamoufoxFetcher`): stealth headless Firefox for JS-heavy / anti-bot pages. Opt-in via `--render`, or **auto-escalated** when static returns blocked/empty/thin content — in single-page (`runner._acquire`) **and** crawl (`crawler.crawl_site`) mode. `fetch()` uses `wait_until="domcontentloaded"` then a best-effort `networkidle` wait (SPAs render after DOM load; `wait_until="load"` triggers a driver crash). Before launch it calls `playwright_patch.ensure_driver_patched()` to self-heal a Playwright Firefox bug that crashes the whole Node driver on SPA `pageError`s with no `location` — idempotent, best-effort, re-applied after any playwright reinstall.

**The one abstraction that matters: `Fetcher` (Protocol in `fetcher.py`).** `StaticFetcher` and `CamoufoxFetcher` both implement `fetch(url) -> FetchResult`. Everything downstream (extractor, crawler) is fetcher-agnostic — that's why swapping in render is a one-line change. Don't leak fetch details past this seam.

**Auth for private sites is constructor state on the fetchers, not a pipeline concern.** `auth.py` parses `--header "Name: Value"` strings and cookie files (Netscape cookies.txt incl. `#HttpOnly_` lines, or a JSON list) into plain dicts; `StaticFetcher(headers=, cookies=)` builds a domain/path-scoped `httpx.Cookies` jar, `CamoufoxFetcher` applies the same material via `set_extra_http_headers` + context cookies. Values are secrets: never echo, log, or write them to any output (error messages name the header, never its value). llms.txt discovery and static crawl discovery (sitemap/BFS) remain unauthenticated — per-page fetches and render discovery carry the auth.

**Escalation quality gate lives in `quality.py`** (single source, re-exported as `runner.THIN_WORDS` for compat): `is_thin()` = under 50 words **or** link-density > 0.7 while under 200 words (nav/footer link-farm extracted instead of the article). Both single-page (`runner._acquire`) and crawl (`crawler.crawl_site`) escalate on it. Word counts strip link URLs first.

**Section-level retrieval metadata:** `outline.sections()` chunks markdown at headings (code-fence-aware via length-preserving masking so offsets index the original text; preamble → slug `_intro`) with per-section `word_count`/`token_estimate`; slugs are shared with `outline.headings()`. Per-page frontmatter carries `outline:` (list of `"## Heading"` strings); `manifest.json` pages carry `sections`. An agent picks a section by slug/size before reading any body.

**CLI orchestration vs. action helpers.** `cli.py` is the thin typer entry point; it delegates actual fetch/extract/convert/write work to `runner.py`. Input-type detection lives in `inputs.py` and filename slug helpers in `slugs.py` — this keeps `cli.py` under the 200-line ceiling. Utility commands (`--doctor`, `--fetch-browser`, `--install-skill`, `--update`) are handled in `commands.py` and `doctor.py`.

**All console output goes through `ui.py` (the single presentation seam).** It wraps one Rich `Console` (+ a stderr console for errors) with markup-safe helpers — `step`/`success`/`error`/`hint`/`note`, a `status()` spinner for single fetches, a `progress_bar()` context (yields `advance(done, total, label)`) for crawl, and `doctor_report()` (colored table). No module calls `typer.echo`/`secho` directly. **Dynamic content is rendered via `rich.text.Text` (never markup parsing)** so a title/path/name containing `[...]` can't vanish or inject styles. Rich auto-degrades on a non-tty / `NO_COLOR` (plain text, no ANSI), so scripts and tests keep the informational substrings (`created`, `discovery`, `Done`, `Error:`). `crawl_site` takes an optional `progress=` callback so the bar advances per page without leaking UI into the crawler.

**File conversion layer** (`convert.py`): lazy markitdown import (mirrors `CamoufoxFetcher` for optional dependencies). Raises `RemoteBlocked` if audio/video/YouTube and `--allow-remote` is off. Returns `Extracted` (reuses existing writer/frontmatter path). No LLM/Azure plugins.

**`discover()` is a runtime gate, not an afterthought.** `cli.main` calls `discover()` *before* any crawl/fetch; the crawler is only reached on a `None` return. New input strategies plug in here.

**Crawl is a two-pass over the whole page set** (`crawler.crawl_site`): fetch+extract every page first (with per-page error isolation — one bad page never aborts the run), *then* build the URL→local-path map, *then* rewrite links and write. The two passes are required because link rewriting needs the complete set of crawled URLs before it can know which links resolve locally.

**Crawl handles JS-rendered SPA sites via the render tier at two seams.** (1) *Discovery* (`crawler.discover_urls`): when static discovery (sitemap → focused_crawler) yields ≤1 URL — or `--render` is set — it renders the start page and harvests same-host `<a href>` links from the live DOM (`_render_discover`), which is the only way to enumerate an SPA whose nav is client-rendered. (2) *Per-page* (`crawler._fetch_one`): a page whose static extraction is empty or thin (`< THIN_WORDS`, imported from `runner`) is re-fetched through the renderer — same escalation as single-page. `cli` passes a lazily-constructed `CamoufoxFetcher()` as `renderer=`; it costs nothing until first use, and escalation is guarded off when the primary already renders (`renderer is not fetcher`).

**Provenance: `token_estimate` and `summary` are derived once at the frontmatter choke point** (`frontmatter.build`), not threaded through callers. `outline.py` provides pure helpers: `slugify_heading`, `headings` (code-fence-aware), `summary_of` (extractive, first paragraph), `token_estimate` (chars/4).

**Crawl artifacts** (`artifacts.py` in crawl mode only): emits `llms.txt` (llmstxt.org-shaped index), `llms-full.txt` (full concatenated markdown), and `manifest.json` (machine-readable metadata). These replace the old `tree.py` index-building role — keep artifact emission alongside per-page writes.

**Folder batch conversion** (`folder.py`, mirrors `crawler.py`): two-pass over a local directory tree — convert-all files with per-file error isolation (one failure never aborts), *then* build the path map, *then* write + emit artifacts. Reuses `artifacts.py` (`build_llms_txt`/`build_llms_full`/`build_manifest`) unchanged. Path mapping uses `slugs.file_slug` (extension-stripped, same as single-file mode) plus sha1[:6] for leaf-name collisions — does NOT use `urls.build_path_map` (URL-only, would keep extension as slug suffix). UI routes through the seam like crawl (`folder_summary` in `ui.py`, progress bar with verb="converting").

**`canonical()` (`urls.py`) is the single source of URL identity** — used by both dedup and the path map, so a URL always resolves identically everywhere. If you touch URL normalization, change it only here.

**Link rewriting contract** (`linkrewrite.py`): internal+crawled → relative local `.md`; internal-but-not-crawled → left absolute (never emit broken local links); external → untouched.

**Versioning** (`writer.py` + `frontmatter.py`): every page is written with a content-hash. Re-running only bumps `version` when the body actually changed (unchanged → skipped). This makes re-crawls idempotent.

**robots.txt single source of truth** (`guards.py`): the BFS branch uses `trafilatura.focused_crawler` which enforces robots itself; `RobotsChecker` is applied **only** to the sitemap branch. Don't double-check.

## Conventions specific to this repo

- Every module stays **< 200 lines**, one responsibility. Many small files > few large ones.
- New CLI capabilities are **flags on the single command** (`cli.main`), not subcommands — the command is `mdnow <url|file|folder> [flags]`.
- `camoufox` and `markitdown` are **optional** dependencies (`[render]` and `[docs]` extras), imported lazily so base-install users never need them.
- Founding constraint: **fully local, no API keys, no data egress by default.** Audio/video transcription and YouTube egress are opt-in via `--allow-remote`. Never use LLM/Azure client keys.

## Distribution & public surfaces

**Git-based distribution (NOT PyPI):** the package is installed straight from the GitHub repo — there is no PyPI release and no publish workflow. Install spec is the PEP 508 direct reference `mdnow[extras] @ git+https://github.com/longlee218/mdnow`. Public users install via:
1. **Shell one-liner** (macOS/Linux): `curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh [--render] [--docs] [--all] [--skill]`
   - `install.sh` ensures `uv` is installed, then `uv tool install "mdnow[extras] @ git+<repo>"`, downloads browser if `--render`, installs skill if `--skill`.
   - Raw-URL branch is `main`.
2. **PowerShell one-liner** (Windows): `irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 | iex`, or save the script and run `.\install.ps1 [-Render] [-Docs] [-All] [-Skill]`.
   - `install.ps1` ensures `uv` is installed, then `uv tool install --force "mdnow[extras] @ git+<repo>"`, downloads browser if `-Render`, installs skill if `-Skill`.
3. **uv** (recommended, cross-platform): `uv tool install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"`
4. **pipx**: `pipx install "git+https://github.com/longlee218/mdnow"`

`pyproject.toml` still carries valid package metadata (name, classifiers, `[project.urls]`) so the git install builds cleanly, but there is no CI/publish workflow and PyPI is intentionally not used.

**Skill bundling:** `mdnow/skill/` directory contains the Claude Code skill. `mdnow --install-skill` (via `commands.py:install_skill`) copies it to `~/.claude/skills/mdnow/` (or `--skill-dir` if provided). Bundled in `pyproject.toml` as `mdnow = ["skill/**/*"]` package data.

**Documentation mirrors:** README.md is English canonical; README.vi.md is a synced Vietnamese mirror — update both in the same change.

## Project workflow

Plans live in `plans/`, docs in `docs/`. The completed build plan is `plans/260621-0714-website-to-markdown-cli/` (per-phase docs explain each module's intent and the decisions behind it — read these before reworking a subsystem). Do not create markdown outside `plans/` or `docs/` except `README.md` / `CLAUDE.md`.
