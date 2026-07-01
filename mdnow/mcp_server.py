"""MCP server for MDNow — exposes fetch_url, crawl_site, convert_file tools.

The server runs over stdio and is optional: it is only importable when the
`[mcp]` extra is installed. It reuses the existing conversion pipeline without
duplicating logic.
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from . import outline
from .doctor import missing_extra_message
from .extractor import Extracted

CHARACTER_LIMIT = 25_000

_INSTALL_HINT = missing_extra_message("mcp")


def _ensure_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(_INSTALL_HINT) from exc
    return FastMCP


FastMCP = _ensure_fastmcp()
mcp = FastMCP("mdnow_mcp")


class FetchUrlInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    url: str = Field(..., description="URL to fetch and convert to markdown", min_length=1)
    render: bool = Field(default=False, description="Use Camoufox stealth browser")
    allow_remote: bool = Field(default=False, description="Allow cloud API egress")


class CrawlSiteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    url: str = Field(..., description="Start URL for crawl", min_length=1)
    max_pages: int = Field(default=100, ge=1, le=1000, description="Max pages to crawl")
    no_llms: bool = Field(default=False, description="Skip llms.txt discovery")
    render: bool = Field(default=False, description="Use Camoufox stealth browser")
    allow_remote: bool = Field(default=False, description="Allow cloud API egress")


class ConvertFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    path: str = Field(..., description="Local file path or remote file URL", min_length=1)
    allow_remote: bool = Field(default=False, description="Allow cloud API egress")


def _truncate(text: str, limit: int = CHARACTER_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[...truncated: {len(text) - limit} chars omitted]"


def _format_result(extracted: Extracted, source_url: str, limit: int = CHARACTER_LIMIT) -> str:
    md = _truncate(extracted.markdown, limit)
    return json.dumps(
        {
            "source_url": source_url,
            "title": extracted.title,
            "word_count": extracted.word_count,
            "token_estimate": outline.token_estimate(md),
            "summary": outline.summary_of(md),
            "markdown": md,
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool(
    name="mdnow_fetch_url",
    annotations={"title": "Fetch URL to Markdown", "readOnlyHint": True, "openWorldHint": True},
)
async def fetch_url(params: FetchUrlInput) -> str:
    """Fetch a single URL and return clean markdown with metadata."""
    from .runner import _acquire

    try:
        result, extracted = await asyncio.to_thread(
            _acquire, params.url, params.render, params.allow_remote
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
    return _format_result(extracted, result.url)


@mcp.tool(
    name="mdnow_crawl_site",
    annotations={"title": "Crawl Site to Markdown", "readOnlyHint": True, "openWorldHint": True},
)
async def crawl_site(params: CrawlSiteInput) -> str:
    """Crawl a website and return a summary of converted pages."""
    from .crawler import crawl_site as _crawl
    from .discovery import discover
    from .fetcher import CamoufoxFetcher, StaticFetcher

    try:
        if not params.no_llms:
            found = await asyncio.to_thread(discover, params.url, crawl=True)
            if found is not None:
                return json.dumps(
                    {
                        "url": params.url,
                        "discovery": found.source_url,
                        "pages": [],
                        "note": "Site publishes llms.txt-compatible discovery content; use fetch_url on the discovery URL for full content.",
                    },
                    indent=2,
                    ensure_ascii=False,
                )

        with tempfile.TemporaryDirectory(prefix="mdnow_mcp_") as tmp:
            out = Path(tmp)
            # renderer created unconditionally (lazy browser) so crawl auto-escalates SPA pages
            if params.render:
                primary = renderer = CamoufoxFetcher()
            else:
                primary, renderer = StaticFetcher(), CamoufoxFetcher()
            try:
                ok, failed = await asyncio.to_thread(
                    _crawl, params.url, out, params.max_pages, False, primary, lambda _msg: None,
                    render=params.render, renderer=renderer,
                )
            finally:
                for f in {primary, renderer}:
                    await asyncio.to_thread(getattr(f, "close", lambda: None))

            manifest_path = out / "manifest.json"
            pages = json.loads(manifest_path.read_text(encoding="utf-8")).get("pages", []) if manifest_path.exists() else []

        return json.dumps(
            {
                "url": params.url,
                "pages_crawled": ok,
                "pages_failed": failed,
                "pages": pages,
            },
            indent=2,
            ensure_ascii=False,
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


@mcp.tool(
    name="mdnow_convert_file",
    annotations={"title": "Convert File to Markdown", "readOnlyHint": True, "openWorldHint": True},
)
async def convert_file(params: ConvertFileInput) -> str:
    """Convert a local file or remote file URL to clean markdown."""
    from .inputs import is_local_file
    from .runner import _acquire, _convert_file_to_extracted

    try:
        if is_local_file(params.path):
            extracted = await asyncio.to_thread(
                _convert_file_to_extracted, Path(params.path), params.allow_remote
            )
            source_url = params.path
        else:
            result, extracted = await asyncio.to_thread(
                _acquire, params.path, False, params.allow_remote
            )
            source_url = result.url
    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
    return _format_result(extracted, source_url)


def run() -> None:
    mcp.run(transport="stdio")
