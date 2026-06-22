# Phase 1 — convert.py + local-file input fork + `[docs]` extra

**Priority:** High · **Status:** done · **Depends:** none

Deliver local-file conversion end-to-end: `mdnow ./report.pdf -o out/` → `out/report.md` with full frontmatter. This is the primary use case and stands alone without the remote work.

## Key Insights (from scout)

- `cli.main` runs the **discovery seam first**, then crawl, then `_convert_single`. The local-file fork must sit at the **very top of `main`**, before `discover()` — a local file skips fetch/discover entirely.
- markitdown's `result.text_content` (markdown) + `result.title` map 1:1 onto the existing `Extracted(markdown, title, published_date)` dataclass → wrapping lets us reuse the whole `write()` path with zero new write logic.
- `_slug(title, url)` uses `urlparse` — wrong for a bare filesystem path. Need a small filename-stem slug helper (keep `canonical()` untouched, per D8).
- markitdown requires Python 3.10+; project is `requires-python = ">=3.11"` → compatible, no bump needed.

## Requirements

- New module `mdnow/convert.py` wrapping `MarkItDown(enable_plugins=False)`. Lazy import (so static-only users without `[docs]` are unaffected); raise a clear `RuntimeError` with the install hint if markitdown is missing (mirror `CamoufoxFetcher._ensure`).
- `pyproject.toml`: add `docs = ["markitdown[all]>=0.1"]` optional extra. (Verify exact min version that the env resolves in the research step; pin conservatively.)
- New CLI branch: if the positional arg is a **local path that exists**, route to a `_convert_file` flow; else fall through to the existing URL funnel.
- `--crawl` + local file → `typer.Exit(1)` with a clear message (D7).

## Architecture

```
main(arg, ...)
  ├─ is_local_file(arg)?  ──yes──▶ _convert_file(path, out, allow_remote)   # NEW, skips discover/fetch
  │                                   convert.from_path(path) → Extracted
  │                                   write(...) with source_url=str(path)
  └─ no ──▶ [existing] discover → crawl → _convert_single                    # UNCHANGED
```

`convert.py` shape (pseudocode, <200 lines):

```python
def _markitdown():
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError("markitdown not installed. Run: pip install 'mdnow[docs]'") from exc
    return MarkItDown(enable_plugins=False)

def from_path(path: Path) -> Extracted:
    res = _markitdown().convert(str(path))
    md = (res.text_content or "").strip()
    if not md:
        raise ValueError(f"No content extracted from {path}")
    return Extracted(markdown=md, title=res.title or None, published_date=None)
```

Input detection (cli.py): treat as local file when the arg has **no URL scheme** (`urlparse(arg).scheme not in ("http","https")`) **and** `Path(arg).is_file()`. Anything with an http(s) scheme is always a URL (Phase 2 handles remote files).

Filename slug helper (cli.py): `_file_slug(path) -> _slugify(path.stem) or "file"` — reuses existing `_slugify`.

## Related Code Files

- **Create:** `mdnow/convert.py`
- **Modify:** `mdnow/cli.py` (import; `is_local_file` check + `_convert_file`; `--crawl`+file guard; `_file_slug`), `pyproject.toml` (`[docs]` extra)
- **Reuse unchanged:** `extractor.Extracted`, `writer.write`, `frontmatter.build`, `outline`

## Implementation Steps

1. Add `docs = ["markitdown[all]>=0.1"]` to `[project.optional-dependencies]`; install into `.venv`. Verify `markitdown --version` and `from markitdown import MarkItDown`.
2. Write `mdnow/convert.py` with lazy `_markitdown()` + `from_path()` returning `Extracted`.
3. In `cli.main`: add `_is_local_file(arg)` and branch at top → `_convert_file(...)`; guard `--crawl` + file.
4. Add `_convert_file(path, out, allow_remote)` mirroring `_convert_single` (echo, write, status line), `source_url=str(path)`, slug via `_file_slug`.
5. `compileall` gate; smoke-test on a tiny local fixture (a small `.docx`/`.csv`/`.json`).

## Todo List

- [x] `[docs]` extra added + installed; markitdown importable
- [x] `convert.py` created (lazy import, `from_path` → `Extracted`)
- [x] local-file fork + `_convert_file` + `_file_slug` in cli.py
- [x] `--crawl` + file → clear error
- [x] compile clean; smoke-test a real local fixture writes a `.md` with frontmatter

## Success Criteria

`mdnow ./fixture.csv -o out/` writes `out/fixture.md` with frontmatter (token_estimate/summary/content_hash present). Re-run → status `unchanged`. Without `[docs]`, the branch raises the clear install-hint error. No existing website behavior touched.

## Risks

- markitdown `convert()` arg form / `result` attribute names may differ by version → verify in step 1 against the installed build before wiring.
- Heavy `[all]` deps may pull native wheels (onnxruntime) → acceptable (opt-in extra); note install size in README (Phase 3).
