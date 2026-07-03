<div align="center">

[English](README.md) · [Tiếng Việt](README.vi.md)

<img src="https://raw.githubusercontent.com/longlee218/mdnow/main/assets/banner-2.png" alt="mdnow — turn anything into Markdown" width="640">

# mdnow

### Any URL. Any site. Any file. → Clean, LLM-ready Markdown.

**100% local. No API keys. No data egress. One command.**

Turn a web page, a whole website, or a PDF/Office/audio file into clean Markdown your LLM can actually read — without shipping your content to someone else's cloud.

[![Python](https://img.shields.io/badge/python-3.11%2B-3b82f6.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-3b82f6.svg)](LICENSE)
[![Install: git](https://img.shields.io/badge/install-via%20git-6f42c1.svg)](#install)
[![Local-first](https://img.shields.io/badge/data%20egress-none%20by%20default-16a34a.svg)](#-why-mdnow)

**macOS / Linux**

```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
```

**Windows**

```powershell
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 | iex
```

**Cross-platform (uv)**

```bash
uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"
```

</div>

---

## The problem

LLMs are only as good as what you feed them — and the web fights you every step:

- **Raw HTML is noise.** Nav, ads, cookie banners, and `<div>` soup bury the actual content.
- **Cloud scrapers cost you twice.** They meter every call _and_ send your content to a third party.
- **Every format needs a different tool.** One thing for pages, another for PDFs, another for audio, another for a whole docs site.

**mdnow collapses all of that into one local command** — pages, whole sites, and files, straight to clean Markdown, with nothing leaving your machine by default.

```console
$ mdnow https://example.com/article -o out/
fetched: example-article.md (v1, 1234 words, ~247 tokens)

$ mdnow https://docs.example.com --crawl --max-pages 50 -o out/
Crawling https://docs.example.com ...
Done: 47 page(s) written, 0 failed → out/   (+ llms.txt, llms-full.txt, manifest.json)
```

<!-- TODO: replace with animated asciinema/vhs cast (assets/demo.svg) before launch -->

---

## ✨ Why mdnow

|                                    |   **mdnow**    | Cloud scraper APIs  | Local single-purpose tools |
| ---------------------------------- | :------------: | :-----------------: | :------------------------: |
| Runs fully local                   |       ✅       |    ❌ cloud-only    |             ✅             |
| No API key / signup                |       ✅       |         ❌          |             ✅             |
| Your content stays private         | ✅ none leaves | ❌ egress by design |             ✅             |
| Web page → Markdown                |       ✅       |         ✅          |     ⚠️ extraction only     |
| Whole-site crawl → `llms.txt`      |       ✅       |      ⚠️ varies      |             ❌             |
| JS / anti-bot stealth render       |       ✅       |         ✅          |             ❌             |
| Files: PDF, Office, audio, images… |       ✅       |      ⚠️ varies      |      ⚠️ one type each      |
| Bundled Claude Code skill          |       ✅       |         ❌          |             ❌             |
| Cost                               | **Free (MIT)** |     💲 metered      |            Free            |

> **The wedge:** everything a cloud scraper does, but on _your_ machine — and everything a local extractor does, but for the whole web _and_ every file type, wired for LLMs out of the box.

---

## 🚀 What you get

|     | Capability            | What it means                                                                                                        |
| --- | --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| ⚡  | **Static fetch**      | `httpx` + `trafilatura`. Fast default, no browser needed.                                                            |
| 🎭  | **Stealth render**    | Camoufox headless Firefox for JS-heavy / anti-bot sites — opt-in, or **auto-escalated** when static content is thin. |
| 🔗  | **Crawl + index**     | Whole-site tree → per-page `.md` + `llms.txt` + `llms-full.txt` + `manifest.json`.                                   |
| 📄  | **Any-file convert**  | PDF, Word, PowerPoint, Excel, EPub, images (OCR), audio, YouTube, CSV/JSON/XML, ZIP.                                 |
| 🔌  | **Bundled skill**     | `mdnow --install-skill` drops a ready-to-use skill into Claude Code.                                                 |
| 🔒  | **Local-first**       | No keys, no telemetry, no egress by default. Content is yours.                                                       |
| 🧾  | **Idempotent output** | Content-hash versioning — re-runs only bump `version` when the body actually changed.                                |

---

## Table of contents

- [Quick start](#quick-start)
- [Install](#install)
- [Usage](#usage)
- [For AI assistants](#-for-ai-assistants)
- [How it works](#how-it-works)
- [Output format](#output-format)
- [Behavior](#behavior)
- [Why mdnow (local-first)](#-why-local)
- [Develop](#develop)
- [License](#license)

---

## Quick start

| Platform            | One-liner                                                                             |
| :------------------ | :------------------------------------------------------------------------------------ |
| macOS / Linux       | `curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh \| sh` |
| Windows             | `irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 \| iex`      |
| Cross-platform (uv) | `uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"`                   |

Then:

```bash
mdnow https://example.com -o out/
```

> **Distributed via git, not PyPI** — install straight from this repo. No registry, no publish step.

Not sure what's installed? Run **`mdnow --doctor`** — it reports every extra and the exact command to fix what's missing.

---

## Install

### Pick your platform

| Platform            | Base install                                                                          |
| :------------------ | :------------------------------------------------------------------------------------ |
| macOS / Linux       | `curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh \| sh` |
| Windows             | `irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 \| iex`      |
| Cross-platform (uv) | `uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"`                   |
| From source         | see below                                                                             |

> **Distributed via git, not PyPI** — install straight from this repo. No registry, no publish step.

### Add extras

Base `mdnow` fetches **static HTML** and converts **local files** with lightweight logic. Add extras only when you need them:

| Extra      | What it adds                                                                       |
| ---------- | ---------------------------------------------------------------------------------- |
| `[render]` | Stealth headless browser (Camoufox, ~300MB one-time) for JS-heavy / anti-bot sites |
| `[docs]`   | Any-file conversion: PDF, Office, images/OCR, audio, YouTube                       |

**macOS / Linux**

```bash
# render only
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --render
# docs only
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --docs
# render + docs + skill
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --all
```

**Windows**

```powershell
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 -o install.ps1
# render only
.\install.ps1 -Render
# docs only
.\install.ps1 -Docs
# render + docs + skill
.\install.ps1 -All
```

**uv (any platform)**

```bash
uv tool install "mdnow[render] @ git+https://github.com/longlee218/mdnow"
uv tool install "mdnow[docs] @ git+https://github.com/longlee218/mdnow"
uv tool install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"
```

After installing `[render]`, download the browser:

```bash
mdnow --fetch-browser
```

> No uv? You can also use `pipx install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"`.

### Upgrade with `--update`

Re-install the latest version from git, preserving your installed extras:

```bash
mdnow --update
```

What it does:

1. Detects which extras you currently have (`render`, `docs`, etc.)
2. Runs `uv tool install --force "mdnow[<extras>] @ git+https://github.com/longlee218/mdnow"`
3. If `uv` is missing, it prints the equivalent manual command

If `uv` is not on your PATH, run the equivalent manually:

```bash
uv tool install --force "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"
```

Replace `[render,docs]` with whichever extras you actually use, or omit extras entirely. No uv? Reinstall with the one-liner above and the flags you need (`--render`, `--docs`, or `--all`).

### From source

```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,docs]"
```

---

## Usage

### Website: single page

```bash
mdnow https://example.com/article -o out/
```

### Website: whole-site crawl

```bash
mdnow https://example.com --crawl -o out/                 # up to 100 pages (default)
mdnow https://example.com --crawl --all -o out/           # no limit
mdnow https://example.com --crawl --max-pages 50 -o out/  # custom limit
```

Output: per-page `.md` + `llms.txt` + `llms-full.txt` + `manifest.json`.

### Website: JS-heavy or anti-bot sites

```bash
mdnow https://example.com/spa --render -o out/   # force stealth browser (needs [render])
mdnow https://example.com --crawl -o out/        # auto-escalates thin/empty pages to render
```

### File: local PDF, Office, image, audio, …

```bash
mdnow ./report.pdf -o out/
mdnow ./slides.pptx -o out/
mdnow ./screenshot.png -o out/         # OCR
mdnow ./talk.m4a --allow-remote -o out/ # audio transcription (needs [docs] + --allow-remote)
```

### File: remote URL

```bash
mdnow https://example.com/paper.pdf -o out/
mdnow "https://youtu.be/watch?v=abc123" --allow-remote -o out/   # YouTube transcript (cloud egress)
```

### Skip discovery, force fetch/crawl

```bash
# By default, if a site publishes /llms.txt, mdnow uses it directly. Force a fresh fetch with:
mdnow https://example.com --crawl --no-llms -o out/
```

### Private / internal sites

For sites behind authentication (session cookies, bearer tokens, etc.):

**Bearer token (API key, OAuth)**

```bash
mdnow https://internal.example.com/docs -H "Authorization: Bearer $TOKEN" -o out/
```

**Session cookies** (exported from browser, e.g., [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/iphcomtajlahbettdcakbotja27ijehe))

```bash
# Netscape format (.txt file, browser extensions export this format)
mdnow https://internal.example.com/wiki --cookie-file ~/cookies.txt -o out/

# JSON list format: [{"name", "value", "domain", "path"}, ...]
mdnow https://internal.example.com/wiki --cookie-file ~/cookies.json -o out/
```

**Multiple headers** (repeatable)

```bash
mdnow https://api.example.com -H "Authorization: Bearer $TOKEN" -H "X-API-Key: $KEY" -o out/
```

**Secret hygiene:** Cookie files and tokens are **never logged, echoed, or written to output**. Recommend `chmod 600` on cookie files and injecting tokens via env vars. Custom headers are re-sent if the site redirects cross-origin (httpx strips only `Authorization`) — point mdnow at the exact host you trust. Note: `llms.txt` discovery probes are unauthenticated (use `--no-llms` if they confuse a private site); static crawl discovery (sitemap/BFS) is unauthenticated too; per-page fetches and render-based discovery carry auth.

### Flags

| Flag              | Meaning                                                                |
| ----------------- | ---------------------------------------------------------------------- |
| `-o, --out`       | Output directory (default `.`)                                         |
| `--crawl`         | Crawl the whole site into a tree (websites only)                       |
| `--max-pages N`   | Max pages to crawl (default 100)                                       |
| `--all`           | Crawl all pages (ignore `--max-pages`)                                 |
| `--render`        | Use the Camoufox stealth browser (JS/anti-bot); requires `[render]`    |
| `--no-llms`       | Skip `llms.txt` discovery; force fetch/crawl                           |
| `--allow-remote`  | Allow cloud APIs: audio/video transcription, YouTube (opt-in egress)   |
| `-H, --header`    | Add HTTP header (repeatable); e.g. `-H "Authorization: Bearer $TOKEN"` |
| `--cookie-file`   | Path to Netscape cookies.txt or JSON cookies list for authentication   |
| `--doctor`        | Report installed/missing extras (and how to fix) and exit              |
| `--fetch-browser` | Download the Camoufox browser for `--render` and exit                  |
| `--install-skill` | Install the bundled Claude Code skill to `~/.claude/skills/mdnow`      |
| `--update`        | Upgrade mdnow to the latest version from git                           |

---

## 🧠 For AI assistants

### Claude Code skill

```bash
mdnow --install-skill                                   # → ~/.claude/skills/mdnow
mdnow --install-skill --skill-dir ~/.claude/skills/foo  # custom location
mdnow --install-skill --force                           # overwrite existing
```

The skill lets Claude Code fetch a URL, crawl a site, or convert a file — right from the editor.

---

## How it works

A **cheapest-path-first funnel** — each tier only runs if the previous one didn't already produce clean Markdown:

1. **Discovery** — if the site publishes `/llms.txt`, `/llms-full.txt` (or variants, or a `<url>.md` twin), use it directly and skip everything else.
2. **Static fetch** — `httpx` + `trafilatura`. Fast default; no browser.
3. **Render** — Camoufox stealth browser for JS-heavy / anti-bot sites. Opt-in via `--render`, or auto-escalated when static returns empty, thin, or boilerplate-heavy content (e.g., navigation/footer link farms).

---

## Output format

Every page is written with YAML frontmatter and content-hash **versioning** — re-running only bumps `version` when the body actually changed:

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
outline:
  - "## Getting Started"
  - "### Installation"
  - "## API Reference"
---
```

The `outline` key lists heading strings (useful for AI agents to quickly identify sections).

Crawl mode also writes three artifacts:

- **`llms.txt`** — [llmstxt.org](https://llmstxt.org)-shaped index: `# <host>` header, `> <summary>`, and a `## Pages` list of `- [title](path): summary`.
- **`llms-full.txt`** — Concatenated Markdown of every crawled page, each prefixed with `## <title>` + `Source: <url>`.
- **`manifest.json`** — Machine-readable metadata: host, page count, per-page hashes, summaries, token counts. Each page includes `sections`: a list of `{slug, heading, level, word_count, token_estimate}` chunks in document order, with `_intro` for the preamble before the first heading (useful for AI agents to pick sections by size).

---

## Behavior

- **Images** — stripped but alt-text preserved (HTML); or OCR-extracted (image files, `[docs]`).
- **Files** — local/remote non-HTML auto-detected and converted via markitdown (PDF, Word, PowerPoint, Excel, EPub, images, CSV/JSON/XML, ZIP).
- **Audio/video & YouTube** — require `--allow-remote` (cloud transcription). Without it, they error clearly.
- **`--crawl`** — invalid for file inputs (single file only); errors clearly.
- **Crawl** — discovers via `sitemap.xml` first, falls back to BFS; respects `robots.txt`, rate-limits, isolates per-page failures.
- **JS-rendered SPAs** (React/Angular docs, etc.) — auto-escalate in crawl mode: if static discovery finds no links, the start page is rendered; thin pages auto-render. Requires `[render]` + `mdnow --fetch-browser`.
- **Cloudflare / anti-bot** — `--render` bypass is best-effort.
- **Terminal output** — colored status, a spinner while fetching, and a live progress bar for `--crawl`, plus actionable next-step hints. Auto-degrades to plain text when piped or on a non-tty / `NO_COLOR`, so scripts are unaffected.

---

## 🔒 Why local?

**Fully local by default is a founding constraint, not a feature flag.**

- Your content **never leaves your machine** — the only exception is audio/video/YouTube, and that's opt-in via `--allow-remote`.
- **No API keys, no signup, no rate limits, no vendor lock-in.**
- **Zero telemetry** — no pings home, no analytics. Read the source; there are no hidden cloud calls.
- Use it as a CLI, in a script, or embedded in your LLM IDE — it's yours to control.

---

## Develop

```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,docs]"
.venv/bin/pytest          # 106 tests, ~88% coverage
```

**Architecture** — modules each < 200 lines, one responsibility: `cli`, `discovery`/`llmstxt`, `fetcher` (`StaticFetcher`/`CamoufoxFetcher` behind one `Fetcher` interface), `playwright_patch` (self-healing render-driver fix), `extractor`, `convert` (markitdown wrapper), `crawler`, `urls`, `linkrewrite`, `guards`, `frontmatter`, `outline`, `artifacts`, `writer`, `commands`, `doctor`.

---

## License

[MIT](LICENSE) © Long Le. Contributions welcome — open an issue or PR.

<div align="center"><sub>Built for people who feed the web to LLMs and want to keep their data to themselves.</sub></div>
