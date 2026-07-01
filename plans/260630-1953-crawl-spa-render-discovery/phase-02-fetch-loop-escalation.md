# Phase 02 — Fetch-loop escalation (Part A)

**Priority:** HIGH (fixes the literal `No main content extracted` error per page)
**Status:** pending
**Files:** `mdnow/crawler.py`, `mdnow/cli.py`

## Problem

`crawl_site`'s per-page loop fetches once with the primary fetcher; on `extract()` `ValueError` (empty) or thin content it gives up and logs a skip. Single-page `runner._acquire` instead escalates to Camoufox. Crawl needs the same.

## Design

### `crawl_site` signature

```python
def crawl_site(
    start_url, out, max_pages, crawl_all, fetcher, echo,
    *, render: bool = False, renderer: Fetcher | None = None,
) -> tuple[int, int]:
```

- `fetcher` — primary per-page fetcher (Static normally; Camoufox under `--render`).
- `renderer` — fetcher to escalate to (and to seed Part-1 discovery). `cli` passes a `CamoufoxFetcher()`. May be None in tests / when rendering is intentionally off.
- `render` — forwarded to `discover_urls` (force render-discovery when `--render`).

### Escalation guard

Escalate only when a renderer exists and is a *different* backend than the primary (no point re-rendering with the same fetcher under `--render`):

```python
can_escalate = renderer is not None and renderer is not fetcher
```

### Per-page helper

```python
from .runner import THIN_WORDS   # DRY: single source of the thin threshold

def _fetch_one(fetcher: Fetcher, url: str) -> Page:
    """Fetch+extract one URL. Raises RuntimeError/ValueError on failure."""
    r = fetcher.fetch(url)
    if not is_html(r.content_type):
        raise ValueError(f"non-HTML content ({r.content_type})")
    e = extract(r.content, url=r.url)
    return Page(canonical(r.url), r.url, e.markdown, e.title, e.published_date)
```

> Note: importing `THIN_WORDS` from `runner` creates a `crawler → runner` import. `runner` imports from `crawler`? No — `runner` does **not** import `crawler` (verified). cli imports both. No cycle. If a cycle ever appears, move `THIN_WORDS` to a constants module.

### Loop rewrite

```python
escalated = 0
render_dead = False  # set once if camoufox is unavailable, to stop retrying
for u in urls:
    limiter.wait()
    try:
        page = _fetch_one(fetcher, u)
        thin = len(page.body.split()) < THIN_WORDS
    except (RuntimeError, ValueError):
        page, thin = None, True

    if thin and can_escalate and not render_dead:
        try:
            page = _fetch_one(renderer, u)   # browser launches lazily here
            escalated += 1
        except RuntimeError as exc:
            if "not installed" in str(exc).lower():
                render_dead = True
                echo("  note: install mdnow[render] to auto-recover JS-heavy pages")
        except ValueError:
            pass  # rendered but still no content → genuine empty page

    if page is None:
        failures.append((u, "No main content extracted"))
        continue
    pages.setdefault(page.canon, page)

if escalated:
    echo(f"  rendered {escalated} page(s) that static fetch could not extract")
```

Thin-but-non-None pages: if escalation fails, keep the original thin page (mirror `_acquire`’s "keep the thin static result"). Adjust: when `page` exists and escalation raised, fall through with the original `page` (don't null it). Implementation detail for the coder — preserve the pre-escalation `page` in a temp.

### `cli.py` wiring

Replace the current `fetcher = Camoufox if render else Static` block:

```python
from .fetcher import CamoufoxFetcher, StaticFetcher
if render:
    primary = CamoufoxFetcher(); renderer = primary
else:
    primary = StaticFetcher(); renderer = CamoufoxFetcher()  # free until used
try:
    ok, failed = crawl_site(url, out, max_pages, crawl_all, primary, typer.echo,
                            render=render, renderer=renderer)
finally:
    for f in {primary, renderer}:          # set() dedupes the --render case
        getattr(f, "close", lambda: None)()
```

`CamoufoxFetcher.close()` is a no-op when the browser never launched — safe to always call.

## Todo

- [ ] Add `_fetch_one` helper + import `THIN_WORDS`
- [ ] Rewrite the per-page loop with escalation + `render_dead` guard
- [ ] Thread `render` into `discover_urls(...)` call
- [ ] Update `cli.py` crawl block (primary + renderer + finally close both)
- [ ] `compileall` clean; module < 200 lines

## Success criteria

- Fake primary that returns the 15KB shell + fake renderer returning the 167KB page → page is written (not skipped), `escalated == 1`.
- `renderer=None` → identical to today (skip on failure).
- `--render` (primary is renderer) → no double-fetch (escalation guard off).
