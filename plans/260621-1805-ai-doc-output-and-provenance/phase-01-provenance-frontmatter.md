# Phase 1 — Provenance Helpers + Frontmatter

**Priority:** High (foundation for Phase 2) · **Status:** pending · **Effort:** ~1 day

## Overview
Add `token_estimate` + extractive `summary` to every page's frontmatter (single + crawl), and create the slug + token + summary helpers Phase 2's manifest reuses. All extractive — no LLM.

> **IMPLEMENTED (divergence from original text below):** `summary`/`token_estimate` are derived from the body inside `frontmatter.build` — the single choke point all write paths funnel through. NOT threaded through `Extracted`/writer/cli/crawler. This is more DRY (one source of truth, zero signature changes). `outline.py` holds `slugify_heading`, `headings` (code-fence-aware), `summary_of`, `token_estimate`. Phase 3 README/CLAUDE sync should document THIS design, not threading.

## Requirements
- **token_estimate:** `ceil(len(text) / 4)` over the markdown body. Zero-dep.
- **summary:** first meaningful paragraph of the extracted markdown (skip headings, blockquotes, list markers, lines <40 chars), capped ~300 chars; prefer trafilatura metadata `description` if present.
- **heading slug helper:** GitHub-style — lowercase, strip non-alphanumerics→`-`, collapse repeats. Reused by Phase 2 (manifest outline). Add now, unit-test now.
- Both fields flow into frontmatter for single mode AND crawl mode (shared write path).
- Determinism: summary/token derived purely from body → re-crawl of unchanged content yields identical frontmatter → versioning still idempotent.

## Where it goes (check existing first — DRY)
- `extractor.py`: extend `Extracted` with `summary` (computed during/after extract). Add `summary_of(markdown, meta_description)` helper.
- `frontmatter.py`: add `token_estimate(body)` + include `token_estimate`, `summary` in `build()` dict.
- New tiny `slugify_heading(text)` — put in `urls.py`? No (that's URL slugs). Put a heading-slug + outline helper in a new `outline.py` (used by manifest in Phase 2) OR fold into extractor. Decide: `outline.py` (cohesive: heading parsing + slugs), <60 lines.
- `writer.py`/`cli.py`: pass summary through (writer already takes body; frontmatter.build gains fields — thread `summary` param).

## Frontmatter (new shape)
```
source_url, title, published_date, fetched_date, version,
content_hash, word_count, token_estimate, summary
```

## Implementation Steps
1. `outline.py`: `slugify_heading(text)`, `headings(markdown) -> list[{level,text,slug}]`.
2. `extractor.py`: compute `summary` (first meaningful para or meta description); add to `Extracted`.
3. `frontmatter.py`: `token_estimate(body)`; add `token_estimate` + `summary` to `build()`.
4. Thread `summary` through `writer.write()` + both cli paths (single `_convert_single`, crawl `crawl_site`).
5. Manual check: single + small crawl show new frontmatter; re-run unchanged → version stays.

## Todo
- [ ] outline.py (slug + headings)
- [ ] Extracted.summary + summary_of()
- [ ] frontmatter token_estimate + fields
- [ ] thread summary through writer + cli + crawler
- [ ] manual verify (single + crawl + idempotent re-run)

## Success Criteria
Every output `.md` has `token_estimate` + non-empty `summary` (when content exists); unchanged re-crawl keeps version (deterministic). `outline.headings()` returns correct slugs (unit-tested in Phase 3).

## Risks
- Summary heuristic picking boilerplate-y first line → tune "meaningful paragraph" filter (min length, skip md syntax). Keep simple; it's a hint, not ground truth.
- Threading `summary` widens `write()` signature — acceptable; keep param order stable.
