# Phase 5 — llms.txt Discovery Short-Circuit

**Priority:** High (big DRY/speed win) · **Status:** pending · **Depends:** Phase 1, Phase 2 (fills the `discover()` seam)
**Build order:** implement RIGHT AFTER Phase 2's seam exists (overall order 0→1→5→2→3→4).

## Overview
Many dev/docs sites publish AI-ready markdown. When present, **use it and skip crawl/extract** — the site already did our job. Implements the `discover()` seam stubbed in Phase 2.

## Key Insight
- `/llms-full.txt` = full docs concatenated → IS our crawl output.
- `/llms.txt` = curated markdown index w/ reference links → IS our context tree.
- Bonus: many pages serve `<url>.md` (Mintlify) or honor `Accept: text/markdown` → skip HTML extract in single mode.

## Probe set (priority tiers; probe lower tiers ONLY after higher miss; validate each)
1. **Standard (llmstxt.org):** `/llms-full.txt`, `/llms.txt`
2. **Markdown-ext variants:** `/llms-full.md`, `/llms.md`
3. **Singular variants:** `/llm.txt`, `/llm.md`
4. **Well-known (emerging):** `/.well-known/llms.txt`
- Excluded: `/ai.txt` (AI-access policy file, not content).

## Mode-dependent priority
- **Single mode:** try `<url>.md` then `Accept: text/markdown` on the URL FIRST. (Do NOT grab whole-site llms-full.txt for one page.)
- **Crawl mode:** prefer `llms-full.txt` (whole site) → else `llms.txt` (index tree) → else fall through to Phase 2 crawl.

## False-positive validator (mandatory — SPA catch-all returns 200 HTML)
Accept a probe only if: status 200 AND content-type textual AND body does NOT start with `<!doctype`/`<html` AND body contains markdown markers (`# ` or `](`). Else treat as miss.

## Requirements
- `discover(url, mode)` → returns markdown content + source label, or `None`.
- `llms-full.txt` found (crawl) → save directly; optionally split by top-level `#`/`##` into per-page files (reuse writer + versioning).
- `llms.txt` found (crawl) → use as `index.md` tree; optionally fetch each linked page (links may be HTML → reuse extractor, don't assume `.md`).
- On by default; `--no-llms` forces manual pipeline.
- Clear log line: which path/source was used.

## Architecture
```
llmstxt.py → probe tiers, validate, parse index links, <url>.md / Accept handling
(cli.py: discover() seam calls this; falls through to crawl/extract on None)
```
Reuse fetcher.py + writer.py + extractor.py. No new fetch backend.

## Files to Create / Modify
- `mdnow/llmstxt.py`
- modify `mdnow/cli.py` (implement the `discover()` seam, `--no-llms` flag)

## Implementation Steps
1. Tiered probe + validator; first valid hit wins.
2. Single mode: `<url>.md` → `Accept: text/markdown` → None.
3. Crawl mode: llms-full.txt (save/split) → llms.txt (tree + optional link fetch) → None.
4. `--no-llms` bypass; clean fall-through to crawl on None.
5. Test: Mintlify site (has both), non-llms site (clean fallback), `<url>.md` case, fake-200 SPA (validator rejects).

## Todo
- [ ] llmstxt.py tiered probe + validator
- [ ] single-mode `<url>.md` + Accept header
- [ ] crawl: llms-full.txt save/split (versioned)
- [ ] crawl: llms.txt → index.md tree (+ optional link fetch via extractor)
- [ ] --no-llms flag + clean fallback + log line

## Success Criteria
- Mintlify/docs site with llms.txt → near-instant clean output, no crawl.
- Non-llms site → silent fallback, no behavior change.
- Fake-200 SPA page → validator rejects, falls through.

## v1 scope decisions (Phase 5 review)
- **Verbatim dump, no split/link-fetch (intentional YAGNI cut):** discovered `llms-full.txt`/`llms.txt` is saved as-is (one file, via `write()` + versioning). An `llms.txt` index already IS the curated context-tree-with-links the user wanted. Splitting `llms-full.txt` by headings + fetching `llms.txt` link targets is a **deferred enhancement**, not v1.
- **Output filename mirrors source** (`llms-full.txt`→`llms-full.md`, `llms.txt`→`llms.md`).
- **PROBE_TIMEOUT = 4s** (worst-case ~28s on a tarpit host across all tiers).
- **Deferred to Phase 4:** content-size cap on discovered files (`Content-Length`/stream guard) — currently reads full body into memory (fine at personal scale; 727KB observed).

## Note from Phase 2 review
- The `discover()` seam is wired in cli.py; currently a non-None result is written via raw `write_text` (no frontmatter/versioning). In Phase 5 decide whether discovered markdown should also flow through `write()` (frontmatter + content-hash versioning) for consistency with crawled pages. Recommended: yes for single-file results.

## Risks
- False positives → validator above.
- llms.txt link targets may be HTML → reuse extractor; don't assume `.md`.
- Keep optional/minimal; don't complicate core pipeline (YAGNI).
