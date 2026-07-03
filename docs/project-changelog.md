# Project Changelog

## [2026-07-03] — Folder batch conversion

**New features:**
- **Local folder input** — `mdnow ./docs -o out/` now recursively converts every file under a local directory to markdown, preserving subfolder structure (e.g. `guide/setup.pdf` → `out/guide/setup.md`). Dotfiles/dotdirs (`.git`, `.venv`, `.DS_Store`) are skipped. Per-file failure isolation: one unconvertible file is reported as skipped and never aborts the run. Emits crawl-style AI artifacts: `llms.txt`, `llms-full.txt`, `manifest.json` (with per-file sections/outline/token_estimate metadata). `--crawl` on a folder is rejected (folder mode always builds the index, so the flag is redundant). Fetch-tier flags (`--render`, `-H`, `--cookie-file`, `--no-llms`) are silently ignored for folder input (same as single-file). UI uses Rich progress bar and "Converting" step label, same as crawl.

**Architecture:**
- New `mdnow/folder.py` mirrors `crawler.py` (two-pass: convert-all with per-file isolation → map paths → write + emit artifacts). Reuses `artifacts.py` unchanged. Path mapping uses `slugs.file_slug` (extension-stripped) + sha1[:6] suffix for collisions, NOT `urls.build_path_map` (URL-only).
- `ui.py` gained `folder_summary` and `progress_bar(verb=…)` parameter; folder mode routes all output through the ui seam.

**Tests:** 141 tests passing.

---

## [2026-07-03] — CLI UI enhancement

**Changed:**
- **Rich-powered CLI output** — All console output now flows through a new `mdnow/ui.py` seam built on [Rich](https://github.com/Textualize/rich) (added as a base dependency). Single-page fetch/convert shows a spinner; `--crawl` shows a live progress bar; `--doctor` renders a colored status table; success lines gain token estimates; errors and actionable next-step hints (e.g. "Read it: …", "Start with manifest.json") are color-coded. Output auto-degrades to plain text on a non-tty / `NO_COLOR`, so scripts and pipes are unaffected. No CLI flags or behavior changed — presentation only.

**Tests:** 141 tests passing.

---

## [2026-07-03] — AI output & private-site features

**New features:**
- **Private/internal site authentication** — New flags `--header/-H` (repeatable) and `--cookie-file` to add HTTP headers and session cookies (Netscape .txt or JSON format). Applies to both static (httpx) and render (Camoufox) tiers. Secrets never logged/echoed. Requires `chmod 600` on cookie files and env var injection for tokens.
- **Section-level output for AI agents** — Per-page frontmatter now includes `outline` (list of heading strings). Crawl mode `manifest.json` pages now include `sections` map with `{slug, heading, level, word_count, token_estimate}` for each section, enabling agents to pick sections by size/slug before reading.
- **Smarter thin-content detection** — Pages with >50 words but >70% inside links (nav/footer boilerplate, <200 total words) now auto-escalate to render tier, same as thin pages. Genuine large link indexes (>200 words) are kept as-is.

**Tests:** 139 tests passing, ~88% coverage.

---

## Versioning notes

mdnow uses **content-hash versioning**: re-running increments `version` only when body content changes, making crawls idempotent.

Distributed via git + `uv tool install`, not PyPI.
