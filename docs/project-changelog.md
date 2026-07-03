# Project Changelog

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
