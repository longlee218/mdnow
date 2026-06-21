# Brainstorm — Website→Markdown CLI (MDNow)

**Date:** 2026-06-21 · **Mode:** brainstorm · **Status:** consensus reached, ready for plan

## Problem Statement

Personal **local CLI** that converts any website link to clean, AI-friendly markdown.
Strip boilerplate (ads, nav, footer, images). Two modes: **single page** and **full-site crawl**.
Crawl mode builds a **context tree** with rewritten reference links.

## Requirements

Functional:
- `mdnow <url>` → single page → one `.md` + YAML frontmatter (source URL, title, date, word count)
- `mdnow <url> --crawl --depth N` → folder of per-page `.md` + `index.md` tree
- Strip ads/nav/footer/images; keep image alt-text as inline text (LLM signal)
- Crawl: discover via sitemap.xml first, fallback BFS same-domain to depth; rewrite internal links → relative local paths; keep external links as-is
- Render tier for JS-heavy / anti-bot sites

Non-functional:
- Local, free, private (no data leaves machine), low maintenance
- Single user / low volume → no queue, anti-abuse, async infra
- KISS/YAGNI/DRY

## Decisions (locked)

| Decision | Choice | Rationale |
|---|---|---|
| Language | **Python** | `trafilatura` bundles extraction + markdown + sitemap + crawl; no Node equiv. Camoufox is Python-native too. |
| Extraction | **trafilatura** | Best-in-class boilerplate removal; native `output_format="markdown"`; metadata; sitemap + spider modules |
| Static fetch | **httpx** | Default fast path |
| Render/anti-bot tier | **Camoufox** (stealth Firefox) | Replaces Firecrawl. Local, free, beats Cloudflare/bot-detection |
| Firecrawl | **Dropped** | Replaced by Camoufox; avoids cost/network/lock-in/data-egress |
| Crawl output | **Folder + index.md tree** | Mirrors llms.txt; best for AI traversal |
| Images | **Strip, keep alt-text** | Diagrams carry meaning; pure drop loses signal |

## Evaluated Approaches

1. **Firecrawl-only wrapper** — ✗ per-page cost, network dep, data egress, lock-in. Overkill for personal use.
2. **Manual Node** (readability + turndown) — ✗ must hand-roll sitemap + crawl + markdown step; weaker extraction.
3. **Manual Python (trafilatura) + Camoufox render tier** — ✓ **chosen.** Free, local, one ecosystem, ~90% of spec from one lib.

## Architecture

```
mdnow <url> [--crawl] [--depth N] [--render] [-o out/]

Fetcher (interface, swappable)        Extractor          Assembler
──────────────────────────────       ─────────          ─────────
StaticFetcher  httpx (default)   ──▶  trafilatura   ──▶  single: page.md + frontmatter
CamoufoxFetcher --render / auto       strip ads/nav/      crawl:  index.md (tree) +
  (JS, Cloudflare, bot-detect)        footer/imgs,                per-page .md,
                                      emit markdown               internal links → relative
                                      + metadata
```

- **Fetcher interface** keeps fetch backends swappable (static ↔ Camoufox ↔ future Firecrawl).
- **Auto-detect**: if static extraction yields thin/empty content, suggest/auto-trigger `--render`.
- **Crawl guards**: max-pages cap, max-depth, same-domain only, URL-hash dedup, respect robots.txt, polite rate-limit.

## Camoufox Integration Note (first spike)

`jo-inc/camofox-browser` = REST server (`npx @askjo/camofox-browser`, localhost:9377), Camoufox-based.
Returns **accessibility snapshots, not raw HTML** by default. trafilatura needs rendered HTML.
→ Spike: confirm endpoint to get `document.documentElement.outerHTML` (evaluate path).
→ Fallback: use **Camoufox Python library** (daijro/camoufox, Playwright-compatible, `page.content()` → raw HTML) — simpler, no separate server, returns HTML directly. Decide at spike.

## Risks

| Risk | L | I | Mitigation |
|---|---|---|---|
| Camoufox server returns a11y snapshot not raw HTML | M | M | Spike outerHTML endpoint; fallback Camoufox Python lib |
| JS site → empty content on static tier | M | M | Auto-detect thin extraction → `--render` |
| Crawl runaway (loops/too broad) | M | M | Caps: max-pages, depth, same-domain, dedup |
| Odd layouts miss content | M | L | trafilatura fallback config; `--render` escape hatch |
| Politeness / site hammering | L | M | rate-limit + robots.txt (trafilatura default) |

## Success Criteria

- Single mode: clean markdown, correct frontmatter, no ads/nav/footer, alt-text preserved
- Crawl mode: valid tree in `index.md`, internal links resolve to local relative paths, caps enforced
- JS-heavy test site (e.g. SPA / Cloudflare-protected) succeeds with `--render`
- Runs fully local, no API keys, no data egress

## Next Steps / Dependencies

1. Spike Camoufox HTML retrieval (REST server vs Python lib) → pick render backend
2. `/plan` to break into phases: (a) static single-page MVP, (b) crawl + tree, (c) Camoufox render tier, (d) polish/guards
3. Deps: `trafilatura`, `httpx`, `camoufox` (or camofox-browser server), a CLI lib (`typer`/`click`)

## Unresolved Questions

- Camoufox: REST server vs Python lib? (resolve at spike)
- Crawl: hard cap on max pages default value? (suggest 100)
- Code-block / table fidelity expectations for "AI-friendly" — assume trafilatura defaults OK?
