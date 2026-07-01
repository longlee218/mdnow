# Phase 01 — Render-aware discovery (Part B)

**Priority:** HIGH (this is the change that actually unblocks a 100-page SPA crawl)
**Status:** pending
**File:** `mdnow/crawler.py`

## Problem

`discover_urls` enumerates pages via static `sitemap_search` + `focused_crawler`. On a JS SPA both come back empty (≤1 URL) because nav links are client-rendered. Even after Part 2's per-page render, the crawl would only ever see the start URL.

## Design

Add an optional renderer + a `render` flag to `discover_urls`. After static discovery, if `renderer` is available AND (`render` forced OR `len(found) <= 1`), render the start page and harvest same-host doc links from the DOM, then merge before sort/dedup/cap.

### New signature

```python
def discover_urls(
    start_url: str,
    max_pages: int,
    crawl_all: bool,
    *,
    render: bool = False,
    renderer: Fetcher | None = None,
) -> list[str]:
```

### New helper (same module)

```python
# asset/non-page extensions to drop from harvested links
_ASSET_RE = re.compile(r"\.(png|jpe?g|gif|svg|ico|webp|css|js|json|xml|pdf|zip|woff2?)$", re.I)
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']')

def _render_discover(start_url: str, host: str, renderer: Fetcher) -> list[str]:
    """Render the start page and harvest same-host page links from the DOM.

    Returns [] (and lets the caller keep static results) if the renderer is
    unavailable — camoufox not installed surfaces as RuntimeError on fetch().
    """
    try:
        r = renderer.fetch(start_url)
    except RuntimeError:
        return []
    html = r.content.decode("utf-8", "ignore")
    out: list[str] = []
    for href in _HREF_RE.findall(html):
        absu = urljoin(r.url, href.split("#")[0])      # resolve + drop fragment
        if not absu.startswith(("http://", "https://")):
            continue
        if same_host(absu, host) and not _ASSET_RE.search(urlsplit(absu).path):
            out.append(absu)
    return out
```

### Integration in `discover_urls`

```python
host = urlsplit(start_url).netloc.lower()
found = [...static sitemap/focused_crawler as today...]

if renderer is not None and (render or len(found) <= 1):
    found = found + _render_discover(start_url, host, renderer)

# existing: sorted(found, key=canonical) → start-first dedup → cap
```

Dedup/sort/cap logic is unchanged — it already canonicalizes and de-duplicates, so merging the rendered links in is safe (the homepage's own link to `/` collapses with the start URL).

## Notes / edge cases

- `urljoin` + `split("#")[0]` drops in-page anchors (`/#installation`) but keeps the bare route. After `canonical()` these collapse to the same path — harmless.
- One render only (the start page). We do **not** recursively render every page for *link discovery* — that would be a full JS BFS (out of scope, YAGNI). For nestjs the sidebar nav is global, so one render exposes the whole doc tree (139 links confirmed). Document this limitation: sites that paginate links across pages won't be fully enumerated without `--all` + deeper crawl (future work).
- `same_host` / `canonical` require absolute URLs → `urljoin` first (done).

## Todo

- [ ] Add `_ASSET_RE`, `_HREF_RE`, `_render_discover` to `crawler.py`
- [ ] Extend `discover_urls` signature + merge logic
- [ ] `from urllib.parse import urljoin, urlsplit` (urlsplit already imported)
- [ ] Keep module < 200 lines (currently 114; this adds ~20)

## Success criteria

- With a fake renderer returning the 167KB nestjs HTML, `discover_urls` returns >100 same-host doc URLs.
- With `renderer=None`, behavior is byte-identical to today (static only).
- Static-rich sites (sitemap present, >1 URL) skip rendering entirely — no perf regression.
