# Phase 2 — AI-Doc Artifacts Emitter

**Priority:** High · **Status:** pending · **Effort:** ~1.5 day · **Depends:** Phase 1

## Overview
From a crawl, emit three artifacts that make MDNow's output a recognized AI-doc standard: `llms.txt` (spec annotated index, replaces bare `index.md`), `llms-full.txt` (concatenated dump), `manifest.json` (machine-readable index). Reuses Phase 1 helpers.

## Requirements
### llms.txt (llmstxt.org shape)
```
# <Site Title>

> <site summary — extractive from home/start page; fallback "Documentation crawled from <host>">

## Pages
- [<title>](<relpath>): <one-line summary>
- ...
```
Grouped by top-level URL path section where natural; each link annotated with the page summary (Phase 1).

### llms-full.txt
H1 + blockquote header (same as llms.txt), then every page's full markdown concatenated in tree order, each preceded by `## <title>` and a `Source: <url>` line.

### manifest.json
```json
{ "host": "...", "generated_from": "<start_url>", "page_count": N,
  "pages": [ { "source_url","local_path","title","content_hash",
               "token_estimate","word_count","summary",
               "headings": [{"level","text","slug"}] } ] }
```

## Where it goes
- New `artifacts.py` (<200 lines): `build_llms_txt`, `build_llms_full`, `build_manifest` (pure functions over the crawled `Page` set + `url_map`).
- `crawler.crawl_site`: after writing pages, write `llms.txt`, `llms-full.txt`, `manifest.json` to `out/`. **Remove the `index.md` write** (llms.txt supersedes; D1).
- `tree.py`: superseded → delete (its `build_index` role moves into `artifacts.build_llms_txt`). Remove orphaned import in crawler.
- `manifest.json` via `json.dumps(..., indent=2, ensure_ascii=False)`.
- Site summary: reuse the start-page `Page.summary` (Phase 1); the crawl already fetches start_url first.

## Data needed
`crawl_site` already holds the `Page` list (now with `.summary` from Phase 1) + `url_map`. Pass both to the builders. headings[] computed via `outline.headings(page.body)`.

## Implementation Steps
1. `artifacts.py` pure builders (llms_txt, llms_full, manifest) — take (host, site_summary, pages, url_map).
2. Wire into `crawl_site`: compute site_summary (start page), write 3 files, drop index.md.
3. Remove `tree.py` + its import; adjust any reference.
4. Manual: crawl small site → inspect llms.txt (valid shape), llms-full.txt (all pages), manifest.json (parses, headings present).

## Todo
- [ ] artifacts.py: build_llms_txt / build_llms_full / build_manifest
- [ ] wire into crawl_site, drop index.md
- [ ] delete tree.py + fix imports
- [ ] manual verify all 3 artifacts

## Success Criteria
Crawl produces valid `llms.txt` (H1+blockquote+annotated links), `llms-full.txt` (all pages, source-tagged), parseable `manifest.json` with per-page headings/summary/token_estimate. No `index.md` emitted.

## Risks
- llms-full.txt size for big `--all` crawls (already hold bodies in RAM — same ceiling as base build; acceptable personal scale).
- Section grouping in llms.txt: keep simple (flat or by first path segment) — don't over-engineer.
- Deleting tree.py: ensure Phase-0 build's tests referencing it are updated (Phase 3).
