# Phase 4 — `mdnow doctor` + `--fetch-browser` + friendly missing-extra hints

**Priority:** Medium · **Status:** pending · **Depends on:** Phase 1 · **Agent:** `fullstack-developer`

Soften the extras cliff: one command to see what's installed/missing, one flag to pull the
Camoufox browser inside the installed env, and consistent actionable messages when a feature
needs an absent extra.

## Key insights

- Existing hints are ad hoc: `--mcp` prints a good `pip install 'mdnow[mcp]'` message
  (`cli.py:42`); render/docs paths hint elsewhere. Standardize them.
- The installer can't easily run `python -m camoufox fetch` against an isolated `uv tool`
  env from outside. Cleanest fix: a `mdnow --fetch-browser` flag that runs the download
  **inside** mdnow's own environment. install.sh (Phase 5) just calls it. Fits single-command
  convention and avoids shell gymnastics.

## Requirements

- `mdnow --doctor` reports: Python version; base OK; `[render]` (camoufox import) present +
  whether the browser is downloaded; `[docs]` (markitdown) present; `[mcp]` present; whether the
  Claude skill is installed. Each missing item prints a copy-paste fix.
- `mdnow --fetch-browser`: runs Camoufox's browser fetch in-process; clear error if `[render]`
  isn't installed.
- One shared helper for "feature X needs extra Y → run: …" messages, reused by mcp/render/docs.

## Related code files

- Create: `mdnow/doctor.py` — probes (import checks, camoufox browser-path check, skill presence)
- Modify: `mdnow/commands.py` — `fetch_browser()` (subprocess/`camoufox` API within env)
- Modify: `mdnow/cli.py` — `--doctor`, `--fetch-browser` flags (short-circuit like `--mcp`)
- Modify: places that hint on missing extras → route through one helper (DRY)
- Create: `tests/test_doctor.py`

## Implementation steps

1. `mdnow/doctor.py`: functions that `importlib.util.find_spec` for camoufox/markitdown/mcp;
   detect Camoufox browser (its cache path / `camoufox` API); detect installed skill dir.
   Return a structured report; render it as human text in the CLI.
2. `fetch_browser()` in `commands.py`: invoke the camoufox fetch entrypoint in the current env;
   friendly `RemoteBlocked`-style message if the extra is absent.
3. Wire both flags; keep cli.py thin.
4. Consolidate missing-extra messaging into a single helper; update `--mcp`, render, and docs
   paths to use it.
5. Tests: monkeypatch `find_spec` to simulate present/absent extras; assert report + exit codes;
   assert `--fetch-browser` errors cleanly without `[render]`. No real browser download in tests.

## Todo

- [ ] `mdnow/doctor.py` probes + human-readable report
- [ ] `mdnow --fetch-browser` runs camoufox fetch in-env
- [ ] `mdnow --doctor` flag wired
- [ ] Single shared missing-extra message helper (DRY across mcp/render/docs)
- [ ] Tests via find_spec monkeypatch (network-free, no download)

## Success criteria

- On a base-only install, `mdnow --doctor` clearly lists what's missing with exact install
  commands; `mdnow --fetch-browser` after `[render]` downloads the browser.

## Risks

- Camoufox browser-presence detection API may differ by version → keep the check best-effort;
  worst case report "unknown, run --fetch-browser".
