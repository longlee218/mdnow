---
status: completed
created: 2026-07-01
completed: 2026-07-01
slug: distribute-mdnow-public
---

# Plan — Distribute `mdnow` as a public OSS tool (CLI + skill + docs)

Turn `mdnow` from an editable clone-from-absolute-path tool into something **anyone** can
install and run: a versioned PyPI package, a one-line `.sh` installer, a bundled Claude skill,
and install-first public docs.

Brainstorm source of truth: `plans/reports/brainstorm-260701-1303-distribute-mdnow-public-cli-skill-docs.md`

## Architecture in one line

`.sh` front door → installs `uv` if absent → `uv tool install "mdnow[extras]"` from **PyPI** →
optional `mdnow --fetch-browser` (Camoufox) + `mdnow --install-skill`. Base install stays thin;
`[render]/[docs]/[mcp]` are opt-in; `mdnow doctor` diagnoses what's missing.

## Locked decisions & assumed defaults

- Public OSS; PyPI name `mdnow` **verified free** — claim it in Phase 1.
- `.sh` installer wraps `uv tool install` (primary) / `pipx` (documented fallback).
- Skill bundled inside the package; canonical source moves to `mdnow/skill/`.
- Thin base + extras; `mdnow doctor` + friendly missing-extra messages.
- **Assumed (override points):** MIT license · `uv` primary · install.sh hosted on GitHub raw ·
  Windows = document-only PowerShell one-liner (no `.ps1` yet).
- **Docs:** attractive README in **two languages** — English `README.md` (canonical, PyPI
  long-description) + Vietnamese `README.vi.md` (synced mirror), language switcher on both.

## Repo constraints (must hold)

- Every module < 200 lines; `cli.py` stays thin → new action logic goes in a new module.
- Capabilities are **flags on the single `mdnow` command**, not subcommands
  (`--doctor` / `--install-skill` / `--fetch-browser`, mirroring `--mcp`).
- README is source of truth — sync in the same change. Tests stay network-free.

## Phases

| # | Phase | Depends on | Agent | Status |
|---|-------|-----------|-------|--------|
| 1 | [PyPI packaging + trusted-publishing CI](phase-01-pypi-packaging.md) | — | `fullstack-developer` | ✅ done (release = manual) |
| 2 | [LICENSE + third-party notices](phase-02-license-notices.md) | — | `fullstack-developer` | ✅ done |
| 3 | [Bundle skill + `--install-skill`](phase-03-bundle-skill.md) | 1 | `fullstack-developer` | ✅ done |
| 4 | [`doctor` + `--fetch-browser` + friendly hints](phase-04-doctor-hints.md) | 1 | `fullstack-developer` | ✅ done |
| 5 | [`install.sh` one-line installer](phase-05-install-sh.md) | 1,3,4 | `fullstack-developer` | ✅ done (manual test matrix pending) |
| 6 | [Attractive bilingual docs (EN+VI) + CLAUDE.md sync](phase-06-docs-sync.md) | 1–5 | `docs-manager` | ✅ done (animated demo asset TODO) |

## Completion notes (2026-07-01)

- **Verified:** 113 tests pass, 88% coverage, `python -m build` + `twine check` pass, compile clean.
- **Code review:** 1 CRITICAL (`--mcp` RuntimeError swallowed → traceback) + 1 HIGH (undeclared
  `pydantic` in `[mcp]`) + 2 MEDIUM (CI least-privilege, install.sh PATH) — all fixed & re-verified.
  Regression test added for the `--mcp` missing-extra path.
- **Manual / external (owner: user):** register PyPI trusted publisher + `git tag v0.1.0`
  (see phase-01 "Manual release steps"); confirm install.sh raw-URL branch (`main` vs `master`);
  run install.sh test matrix on clean macOS/Linux; record animated demo asset for README.
- **Pre-existing follow-up (NOT introduced here):** `mdnow[docs]` (`markitdown[all]`) fails to
  re-resolve on a fresh install — needs dep-pinning investigation before public `[docs]` install
  is advertised as frictionless.

Phases 1 and 2 are independent and can run first/parallel. 3 and 4 both need the package layout
from 1. 5 ties the CLI pieces together. 6 documents the finished behavior.

## Agent assignment

- **Documentation → `docs-manager`** (README/docs skill): Phase 6 (bilingual README EN+VI,
  CLAUDE.md sync, changelog/roadmap). It owns all prose/markdown deliverables.
- **Engineering → `fullstack-developer`**: Phases 1–5 (pyproject/CI, LICENSE wiring, skill
  bundling + CLI flags, `doctor`/`--fetch-browser`, `install.sh`). Owns all code + config.
- **Seam:** engineer finalizes flag names/behavior (Phases 3–5) *before* `docs-manager` writes
  Phase 6 — docs describe shipped behavior, not intended behavior (kills doc drift).

## Definition of done

- Clean machine (no clone, no Python assumed): `curl … | sh` → `mdnow <url>` works.
- `mdnow --install-skill` makes the skill usable in a fresh Claude profile, zero path edits.
- `uv tool install "mdnow[render]"` + `mdnow --fetch-browser` → `--render`/SPA crawl works.
- `mdnow doctor` reports missing extras with copy-paste fixes.
- CI publishes to PyPI on a version tag via OIDC (no stored token).
- README leads with install; base install pulls no heavy deps. Tests green, network-free.

## Open questions (non-blocking; defaults assumed above)

1. PyPI account: personal or org (apero)?
2. Surface MCP server prominently in public docs, or keep low-key at launch?
