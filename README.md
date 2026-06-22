# mdnow

Convert any website URL — or local/remote file (PDF, Office, EPub, audio, images, etc.) — to clean, AI-friendly markdown. Strips ads/nav/footer, keeps image alt-text, and builds a context tree when crawling. Fully local by default — no API keys, no data leaves your machine.

## How it works

A cheapest-path-first funnel — each tier only runs if the one above didn't already produce clean markdown:

1. **Discovery** — if the site publishes `/llms.txt`, `/llms-full.txt` (or variants, or a `<url>.md` twin), use it directly and skip everything else.
2. **Static fetch** — `httpx` + `trafilatura` extraction. Fast default.
3. **Render** — Camoufox stealth browser for JS-heavy / anti-bot sites (opt-in or auto-escalated).

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e .

# Only needed for the --render tier (downloads a Firefox build, ~300MB, one time):
.venv/bin/python -m camoufox fetch

# Only needed for file conversion (PDF, Office, images, audio, etc.):
.venv/bin/pip install -e ".[docs]"    # pulls markitdown + heavy deps (onnxruntime, pandas, etc.)
```

## Usage

```bash
# Website: Single page
mdnow https://example.com/article -o out/

# Website: Whole site → folder of per-page .md + llms.txt / llms-full.txt / manifest.json
mdnow https://example.com --crawl --max-pages 100 -o out/
mdnow https://example.com --crawl --all -o out/        # no page cap

# Website: JS-heavy / anti-bot site → stealth render
mdnow https://example.com/spa --render -o out/

# Website: Skip llms.txt discovery, force fetch/crawl
mdnow https://example.com --crawl --no-llms -o out/

# File: Local file (auto-detected as PDF, Office, image, etc.)
mdnow ./report.pdf -o out/
mdnow ./slides.pptx -o out/
mdnow ./document.docx -o out/

# File: Remote file (fetched as non-HTML)
mdnow https://example.com/paper.pdf -o out/
mdnow https://example.com/sheet.xlsx -o out/

# File: Audio or YouTube (requires --allow-remote for cloud APIs)
mdnow ./talk.mp3 --allow-remote -o out/
mdnow https://youtu.be/video-id --allow-remote -o out/
```

### Flags

| Flag | Meaning |
|------|---------|
| `-o, --out` | Output directory (default `.`) |
| `--crawl` | Crawl the whole site into a tree (websites only) |
| `--max-pages N` | Max pages to crawl (default 100) |
| `--all` | Crawl all pages (ignore `--max-pages`) |
| `--render` | Use the Camoufox stealth browser (JS/anti-bot sites) |
| `--no-llms` | Skip llms.txt discovery; force fetch/crawl (websites only) |
| `--allow-remote` | Allow converters that egress to cloud APIs (audio/video transcription, YouTube) |

## Output

Each page is written with YAML frontmatter and content-hash **versioning** — re-running only bumps `version` when the content actually changed:

```yaml
---
source_url: https://example.com/article
title: Example Article
published_date: 2026-01-01
fetched_date: 2026-06-21
version: 1
content_hash: <sha256>
word_count: 1234
token_estimate: 247
summary: "The world as we have created it is a process of our thinking."
---
```

Crawl mode also writes three artifacts to the output directory:

- **`llms.txt`** — llmstxt.org-shaped index: `# <host>` header, `> <summary>` blockquote, then a `## Pages` list of `- [title](relpath): summary`.
- **`llms-full.txt`** — concatenated full markdown of every crawled page, each section prefixed with `## <title>` and a `Source: <url>` line.
- **`manifest.json`** — machine-readable index with metadata: `{host, generated_from, page_count, pages:[{source_url, local_path, title, content_hash, token_estimate, word_count, summary, headings:[...]}]}`.

Per-page `.md` files and relative-link rewriting are unchanged.

## Behavior notes

- **Images** are dropped but their alt-text is kept inline (websites); or extracted via OCR (image files, requires `[docs]` extra).
- **File inputs** (local or remote non-HTML) are auto-detected and converted via markitdown. Supported: PDF, Word, PowerPoint, Excel, images (OCR), EPub, CSV/JSON/XML, ZIP archives.
- **Audio/video files** (incl. `.mp4`) and **YouTube URLs** require `--allow-remote` to allow cloud transcription APIs. Without it, they error clearly.
- **--crawl** is invalid for file inputs (single file only); errors clearly.
- **Fully local by default:** only audio/video transcription and YouTube egress are opt-in via `--allow-remote`. No LLM/Azure client keys ever used — markitdown runs with plugins off.
- **Crawl** (websites only) discovers via `sitemap.xml` first, falls back to a same-domain BFS; respects `robots.txt`, rate-limits, and isolates per-page failures. Artifacts (`llms.txt`, `llms-full.txt`, `manifest.json`) are always emitted in crawl mode.
- **Cloudflare / anti-bot** bypass via `--render` is best-effort.

## Develop

```bash
.venv/bin/pip install -e ".[dev,docs]"
.venv/bin/pytest          # 72 tests, ~86% coverage
```

## Architecture

Plan & phase docs: `plans/260621-0714-website-to-markdown-cli/`. Modules (each <200 lines): `cli`, `discovery`/`llmstxt`, `fetcher` (`StaticFetcher`/`CamoufoxFetcher` behind one `Fetcher` interface), `extractor`, `convert` (markitdown wrapper), `crawler`, `urls`, `linkrewrite`, `guards`, `frontmatter`, `outline`, `artifacts`, `writer`.
