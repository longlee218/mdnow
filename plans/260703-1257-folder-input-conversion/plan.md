---
title: "Folder input: batch-convert a local directory to markdown"
description: "mdnow accepts a local folder and recursively converts every file to markdown + artifacts"
status: completed
priority: P2
effort: 5h
branch: feat/add-folder-input
tags: [feature, cli, convert, folder]
created: 2026-07-03
---

# Folder Input Conversion

Add a **third local input type** to `mdnow`: pass a directory and it recursively
converts every file inside to markdown, then emits crawl-style artifacts
(`llms.txt` / `llms-full.txt` / `manifest.json`) — alongside the existing
URL / single-file / YouTube inputs.

Design is pre-approved (see task spec). This plan implements it verbatim.
Founding principle: **reuse existing seams, write no new path/write/artifact
logic** — `folder.py` mirrors `crawler.py`'s role over a local directory.

## Key dependencies (all existing, reused unchanged)
- `convert.from_path()` — per-file file→markdown (markitdown); `RemoteBlocked` is a `RuntimeError` subclass.
- `slugs.file_slug()` — existing per-file stem slug (used by single-file conversion output naming); reused for folder-mode leaf names. `folder.py` does **not** reuse `urls.build_path_map` (see correction note below).
- `writer.write()` — nested-dir mkdir + content-hash versioning/idempotency.
- `artifacts.build_llms_txt / build_llms_full / build_manifest` — accept generic page dicts.
- `inputs.is_local_file` / `cli.main` input-type fork — the routing pattern to mirror.
- `ui.py` (Rich presentation seam, added on `main` 7ff2dcf) — folder UX mirrors crawl: `ui.step` (WIP header), `ui.progress_bar` (live bar), `ui.note` (skip/failure lines), a `folder_summary` (colored Done line), `ui.hint` (manifest next-step). No direct `typer.echo/secho` anywhere.

## UI (mirrors `--crawl`, built on `ui.py`)
Folder mode is a multi-item batch like crawl, so it uses the **same UI shape**:
`ui.step("Converting", <dir>)` → live `ui.progress_bar("converting")` advancing
per file → per-failure `ui.note("skipped …")` → `ui.folder_summary(ok, failed, out)`
(✓ green / ! yellow) → `ui.hint("Start with …/manifest.json …")`. Non-tty degrades
to plain text (bar renders nothing; `Converting`/`Found`/`skipped`/`Done`
substrings preserved for scripts).

Two **additive, backward-compatible** `ui.py` changes this feature needs:
- `progress_bar(verb: str = "crawling")` — parametrize the hardcoded label so
  folder shows `converting`; crawl's `ui.progress_bar()` call stays unchanged.
  `verb` is a controlled internal string → markup-safe.
- `folder_summary(ok, failed, out)` → `"Done: N file(s) converted, M failed → out"`.
  DRY via a private `_done_summary(ok, failed, out, unit)`; `crawl_summary`
  becomes a thin wrapper (unit=`"page(s) written"`) so its existing test passes.
`folder.convert_folder` gains an optional `progress=` callback (same signature
shape crawl_site already uses).

## Phases
| # | Phase | Status | Est |
|---|-------|--------|-----|
| 01 | [Input detection: `is_local_dir`](phase-01-input-detection.md) | ✅ done | 0.5h |
| 02 | [`folder.py` batch-convert module](phase-02-folder-module.md) | ✅ done | 2h |
| 03 | [CLI routing + Rich UI](phase-03-cli-routing.md) | ✅ done | 1.5h |
| 04 | [Docs sync (README ×2 + CLAUDE.md)](phase-04-docs-sync.md) | ✅ done | 1h |

Order is dependency-driven: 01 → 02 → 03 → 04. Each phase is TDD (RED→GREEN),
network-free, and must keep every module < 200 lines and coverage ≥ ~88%.

## Outcome (2026-07-03)
Shipped. **170 tests pass, 89% coverage** (folder.py 100%, ui.py 98%). All
modules < 200 lines. Verified end-to-end (nested convert, dotdir/dotfile skip,
`--crawl` guard, audio RemoteBlocked isolation). Code review found one HIGH bug
(**H1**: markitdown's `UnsupportedFormat`/`FileConversion` exceptions subclass
neither `RuntimeError` nor `ValueError`, so an unsupported/empty file crashed the
whole batch) — fixed at the `convert.from_path` seam (normalize
`MarkItDownException` → `ValueError`), which also fixes a latent single-file
crash; guarded by a regression test. Reviewer M2 (`out` inside/equal `root` →
source mutation on re-run) is a **known, user-accepted trade-off** (guard
declined). L3/L4/L5/L7 are cosmetic/note-only; L6 tidied.

## Critical implementation note (corrected — do NOT reuse `urls.build_path_map`)
`urls.build_path_map` slugifies the **whole** last path segment incl. the
extension dot: `guide/setup.pdf` → `guide/setup-pdf.md` — it was designed for
URL paths, not local filenames, and would mangle extensions (`setup-pdf.md`
instead of `setup.md`). The existing single-file conversion path already has
the correct helper for this: `slugs.file_slug(Path.stem)` → `setup` (drops
the extension via `Path.stem`, same convention `runner._convert_file` already
uses). Folder mode reuses **that** helper instead:
- `parent` = the file's POSIX directory components, kept as-is (user's own
  local directory names — not attacker-controlled, no slugify needed).
- `leaf` = `file_slug(Path(relpath).name) + ".md"`.
- Genuine collisions (two files in the same output dir whose leaf slugs
  match, e.g. `Report.pdf` + `report.docx` → both `report`) are disambiguated
  with a small **local** dedup in `folder.py`: track used `parent/leaf`
  relpaths in a `set[str]`; on collision, append a short deterministic
  `-<sha1[:6]>` suffix derived from the file's *original* relpath (spirit of
  `urls._short()`, but implemented locally — `urls._short` is private to that
  module and must not be imported). ~10-15 lines, no new subsystem.

## Definition of done
- `mdnow <dir>` recursively converts files → `out/` with artifacts.
- `mdnow <dir> --crawl` errors, exit 1 (same style as local-file guard).
- Failures are isolated per file; dotfiles/dotdirs skipped; empty folder → (0,0).
- All tests pass, coverage held; README.md + README.vi.md + CLAUDE.md synced.
