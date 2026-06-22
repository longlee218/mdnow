# Phase 3 — Tests + README/CLAUDE sync

**Priority:** High · **Status:** done · **Depends:** Phases 1, 2

Verify the new logic network-free, prove no regression to website behavior, and re-sync the source-of-truth docs. **A change isn't done until README.md reflects it.**

## Requirements

- New `tests/test_convert.py`: network-free.
  - `from_path` on tiny **real local fixtures** committed under `tests/fixtures/` (e.g. a small `.csv`, `.json`, `.docx` if cheap) → asserts non-empty markdown + `Extracted` shape. (markitdown does the conversion locally — allowed, like running trafilatura on a fixture. Do NOT unit-test audio/YouTube — those egress; treat like camoufox, integration-only.)
  - `_guard_remote`/`_require_remote`: audio ext + YouTube refused without `allow_remote` (raise), pass with it (no network — assert the guard, monkeypatch the actual markitdown call).
  - `_ext_from` sniffing: URL ext wins; octet-stream falls back correctly.
- `tests/test_cli*.py` additions: local-file fork routes to convert (monkeypatch `convert.from_path`); `--crawl` + file errors; URL still routes to the funnel (regression).
- Regression: a non-HTML remote response with `[docs]` present routes to markitdown not render; the existing HTML/thin/render escalation tests still pass.
- Keep ≥80% coverage on new logic. Run full suite — all green.
- **README.md sync** (via `docs` skill or `docs-manager`): new `[docs]` install extra + `python -m camoufox`-style note on install size; the any-file capability; `--allow-remote` in the flags table; behavior notes (local files, remote files, audio/YouTube gating, `--crawl` invalid for files). Update the one-line description if it still says "website URL".
- **CLAUDE.md sync:** architecture — input-type fork (top of `main`), content-type fork (`_acquire`), `convert.py` module, `[docs]` extra, `--allow-remote`, the "local by default" nuance for egress converters.
- **pipx line:** update to `pipx install "/abs/path[render,docs]" --force`.

## Related Code Files

- **Create:** `tests/test_convert.py`, `tests/fixtures/*` (tiny sample files)
- **Modify:** `tests/test_cli.py`/`test_cli_main.py` (new routing assertions), `README.md`, `CLAUDE.md`
- **Verify:** existing tests unchanged & passing

## Implementation Steps

1. Add tiny fixtures + `tests/test_convert.py` (monkeypatch markitdown for guard tests; real fixtures for `from_path`).
2. Add CLI routing/regression tests.
3. `pytest -q --cov=mdnow` → all pass, coverage ≥80% on new lines.
4. Delegate README + CLAUDE sync to `docs-manager` (or `docs` skill); verify flags table, install, behavior notes, description.
5. Final: full suite green + docs reflect every new flag/extra/behavior.

## Todo List

- [x] `test_convert.py` + fixtures (network-free)
- [x] CLI routing + regression tests
- [x] full suite green, ≥80% on new logic
- [x] README synced (extra, capability, `--allow-remote`, behavior, description)
- [x] CLAUDE.md synced (forks, convert.py, extra, egress nuance)
- [x] pipx install line updated to `[render,docs]`
- [ ] cli.py extraction under 200-line ceiling (DEFERRED follow-up)

## Success Criteria

All tests pass with no network. README + CLAUDE.md accurately describe file conversion, the `[docs]` extra, and `--allow-remote`. A reader installing fresh from the README can convert a PDF.

## Risks

- Fixture choice: a `.docx`/`.pdf` fixture may drag heavy converters into CI runtime. Mitigation: prefer the lightest formats (`.csv`/`.json`/`.html`) for the real-conversion test; monkeypatch for everything else.
