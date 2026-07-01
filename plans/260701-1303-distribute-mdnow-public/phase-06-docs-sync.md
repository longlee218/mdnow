# Phase 6 — Attractive bilingual docs (EN + VI) + CLAUDE.md sync

**Priority:** High · **Status:** pending · **Depends on:** Phases 1–5 · **Agent:** `docs-manager`

README is the source of truth (repo rule). Rewrite it for a public audience that installs
without cloning, make it **visually attractive**, and ship it in **two languages: English
(canonical) + Vietnamese**. Sync CLAUDE.md for the new commands/architecture.

## Key insights

- Current README Install section leads with `python3 -m venv .venv && pip install -e .` — a
  developer/clone story. Public users need the `.sh` / `uv tool install` story first.
- New surfaces to document: `install.sh`, `uv tool install "mdnow[extras]"`, `pipx` fallback,
  Windows PowerShell one-liner, `mdnow --install-skill`, `mdnow --doctor`, `mdnow --fetch-browser`,
  License, "for AI assistants" (skill + MCP).

## Bilingual decision (locked, override point)

- **English `README.md` is canonical.** Reasons: repo rule ("README.md is source of truth") +
  **PyPI renders `README.md`** as the package long_description (a non-English or split README
  hurts the PyPI listing). International OSS convention is English-primary.
- **Vietnamese lives in `README.vi.md`** — a full translation kept in sync with the English one.
- Both files carry a **language switcher** at the very top:
  `English | [Tiếng Việt](README.vi.md)` and the mirror in `README.vi.md`.
- Sync rule: English changes first, VI follows in the same change set (treat VI drift as a bug,
  same as any README drift). Add a one-line note to CLAUDE.md / docs-management so future edits
  update both.

## "Attractive" checklist (applies to both languages)

- Hero: centered project name + one-line tagline + short value sentence.
- **Badges** (all render on PyPI/GitHub, no external tracking): PyPI version, Python versions,
  License (MIT), CI status. Use shields.io.
- **Terminal demo**: an asciinema/SVG cast (e.g. `vhs`/`asciinema-agg` → GIF or SVG) of
  `mdnow <url>` and a `--crawl` run. Embed as an image so it renders on PyPI too. (Static ASCII
  code-block fallback if an animated asset is too heavy.)
- **Feature table** (icon + one-liner): static fetch, SPA render, crawl→llms.txt, any-file
  convert, MCP, skill — makes scope scannable in 5 seconds.
- Quickstart box first (the one-liner), then progressive disclosure for extras.
- "Why mdnow" one-liner: **fully local, no API keys, no data egress by default** — the
  differentiator. Keep it truthful (no telemetry).
- Optional: a tiny before/after (raw HTML → clean markdown) snippet; TOC for long README.

## Requirements

- `README.md` (EN, canonical) restructured: language switcher → hero + badges → demo →
  feature table → Quickstart (one-liner) → Install options (uv / pipx / from source) →
  Extras (`[render]/[docs]/[mcp]` + `--fetch-browser`) → Windows note → "For AI assistants"
  (`--install-skill`, `--mcp`) → Usage → Why-local → License.
- `README.vi.md` — complete Vietnamese mirror, same structure/assets, natural technical Vietnamese
  (keep command/flag names and code verbatim; translate prose). Not machine-literal.
- Base install described as fully working (no heavy deps); extras clearly opt-in.
- Visual assets (demo cast, any logo) stored in-repo (e.g. `docs/assets/` or `assets/`) and
  referenced by relative path so they render on GitHub and PyPI.
- CLAUDE.md: document new flags (`--install-skill`, `--doctor`, `--fetch-browser`), `mdnow/skill/`
  bundling, `mdnow/commands.py` + `mdnow/doctor.py`, PyPI/install.sh distribution model, and the
  **EN-canonical + VI-mirror** README rule. Update the dev-install commands block.
- Delegate structure/consistency to the `docs` skill / `docs-manager` where practical.

## Related code files

- Modify: `README.md` (EN); Create: `README.vi.md` (VI)
- Create: visual assets (demo cast/GIF/SVG, optional logo) under an `assets/` path
- Modify: `CLAUDE.md` (+ bilingual sync rule)
- Optionally: `docs/project-changelog.md`, `docs/system-architecture.md`,
  `docs/development-roadmap.md`

## Implementation steps

1. Rewrite EN `README.md`: attractive structure above, install-first, keep "from source" for
   contributors.
2. Produce the demo asset (record `mdnow` run → GIF/SVG); add badges (shields.io) + feature table.
3. Add Extras, Windows, "For AI assistants", Why-local, License sections.
4. Translate to `README.vi.md` (full mirror, same assets, verbatim code/flags).
5. Add language switcher links at the top of both.
6. Sync CLAUDE.md (flags, modules, distribution model, EN-canonical + VI-mirror rule).
7. Update changelog/roadmap.
8. Verify: every documented command matches real CLI (no drift); badges/images render on both
   GitHub and a local `twine`/PyPI long-description preview; VI ↔ EN section parity.

## Todo

- [ ] EN `README.md`: hero + badges + demo + feature table + install-first rewrite
- [ ] Terminal demo asset (GIF/SVG) in-repo, renders on GitHub + PyPI
- [ ] EN sections: Extras, Windows, "For AI assistants", Why-local, License
- [ ] `README.vi.md` full Vietnamese mirror (code/flags verbatim, prose natural)
- [ ] Language switcher at top of both files
- [ ] CLAUDE.md sync incl. EN-canonical + VI-mirror rule
- [ ] Changelog/roadmap update
- [ ] Verify: no command drift, images render on PyPI preview, EN↔VI parity

## Success criteria

- A new user (EN or VI) can install and run `mdnow` from the README alone, without cloning.
- README renders attractively on **both GitHub and the PyPI project page** (badges + demo image).
- README ↔ actual CLI flags/behavior: zero drift. `README.vi.md` mirrors `README.md` section-for-
  section.

## Risks

| Risk | L | I | Mitigation |
|------|---|---|------------|
| VI translation drifts from EN over time | H | M | EN-canonical rule; update both in one change; note in CLAUDE.md |
| Animated demo asset bloats repo / won't render on PyPI | M | M | Prefer lightweight SVG cast; static code-block fallback; verify in PyPI preview |
| Docs written before flag names finalize (Phases 3–5) | M | M | Write this phase last |
| Non-English chars / emoji break PyPI long-description render | L | M | `twine check` + local long-description preview before release |
