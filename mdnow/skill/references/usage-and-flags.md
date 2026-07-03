# mdnow — usage, flags & inputs

Full reference for driving the `mdnow` CLI. Load when choosing flags for a non-trivial
input or when the quick cases in `SKILL.md` don't cover the request.

## Input-type detection (automatic)

`mdnow` inspects the argument and picks a path — you never declare the type:

| Argument | Treated as |
|----------|-----------|
| `http(s)://…` HTML page | Web page → static fetch, render fallback |
| `http(s)://…` non-HTML (`.pdf`, `.xlsx`, …) | Remote file → markitdown convert |
| `http(s)://…` YouTube (`youtu.be`, `youtube.com/watch`) | Timestamped transcript (needs `--allow-remote`) |
| Local path (`./report.pdf`, `/abs/file.docx`) | Local file → markitdown convert |
| Local directory (`./docs`, `/abs/dir`) | Folder → recursive batch convert + crawl-style artifacts |

## Flags

| Flag | Meaning |
|------|---------|
| `-o, --out <dir>` | Output directory (default: current dir) |
| `--login` | Capture a session interactively: opens a headed Camoufox browser; you log in by hand (2FA/CAPTCHA work), then press Enter; saves cookies to `~/.mdnow/sessions/host.txt` for auto-reuse on future runs (requires `[render]`) |
| `--crawl` | Crawl the whole site into a folder tree (web only; errors on file/folder inputs) |
| `--max-pages N` | Cap crawl at N pages (default 100) |
| `--all` | Crawl every page (ignore `--max-pages`) |
| `--render` | Force the Camoufox stealth browser (JS / anti-bot) |
| `--no-llms` | Skip the `llms.txt` discovery shortcut; force fetch/crawl |
| `-H, --header "Name: Value"` | Add a request header (repeatable) for private/internal sites; applies to both static and render tiers |
| `--cookie-file <path>` | Cookies for a private site: Netscape `cookies.txt` (browser-extension export) or a JSON list `[{name,value,domain,path}]`; takes precedence over auto-reuse |
| `--allow-remote` | Allow cloud-egress converters (audio/video transcription, YouTube) |

Flags are additive on the single command; there are no subcommands. Utility flags
(`--doctor` to report missing extras, `--update` to self-upgrade, `--fetch-browser`,
`--install-skill`) exit without converting.

## Intent → command

| Intent | Command |
|--------|---------|
| One web page | `mdnow <url> -o <dir>` |
| Whole site, capped | `mdnow <url> --crawl --max-pages N -o <dir>` |
| Whole site, no cap | `mdnow <url> --crawl --all -o <dir>` |
| Capture session interactively (2FA/CAPTCHA) | `mdnow --login <url>` (then next time: `mdnow <url> -o <dir>` auto-reuses) |
| Private site (bearer/API-key) | `mdnow <url> -H "Authorization: Bearer $TOKEN" -o <dir>` |
| Private site (session cookie) | `mdnow <url> --cookie-file cookies.txt -o <dir>` |
| JS-heavy / SPA / anti-bot page | `mdnow <url> --render -o <dir>` |
| Local document | `mdnow ./report.pdf -o <dir>` |
| Local folder (recursive batch) | `mdnow ./docs -o <dir>` |
| Remote non-HTML file | `mdnow https://host/paper.pdf -o <dir>` |
| Audio / video / YouTube | `mdnow <input> --allow-remote -o <dir>` |
| Force fetch (skip llms.txt) | add `--no-llms` |

## Costs & caveats

- **Local-first:** only audio/video/YouTube need `--allow-remote`. Never add it for plain
  pages/documents. Without it, those inputs error clearly instead of egressing.
- **Session capture (`--login`):** opens a real browser window; you log in by hand (supports 2FA, CAPTCHA);
  mdnow reads the browser context cookies and saves them to `~/.mdnow/sessions/host.txt` with owner-only
  permissions (600). Sessions are stored plaintext on disk — secure your machine accordingly. Auto-reuse on
  next run if no `--cookie-file` is passed. Explicit `--cookie-file` always takes precedence over auto-reuse.
  Host match is exact (lowercased, port stripped) — `www.host.com` and `host.com` are separate sessions.
  Revoke by deleting the file: `rm ~/.mdnow/sessions/host.txt`.
- **Private sites:** `-H`/`--cookie-file` auth both fetch tiers. Cookie values without a
  `domain` are scoped to the requested host (never leaked to a redirect target); custom
  headers *are* re-sent on a cross-origin redirect, so point mdnow at the exact trusted host.
  Auth secrets are never written to output. `llms.txt` discovery probes are unauthenticated —
  add `--no-llms` if they confuse a private site.
- **Images** are dropped but their alt-text is kept inline (web) or OCR'd (image files).
- **Crawling an SPA renders every page (~3s each)** — a 100-page site ≈ several minutes,
  and looks idle during the fetch phase (two-pass: fetch all → write all). Prefer
  `--max-pages` over `--all` unless the whole site is truly wanted. Crawl auto-escalates
  thin/empty pages to the renderer on its own, so `--render` is rarely needed with `--crawl`.
- **`--render` needs the `[render]` extra** + one-time `python -m camoufox fetch`. If
  missing, render/SPA pages are skipped with a hint; static pages still convert.
- **File conversion needs the `[docs]` extra** (markitdown). If missing, file inputs error
  with an install hint.
- **YouTube transcripts** come out as coarse `[mm:ss]` timestamped, deep-linked paragraphs.
  YouTube often rate-limits/blocks transcript requests from cloud/VPN/datacenter IPs — a
  block is a transient, clearly-worded error (not a mdnow bug); wait a few minutes and retry.
- **`--crawl` is web-only** and errors on file and folder inputs.
- **Folder input** converts every file recursively (needs `[docs]`), mirrors the source
  tree under `-o`, and skips dotfiles/dotdirs (`.git`, `.DS_Store`, …). One unconvertible
  file (e.g. audio without `--allow-remote`, an unsupported/corrupt file) is reported as
  skipped and never aborts the batch. Always emits `manifest.json`/`llms.txt`/`llms-full.txt`
  (like `--crawl`); fetch-tier flags (`--render`, `-H`, `--cookie-file`, `--no-llms`) don't apply.
