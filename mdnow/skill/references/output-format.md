# mdnow — output format

What `mdnow` writes on success, and how to read it back. Load when you need to locate or
parse the converted files.

## Single page / file → one `.md`

Filename is slugified from the page/document title (or URL). Contents = YAML frontmatter
then the markdown body:

```yaml
---
source_url: https://example.com/article   # or the local/remote file path
title: Example Article
published_date: 2026-01-01                 # when detectable
fetched_date: 2026-06-21
version: 1
content_hash: <sha256>
word_count: 1234
token_estimate: 247                        # ~chars/4
summary: "First paragraph, extracted."
outline:                                    # heading anchors, for fast navigation
  - "# Example Article"
  - "## Usage"
---

# Example Article
…clean markdown body…
```

**Versioning:** `version` is content-hash based. Re-running over an existing output only
bumps `version` when the body actually changed; unchanged pages are skipped. Conversions
and crawls are therefore idempotent.

## Crawl mode → folder tree + 3 artifacts

Per-page `.md` files are written nested by URL path (e.g. `cli/`, `devtools/`), with
internal links rewritten to relative local `.md` (internal-but-not-crawled links stay
absolute; external links untouched). Plus three artifacts in the output dir:

- **`llms.txt`** — llmstxt.org-shaped index: `# <host>` header, `> <summary>` blockquote,
  then a `## Pages` list of `- [title](relpath): summary`.
- **`llms-full.txt`** — every page's full markdown concatenated; each section prefixed
  with `## <title>` and a `Source: <url>` line.
- **`manifest.json`** — machine-readable index:

  ```json
  {
    "host": "example.com",
    "generated_from": "https://example.com",
    "page_count": 12,
    "pages": [
      {
        "source_url": "https://example.com/cli",
        "local_path": "cli/index.md",
        "title": "CLI",
        "content_hash": "…",
        "token_estimate": 247,
        "word_count": 1234,
        "summary": "…",
        "headings": ["Overview", "Usage", "…"],
        "sections": [
          {"slug": "_intro", "heading": "", "level": 0, "word_count": 40, "token_estimate": 53},
          {"slug": "usage", "heading": "Usage", "level": 2, "word_count": 300, "token_estimate": 396}
        ]
      }
    ]
  }
  ```

  `sections` is a heading-delimited chunk map (in document order; `_intro` = text before
  the first heading). Use each section's `token_estimate`/`word_count` to pick which part
  of a page to read before opening the full `local_path`.

## Folder mode → mirrored tree + the same 3 artifacts

A local folder input produces the same layout as crawl, over local files instead of URLs:
per-file `.md` written **mirroring the source subfolder structure** (e.g. `guide/setup.pdf`
→ `guide/setup.md`; extension stripped, parent dirs preserved), plus `llms.txt`,
`llms-full.txt`, and `manifest.json`. In the manifest, `host` is the folder's basename,
`generated_from` is the folder path, and each `source_url` is the local file's path (no
link rewriting — arbitrary documents have no inter-file links). Unconvertible/skipped files
don't appear in the artifacts.

## Reading it back

- Single page/file → `Read` the one `.md`.
- Crawl or folder → `Read` `manifest.json` first to pick relevant pages/files (title/
  summary/headings/sections), then open only the `local_path`s you need. Use `llms-full.txt`
  when you want everything in one pass.
