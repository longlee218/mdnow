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
        "headings": ["Overview", "Usage", "…"]
      }
    ]
  }
  ```

## Reading it back

- Single page/file → `Read` the one `.md`.
- Crawl → `Read` `manifest.json` first to pick relevant pages (title/summary/headings),
  then open only the `local_path`s you need. Use `llms-full.txt` when you want everything
  in one pass.
