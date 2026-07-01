# Phase 1 — PyPI packaging + trusted-publishing CI

**Priority:** High · **Status:** pending · **Depends on:** none · **Agent:** `fullstack-developer`

Make the package publishable and claim the name `mdnow` on PyPI (verified free). This unblocks
the `.sh` installer, which installs from PyPI.

## Key insights

- Current `pyproject.toml` is minimal: no license field, no readme, no classifiers, no URLs,
  no authors. That's fine for editable-local, not for a public PyPI listing.
- Build backend is already `setuptools`; keep it (no need for hatchling — KISS).
- Don't publish a fake empty "placeholder". Do metadata + LICENSE (Phase 2) first, then cut a
  real minimal `0.1.x` to claim the name.

## Requirements

- `[project]` gains: `readme = "README.md"`, `license`, `authors`, `keywords`, `classifiers`
  (Python 3.11/3.12/3.13, License :: OSI Approved :: MIT, Topic :: Text Processing :: Markup),
  `[project.urls]` (Homepage, Repository, Issues).
- Version bump policy: keep `0.1.x` for the first public release; document tag → release flow.
- CI publishes on a `v*` tag via **OIDC trusted publishing** (no API token stored).

## Related code files

- Modify: `pyproject.toml`
- Create: `.github/workflows/publish.yml`
- Depends on Phase 2 for the `LICENSE` file the metadata references.

## Implementation steps

1. Add project metadata to `pyproject.toml` (readme, license = `{ text = "MIT" }` or
   `license = "MIT"` + `license-files`, authors, keywords, classifiers, urls).
2. Confirm `[tool.setuptools] packages = ["mdnow"]` still holds; Phase 3 adds package-data for
   the bundled skill (coordinate so both land together).
3. Local build check: `python -m build` (add `build` as a dev tool) → inspect the wheel/sdist
   contains `README.md`, `LICENSE`, and (after Phase 3) `mdnow/skill/**`.
4. `twine check dist/*` passes.
5. Create `.github/workflows/publish.yml`:
   - Trigger: `on: push: tags: ['v*']`.
   - Job: `permissions: id-token: write`; build sdist+wheel; `pypa/gh-action-pypi-publish`
     (no username/password — trusted publishing).
   - Optional pre-step: run the test suite as a gate before publish.
6. Register the PyPI trusted-publisher entry (repo + workflow name) on pypi.org (manual, one-time
   — note in docs; requires the account decision in the open questions).
7. Tag `v0.1.x` → confirm the workflow publishes and `pip index versions mdnow` shows it.

## Todo

- [ ] Enrich `pyproject.toml` metadata
- [ ] Add `build`/`twine` to dev deps; local `python -m build` + `twine check` pass
- [ ] Add `.github/workflows/publish.yml` (OIDC, tag-triggered)
- [ ] Configure PyPI trusted publisher (one-time, manual)
- [ ] Cut first real `v0.1.x` release; verify on PyPI

## Success criteria

- `pipx install mdnow` / `uv tool install mdnow` works from PyPI on a clean machine.
- Wheel contains README, LICENSE, and bundled skill (post-Phase 3).
- Tagging publishes automatically with no stored secret.

## Risks

- Name squatted before release → mitigate by cutting the real release as soon as Phases 1–2 done.
- Trusted-publishing misconfig → first publish fails loudly; fix the PyPI publisher entry.

## Manual release steps

1. Register the trusted publisher on pypi.org: project `mdnow` → Publishing → add GitHub
   publisher with repo `longlee218/mdnow`, workflow `publish.yml`, environment `pypi`.
2. Cut the release: `git tag v0.1.0 && git push --tags` — this triggers `.github/workflows/publish.yml`
   (test → build → publish via OIDC, no stored secret).
