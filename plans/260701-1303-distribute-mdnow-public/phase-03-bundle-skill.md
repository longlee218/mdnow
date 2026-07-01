# Phase 3 — Bundle the Claude skill + `mdnow --install-skill`

**Priority:** High · **Status:** pending · **Depends on:** Phase 1 (package layout) · **Agent:** `fullstack-developer`

Ship the Claude skill *inside* the pip package so one install gets both, and add a flag to copy
it into the user's Claude skills dir. Fix the machine-specific breakage in the skill.

## Key insights (verified)

- Current skill: `.agents/mdnow/SKILL.md` (72 lines) + `.agents/mdnow/references/`, plus
  `.agents/mdnow-command.md`.
- **`.agents/mdnow/SKILL.md:47` hardcodes `/Users/longlh/Documents/Longle/MDNow/.venv/bin/mdnow`**
  — the exact "only runs on my computer" bug at the skill layer. Must become bare `mdnow` (PATH).
- To bundle as package data, the canonical skill must live **under the `mdnow/` package dir**.

## Requirements

- Canonical skill source relocates to `mdnow/skill/` (`SKILL.md` + `references/**`).
- Skill invokes `mdnow` from PATH only — no venv/absolute paths anywhere.
- `mdnow --install-skill [--dir PATH]` copies the bundled skill to `~/.claude/skills/mdnow/`
  (default), creating dirs, refusing to clobber without `--force` (or overwriting with a notice).
- Package build includes `mdnow/skill/**` (sdist + wheel).
- `cli.py` stays thin: action logic lives in a new module (e.g. `mdnow/commands.py`).

## Related code files

- Create: `mdnow/skill/SKILL.md` (+ `mdnow/skill/references/**`) — moved & de-pathed
- Create: `mdnow/commands.py` — `install_skill(dir, force)` using `importlib.resources`
- Modify: `mdnow/cli.py` — add `--install-skill` / `--skill-dir` flags, short-circuit like `--mcp`
- Modify: `pyproject.toml` — `[tool.setuptools.package-data]` (or `include-package-data` +
  `MANIFEST.in`) to ship `mdnow/skill/**`
- Delete/replace: `.agents/mdnow/` and `.agents/mdnow-command.md` (or make repo dev usage a thin
  pointer to the package copy to avoid drift — single source of truth = `mdnow/skill/`)
- Create: `tests/test_install_skill.py`

## Implementation steps

1. Move skill files into `mdnow/skill/`; scrub line 47 and any other path/venv refs → `mdnow`.
2. Add `mdnow/commands.py::install_skill()`: locate bundled dir via
   `importlib.resources.files("mdnow") / "skill"`, copy tree to target, handle exists/force.
3. Wire `--install-skill` + `--skill-dir` into `cli.main` (boolean/opt flags, short-circuit).
4. Package data: ensure the wheel contains `mdnow/skill/**` (verify by unzipping the built wheel).
5. Tests (network-free): install into a tmp dir, assert `SKILL.md` present and contains no
   `/Users/`/`.venv` strings; `--force` overwrites; missing-source path errors cleanly.
6. Decide repo-dev skill story: keep `.claude/skills/mdnow` as a symlink/pointer to
   `mdnow/skill/`, or drop it — document the single source of truth.

## Todo

- [ ] Relocate skill to `mdnow/skill/`, remove hardcoded interpreter path
- [ ] `mdnow/commands.py::install_skill()` via importlib.resources
- [ ] `--install-skill` / `--skill-dir` flags in cli.py (keep cli.py < 200 lines)
- [ ] package-data / MANIFEST so skill ships in the wheel
- [ ] Tests: install to tmp, assert no machine-specific paths, force-overwrite
- [ ] Resolve `.agents/` vs `.claude/skills` duplication (one source of truth)

## Success criteria

- Fresh Claude profile: `mdnow --install-skill` → skill loads and its commands call `mdnow`
  (on PATH) successfully — no edits needed.
- Built wheel contains the skill; grep of installed skill finds zero `/Users/` or `.venv`.

## Risks

- Package-data omission (skill silently missing from wheel) → explicit unzip-the-wheel check.
- Skill/CLI version drift → acceptable & intended (bundled together); note in docs.
