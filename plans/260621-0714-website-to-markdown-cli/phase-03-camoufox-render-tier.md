# Phase 3 — Camoufox Render Tier + Auto-Detect

**Priority:** Medium · **Status:** pending · **Effort:** ~1 day · **Depends:** Phase 0, Phase 1

## Overview
Add `--render` tier for JS-heavy / Cloudflare / bot-detected sites, using the Camoufox backend chosen in Phase 0. Auto-detect thin static extraction and suggest/trigger render.

## Requirements
- `CamoufoxFetcher` implementing the `Fetcher` interface → returns rendered HTML.
- `--render` flag forces render tier; otherwise static.
- Auto-detect: if static extraction is empty/thin (below word-count threshold), warn and auto-trigger render ONCE (one-shot retry, never a loop).
- Works in both single and crawl modes. Crawl+render = **sequential** (KISS, fine at personal scale; no async concurrency).
- Explicit page-load timeout + single retry (Camoufox loads can hang).

## Architecture
```
fetcher.py → add CamoufoxFetcher (backend from Phase 0 decision)
cli.py     → --render flag; auto-detect fallback logic
```
No new orchestration — just a swapped Fetcher (proves the interface from Phase 1).

## Key Detail
Render returns raw HTML (`page.content()` for Python lib, or outerHTML endpoint for camofox-browser) → fed into the SAME extractor. DRY.

## Files to Modify
- `mdnow/fetcher.py` (add CamoufoxFetcher)
- `mdnow/cli.py` (flag + auto-detect)

## Implementation Steps
1. Implement CamoufoxFetcher per Phase 0 backend.
2. Add `--render`: select CamoufoxFetcher.
3. Auto-detect: run static; if thin, retry with render (or prompt).
4. Test on JS SPA + a Cloudflare-protected page.

## Todo
- [ ] CamoufoxFetcher
- [ ] --render flag
- [ ] thin-extraction auto-detect
- [ ] JS + Cloudflare test

## Success Criteria
- JS-rendered page yields full content with `--render`; static-only would be empty.
- Auto-detect catches a thin static result and recovers via render.
- Cloudflare/anti-bot bypass = **best-effort**, NOT a pass/fail gate (it's an arms race).

## Risks
- Camoufox slower/heavier → render is opt-in, never default.
- Crawl + render = slow at scale → cap concurrency; acceptable for personal use.
