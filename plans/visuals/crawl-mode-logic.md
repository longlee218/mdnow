# Diagram: Crawl Mode Logic

How `mdnow <url> --crawl` turns a website into a tree of markdown files.
Includes the SPA fixes (render-aware discovery + per-page render escalation) and
the open Playwright driver-crash blocker.

## ASCII Version

```
                        mdnow <url> --crawl
                               │
                               ▼
                    ┌─────────────────────┐
                    │  cli.main            │
                    │  input-type fork     │  local file? youtube? → other paths
                    └──────────┬──────────┘
                               │ web URL
                               ▼
            ┌──────────────────────────────────────┐
            │  DISCOVERY GATE  (unless --no-llms)    │
            │  discover(url, crawl=True)             │
            │  → probe llms.txt / llms-full.txt      │
            └───────────┬───────────────┬───────────┘
                 found  │               │ None (e.g. nestjs)
                        ▼               ▼
                 write & RETURN   ┌──────────────────────────┐
                 (crawler skipped)│  build fetchers           │
                                  │  --render: primary=cam    │
                                  │  else: primary=static,    │
                                  │        renderer=cam(lazy) │
                                  └────────────┬─────────────┘
                                               ▼
        ╔══════════════════════════ crawl_site ══════════════════════════╗
        ║                                                                 ║
        ║  STEP 1 — discover_urls                                         ║
        ║  ┌───────────────────────────────────────────────────────┐    ║
        ║  │ sitemap_search ──found?──► filter same-host + robots    │    ║
        ║  │      │ empty                                            │    ║
        ║  │ focused_crawler (static BFS link-follow)                │    ║
        ║  │      │                                                  │    ║
        ║  │ if renderer AND (--render OR found<=1):   ◄── SPA FIX   │    ║
        ║  │      _render_discover → render page, scrape DOM <a>     │    ║
        ║  │      │            (nestjs: 1 → 12/139 links)            │    ║
        ║  │ sort · start-first · dedup · cap at max_pages           │    ║
        ║  └───────────────────────────────────────────────────────┘    ║
        ║                          │  URL set                             ║
        ║                          ▼                                      ║
        ║  STEP 2 — PASS A: fetch + extract each (isolated per page)      ║
        ║  ┌───────────────────────────────────────────────────────┐    ║
        ║  │ for url in urls:                                        │    ║
        ║  │   page = _fetch_one(primary, url)   static → extract    │    ║
        ║  │   thin = words < 50                                     │    ║
        ║  │   if (empty OR thin) AND can_escalate:   ◄── ESC FIX    │    ║
        ║  │        page = _fetch_one(renderer, url)  ⚠ browser here │    ║
        ║  │   None → failures[];  else → pages{canonical}          │    ║
        ║  └───────────────────────────────────────────────────────┘    ║
        ║                          │  pages{}                             ║
        ║                          ▼                                      ║
        ║  STEP 2 — PASS B: map · rewrite · write                         ║
        ║  ┌───────────────────────────────────────────────────────┐    ║
        ║  │ build_path_map(all canonical URLs)   URL → local .md   │    ║
        ║  │ rewrite_links(body, map)  internal+crawled → rel .md   │    ║
        ║  │ write(out/<path>, frontmatter, body)  hash-versioned   │    ║
        ║  └───────────────────────────────────────────────────────┘    ║
        ║                          │                                      ║
        ║  STEP 3 — artifacts:  llms.txt · llms-full.txt · manifest.json  ║
        ╚═════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
                 Done: N written, M failed → out/

  LEGEND
  ◄── SPA FIX / ESC FIX   my changes (discovery render + fetch escalation)
  ⚠ browser here          CamoufoxFetcher launches lazily on first render
  {canonical}             dedup key = canonical() URL identity (single source)
```

## Mermaid Version

```mermaid
flowchart TD
    A["mdnow url --crawl"] --> B{"input type?"}
    B -->|local file / youtube| Z1["other pipelines"]
    B -->|web URL| C{"--no-llms?"}

    C -->|no| D{"discover llms.txt?"}
    D -->|found| E["write & RETURN<br/>(crawler skipped)"]
    D -->|None| F["build fetchers"]
    C -->|yes| F

    F --> G["primary = static<br/>renderer = camoufox (lazy)"]
    G --> H["STEP 1: discover_urls"]

    subgraph DISC ["discover_urls"]
        H1["sitemap_search"] --> H2{"found?"}
        H2 -->|yes| H3["filter same-host + robots"]
        H2 -->|no| H4["focused_crawler (static BFS)"]
        H3 --> H5{"renderer AND<br/>(--render OR found<=1)?"}
        H4 --> H5
        H5 -->|yes| H6["_render_discover<br/>scrape DOM links · SPA FIX"]
        H5 -->|no| H7["static links only"]
        H6 --> H8["sort · dedup · cap"]
        H7 --> H8
    end

    H --> DISC
    DISC --> I["PASS A: fetch + extract each"]

    subgraph LOOP ["per-page loop (isolated)"]
        L1["_fetch_one(primary)"] --> L2{"empty OR thin<br/>(words<50)?"}
        L2 -->|no| L4["keep page"]
        L2 -->|yes, can_escalate| L3["_fetch_one(renderer)<br/>ESC FIX · browser launches"]
        L3 --> L5{"crash?"}
        L5 -->|"driver bug ⚠"| L6["Node driver dies<br/>→ hang (BLOCKER)"]
        L5 -->|ok| L4
        L3 -->|still empty| L7["failures[]"]
    end

    I --> LOOP
    LOOP --> J["PASS B: build_path_map ·<br/>rewrite_links · write (hash-versioned)"]
    J --> K["artifacts:<br/>llms.txt · llms-full.txt · manifest.json"]
    K --> M["Done: N written, M failed"]

    style H6 fill:#d4f7d4,stroke:#2a2
    style L3 fill:#d4f7d4,stroke:#2a2
    style L6 fill:#f7d4d4,stroke:#a22
```

## The one seam that matters

`Fetcher` is a Protocol: `fetch(url) -> FetchResult`. Static and Camoufox both
implement it, so **"escalate to render" = call `_fetch_one` with a different
fetcher** — nothing downstream (extractor, link-rewriter, writer) knows which
backend produced the bytes.

## Status

- 🟢 Discovery render-fallback — works (nestjs 1 → 12 pages)
- 🟢 Per-page escalation — works (fires on thin/empty)
- 🔴 **Blocker** — `CamoufoxFetcher.fetch` hits a Playwright Firefox driver crash
  (`pageError.location.url` TypeError) on SPA pages that throw uncaught JS errors;
  the reused browser makes one crash abort the whole run. This is below the
  `Fetcher` seam — the crawl logic above is unaffected.
