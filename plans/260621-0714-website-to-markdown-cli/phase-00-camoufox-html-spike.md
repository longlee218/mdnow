# Phase 0 — Camoufox HTML Spike

**Priority:** High (de-risks Phase 3) · **Status:** pending · **Effort:** ~0.5 day

## Overview
Resolve how to get **raw rendered HTML** from Camoufox so trafilatura can extract markdown from JS/anti-bot sites. This is the only real unknown in the project.

## Key Insight
`jo-inc/camofox-browser` is a REST server (`npx @askjo/camofox-browser`, localhost:9377) that returns **accessibility snapshots, NOT raw HTML**. trafilatura needs rendered HTML (`document.documentElement.outerHTML`).

## Requirements
- Determine if camofox-browser can return full rendered HTML (e.g. an evaluate/JS endpoint).
- Fallback: **Camoufox Python lib** (`daijro/camoufox`, Playwright-compatible) → `page.content()` returns raw HTML directly, no separate server.
- Decide the render backend for Phase 3.

## Steps
1. Install + run camofox-browser; hit its endpoints; check for raw-HTML or JS-evaluate path returning `document.documentElement.outerHTML`.
2. Spike Camoufox Python lib: `pip install camoufox[geoip]`; launch headless; `page.goto(url)`; `html = page.content()`; feed to `trafilatura.extract`.
3. Compare: setup complexity, HTML fidelity, stealth (Cloudflare test), maintenance.
4. Pick backend; record decision in this file.

## Decision Criteria
Prefer Python lib if it returns clean HTML with no extra server process (simpler, KISS). Use camofox-browser only if its stealth materially beats the lib AND it exposes raw HTML.

## Success Criteria
- A working snippet: URL → rendered HTML → trafilatura markdown, on a JS-heavy test page.
- Backend choice documented with rationale.

## Risks
- camofox-browser may not expose raw HTML → fall back to Python lib (low risk, good fallback exists).
- Camoufox install (downloads Firefox build) may be heavy → document one-time setup.

## Output
Append "DECISION: <backend> because <reason>" to this file. Feeds Phase 3.

DECISION: **Camoufox Python library** (daijro/camoufox, `camoufox.sync_api`) — because `page.content()` returns full rendered HTML directly (verified: rendered en.wikipedia.org/wiki/Markdown, which 403'd the static httpx fetcher, → 209KB HTML → trafilatura extracted 2645 words, images stripped). No separate server process; one-time browser download (~298MB) via `python -m camoufox fetch`. The `jo-inc/camofox-browser` REST server was NOT chosen (returns a11y snapshots, not raw HTML — mismatch for trafilatura).
