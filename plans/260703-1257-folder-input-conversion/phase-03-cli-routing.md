# Phase 03 — CLI routing branch + Rich UI

## Context Links
- `mdnow/cli.py` (post-sync: imports `ui`; `is_local_file` branch uses `ui.error`; `--crawl` branch uses `ui.step`/`ui.progress_bar`/`ui.crawl_summary`/`ui.hint`)
- `mdnow/ui.py` (Rich seam added on `main` 7ff2dcf — `step`/`note`/`hint`/`error`/`crawl_summary`/`progress_bar`)
- `mdnow/folder.py` (Phase 02 — `convert_folder(..., *, progress=None)`)
- `mdnow/inputs.py` `is_local_dir` (Phase 01)
- `tests/test_cli_main.py` (local-file routing tests) + `tests/test_ui.py` (`_capture` non-tty helper) — patterns to mirror

## Overview
- **Priority:** P2
- **Status:** ✅ done
- **Description:** Route a directory argument to `folder.convert_folder` with a
  crawl-style Rich UI (progress bar + colored summary + hint), placed before the
  URL-only branches. Adds two small additive helpers to `ui.py`.

## Key Insights
- The folder branch **must precede** discovery/crawl/single-page (those are URL-only). Place it adjacent to the `is_local_file` branch — both are local-path forks. `is_local_file`/`is_local_dir` are mutually exclusive, so their relative order is irrelevant; only "before the URL funnel" matters.
- **All output goes through the `ui.py` seam — never `typer.echo/secho`** (repo convention since 7ff2dcf). The folder UX is a batch, so it mirrors the `--crawl` UI exactly: `ui.step` header → `ui.progress_bar` → `ui.note` failures → colored summary → `ui.hint`.
- `--crawl` + folder → `ui.error(...)` + `raise typer.Exit(1)`, same wording/style as the local-file guard (`ui.error("--crawl is not valid for a local file (single file only).")`). Folder mode always emits the index, so `--crawl` is redundant.
- `--render`, `--no-llms`, `-H`/`--cookie-file` are parsed but **silently unused** for folder input (no fetch tier) — matches today's local-file precedent.
- `cli.py` already imports `ui` and `folder` needs adding to `from . import …`; add `is_local_dir` to the `from .inputs import` line.

## ui.py additions (additive, backward-compatible)
1. **`progress_bar(verb: str = "crawling")`** — the current hardcoded `TextColumn("[muted]crawling[/muted]")` becomes `TextColumn(f"[muted]{verb}[/muted]")`. `verb` is a controlled internal literal (`"converting"`), so markup stays safe. Crawl's `ui.progress_bar()` call is unchanged (default keeps `"crawling"`).
2. **`folder_summary(ok, failed, out)`** — `"✓/! Done: N file(s) converted, M failed → out"` (✓ green when `failed==0`, else `!` yellow). Extract the shared body of the existing `crawl_summary` into a private `_done_summary(ok, failed, out, unit)`; `crawl_summary` becomes `_done_summary(ok, failed, out, "page(s) written")` and `folder_summary` is `_done_summary(ok, failed, out, "file(s) converted")`. Keeps `crawl_summary`'s public signature + existing test green (DRY, no duplication).

## Requirements
- Functional:
  - `ui.py`: add `progress_bar(verb=...)` param + `folder_summary` + private `_done_summary` (crawl_summary refactored to delegate).
  - `cli.py`: if `is_local_dir(url)`:
    - if `crawl`: `ui.error("--crawl is not valid for a local folder (folder mode always builds an index).")` then `raise typer.Exit(1)`.
    - else: `out.mkdir(parents=True, exist_ok=True)`; `ui.step("Converting", str(url))`; run `convert_folder` inside `ui.progress_bar("converting")`, passing `ui.note` as `echo` and `advance` as `progress`; then `ui.folder_summary(ok, failed, str(out))` and `ui.hint(f"Start with {out/'manifest.json'} (index), then open the files you need")`; `return`.
- Non-functional: `cli.py` < 200 lines; `ui.py` < 200 lines (currently 120); no behavior change to existing branches; `crawl_summary` API + test unchanged.

## Architecture
`ui.py` refactor:
```python
def _done_summary(ok, failed, out, unit):
    mark, style = ("✓", "ok") if failed == 0 else ("!", "warn")
    _line(_out, Text.assemble(
        (f"{mark} Done: ", style), f"{ok} {unit}, {failed} failed ",
        ("→ ", "muted"), (out, "muted")))

def crawl_summary(ok, failed, out):  _done_summary(ok, failed, out, "page(s) written")
def folder_summary(ok, failed, out): _done_summary(ok, failed, out, "file(s) converted")

def progress_bar(verb: str = "crawling"):
    prog = Progress(TextColumn(f"[muted]{verb}[/muted]"), BarColumn(), MofNCompleteColumn(),
                    TextColumn("{task.description}", markup=False), console=_out, transient=True)
    ...  # body unchanged
```

`cli.py` branch (immediately after the `is_local_file` block):
```python
if is_local_dir(url):
    if crawl:
        ui.error("--crawl is not valid for a local folder (folder mode always builds an index).")
        raise typer.Exit(1)
    out.mkdir(parents=True, exist_ok=True)
    ui.step("Converting", str(url))
    with ui.progress_bar("converting") as advance:
        ok, failed = folder.convert_folder(Path(url), out, allow_remote, ui.note, progress=advance)
    ui.folder_summary(ok, failed, str(out))
    ui.hint(f"Start with {out / 'manifest.json'} (index), then open the files you need")
    return
```
Imports: `from . import auth, commands, doctor, folder, ui` and
`from .inputs import is_local_dir, is_local_file, is_youtube`.

## Related Code Files
- **Modify:** `mdnow/ui.py` (add `folder_summary`, `_done_summary`, `progress_bar(verb=)`)
- **Modify:** `mdnow/cli.py` (add import + branch)
- **Modify:** `tests/test_ui.py` (folder_summary + progress verb tests)
- **Modify:** `tests/test_cli_main.py` (folder-routing tests)

## Implementation Steps
1. (RED) `tests/test_ui.py`: `test_folder_summary_substrings` (uses `_capture`; assert `"file(s) converted"`, ok/failed counts, out path present; ✓ vs ! by failed count); `test_progress_bar_accepts_verb` (`ui.progress_bar("converting")` context enters/advances without error).
2. (RED) `tests/test_cli_main.py`:
   - `test_folder_routes_to_convert_folder`: `tmp_path` dir, monkeypatch `folder.convert_folder` → `(2,0)`; assert called with `Path(dir)`, `out`, `allow_remote`, and a `progress` kwarg; exit 0; `"Done:"` + `"file(s) converted"` in output. `_no_discover(monkeypatch)` so discovery never runs.
   - `test_folder_with_crawl_errors`: dir + `--crawl` → exit 1, error text; `convert_folder` NOT called.
   - `test_folder_ignores_render_and_no_llms`: dir + `--render --no-llms` still routes to `convert_folder`.
3. Run → fail. (GREEN) Edit `ui.py` then `cli.py`.
4. Run tests → pass; `compileall`; confirm both modules < 200 lines.

## Todo List
- [ ] `tests/test_ui.py`: folder_summary + progress-verb tests (RED)
- [ ] `tests/test_cli_main.py`: folder-routing tests (RED)
- [ ] `ui.py`: `_done_summary` + `folder_summary` + `crawl_summary` delegate + `progress_bar(verb=)`
- [ ] `cli.py`: import `folder`/`is_local_dir` + folder branch (crawl-guard, step, progress bar, summary, hint)
- [ ] Tests pass (GREEN); `cli.py` & `ui.py` < 200 lines; compileall clean

## Success Criteria
- Directory arg routes to `folder.convert_folder` with `progress=`; renders `ui.step`, a live bar, `ui.folder_summary` (`Done: N file(s) converted, M failed → out`), and the manifest `ui.hint`; exit 0.
- Directory + `--crawl` → exit 1 with the guard message via `ui.error`.
- `--render`/`--no-llms`/`-H`/`--cookie-file` don't alter folder routing.
- `crawl_summary` output/test unchanged; non-tty output keeps plain `Done`/`Converting`/`skipped` substrings.
- Existing CLI + UI tests still pass.

## Risk Assessment
- **Ordering bug:** if placed after discovery, a dir arg could hit URL logic. Mitigation: place with the local-file fork (before `is_youtube`/discovery); covered by `_no_discover` in tests.
- Low blast radius; single additive branch.

## Security Considerations
- Auth headers/cookies are parsed earlier but unused here — never reach folder writes, so no secret can leak into local-path artifacts.

## Next Steps
- Phase 04 documents the new input type across README ×2 and CLAUDE.md.
