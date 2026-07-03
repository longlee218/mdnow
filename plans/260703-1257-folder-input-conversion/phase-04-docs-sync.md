# Phase 04 — Docs sync (README.md + README.vi.md + CLAUDE.md)

## Context Links
- `README.md` (English canonical — SOURCE OF TRUTH per CLAUDE.md)
- `README.vi.md` (Vietnamese mirror — must stay in sync)
- `CLAUDE.md` → "Architecture — the big picture", "Crawl artifacts", input-type-fork section
- `.claude/rules/documentation-management.md` (README-is-source-of-truth rule)

## Overview
- **Priority:** P2 — MANDATORY, not optional. A change is not "done" until docs reflect it (repo rule: stale README = bug).
- **Status:** ✅ done
- **Description:** Document folder input as the **third input type** (URL / file /
  YouTube → now + folder) across both READMEs and CLAUDE.md, in the same change.

## Key Insights
- README.md and README.vi.md are a full mirror — every English edit needs the matching Vietnamese edit. Prefer the `docs` skill / `docs-manager` agent for consistency.
- Folder input reuses `artifacts.py` unchanged — call this out in CLAUDE.md so future readers know `folder.py` and `crawler.py` share the artifact seam.
- Keep additions concise and mirror how existing local-file/YouTube branches are described.

## Requirements
- **README.md** (canonical):
  - Input-type list/overview: add "local folder (recursive batch convert)" alongside URL / file / YouTube.
  - Usage examples: add `mdnow ./docs -o out/` producing per-file `.md` + `llms.txt`/`llms-full.txt`/`manifest.json`. If the existing Rich-UI behavior note mentions the crawl progress bar, extend it: folder mode shows the same live progress bar + colored `Done: N file(s) converted` summary + manifest next-step hint (degrades to plain text on non-tty/NO_COLOR).
  - Note dotfile/dotdir skip, per-file failure isolation, and that `--crawl` is rejected (folder always builds the index). Note fetch-tier flags (`--render`, `-H`, `--cookie-file`, `--no-llms`) don't apply.
- **README.vi.md:** same additions, translated, in the mirrored locations.
- **CLAUDE.md:**
  - "Input-type fork at CLI entry" list: add a **Local folder** bullet → `folder.convert_folder()` (recursive markitdown batch, crawl-style artifacts, skips the URL funnel).
  - Add a short note (near "Crawl artifacts") that `folder.py` reuses `artifacts.py` (`build_llms_txt`/`build_llms_full`/`build_manifest`) unchanged — mirroring `crawler.py` over a local directory. Path mapping is **not** `urls.build_path_map` (that's URL-only and would mangle file extensions); folder mode maps each converted file's output name via the existing `slugs.file_slug` helper (same one single-file conversion uses) plus a small local sha1-suffix dedup for genuine leaf-name collisions.
  - If CLAUDE.md documents the `ui.py` presentation seam, note that folder mode routes all output through it like crawl (`ui.step`/`ui.progress_bar("converting")`/`ui.folder_summary`/`ui.hint`), and that `ui.py` gained `folder_summary` + a `progress_bar(verb=…)` param.

## Related Code Files
- **Modify:** `README.md`, `README.vi.md`, `CLAUDE.md`
- (No code changes in this phase.)

## Implementation Steps
1. Read current input-type + usage sections in `README.md` to match tone/structure.
2. Add folder input to the input-type overview + a usage example block.
3. Mirror the exact edits into `README.vi.md` (translated).
4. Update `CLAUDE.md`: input-type-fork bullet + artifact-reuse note.
5. Grep both READMEs for any input-type enumeration ("URL, file, YouTube") to ensure none is left stale.
6. (Optional) delegate to `docs-manager`/`docs` skill for the sync + link check.

## Todo List
- [ ] README.md: input-type overview + usage example for folder input
- [ ] README.md: note `--crawl` rejected, fetch-flags N/A, dotfile skip, failure isolation
- [ ] README.vi.md: mirrored + translated edits
- [ ] CLAUDE.md: input-type-fork bullet for `folder.convert_folder`
- [ ] CLAUDE.md: artifact reuse note for `folder.py` (`artifacts.py` reused; `urls.build_path_map` NOT used — `slugs.file_slug` + local dedup instead)
- [ ] CLAUDE.md/README: folder UI mirrors crawl via `ui.py` (progress bar + summary + hint); note `ui.py` `folder_summary` + `progress_bar(verb=)` additions
- [ ] Grep-verify no stale "URL/file/YouTube" enumeration remains

## Success Criteria
- Both READMEs describe folder input identically (EN canonical, VI mirror), incl. a runnable example.
- CLAUDE.md architecture section reflects the new branch and the reuse of `artifacts.py` (not `urls.build_path_map`).
- No remaining doc enumeration omits folder input.

## Risk Assessment
- **Translation drift** between READMEs — mitigate by editing both in one pass and diff-checking structure.
- Low technical risk (docs only).

## Security Considerations
- Ensure examples show local-path `source_url` behavior; do not document auth flags as applicable to folder mode (they aren't), avoiding user confusion about secrets in a no-egress path.

## Next Steps
- Feature complete: run full suite + coverage, then hand off for `code-reviewer`.
