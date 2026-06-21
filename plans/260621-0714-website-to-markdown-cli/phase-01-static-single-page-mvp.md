# Phase 1 — Static Single-Page MVP

**Priority:** High (delivers usable value alone) · **Status:** pending · **Effort:** ~1.5 day

## Overview
`mdnow <url>` → fetch (static) → extract → one clean `.md` with YAML frontmatter (incl. versioning). The core happy path.

## Requirements
- CLI entrypoint `mdnow <url> [-o out/]` (typer).
- StaticFetcher (httpx) behind a `Fetcher` interface (Protocol/ABC) for later swap.
- Extract via trafilatura → markdown; strip ads/nav/footer.
- **Images:** extract with `include_images=True`, then regex post-process `![alt](src)` → `alt` (keep alt-text, drop image). trafilatura has NO native "drop image keep alt" mode — this step is mandatory.
- **Encoding:** pass `resp.content` (bytes) to trafilatura, NOT `resp.text` (correct charset handling).
- **Timeouts/retry:** explicit httpx timeout (e.g. 20s) + single retry.
- Frontmatter (YAML-safe via a real yaml dumper, titles may contain `:`/quotes):
  ```
  source_url, title, published_date (trafilatura date, nullable),
  fetched_date (this fetch), version (int, starts 1),
  content_hash (sha256 of normalized body), word_count
  ```
- **Versioning on re-write:** if target file exists → read its frontmatter `content_hash`; if changed → `version = old+1`, update `fetched_date`, rewrite; if same → skip (no-op). Works for single + crawl.

## Architecture
```
cli.py        → arg parsing, orchestration
fetcher.py    → Fetcher (Protocol) + StaticFetcher(httpx, timeout+retry)
extractor.py  → bytes → markdown (+ image regex strip) + metadata (trafilatura)
frontmatter.py→ build YAML frontmatter + content_hash + version bump logic
writer.py     → existence/hash check → write or skip
```
Each file <200 lines, single responsibility (DRY/KISS).

## Key APIs
- `httpx.get(url, follow_redirects=True, timeout=..., headers={UA})` → `resp.content` (bytes)
- `trafilatura.extract(html_bytes, output_format="markdown", include_images=True, include_links=True)`
- `trafilatura.extract_metadata(html_bytes)` → title/date
- regex: `!\[([^\]]*)\]\([^)]*\)` → `\1`
- `hashlib.sha256(body.encode()).hexdigest()`

## Files to Create
- `mdnow/__init__.py`, `mdnow/cli.py`, `mdnow/fetcher.py`, `mdnow/extractor.py`, `mdnow/frontmatter.py`, `mdnow/writer.py`
- `pyproject.toml` (deps: typer, httpx, trafilatura, pyyaml), `README.md`

## Implementation Steps
1. `pyproject.toml` + package skeleton; `mdnow` console script.
2. Fetcher Protocol + StaticFetcher (bytes, timeout, 1 retry).
3. Extractor: bytes → markdown; strip images→alt via regex; metadata.
4. Frontmatter builder (yaml dumper, content_hash) + writer (existence/hash → version bump or skip). Slug filename from title/URL.
5. Wire in cli.py; manual test on a static article (+ re-run to verify version stays 1 when unchanged).

## Todo
- [ ] pyproject + skeleton
- [ ] Fetcher interface + StaticFetcher (bytes/timeout/retry)
- [ ] Extractor (trafilatura + image→alt regex, bytes input)
- [ ] Frontmatter (yaml-safe, hash, version) + writer (skip-if-unchanged)
- [ ] CLI wiring + manual test (incl. unchanged re-run)

## Success Criteria
- Real article → clean markdown, no boilerplate/images, alt-text retained, valid YAML frontmatter, sensible filename.
- Re-run on unchanged page → version stays 1, no rewrite. Changed page → version 2.

## Risks
- Some sites block default UA → set browser-like UA (full anti-bot is Phase 3).
- Pathological titles → rely on yaml dumper, never hand-format frontmatter.
