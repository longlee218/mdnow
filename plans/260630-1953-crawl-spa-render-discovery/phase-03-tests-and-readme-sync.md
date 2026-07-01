# Phase 03 — Tests + README/CLAUDE sync

**Priority:** MEDIUM (gate before done)
**Status:** pending
**Files:** `tests/test_crawler.py`, `README.md`, `CLAUDE.md`

## Tests (network-free — inject fake fetchers, as existing tests do)

Existing pattern: `_FakeFetcher` returns `FetchResult`; `discover_urls` is monkeypatched. Reuse it.

### New / updated cases

1. **`test_discover_urls_renders_when_static_empty`**
   - Fake renderer returns HTML with many same-host `<a href>` doc links + asset links.
   - Monkeypatch `sitemap_search` → `[]`, `focused_crawler` → `([], {start})`.
   - Assert `discover_urls(start, 100, False, renderer=fake)` returns the doc routes, drops asset links, includes start URL first.

2. **`test_discover_urls_static_skips_render`**
   - `focused_crawler` returns >1 URL → renderer's `fetch` must **not** be called (spy: raise if called).

3. **`test_crawl_escalates_thin_page_to_renderer`**
   - Primary fetcher returns a thin shell (< THIN_WORDS) → `extract` raises / thin.
   - Renderer returns full content. Assert page written, `ok == 1`, `failed == 0`.
   - Use real `crawl_site` with `renderer=` injected (don't monkeypatch the loop).

4. **`test_crawl_no_renderer_skips_as_before`**
   - `renderer=None`, primary returns shell → `failed == 1` (regression guard for today's behavior).

5. **`test_crawl_render_flag_no_double_fetch`**
   - primary is renderer (same instance) → escalation guard off; fetch called once per URL (counter).

6. **Update existing two tests** — `crawl_site(...)` calls gain no required args (new params are keyword-only with defaults), so existing calls still pass. Verify they do; if signature forces it, add `renderer=None`.

### Coverage

- Run `.venv/bin/python -m pytest tests/test_crawler.py -q` then full suite.
- Keep ≥ 80% (repo currently ~87%). New branches: render-fallback, escalation, render_dead, asset filter.

## README sync (MANDATORY — source of truth)

Update `README.md` where it describes `--crawl` and `--render`:

- Crawl now **auto-escalates** to the stealth browser per-page (like single-page mode) when static extraction is empty/thin — no `--render` needed for JS-heavy docs.
- Discovery now **auto-renders** the start page to harvest nav links when static discovery finds ≤1 URL (SPA sites like Angular/React docs).
- `--render` still forces the browser for the whole crawl (discovery + every page).
- Note the dependency: auto-escalation needs the `[render]` extra + `python -m camoufox fetch`; without it, crawl logs a one-time hint and falls back to skipping un-extractable pages.

Prefer the `docs` skill / `docs-manager` agent for the sync.

## CLAUDE.md sync

Update the architecture notes:
- "Render tier auto-escalated when static returns blocked/empty/thin" → add: **applies to crawl too**, and **discovery** renders the start page to seed link enumeration on SPA sites.

## Todo

- [ ] Add 5 new test cases + verify 2 existing pass
- [ ] Full suite green, coverage ≥ 80%
- [ ] README `--crawl`/`--render` sections updated
- [ ] CLAUDE.md architecture note updated

## Success criteria

- All tests pass network-free.
- Manual smoke (optional, needs browser): `mdnow https://docs.nestjs.com --crawl --max-pages 20 -o /tmp/nest` writes ~20 pages, 0 `No main content` skips.
- README + CLAUDE.md reflect new behavior (no drift).
