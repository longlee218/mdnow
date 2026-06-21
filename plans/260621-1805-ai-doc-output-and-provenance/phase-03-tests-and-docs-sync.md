# Phase 3 — Tests + README/CLAUDE Sync

**Priority:** High (gate) · **Status:** pending · **Effort:** ~1 day · **Depends:** Phase 1, 2

## Overview
Lock in the new behavior with network-free tests (≥80% on new logic) and re-sync the docs. **Per project rule, the feature is not done until README.md reflects it.**

## Requirements
### Tests (pytest, network-free — reuse tests/conftest.py)
- `test_outline.py`: `slugify_heading` (cases incl. punctuation, unicode→ascii, dup collapse), `headings()` parses levels+slugs from markdown.
- `test_frontmatter_writer.py` (extend): `token_estimate` math; frontmatter includes `token_estimate`+`summary`; idempotent re-write unaffected by new fields.
- `test_extractor.py` (extend): `summary` = first meaningful paragraph; skips headings/short lines; uses meta description when present.
- `test_artifacts.py` (new): `build_llms_txt` shape (H1, `>` blockquote, annotated `- [t](p): summary`); `build_llms_full` contains every page + source tags; `build_manifest` returns valid dict with all fields + headings[].
- `test_crawler.py` (extend): crawl writes llms.txt/llms-full.txt/manifest.json and NO index.md.
- Remove/replace `test_tree.py` (module deleted).

### Docs sync (MANDATORY)
- **README.md** via `docs` skill or `docs-manager` agent: new crawl outputs (llms.txt/llms-full.txt/manifest.json, index.md gone), new frontmatter fields (`token_estimate`, `summary`), any flag changes. Update the "Output" section + frontmatter example.
- **CLAUDE.md**: architecture note — new `artifacts.py` emitter, `outline.py` helper, tree.py removed, frontmatter fields. Update only the changed lines.

## Implementation Steps
1. Write/extend the test modules above; run `pytest --cov=mdnow` → ≥80% on new code.
2. Fix any regressions (especially tree.py removal fallout).
3. Delegate README + CLAUDE.md sync to `docs-manager` (or run `docs` skill).
4. Verify README "Output" + frontmatter example match actual output of a real crawl.

## Todo
- [ ] test_outline.py
- [ ] extend test_frontmatter_writer + test_extractor
- [ ] test_artifacts.py
- [ ] extend test_crawler (artifacts written, no index.md); drop test_tree.py
- [ ] full suite green, ≥80% new-logic coverage
- [ ] README.md synced (docs-manager / docs skill)
- [ ] CLAUDE.md synced

## Success Criteria
All tests pass, ≥80% coverage on new logic. README + CLAUDE.md accurately describe the new artifacts + frontmatter (verified against a live crawl). No stale references to `index.md`/`tree.py`.

## Risks
- README drift if sync skipped → explicitly gated here; do not mark plan done until verified.
- Coverage dip from deleted tree.py tests → replaced by artifacts/crawler tests.
