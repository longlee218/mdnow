[English](README.md) | [Tiếng Việt](README.vi.md)

# mdnow

**Convert any website URL or file to clean, AI-friendly markdown.**

Fully local by default — no API keys, no data egress. Website single-page, whole-site crawl (→ llms.txt + llms-full.txt), any-file conversion (PDF, Office, images, audio), or MCP server for Claude / Cursor. Choose your tier: fast static fetch, stealth JS render, or bundled Claude skill.

[![PyPI version](https://img.shields.io/pypi/v/mdnow.svg)](https://pypi.org/project/mdnow/)
[![Python versions](https://img.shields.io/pypi/pyversions/mdnow.svg)](https://pypi.org/project/mdnow/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub Actions](https://github.com/longlee218/mdnow/actions/workflows/publish.yml/badge.svg)](https://github.com/longlee218/mdnow/actions)

## Quick start

```bash
# One-liner (macOS / Linux)
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh

# Or with uv (recommended)
uv tool install mdnow

# Or with pipx
pipx install mdnow

# Then:
mdnow https://example.com -o out/
```

<!-- TODO: replace with animated asciinema/vhs cast (assets/demo.svg) before launch -->

```
$ mdnow https://example.com/article -o out/
fetched: example-article.md (v1, from https://example.com/article, 1234 words, ~247 tokens)

$ mdnow https://example.com --crawl --max-pages 50 -o out/
Crawling https://example.com ...
Done: 47 page(s) written, 0 failed → out/
```

## Features

| Feature | Description |
|---------|-------------|
| ⚡ **Static fetch** | `httpx` + `trafilatura`: fast, no JS rendering needed |
| 🎭 **Stealth render** | Camoufox headless Firefox for JS-heavy / anti-bot sites (opt-in or auto-escalate) |
| 🔗 **Crawl + index** | Whole-site tree: per-page `.md` + `llms.txt` + `llms-full.txt` + `manifest.json` |
| 📄 **Any-file convert** | PDF, Office, EPub, images (OCR), audio, YouTube, CSV/JSON/XML, ZIP |
| 🧠 **MCP server** | Expose tools to Claude Desktop, Claude Code, Cursor, and other LLM clients |
| 🔌 **Bundled skill** | `mdnow --install-skill` → install to `~/.claude/skills/mdnow` |

## Install

### 1. Base install (all users)

Choose one:

**Via shell one-liner** (macOS / Linux):
```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
```

**Via uv** (recommended, cross-platform):
```bash
uv tool install mdnow
```

**Via pipx** (Python-only, no uv required):
```bash
pipx install mdnow
```

**From source** (contributors):
```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 2. Extras (optional, install together)

Base `mdnow` fetches **static HTML only** and converts **local files** via the lightweight bundled logic. Opt into heavier dependencies as needed:

**`[render]`** — Stealth headless browser (Camoufox Firefox, ~300MB one-time download):
```bash
# Shell one-liner: add --render flag
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --render

# uv / pipx
uv tool install "mdnow[render]"
pipx install "mdnow[render]"

# Then download the browser (one-time):
mdnow --fetch-browser
```

**`[docs]`** — Any-file conversion: PDF, Word, PowerPoint, Excel, EPub, images (OCR), audio, YouTube (markitdown + heavy ML deps):
```bash
# Shell: --docs
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --docs

# uv / pipx
uv tool install "mdnow[docs]"
pipx install "mdnow[docs]"
```

**`[mcp]`** — MCP server mode for Claude / Cursor:
```bash
# Shell: --mcp
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --mcp

# uv / pipx
uv tool install "mdnow[mcp]"
pipx install "mdnow[mcp]"
```

**`--all`** — All extras at once:
```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --all
```

### Windows

Windows users: use **PowerShell** (no shell one-liner). Install uv or pipx first, then:

```powershell
uv tool install "mdnow[render,docs,mcp]"
```

To download the Camoufox browser on Windows:
```powershell
mdnow --fetch-browser
```

## Usage

### Website: single page

```bash
mdnow https://example.com/article -o out/
```

### Website: whole-site crawl

```bash
# Max 100 pages (default)
mdnow https://example.com --crawl -o out/

# No page limit
mdnow https://example.com --crawl --all -o out/

# Custom limit
mdnow https://example.com --crawl --max-pages 50 -o out/
```

Output: per-page `.md` files + `llms.txt` + `llms-full.txt` + `manifest.json`.

### Website: JS-heavy or anti-bot sites

```bash
# Force stealth browser (requires [render] extra)
mdnow https://example.com/spa --render -o out/

# Auto-escalate: if static HTML is thin or empty, render is triggered automatically
mdnow https://example.com --crawl -o out/
```

### File: local PDF, Office, image, audio, etc.

```bash
mdnow ./report.pdf -o out/
mdnow ./slides.pptx -o out/
mdnow ./document.docx -o out/
mdnow ./screenshot.png -o out/        # OCR
mdnow ./talk.m4a -o out/              # cloud transcription (requires --allow-remote + [docs] extra)
```

### File: remote URL

```bash
mdnow https://example.com/paper.pdf -o out/
mdnow https://youtu.be/watch?v=abc123 --allow-remote -o out/  # YouTube transcript (cloud egress)
```

### Skip discovery, force fetch/crawl

```bash
# Normally: if /llms.txt exists on the site, use it directly and skip fetch
# Use --no-llms to force fetch/crawl instead
mdnow https://example.com --crawl --no-llms -o out/
```

### Flags

| Flag | Meaning |
|------|---------|
| `-o, --out` | Output directory (default `.`) |
| `--crawl` | Crawl the whole site into a tree (websites only) |
| `--max-pages N` | Max pages to crawl (default 100) |
| `--all` | Crawl all pages (ignore `--max-pages`) |
| `--render` | Use the Camoufox stealth browser (JS/anti-bot sites); requires `[render]` extra |
| `--no-llms` | Skip llms.txt discovery; force fetch/crawl (websites only) |
| `--allow-remote` | Allow cloud APIs: audio/video transcription, YouTube (opt-in data egress) |
| `--doctor` | Report installed/missing extras (and how to fix) and exit |
| `--fetch-browser` | Download the Camoufox browser for `--render` and exit |
| `--install-skill` | Install the bundled Claude Code skill to `~/.claude/skills/mdnow` |
| `--mcp` | Run as an MCP server (stdio transport) for Claude / Cursor |

## For AI assistants

### Claude Code skill

Install the bundled Claude Code skill:

```bash
mdnow --install-skill
```

The skill exposes the mdnow conversion pipeline to Claude Code: fetch a URL, crawl a site, or convert a file — all from the Claude Code editor.

To specify a custom destination:

```bash
mdnow --install-skill --skill-dir ~/.claude/skills/my-mdnow
mdnow --install-skill --force    # overwrite if already installed
```

### MCP server

Expose mdnow as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server for Claude Desktop, Claude Code, or Cursor:

```bash
mdnow --mcp
```

**Claude Desktop config** (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mdnow": {
      "command": "/path/to/mdnow",
      "args": ["--mcp"]
    }
  }
}
```

**Tools exposed:**
- `mdnow_fetch_url`: Fetch a single URL → markdown with metadata
- `mdnow_crawl_site`: Crawl a site → summary of per-page conversions
- `mdnow_convert_file`: Convert a local or remote file → markdown

## How it works

A cheapest-path-first funnel — each tier only runs if the prior didn't already produce clean markdown:

1. **Discovery** — if the site publishes `/llms.txt`, `/llms-full.txt` (or variants, or a `<url>.md` twin), use it directly and skip everything else.
2. **Static fetch** — `httpx` + `trafilatura` extraction. Fast default; no browser needed.
3. **Render** — Camoufox stealth browser for JS-heavy / anti-bot sites. Opt-in via `--render`, or auto-escalated when static returns empty/thin content.

## Output

Each page is written with YAML frontmatter and content-hash **versioning** — re-running only bumps `version` when the body actually changed:

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

Crawl mode also writes three artifacts:

- **`llms.txt`** — [llmstxt.org](https://llmstxt.org)-shaped index: `# <host>` header, `> <summary>` blockquote, `## Pages` with `- [title](path): summary` list.
- **`llms-full.txt`** — Concatenated markdown of every crawled page, each prefixed with `## <title>` and `Source: <url>`.
- **`manifest.json`** — Machine-readable metadata: host, page count, and per-page hashes, summaries, token counts.

## Behavior

- **Images** are stripped but alt-text is preserved (HTML); or extracted via OCR (image files, `[docs]` extra).
- **Files** (local or remote non-HTML) are auto-detected and converted via markitdown. Supported: PDF, Word, PowerPoint, Excel, EPub, images, CSV/JSON/XML, ZIP archives.
- **Audio/video** and **YouTube** require `--allow-remote` (cloud transcription APIs). Without it, they error clearly.
- **`--crawl`** is invalid for file inputs (single file only); errors clearly.
- **Fully local by default** — only audio/video/YouTube egress is opt-in via `--allow-remote`. No LLM keys or telemetry.
- **Crawl** discovers via `sitemap.xml` first, falls back to BFS; respects `robots.txt`, rate-limits, and isolates per-page failures.
- **JS-rendered SPAs** (React/Angular docs, etc.) auto-escalate in crawl mode: if static discovery finds no links, the start page is rendered, and thin pages auto-render. Requires `[render]` extra + `mdnow --fetch-browser`.
- **Cloudflare / anti-bot** bypass via `--render` is best-effort.

## Why local?

**mdnow is fully local by default** — no API keys, no data egress, no telemetry. This is a founding constraint.

- Your website content never leaves your machine (except audio/video/YouTube, which is opt-in via `--allow-remote`).
- No network dependency after first install (except the actual website fetch, of course).
- No third-party vendor lock-in or API rate limits.
- Zero telemetry — no pings home, no analytics.
- Transparent: read the source code; no hidden cloud calls.

Use mdnow as a CLI, in a script, or embedded in your LLM IDE — it's yours to control.

## Develop

```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,docs,mcp]"
.venv/bin/pytest          # 95 tests, ~88% coverage
```

## Architecture

Plan & phase docs: `plans/260621-0714-website-to-markdown-cli/`. Modules (each <200 lines): `cli`, `discovery`/`llmstxt`, `fetcher` (`StaticFetcher`/`CamoufoxFetcher` behind one `Fetcher` interface), `playwright_patch` (self-healing render-driver fix), `extractor`, `convert` (markitdown wrapper), `crawler`, `urls`, `linkrewrite`, `guards`, `frontmatter`, `outline`, `artifacts`, `writer`, `mcp_server`.

## License

MIT
