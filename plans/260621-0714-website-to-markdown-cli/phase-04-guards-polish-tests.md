# Phase 4 — Guards, Polish, Tests

**Priority:** Medium · **Status:** pending · **Effort:** ~1 day · **Depends:** Phase 2, Phase 3

## Overview
Harden the crawler, polish UX, add tests. Make it safe to point at any site.

## Requirements
Crawl guards:
- `--max-pages` (default 100) + `--all` (finalized in Phase 2 — verify enforced on both discovery branches)
- same-domain only
- URL dedup via `canonical()` (defined Phase 2 — finalize edge cases)
- **robots.txt — single source of truth:** focused_crawler already respects robots on the BFS path. Only add `urllib.robotparser` for the sitemap branch + llms.txt probes (paths focused_crawler doesn't cover). Do NOT double-implement on the BFS path.
- polite rate-limit (extend Phase 2's single delay into a shared limiter)
- **output overwrite policy:** overwrite existing files with a warning (versioning in writer already guards unchanged content).

Polish:
- Progress output (page count, current URL)
- Clear errors (network, 404, blocked) — never silent
- `--quiet` / sensible logging

## Architecture
```
guards.py  → robots.txt check, rate limiter, domain filter, caps
(extend crawler.py to consume guards)
tests/     → unit + a couple integration tests
```

## Files to Create / Modify
- `mdnow/guards.py`
- modify `mdnow/crawler.py`, `mdnow/cli.py`
- `tests/test_extractor.py`, `tests/test_linkrewrite.py`, `tests/test_crawler.py`, `tests/test_guards.py`

## Implementation Steps
1. robots.txt parser + check (urllib.robotparser).
2. Rate limiter (min delay) + domain filter + caps wired into crawler.
3. Progress + error handling polish.
4. Tests: extractor (html fixture → md), link rewriting, URL→path mapping, guards (robots/caps), crawler BFS limits. Aim ≥80% on core logic.

## Todo
- [ ] robots.txt respect
- [ ] rate limit + caps + domain filter
- [ ] progress + error UX
- [ ] unit tests (extractor, linkrewrite, guards)
- [ ] integration test (small crawl)
- [ ] README usage + examples

## Success Criteria
- Crawl respects robots/caps/rate-limit, can't run away or leave domain.
- Tests pass, ≥80% coverage on core logic.
- Clear errors and progress; README documents both modes + `--render`.

## Deferred from Phase 2 review (address here)
- **focused_crawler determinism + timeout:** BFS discovers a non-deterministic page subset across runs (set iteration); add stable sort/seed + a discovery timeout/cap so a huge site can't stall before any write.
- **`--all` memory:** crawl holds all page bodies in RAM (needed for 2-pass link rewrite). Fine at personal scale; note the ceiling, consider streaming only if it ever matters.
- **canonical() default ports:** `:80`/`:443` not stripped → `http://h:80/` dedups as distinct from `http://h/`. Cheap one-line strip if desired.

## Risks
- Over-engineering guards → keep minimal, personal-scale (no distributed concerns). YAGNI.
