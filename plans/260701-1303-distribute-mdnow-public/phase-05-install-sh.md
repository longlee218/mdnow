# Phase 5 — `install.sh` one-line installer

**Priority:** High · **Status:** pending · **Depends on:** Phases 1, 3, 4 · **Agent:** `fullstack-developer`

The friendly front door: `curl -LsSf https://<host>/install.sh | sh`. Thin POSIX shell that
delegates all real work to `uv` (KISS — no hand-rolled venv logic).

## Key insights

- `uv` can bootstrap the right Python and give isolated tool installs — kills the #1
  "wrong/missing Python" failure. Primary path; `pipx` documented as fallback.
- Browser download + skill install are done by the CLI itself (`--fetch-browser`,
  `--install-skill` from Phases 3–4), so the shell script never touches the isolated env
  internals.
- macOS/Linux only. Windows → documented PowerShell one-liner in Phase 6 (no `.ps1` now).

## Requirements

- `install.sh` (repo root, served from GitHub raw). POSIX `sh`, `set -eu`, HTTPS only.
- Ensures `uv`: if `command -v uv` fails, install via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- Flags/env to select extras: `--render --docs --mcp --all` → builds `mdnow[render,docs,mcp]`.
- `uv tool install "mdnow[<extras>]"`.
- If `[render]` selected: run `mdnow --fetch-browser`.
- Optional `--skill`: run `mdnow --install-skill`.
- Prints next steps + how to add `~/.local/bin` to PATH if needed.
- Readable, non-piped alternative documented (download, inspect, run) for the security-conscious.

## Related files

- Create: `install.sh`
- (Phase 6 documents its usage in README.)

## Implementation steps

1. Write `install.sh`: `set -eu`; detect OS; ensure `uv`; parse args into an extras list;
   `uv tool install "mdnow[$extras]"` (or plain `mdnow` if none).
2. Conditionally `mdnow --fetch-browser` (render) and `mdnow --install-skill` (skill flag).
3. Post-install: verify `mdnow --version`/`mdnow doctor`; print PATH hint.
4. Manual test matrix: fresh macOS + fresh Linux container, with/without `uv` preinstalled,
   base vs `--all`. (Not a unit test — it's an integration/manual gate; document results.)
5. Keep it small and auditable; shellcheck-clean.

## Todo

- [ ] `install.sh` — ensure uv, install from PyPI with selected extras
- [ ] Wire `--fetch-browser` (render) + `--install-skill` (skill) passthrough
- [ ] PATH + next-steps output; non-piped install note
- [ ] shellcheck clean; manual test on clean macOS + Linux

## Success criteria

- Clean machine with neither `mdnow` nor `uv`: one-liner → `mdnow <url>` works; `--all` variant
  yields working `--render`, `--docs`, `--mcp`, and installed skill.

## Risks

- `curl | sh` optics → HTTPS, readable script, documented manual alternative.
- `~/.local/bin` not on PATH → detect and print the exact export line.
- Piping `astral.sh/uv/install.sh` inside our script = nested curl|sh → acceptable (official uv
  installer); pin/verify per uv guidance.
