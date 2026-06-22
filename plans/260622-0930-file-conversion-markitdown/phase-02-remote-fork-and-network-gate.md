# Phase 2 — Remote content-type fork + `--allow-remote` gate + YouTube branch

**Priority:** High · **Status:** done · **Depends:** Phase 1

Add remote-file support (`mdnow https://x.com/report.pdf`) and the network-egress gate. Reuses the existing fetch → bytes seam; the new convert module from Phase 1 does the work.

## Key Insights (from scout)

- `_acquire` **currently escalates non-HTML to the browser**: `if not is_html(result.content_type): return _render(url)`. This is the exact interception point — non-HTML bytes must go to **markitdown**, not Camoufox. This is a behavior change to an existing path; a regression test must prove a PDF URL no longer triggers render.
- `FetchResult` already carries `content: bytes` + `content_type` + final `url`. markitdown converts a stream via `convert_stream(BytesIO(bytes), stream_info=StreamInfo(...))` — **research must confirm the exact signature**; fallback is to write bytes to a `tempfile` and `convert()` the path.
- **YouTube is NOT free:** a YouTube URL fetches as HTML and would go to trafilatura. Supporting markitdown's YouTube converter needs an explicit `youtube.com`/`youtu.be` host branch that hands the **URL** (not bytes) to markitdown.
- Audio egress happens inside markitdown's transcription regardless of how we obtained the bytes → the gate is by **format/extension**, checked before calling convert.

## Requirements

- `--allow-remote` flag (default `False`) on `mdnow`. Threaded into the convert path.
- Content-type fork in `_acquire`: non-HTML + `[docs]` available → `convert.from_bytes(result.content, result.url, content_type)` → `Extracted`; return `(result, extracted)` into the unchanged `_convert_single` write path.
- Network gate: audio formats (`.mp3/.wav/.m4a/...`) and YouTube URLs are **refused** unless `--allow-remote`, with a message naming the flag.
- YouTube host branch in `cli.main`: detect `youtube.com`/`youtu.be` → (gated) `convert.from_url(url)`.
- Fallback when `[docs]` not installed: keep today's behavior (escalate to render) so nothing regresses for static-only users.

## Architecture

```
URL path:
  main → discover → (none)
       → youtube host?  ──yes──▶ gate → convert.from_url(url)        # NEW
       → _convert_single → _acquire:
             static fetch → is_html(ct)?
                 ├─ yes → trafilatura            (UNCHANGED)
                 └─ no  → [docs]? gate(ct/ext) → convert.from_bytes(...)   # NEW
                          else → _render(url)    (fallback, unchanged)
```

`convert.py` additions (pseudocode):

```python
_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}

def from_bytes(data: bytes, url: str, content_type: str, *, allow_remote: bool) -> Extracted:
    ext = _ext_from(url, content_type)            # sniff URL path ext, fall back to ctype map
    _guard_remote(ext, allow_remote)              # raise if audio & not allow_remote
    md = _markitdown().convert_stream(BytesIO(data), stream_info=StreamInfo(extension=ext, mimetype=content_type or None))
    ...wrap into Extracted...

def from_url(url: str, *, allow_remote: bool) -> Extracted:   # YouTube
    _require_remote(allow_remote, "YouTube")
    res = _markitdown().convert(url); ...
```

Content-type ambiguity (server sends `application/octet-stream` for a PDF): prefer the **URL path extension**; fall back to a small mimetype→ext map; if still unknown, let markitdown sniff (it accepts a bare stream).

## Related Code Files

- **Modify:** `mdnow/cli.py` (`--allow-remote` option; YouTube host branch; thread `allow_remote` into `_acquire`/`_convert_single`), `mdnow/convert.py` (add `from_bytes`, `from_url`, `_ext_from`, `_guard_remote`)
- **Reuse unchanged:** `is_html`, `write`, `Extracted`

## Implementation Steps

1. Research: confirm `convert_stream` + `StreamInfo` signature against the installed markitdown; decide stream vs tempfile. Note default in convert.py docstring.
2. Add `from_bytes`/`from_url`/`_ext_from`/`_guard_remote` to `convert.py`.
3. Add `--allow-remote` to `main`; thread through `_convert_single`/`_acquire`.
4. Intercept the non-HTML branch in `_acquire` → markitdown (guard `[docs]` presence; else fall back to `_render`).
5. Add YouTube host branch in `main` (before fetch), gated.
6. compile gate; smoke-test a real remote PDF URL and a gated `.mp3` URL (refused without flag).

## Todo List

- [x] `--allow-remote` flag wired through
- [x] `convert.from_bytes` (stream/tempfile) + ext sniffing
- [x] `_acquire` routes non-HTML → markitdown (not render); render kept as no-`[docs]` fallback
- [x] audio + YouTube refused without `--allow-remote`, work with it
- [x] compile clean; remote-PDF smoke test converts via markitdown

## Success Criteria

`mdnow https://<host>/file.pdf` converts via markitdown and writes a versioned `.md`. A `.mp3` URL or YouTube URL is refused without `--allow-remote` and converted with it. Existing HTML/static/render paths unchanged (Phase 3 regression tests confirm).

## Risks

- **Regression in `_acquire`:** the non-HTML→render escalation is load-bearing for JS SPAs served with odd content-types. Mitigation: only divert to markitdown when `[docs]` is installed AND the content-type/ext looks like a real document; otherwise keep render. Cover with a test.
- `convert_stream` signature drift across versions → tempfile fallback path documented.
