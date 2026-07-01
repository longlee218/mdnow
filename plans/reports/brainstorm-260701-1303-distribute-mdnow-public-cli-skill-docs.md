# Brainstorm — Make `mdnow` installable by everyone (CLI + skill + docs)

Date: 2026-07-01 · Mode: brainstorm (advisory only, no implementation)

## Problem statement

`mdnow` today only installs as an **editable clone from an absolute path**
(`pip install -e /abs/path/MDNow[...]`). That is the "only runs on my computer" ceiling.
Goal: ship it so **anyone** can install and run it — as a CLI, with the bundled Claude
skill, backed by public-facing docs.

## Decisions locked (from Q&A)

| Axis | Decision |
|------|----------|
| Audience | **Public OSS** — PyPI + public GitHub, LICENSE + notices required |
| CLI install | **One-line `.sh` installer** as the easy front door (wraps `uv`/`pipx` → PyPI) |
| Skill delivery | **Bundle in the package** — `mdnow --install-skill` copies it into `~/.claude/skills` |
| Heavy deps | **Thin base + opt-in extras** (`[render]`/`[docs]`/`[mcp]`) + friendly `doctor`/hints |

Verified fact: PyPI name **`mdnow` is free** (HTTP 404). Reserve it early.

## Recommended architecture

The `.sh` is the friendly face; the real backend is **PyPI + `uv`**. Do NOT hand-roll
venv logic in the shell script — delegate to `uv`/`pipx` (KISS).

```
curl -LsSf https://<host>/install.sh | sh        # front door
        │
        ▼
install.sh:  ensure `uv` (bootstraps Python 3.11+) ──► uv tool install "mdnow[extras]"
                                                   ──► (if render) python -m camoufox fetch
                                                   ──► (optional) mdnow --install-skill
        │
        ▼
PyPI: mdnow 0.x  (thin base + [render] [docs] [mcp] extras)  ← published via GitHub Actions + OIDC trusted publishing
        │
        ▼
Package data: mdnow/skill/SKILL.md  ← `mdnow --install-skill` copies to ~/.claude/skills
```

### Why `uv` as the backend (not raw pip/venv)
- `uv tool install` gives isolated, versioned CLI installs (like pipx) **and** can bootstrap
  the right Python — kills the #1 "works on my machine" failure (wrong/missing Python).
- Fast; single static binary; `.sh` just installs `uv` if absent then one `uv tool install`.
- Fallback documented: `pipx install mdnow`.

### Extras handling (thin base + hints)
- Base install = static-fetch pipeline only (already the design). Fast, small.
- `.sh` flags: `--render --docs --mcp --all` → `uv tool install "mdnow[render,docs,mcp]"`.
- Add **`mdnow doctor`**: prints Python version, which extras present, whether the Camoufox
  browser is downloaded, MCP availability — the friendly diagnostic for the extras cliff.
- Keep the existing one-time "feature needs extra X" hints when a missing extra is hit.

### Skill bundling
- Move skill into the package as package data: `mdnow/skill/SKILL.md` (+ assets).
- New CLI command `mdnow --install-skill [--dir ...]`: copies bundled skill into the user's
  Claude skills dir. **Skill commands must invoke `mdnow` on PATH** — audit for and remove any
  hardcoded venv/absolute-path references (current skill was repo-local).
- Coupling skill version to CLI version is desirable: skill instructions always match the
  installed flags.

## Options considered (and why rejected)

| Approach | Verdict |
|----------|---------|
| `.sh` → `uv`/PyPI (chosen) | Easiest UX, versioned, extras work, standard for Python CLIs |
| `pipx install git+https://…` | Works without PyPI but no version UX, less discoverable — keep only as no-PyPI fallback |
| Docker as primary | Bundles browser/native deps but heavy, awkward file I/O for a CLI — offer only for render/docs-heavy users, not the default |
| Batteries-included default install | Rejected — 300MB browser + native wheels on first `install` is a bad first impression |

## Risk assessment

| Risk | L | I | Mitigation |
|------|---|---|------------|
| PyPI name lost to squatter before publish | M | M | Publish placeholder `0.x` to reserve `mdnow` **now** |
| `curl \| sh` security optics (public OSS) | L | M | HTTPS only, readable/pinned script, also document non-piped `uv tool install` |
| Extras cliff still frustrates users | M | M | `mdnow doctor` + actionable missing-extra messages; docs lead with base = works |
| Skill ships absolute paths / breaks off-machine | M | H | Audit skill; invoke `mdnow` from PATH only; test `--install-skill` on clean profile |
| Missing LICENSE / incomplete third-party notices on public release | M | H | Add root `LICENSE` (MIT suggested) + verify notices before first public push |
| Windows users un</br>served by `.sh` | M | L | Document PowerShell one-liner (`uv`/`pipx`); don't build a `.ps1` yet (YAGNI) |
| OSS maintenance burden (issues/PRs/security) for a "built-for-one" tool | M | M | Set expectations in README; resist scope creep (no telemetry, no queues) |

## Business impact / effort

Rough effort, one engineer: **~3–4 days total**.
- PyPI metadata polish (classifiers, URLs, README as long_description) + reserve name: 0.5d
- GitHub Actions publish workflow (OIDC trusted publishing, tag-triggered): 0.5d
- `LICENSE` + verify third-party notices: 0.5d
- Bundle skill as package data + `mdnow --install-skill` + path audit: 0.5–1d
- `mdnow doctor` + friendly missing-extra hints: 0.5d
- `install.sh` (uv bootstrap + extras + camoufox fetch + optional skill): 0.5–1d
- README/docs rewrite (install-first, "for AI assistants" section): 0.5d

Value: turns a personal tool into a shareable one; "fully local, no API keys, no egress by
default" is a strong public differentiator — lean into it in docs, keep it true (no telemetry).

## Success criteria

- On a clean machine (no clone, no Python assumptions): `curl … | sh` → `mdnow <url>` works.
- `mdnow --install-skill` makes the skill usable in a fresh Claude profile with no path edits.
- `uv tool install "mdnow[render]"` + `camoufox fetch` → `--render`/crawl SPA works.
- `mdnow doctor` clearly reports missing extras with a copy-paste fix.
- README leads with install; base install has zero heavy downloads.
- CI publishes to PyPI on version tag without a stored token.

## Decisions still needed (owner: you)

1. **License** — MIT (recommended, simplest for a permissive utility) vs Apache-2.0 (patent grant)?
2. **Installer host** — GitHub raw URL, GitHub Pages, or a short custom domain?
3. **`uv` vs `pipx`** as the primary backend the `.sh` installs (recommend `uv`; pipx fallback).
4. **Windows scope now or later** — document-only vs ship a `.ps1` (recommend document-only, YAGNI).

## Unresolved questions
- Is there an existing org PyPI account (apero) to publish under, or a personal one?
- Do you want the MCP server surfaced in the public docs, or keep it low-key initially?
