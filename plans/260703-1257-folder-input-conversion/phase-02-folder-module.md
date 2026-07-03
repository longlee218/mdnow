# Phase 02 — `folder.py` batch-convert module

## Context Links
- `mdnow/crawler.py` (role model: two-pass, per-item isolation, artifact emission)
- `mdnow/convert.py` (`from_path`, `RemoteBlocked(RuntimeError)`)
- `mdnow/slugs.py` (`file_slug(Path) -> str`) — reused for leaf filenames (see correction below)
- `mdnow/writer.py` (`write` — nested mkdir + versioning)
- `mdnow/artifacts.py` (`build_llms_txt`/`build_llms_full`/`build_manifest`)
- `mdnow/extractor.py` (`Extracted`: `markdown`, `title`, `published_date`)
- `tests/test_crawler.py` (fake-fetcher / monkeypatch style to mirror)

## Overview
- **Priority:** P2 (core of the feature)
- **Status:** ✅ done
- **Description:** New module `folder.py` that walks a directory, converts each
  file via `convert.from_path`, writes markdown via `writer.write`, and emits the
  three crawl-style artifacts — all by reusing existing seams, no new path/write/
  artifact logic.

## Key Insights
- **Mirror `crawler.crawl_site`'s contract exactly:** signature returns `(ok, failed)`; per-item `try/except (RuntimeError, ValueError)` isolates failures; artifacts emitted after the write loop.
- **`RemoteBlocked` is a `RuntimeError` subclass** (confirmed in `convert.py:45`), so audio/video without `--allow-remote` surfaces as a normal per-file failure line — no special-casing needed.
- **CORRECTED: do NOT reuse `urls.build_path_map`.** It was built for URL paths and slugifies the *whole* final path segment incl. the extension dot: `build_path_map(['guide/setup.pdf'])` → `guide/setup-pdf.md` — it keeps the extension as a slugified suffix (`-pdf`) instead of dropping it. That's wrong for local files. The **existing** `slugs.file_slug(Path('setup.pdf'))` → `setup` already does the right thing (uses `Path.stem`, drops the extension) — it's the same helper `runner._convert_file` already uses for single-file conversion output naming. Folder mode reuses `file_slug`, not `build_path_map`.
- **Path mapping mechanism (local, ~10-15 lines, no new subsystem):** for each successfully-converted file's relpath, split into `parent` (POSIX dir components, kept as-is — user's own local directory names, not attacker-controlled, no slugify needed) and `leaf = file_slug(Path(relpath).name) + ".md"`. Track a `set[str]` of used `parent/leaf` full relpaths; on a genuine collision (e.g. `Report.pdf` and `report.docx` in the same dir both slug to `report`), disambiguate the second (and later) file by appending a short deterministic suffix: `hashlib.sha1(original_relpath.encode()).hexdigest()[:6]` (mirrors the spirit of `urls._short()`, but implemented **locally in `folder.py`** — `urls._short` is a private helper of that module and must not be imported). E.g. second file becomes `report-a1b2c3.md`.
- **Determinism:** sort collected relpaths (POSIX strings) before mapping/writing so artifacts and collision suffixes are stable across runs.
- No `canonical()` involved — that's URL-only; folder mode keys everything off the relative POSIX path string.

## Requirements
- **Functional:**
  - `convert_folder(root, out, allow_remote, echo, *, progress=None) -> tuple[int,int]`. `progress` is an optional `Callable[[int, int, str], None]` mirroring `crawl_site`'s `progress=` param — called `advance(done, total, label)` per processed file so the CLI's `ui.progress_bar("converting")` can render a live bar. `None` → no progress (e.g. tests).
  - Recursively walk `root.rglob("*")`, files only.
  - Skip any path where **any** component starts with `.` (dotfiles/dotdirs: `.git`, `.DS_Store`, `.venv`, …).
  - `echo(f"Found {total} file(s) to convert")` once before the loop (mirrors crawl's `Discovered N page(s)` note; keeps the plain "Found" substring on non-tty).
  - Per file: `convert.from_path(root / relpath, allow_remote=allow_remote)`; on `(RuntimeError, ValueError)` record `(relpath, str(exc))` and continue. Call `progress(i, total, relpath)` after each file (converted OR failed), like crawl advances after each URL.
  - **No per-file success line** — batch mode stays quiet like crawl; the progress bar + final summary carry the outcome (only failures echo, via `ui.note`).
  - Map successful relpaths to output paths via `file_slug` + local dedup (see Key Insights — parent dirs kept as-is, leaf = `file_slug(name) + ".md"`, sha1[:6] suffix on collision); write each with `writer.write(out/rel, source_url=str(root/relpath), title=…, published_date=…, fetched_date=today, body=extracted.markdown)`.
  - Build `rendered` list of `{title, source_url, local_path, body}` per success.
  - Emit `llms.txt`, `llms-full.txt`, `manifest.json` into `out` using `host=root.name`, `generated_from=str(root)`, `site_summary=f"Documentation converted from {host}"`.
  - `echo(f"  skipped {relpath}: {reason}")` per failure; return `(len(rendered), len(failures))`.
  - Empty folder → writes empty artifacts, returns `(0, 0)`.
- **Non-functional:** module < 200 lines; network-free; no new slug/write/artifact logic; deterministic ordering.

## Architecture
Single module, one public function, thin private helpers.

```
convert_folder(root, out, allow_remote, echo, *, progress=None):
  relpaths = sorted( POSIX relpath for f in root.rglob("*")
                     if f.is_file() and no part startswith "." )
  total = len(relpaths); echo(f"Found {total} file(s) to convert")
  extracted_by_rel = {}          # relpath -> Extracted
  failures = []
  for i, rel in enumerate(relpaths, 1):
      try:    extracted_by_rel[rel] = convert.from_path(root/rel, allow_remote=allow_remote)
      except (RuntimeError, ValueError) as exc: failures.append((rel, str(exc)))
      if progress is not None: progress(i, total, rel)
  path_map = _map_paths(list(extracted_by_rel))          # relpath -> out .md relpath (local helper, below)
  today = date.today().isoformat()
  rendered = []
  for rel, ex in extracted_by_rel.items():
      local = path_map[rel]; src = str(root/rel)
      write(out/local, src, ex.title, ex.published_date, today, ex.markdown)
      rendered.append({"title": ex.title, "source_url": src, "local_path": local, "body": ex.markdown})
  host = root.name; summary = f"Documentation converted from {host}"
  (out/"llms.txt").write_text(artifacts.build_llms_txt(host, summary, rendered), "utf-8")
  (out/"llms-full.txt").write_text(artifacts.build_llms_full(host, summary, rendered), "utf-8")
  (out/"manifest.json").write_text(artifacts.build_manifest(host, str(root), rendered), "utf-8")
  for rel, err in failures: echo(f"  skipped {rel}: {err}")
  return len(rendered), len(failures)
```

```
_map_paths(relpaths: list[str]) -> dict[str, str]:      # local helper — NOT urls.build_path_map
  mapping = {}; used = set()
  for rel in relpaths:                                   # iterate in sorted order for determinism
      p = PurePosixPath(rel)
      leaf = file_slug(Path(p.name)) + ".md"
      candidate = str(p.parent / leaf) if p.parent != PurePosixPath(".") else leaf
      if candidate in used:
          suffix = hashlib.sha1(rel.encode("utf-8")).hexdigest()[:6]
          candidate = f"{candidate[:-3]}-{suffix}.md"
      used.add(candidate)
      mapping[rel] = candidate
  return mapping
```

- **Dotfile filter helper:** `_is_hidden(rel: Path) -> bool` = `any(part.startswith(".") for part in rel.parts)`.
- Use `Path.as_posix()` for relpath strings (Windows-safe, deterministic).
- `manifest`/`build_manifest` takes `(host, generated_from, pages)` → pass `str(root)` as the `generated_from`/`start_url` arg.
- `_map_paths` is a private helper local to `folder.py` — it reuses `slugs.file_slug` (existing, imported) but implements the parent/leaf split and sha1 dedup itself; it does **not** import `urls.build_path_map` or `urls._short`.

## Related Code Files
- **Create:** `mdnow/folder.py`
- **Create:** `tests/test_folder.py`
- **Reuse (do NOT modify):** `convert.py`, `slugs.py` (`file_slug`), `writer.py`, `artifacts.py`, `extractor.py`
- **Consume (added in Phase 03):** the `progress` callback is supplied by `cli.py` via `ui.progress_bar("converting")`; `folder.py` itself only *calls* it, never imports `ui` (keeps the module presentation-agnostic, exactly like `crawler.py`).
- **Not used:** `urls.build_path_map` / `urls._short` (wrong tool for local filenames — see Key Insights)

## Implementation Steps
1. (RED) Write `tests/test_folder.py` covering the cases in Success Criteria; stub `convert.from_path` via `monkeypatch` to return `Extracted(...)` per path (avoid real markitdown), and raise for the "bad file" case. Mirror `tests/test_crawler.py` monkeypatch style.
2. Run → fail (`folder` undefined).
3. (GREEN) Implement `mdnow/folder.py` per Architecture.
4. Run `tests/test_folder.py` → pass.
5. `python -m compileall -q mdnow`; full suite + coverage check.

## Todo List
- [ ] Write `tests/test_folder.py` (RED): nested tree, isolated failure, dotfile/dotdir skip, leaf-slug collision (sha1 suffix), empty folder, artifact contents/fields, `progress` callback invoked once per file with `(i, total, rel)`
- [ ] Implement `mdnow/folder.py` (GREEN), incl. local `_map_paths` helper (file_slug + sha1 dedup)
- [ ] `_is_hidden` skips dotfiles/dotdirs
- [ ] Artifacts written with `host=root.name`, `generated_from=str(root)`
- [ ] Module < 200 lines; compileall clean; coverage held

## Success Criteria
- Nested dir (`a.md`, `sub/b.pdf`) → both converted; correct `out/a.md`, `out/sub/b.md` (extension stripped via `file_slug`, parent dirs preserved); `(2,0)`.
- One unconvertible file → recorded as failure, others still written; run not aborted; skip line echoed.
- Dotfiles/dotdirs (`.git/x`, `.DS_Store`) never converted.
- Collision (two files in the same output dir whose leaf slugs match, e.g. `Report.pdf` + `report.docx` → both `report`) → two distinct `.md` outputs are produced: one clean stem (`report.md`) and one with a disambiguating `-<sha1[:6]>` suffix (`report-<hash6>.md`); test asserts distinctness and suffix presence without hardcoding the exact hash.
- Empty folder → `(0,0)`, artifacts present (empty page list).
- `llms.txt`/`llms-full.txt`/`manifest.json` contain expected host/summary/page entries and manifest `generated_from == str(root)`, `page_count` correct.

## Risk Assessment
- **Wrong helper reused for path mapping:** initial draft proposed reusing `urls.build_path_map`, which mangles extensions (`setup.pdf` → `setup-pdf.md`) since it's designed for URL paths, not filenames. Corrected to `slugs.file_slug` + a small local dedup helper in `folder.py` (see Key Insights) — `setup.pdf` → `setup.md` as expected.
- **Symlink loops / huge trees:** out of scope (personal, low-volume tool — YAGNI). `rglob` follows dirs but not symlinked dirs by default on modern Python; acceptable.
- **Same source file mtime → idempotency:** `writer.write` content-hash handles re-runs; no action needed.

## Security Considerations
- `source_url` here is a **local path string**, not a secret; safe to embed in frontmatter/artifacts (consistent with existing single-file behavior which writes `str(path)`).
- No auth material touches this path (folder mode has no fetch tier).
- Audio/video egress stays gated: without `--allow-remote`, `RemoteBlocked` → failure line, no network call.

## Next Steps
- Phase 03 wires `convert_folder` into `cli.main`.
