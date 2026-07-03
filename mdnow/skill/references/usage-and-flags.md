# mdnow — usage, flags & inputs

Full reference for driving the `mdnow` CLI. Load when choosing flags for a non-trivial
input or when the quick cases in `SKILL.md` don't cover the request.

## Input-type detection (automatic)

`mdnow` inspects the argument and picks a path — you never declare the type:

| Argument | Treated as |
|----------|-----------|
| `http(s)://…` HTML page | Web page → static fetch, render fallback |
| `http(s)://…` non-HTML (`.pdf`, `.xlsx`, …) | Remote file → markitdown convert |
| `http(s)://…` YouTube (`youtu.be`, `youtube.com/watch`) | Transcript (needs `--allow-remote`) |
| Local path (`./report.pdf`, `/abs/file.docx`) | Local file → markitdown convert |

## Flags

| Flag | Meaning |
|------|---------|
| `-o, --out <dir>` | Output directory (default: current dir) |
| `--crawl` | Crawl the whole site into a folder tree (web only) |
| `--max-pages N` | Cap crawl at N pages (default 100) |
| `--all` | Crawl every page (ignore `--max-pages`) |
| `--render` | Force the Camoufox stealth browser (JS / anti-bot) |
| `--no-llms` | Skip the `llms.txt` discovery shortcut; force fetch/crawl |
| `--allow-remote` | Allow cloud-egress converters (audio/video transcription, YouTube) |

Flags are additive on the single command; there are no subcommands.

## Intent → command

| Intent | Command |
|--------|---------|
| One web page | `mdnow <url> -o <dir>` |
| Whole site, capped | `mdnow <url> --crawl --max-pages N -o <dir>` |
| Whole site, no cap | `mdnow <url> --crawl --all -o <dir>` |
| JS-heavy / SPA / anti-bot page | `mdnow <url> --render -o <dir>` |
| Local document | `mdnow ./report.pdf -o <dir>` |
| Remote non-HTML file | `mdnow https://host/paper.pdf -o <dir>` |
| Audio / video / YouTube | `mdnow <input> --allow-remote -o <dir>` |
| Force fetch (skip llms.txt) | add `--no-llms` |

## Costs & caveats

- **Local-first:** only audio/video/YouTube need `--allow-remote`. Never add it for plain
  pages/documents. Without it, those inputs error clearly instead of egressing.
- **Images** are dropped but their alt-text is kept inline (web) or OCR'd (image files).
- **Crawling an SPA renders every page (~3s each)** — a 100-page site ≈ several minutes,
  and looks idle during the fetch phase (two-pass: fetch all → write all). Prefer
  `--max-pages` over `--all` unless the whole site is truly wanted. Crawl auto-escalates
  thin/empty pages to the renderer on its own, so `--render` is rarely needed with `--crawl`.
- **`--render` needs the `[render]` extra** + one-time `python -m camoufox fetch`. If
  missing, render/SPA pages are skipped with a hint; static pages still convert.
- **File conversion needs the `[docs]` extra** (markitdown). If missing, file inputs error
  with an install hint.
- **`--crawl` is web-only** and errors on file inputs.
