---
title: "Phase 2: Implement mdnow/mcp_server.py"
description: "Implement the MCP server with three tools: fetch_url, crawl_site, convert_file."
status: completed
priority: P2
effort: 2h
branch: main
tags: [mcp, server, implementation]
created: 2026-06-25
---

## Context Links

- [plan.md](plan.md) — Overview
- [mdnow/cli.py](/Users/longlh/Documents/Longle/MDNow/mdnow/cli.py) — Reuse `_acquire`, `_write_extracted`, `_convert_file`, `_convert_youtube`
- [mdnow/crawler.py](/Users/longlh/Documents/Longle/MDNow/mdnow/crawler.py) — Reuse `crawl_site`
- [mdnow/convert.py](/Users/longlh/Documents/Longle/MDNow/mdnow/convert.py) — Reuse `from_path`, `from_url`, `from_bytes`
- [mdnow/fetcher.py](/Users/longlh/Documents/Longle/MDNow/mdnow/fetcher.py) — Reuse `StaticFetcher`, `CamoufoxFetcher`
- [mdnow/writer.py](/Users/longlh/Documents/Longle/MDNow/mdnow/writer.py) — Reuse `write` (indirectly via `_write_extracted`)
- [Python MCP Guide](/Users/longlh/Documents/Longle/MDNow/.claude/skills/mcp-builder/reference/python_mcp_server.md) — FastMCP patterns, Pydantic v2, annotations

## Overview

Create `mdnow/mcp_server.py` — a FastMCP-based MCP server exposing three tools. The module is <200 lines, lazy-imports the MCP SDK, and reuses existing internal functions from `cli.py`, `crawler.py`, and `convert.py`.

## Key Insights

- **FastMCP auto-generates schemas** from Pydantic models and docstrings — minimal boilerplate.
- **Stdio transport** is default when `mcp.run()` is called; perfect for CLI integration.
- **Never log to stdout** in MCP mode — protocol messages use stdout. Use `logging` (stderr) or silence entirely.
- **Character limit** — 25,000 chars per response to avoid overwhelming LLM context windows.
- **Tool annotations** — all tools are `readOnlyHint=True`, `openWorldHint=True` (they fetch external content).
- **Crawl output** — return a JSON summary (page count, file paths, manifest) rather than full concatenated text to stay within limits.

## Requirements

### Functional

1. `fetch_url(url: str, render: bool = False, allow_remote: bool = False) -> str`
   - Fetches a single URL, extracts markdown, returns it (truncated to 25k chars if needed).
   - Reuses `cli._acquire` for the fetch/extract funnel.
   - Returns the markdown body with frontmatter metadata as JSON.

2. `crawl_site(url: str, max_pages: int = 100, render: bool = False, allow_remote: bool = False) -> str`
   - Crawls a site, returns a JSON summary: page count, output directory, list of files written.
   - Reuses `crawler.crawl_site`.
   - Does NOT return full concatenated markdown (too large); returns manifest summary.

3. `convert_file(path: str, allow_remote: bool = False) -> str`
   - Converts a local file or remote non-HTML URL to markdown.
   - Reuses `convert.from_path` (local) or `cli._acquire` (remote non-HTML).
   - Returns markdown body with metadata.

### Non-Functional

- Module must be <200 lines.
- Lazy-import `mcp` SDK (raise `RuntimeError` with install hint if missing).
- All network I/O via async/await (FastMCP tools are async by default).
- Pydantic v2 models for input validation with `Field(..., description=...)`.
- Consistent error formatting: `{"error": "..."}` JSON on failure.

## Architecture

```
mdnow/mcp_server.py
├── FastMCP("mdnow_mcp")
├── Pydantic input models (FetchUrlInput, CrawlSiteInput, ConvertFileInput)
├── _ensure_mcp() — lazy import guard
├── _truncate(text, limit=25000) — shared truncation helper
├── _format_result(extracted, source_url) → JSON string with metadata
├── fetch_url(params) → str
├── crawl_site(params) → str
├── convert_file(params) → str
└── run() → mcp.run() (stdio transport)
```

## Related Code Files

| File | Action | Notes |
|------|--------|-------|
| `mdnow/mcp_server.py` | Create | New file, <200 lines |
| `mdnow/cli.py` | Read | Reuse `_acquire`, `_write_extracted`, `_convert_file`, `_convert_youtube` |
| `mdnow/crawler.py` | Read | Reuse `crawl_site` |
| `mdnow/convert.py` | Read | Reuse `from_path`, `from_url`, `from_bytes` |
| `mdnow/fetcher.py` | Read | Reuse `StaticFetcher`, `CamoufoxFetcher` |

## Implementation Steps

1. **Create `mdnow/mcp_server.py`** with the following structure:

   ```python
   """MCP server for MDNow — exposes fetch_url, crawl_site, convert_file tools."""
   from __future__ import annotations

   import json
   import logging
   from pathlib import Path
   from typing import Literal

   from pydantic import BaseModel, Field, ConfigDict

   # Lazy import guard for mcp SDK
   def _ensure_mcp():
       try:
           from mcp.server.fastmcp import FastMCP
           return FastMCP
       except ImportError as exc:
           raise RuntimeError(
               "mcp not installed. Run: pip install 'mdnow[mcp]'"
           ) from exc

   FastMCP = _ensure_mcp()
   mcp = FastMCP("mdnow_mcp")

   CHARACTER_LIMIT = 25000

   class FetchUrlInput(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
       url: str = Field(..., description="URL to fetch and convert to markdown", min_length=1)
       render: bool = Field(default=False, description="Use Camoufox stealth browser for JS-heavy sites")
       allow_remote: bool = Field(default=False, description="Allow cloud API egress (audio/video/YouTube)")

   class CrawlSiteInput(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
       url: str = Field(..., description="Start URL for crawl", min_length=1)
       max_pages: int = Field(default=100, ge=1, le=1000, description="Max pages to crawl")
       render: bool = Field(default=False, description="Use Camoufox stealth browser")
       allow_remote: bool = Field(default=False, description="Allow cloud API egress")

   class ConvertFileInput(BaseModel):
       model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
       path: str = Field(..., description="Local file path or remote file URL to convert", min_length=1)
       allow_remote: bool = Field(default=False, description="Allow cloud API egress")

   def _truncate(text: str, limit: int = CHARACTER_LIMIT) -> str:
       if len(text) <= limit:
           return text
       return text[:limit] + f"\n\n[...truncated: {len(text) - limit} chars omitted]"

   def _format_result(extracted, source_url: str, word_count: int) -> str:
       return json.dumps({
           "source_url": source_url,
           "title": extracted.title,
           "word_count": word_count,
           "markdown": extracted.markdown,
       }, indent=2, ensure_ascii=False)

   @mcp.tool(
       name="mdnow_fetch_url",
       annotations={"title": "Fetch URL to Markdown", "readOnlyHint": True, "openWorldHint": True}
   )
   async def fetch_url(params: FetchUrlInput) -> str:
       """Fetch a single URL and return clean markdown.

       Reuses the cheapest-path-first funnel: discovery (llms.txt) → static fetch
       → render escalation. Returns markdown with metadata.
       """
       from .cli import _acquire, _slug
       from .extractor import Extracted

       result, extracted = _acquire(params.url, params.render, params.allow_remote)
       slug = _slug(extracted.title, result.url)
       body = _format_result(extracted, result.url, extracted.word_count)
       return _truncate(body)

   @mcp.tool(
       name="mdnow_crawl_site",
       annotations={"title": "Crawl Site to Markdown", "readOnlyHint": True, "openWorldHint": True}
   )
   async def crawl_site(params: CrawlSiteInput) -> str:
       """Crawl a website and return a summary of pages converted to markdown.

       Returns a JSON summary with page count, output files, and per-page metadata.
       Does NOT return full concatenated text (use fetch_url for individual pages).
       """
       from .crawler import crawl_site as _crawl
       from .fetcher import CamoufoxFetcher, StaticFetcher
       from .urls import canonical
       from urllib.parse import urlsplit
       import tempfile

       out = Path(tempfile.mkdtemp(prefix="mdnow_mcp_"))
       fetcher = CamoufoxFetcher() if params.render else StaticFetcher()
       try:
           ok, failed = _crawl(params.url, out, params.max_pages, False, fetcher, lambda msg: None)
       finally:
           getattr(fetcher, "close", lambda: None)()

       # Build manifest from written files
       pages = []
       for md_file in sorted(out.glob("*.md")):
           if md_file.name in ("llms.txt", "llms-full.txt"):
               continue
           text = md_file.read_text(encoding="utf-8")
           # Extract title from frontmatter or first heading
           title = None
           if text.startswith("---"):
               parts = text.split("---", 2)
               if len(parts) >= 3:
                   import yaml
                   meta = yaml.safe_load(parts[1])
                   if isinstance(meta, dict):
                       title = meta.get("title")
           pages.append({
               "local_path": str(md_file.relative_to(out)),
               "title": title or md_file.stem,
           })

       return json.dumps({
           "url": params.url,
           "pages_crawled": ok,
           "pages_failed": failed,
           "output_directory": str(out),
           "pages": pages,
       }, indent=2, ensure_ascii=False)

   @mcp.tool(
       name="mdnow_convert_file",
       annotations={"title": "Convert File to Markdown", "readOnlyHint": True, "openWorldHint": True}
   )
   async def convert_file(params: ConvertFileInput) -> str:
       """Convert a local file or remote file URL to clean markdown.

       Supports PDF, Office, images (OCR), audio/video (with allow_remote),
       and other formats via markitdown.
       """
       from .cli import _is_local_file, _convert_file, _acquire, _slug
       from pathlib import Path

       if _is_local_file(params.path):
           extracted = _convert_file(Path(params.path), Path("."), params.allow_remote)
           # _convert_file writes to disk; we need the Extracted object directly
           # TODO: refactor cli._convert_file to return Extracted without writing
       else:
           # Remote non-HTML file — treat as URL
           result, extracted = _acquire(params.path, False, params.allow_remote)
       body = _format_result(extracted, params.path, extracted.word_count)
       return _truncate(body)
   ```

2. **Refactor `cli._convert_file` to return `Extracted` without side effects** — or create a new `_convert_file_to_extracted` helper that returns the `Extracted` directly, leaving `_write_extracted` to the caller. This avoids writing to disk in the MCP tool.

   ```python
   # In cli.py, split _convert_file:
   def _convert_file_to_extracted(path: Path, allow_remote: bool) -> Extracted:
       """Convert a local file to markdown. Raises ValueError if nothing usable."""
       return convert.from_path(path, allow_remote=allow_remote)

   def _convert_file(path: Path, out: Path, allow_remote: bool) -> None:
       """Convert a local file and write it to out/."""
       extracted = _convert_file_to_extracted(path, allow_remote)
       _write_extracted(out, _file_slug(path), str(path), extracted)
   ```

3. **Update `mcp_server.py` `convert_file` to use `_convert_file_to_extracted`**.

4. **Verify compile**:
   ```bash
   .venv/bin/python -m py_compile mdnow/mcp_server.py
   ```

## Todo List

- [x] Create `mdnow/mcp_server.py` with FastMCP setup and Pydantic models
- [x] Implement `_truncate` helper
- [x] Implement `_format_result` helper
- [x] Implement `fetch_url` tool (reuse `_acquire`)
- [x] Implement `crawl_site` tool (reuse `crawl_site`, return summary)
- [x] Implement `convert_file` tool (reuse `convert.from_path` / `_acquire`)
- [x] Refactor `cli._convert_file` to return `Extracted` without writing
- [x] Verify `python -m py_compile mdnow/mcp_server.py`

## Success Criteria

- `python -c "from mdnow.mcp_server import mcp; print(mcp.name)"` prints `mdnow_mcp`.
- `python mdnow/mcp_server.py` starts the stdio server (blocks, no error).
- All three tools are discoverable via `tools/list` MCP request.
- Input validation rejects invalid URLs / paths via Pydantic.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `cli._acquire` is sync (network I/O) | High | Medium | Wrap in `asyncio.to_thread()` inside async tools |
| `crawl_site` is sync | High | Medium | Wrap in `asyncio.to_thread()` |
| Circular import cli↔mcp_server | Low | High | Import inside functions, not at module level |
| Large file conversion blocks event loop | Medium | High | Use `asyncio.to_thread()` for all sync I/O |

## Security Considerations

- Input validation via Pydantic prevents malformed URLs/paths.
- `allow_remote` is opt-in (default `False`) — same as CLI.
- No secrets or credentials exposed.
- Crawl output uses a temp directory; no persistent disk writes unless explicitly requested.

## Next Steps

Phase 3: Wire `--mcp` flag into `mdnow/cli.py`.
