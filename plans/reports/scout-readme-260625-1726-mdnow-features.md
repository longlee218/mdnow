# MDNow Feature Scout Report

## What it does (one-liner)
Convert any website URL or local/remote file (PDF, Office, EPub, audio, images, etc.) to clean, AI-friendly markdown. Fully local by default — no API keys, no data egress.

## Install options
- Base: `pip install -e .` (website conversion only)
- With render: `pip install -e ".[render]"` (Camoufox stealth browser, ~300MB one-time download)
- With docs: `pip install -e ".[docs]"` (markitdown for PDF/Office/image/audio, heavy deps)
- Dev: `pip install -e ".[dev,docs]"` (includes test deps)
- Global: `pipx install "/path/to/MDNow[render,docs]" --force`

## Usage examples
- Single page: `mdnow https://example.com/article -o out/`
- Crawl site: `mdnow https://example.com --crawl --max-pages 100 -o out/`
- Crawl all: `mdnow https://example.com --crawl --all -o out/`
- Render (JS/anti-bot): `mdnow https://example.com/spa --render -o out/`
- Skip discovery: `mdnow https://example.com --crawl --no-llms -o out/`
- Local file: `mdnow ./report.pdf -o out/`
- Remote file: `mdnow https://example.com/paper.pdf -o out/`
- Audio/YouTube (cloud): `mdnow ./talk.mp3 --allow-remote -o out/`

## CLI flags
| Flag | Meaning |
|------|---------|
| `-o, --out` | Output directory (default `.`) |
| `--crawl` | Crawl whole site into tree (websites only) |
| `--max-pages N` | Max pages to crawl (default 100) |
| `--all` | Crawl all pages (ignore `--max-pages`) |
| `--render` | Use Camoufox stealth browser |
| `--no-llms` | Skip llms.txt discovery; force fetch/crawl |
| `--allow-remote` | Allow cloud API egress (audio/video/YouTube) |

## Supported input types
- **Websites**: Single page or full crawl (respects robots.txt, sitemap-first then BFS)
- **Local files**: PDF, Word, PowerPoint, Excel, images (OCR), EPub, CSV/JSON/XML, ZIP archives
- **Remote files**: Same types, fetched as non-HTML
- **Audio/Video**: `.mp3`, `.mp4`, etc. (requires `--allow-remote`)
- **YouTube URLs**: Transcript extraction (requires `--allow-remote`)

## Output behavior
- Per-page `.md` with YAML frontmatter (source_url, title, dates, version, content_hash, word_count, token_estimate, summary)
- Content-hash versioning: re-running only bumps `version` when content actually changes
- Images dropped but alt-text kept inline (websites); OCR for image files
- Crawl mode artifacts: `llms.txt`, `llms-full.txt`, `manifest.json`
- Relative link rewriting for internal+crawled pages

## Limitations / caveats
- `--crawl` invalid for file inputs (single file only)
- Audio/video/YouTube require `--allow-remote` (only cloud egress paths)
- Camoufox render is best-effort for anti-bot; not guaranteed
- markitdown `[docs]` extra is heavy (onnxruntime, pandas)
- No API keys ever used; no LLM/Azure plugins
- Low volume design: no queues, no anti-abuse, no distributed concerns

## Development commands
- `python -m pytest` (72 tests, ~86% coverage)
- `python -m compileall -q mdnow` (fast syntax gate)
- `.venv/bin/python -m camoufox fetch` (one-time browser download)

## Architecture modules
cli, discovery/llmstxt, fetcher (StaticFetcher/CamoufoxFetcher), extractor, convert, crawler, urls, linkrewrite, guards, frontmatter, outline, artifacts, writer. Each <200 lines.
