# Phase 2 — LICENSE + third-party notices

**Priority:** High · **Status:** pending · **Depends on:** none · **Agent:** `fullstack-developer` (notices wording may pair with `docs-manager`)

Public OSS release requires an explicit license and honest attribution. There is **no root
`LICENSE`** today.

## Key insights

- Dependencies are permissive-friendly (typer, httpx, trafilatura, pyyaml; optional camoufox,
  markitdown, mcp). MIT for `mdnow` itself is clean and simplest (assumed default).
- A `THIRD_PARTY_NOTICES.md` exists only under `.claude/skills/` (unrelated tooling) — do **not**
  reuse it; generate a fresh notice scoped to `mdnow`'s actual deps if one is warranted.
- MIT does not require bundling dependency licenses, but listing them is good OSS hygiene.

## Requirements

- Root `LICENSE` (MIT, correct year + author).
- `pyproject.toml` license metadata references it (coordinated with Phase 1).
- Verify optional deps' licenses are compatible with redistribution/mention (camoufox, markitdown
  and its heavy transitive deps like onnxruntime).

## Implementation steps

1. Add root `LICENSE` (MIT). Confirm author/holder name with the user (open question).
2. Wire `license`/`license-files` in `pyproject.toml` (Phase 1).
3. Quick license audit of direct deps (base + extras); note any copyleft surprises. Trafilatura
   is Apache-2.0/GPL-dual historically — **verify current license** and that our use is fine.
4. If warranted, add a concise `NOTICE`/`THIRD_PARTY_LICENSES.md` at root listing dep + license.
5. README gets a License section (Phase 6).

## Todo

- [ ] Add root `LICENSE` (MIT), confirm holder
- [ ] Audit direct dep licenses (esp. trafilatura, camoufox, markitdown chain)
- [ ] Optional root notices file if any dep requires attribution
- [ ] Link license in pyproject + README

## Success criteria

- `LICENSE` present; PyPI page shows the license; no incompatible-license blocker found.

## Risks

- A dep with unexpected copyleft terms → surface before public push; worst case gate a feature
  behind an extra with a clear note. Low likelihood given the stack.
