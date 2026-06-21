---
status: completed
created: 2026-06-21
slug: ai-doc-output-and-provenance
---

# MDNow — AI-Doc Output + Provenance Frontmatter

Extend the completed MDNow CLI so its OUTPUT is itself a recognized AI-doc standard, and enrich per-page provenance — better agent search, stronger structure, less hallucination. **100% local, no API keys** (founding constraint preserved — all extractive, no LLM).

Source: solution-architecture recommendation (#1 + #2). Base build: `plans/260621-0714-website-to-markdown-cli/`.

## Scope

- **#1 Artifacts (crawl):** emit `llms.txt` (spec annotated index), `llms-full.txt` (concatenated dump), `manifest.json` (machine-readable page index).
- **#2 Provenance frontmatter (single + crawl):** `token_estimate` (chars/4, zero-dep), extractive `summary` (no LLM), heading outline (slugged) surfaced in manifest.

## Locked Decisions

| # | Decision |
|---|---|
| D1 | `llms.txt` **replaces** the bare `index.md` (spec-compliant annotated index supersedes the plain tree). |
| D2 | Site blockquote summary = extractive summary of the start/home page; fallback `Documentation crawled from <host>`. |
| D3 | Artifacts **always emitted** in crawl mode (no toggle flag — YAGNI; add later if needed). |
| D4 | Heading anchors surfaced as an **outline in manifest.json** (GitHub-style slugs); body is NOT mutated (keeps `content_hash` meaningful). |
| D5 | `token_estimate = ceil(len(text)/4)`, zero-dep. No tiktoken. |
| D6 | `summary` = first meaningful paragraph (or trafilatura metadata description), ~300 char cap. Extractive only. |

## Phases

| # | Phase | Status | Depends |
|---|-------|--------|---------|
| 1 | [Provenance helpers + frontmatter](phase-01-provenance-frontmatter.md) | done | — |
| 2 | [AI-doc artifacts emitter](phase-02-artifacts-emitter.md) | done | 1 |
| 3 | [Tests + README/CLAUDE sync](phase-03-tests-and-docs-sync.md) | done | 1,2 |

**ALL PHASES COMPLETE.** 54 tests / 86% coverage. Crawl now emits llms.txt + llms-full.txt + manifest.json (index.md retired); per-page frontmatter gains token_estimate + summary. README + CLAUDE.md synced.

Build order 1 → 2 → 3. Phase 1 adds reusable helpers (token, summary, slug) that Phase 2's manifest consumes.

## Reuse (DRY — do NOT reinvent)

`canonical()`/`build_path_map` (urls.py), `Extracted`/`extract` (extractor.py), `content_hash`/frontmatter build (frontmatter.py), `write()` versioning (writer.py), crawl two-pass page set (crawler.py). `tree.build_index` is superseded by the new llms.txt builder.

## Success Criteria

- `mdnow <url> --crawl` writes `llms.txt` + `llms-full.txt` + `manifest.json` (no more bare `index.md`); `llms.txt` validates against the llmstxt.org shape (H1 + blockquote + annotated links).
- Every page `.md` frontmatter gains `token_estimate` + `summary`; re-crawl still idempotent (versioning unaffected — summary/token derived deterministically).
- `manifest.json` parses; each entry has source_url, local_path, title, content_hash, token_estimate, word_count, summary, headings[].
- Tests ≥80% on new logic, network-free. README + CLAUDE.md synced.

## Constraints

Modules <200 lines; new capability stays flags on the single `mdnow` command; fully local. **A change isn't done until README.md reflects it** (Phase 3).
