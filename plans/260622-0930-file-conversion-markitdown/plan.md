---
status: completed
created: 2026-06-22
slug: file-conversion-markitdown
---

# MDNow — Any-File → Markdown via markitdown

Extend the completed MDNow CLI so `mdnow <anything>` converts **any file** (PDF, Office, EPub, images, CSV/JSON/XML, ZIP, audio, YouTube) to clean markdown — not just websites. Powered by Microsoft's open-source `markitdown`. Auto-routes by input type; reuses every existing seam; existing website behavior is unchanged. **Local by default, no API keys** — the only network-egress converters (audio, YouTube) are gated behind an opt-in `--allow-remote` flag.

Source: brainstorm 2026-06-22 (locked decisions below). Base build: `plans/260621-0714-website-to-markdown-cli/` + `plans/260621-1805-ai-doc-output-and-provenance/`.

## Locked Decisions

| # | Decision |
|---|---|
| D1 | Input accepts **both** local file paths and remote file URLs. |
| D2 | Coverage = `markitdown[all]` (full breadth). |
| D3 | **Auto-detect** input type — NO new selector flag. Local path → markitdown; URL → existing funnel, then content-type decides HTML(trafilatura) vs binary(markitdown). |
| D4 | Audio + YouTube converters egress to cloud APIs → gated behind `--allow-remote` (default **off**); refused with a clear message otherwise. LLM/Azure paths stay inert (no keys). |
| D5 | New `mdnow/convert.py` (<200 lines), lazy-imports markitdown — mirrors the `[render]`/camoufox optional-extra pattern. New `[docs]` extra in pyproject. |
| D6 | markitdown output maps onto the existing `Extracted` dataclass → reuse `write()`/frontmatter/outline unchanged. `published_date=None` for files. |
| D7 | `--crawl` + a file input → clear error. File conversion is single-input only. |
| D8 | `canonical()` (urls.py) stays URL-only — local files get a separate filename-slug helper. |
| D9 | ZIP/folder *batch* iteration: **deferred** (YAGNI). markitdown's single-ZIP converter still works (it inlines contents); we just don't add multi-file fan-out. |

## Phases

| # | Phase | Status | Depends |
|---|-------|--------|---------|
| 1 | [convert.py + local-file input fork + `[docs]` extra](phase-01-convert-module-and-local-input.md) | done | — |
| 2 | [Remote content-type fork + `--allow-remote` gate + YouTube branch](phase-02-remote-fork-and-network-gate.md) | done | 1 |
| 3 | [Tests + README/CLAUDE sync](phase-03-tests-and-docs-sync.md) | done | 1,2 |

**ALL PHASES COMPLETE.** 74 tests / 86% coverage. mdnow now converts local files (PDF, Office, EPub, images, CSV/JSON/XML, ZIP) + remote files + YouTube via markitdown. `--allow-remote` gates audio/video/YouTube egress; refused by default with clear message. README + CLAUDE.md synced. Deferred: extract cli.py (242 lines) under 200-line ceiling as standalone follow-up. Caught in review: markitdown transcribes .mp4/video streams too — audio guard widened to cover video formats.

Build order 1 → 2 → 3. Phase 1 delivers local files working end-to-end (the primary use case). Phase 2 adds remote files + the network gate. Phase 3 verifies and syncs the source-of-truth docs.

## Reuse (DRY — do NOT reinvent)

`Extracted` (extractor.py) — wrap markitdown's `(markdown, title)` into it; `is_html()` (extractor.py) — the content-type fork's discriminator; `write()` versioning + `frontmatter.build` + `outline` (token_estimate/summary) — unchanged; `_slug`/`_slugify` (cli.py) — extend for filename slugs; `FetchResult` bytes (fetcher.py) — feed markitdown's stream API.

## Success Criteria

- `mdnow ./report.pdf -o out/` writes `report.md` with full frontmatter (token_estimate, summary, content_hash); re-run is idempotent (version unchanged).
- `mdnow https://x.com/report.pdf -o out/` fetches and converts via markitdown (NOT trafilatura, NOT render).
- `mdnow ./song.mp3` and YouTube URLs are **refused** without `--allow-remote`, **converted** with it.
- `mdnow ./report.pdf --crawl` errors clearly.
- Existing website single/crawl/render behavior is byte-for-byte unchanged (regression tests pass).
- New logic ≥80% covered, network-free tests. README + CLAUDE.md synced.

## Constraints

Modules <200 lines; new capability is a flag on the single `mdnow` command (not a subcommand); local by default. markitdown lazy-imported so static-only users pay nothing. **A change isn't done until README.md reflects it** (Phase 3).
