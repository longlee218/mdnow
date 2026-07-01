---
title: "MCP Server Integration for MDNow"
description: "Add an MCP server exposing mdnow tools (fetch_url, crawl_site, convert_file) via stdio, with a --mcp CLI flag."
status: completed
priority: P2
effort: 6h
branch: main
tags: [mcp, integration, cli, server]
created: 2026-06-25
---

## Overview

Expose MDNow's core capabilities as an MCP (Model Context Protocol) server so that LLM clients (Claude Desktop, Claude Code, etc.) can invoke `fetch_url`, `crawl_site`, and `convert_file` as tools. The server is optional: installed via `[mcp]` extra, activated via `--mcp` flag.

## Phases

| Phase | Description | Status | Effort |
|-------|-------------|--------|--------|
| [phase-01-add-mcp-dependency](phase-01-add-mcp-dependency.md) | Add `[mcp]` optional dependency to pyproject.toml | done | 15m |
| [phase-02-implement-mcp-server](phase-02-implement-mcp-server.md) | Implement `mdnow/mcp_server.py` with three tools | done | 2h |
| [phase-03-wire-mcp-flag](phase-03-wire-mcp-flag.md) | Wire `--mcp` flag into `mdnow/cli.py` | done | 30m |
| [phase-04-write-tests](phase-04-write-tests.md) | Write tests for MCP server and tool handlers | done | 2h |
| [phase-05-readme-sync](phase-05-readme-sync.md) | README sync + demo example | done | 1h |

## Key Decisions

- **FastMCP** from `mcp` Python SDK — simplest, decorator-based, auto-generates schemas.
- **Stdio transport** — MDNow is a CLI tool, stdio is the natural fit.
- **Lazy import** of `mcp` SDK — mirrors `camoufox` and `markitdown` patterns; base install unaffected.
- **Three tools** — `fetch_url`, `crawl_site`, `convert_file` — map 1:1 to existing CLI use cases.
- **Reuse internal functions** — `runner._acquire`, `crawler.crawl_site`, `runner._convert_file_to_extracted` — no duplication.
- **Character limit** — 25,000 chars per tool response to respect context windows.
- **No state mutation** — all tools are read-only; annotations set accordingly.

## Risks

| Risk | Mitigation |
|------|------------|
| MCP SDK version churn | Pin `mcp>=1.0,<2.0` in pyproject.toml |
| Stdio logging collision | Log to stderr only; never print to stdout in MCP mode |
| Large crawl output | Truncate to CHARACTER_LIMIT; suggest `--max-pages` in error |
| Circular import cli↔mcp_server | Keep mcp_server.py independent; cli imports it only inside `--mcp` branch |

## Unresolved Questions

1. Should `crawl_site` return a manifest summary or the full concatenated markdown? — Decision: summary JSON with file paths; full content via `fetch_url` on individual pages.
2. Should we expose MCP resources (e.g., `file://out/article.md`) in addition to tools? — Decision: defer to Phase 2 stretch; tools are MVP.
3. Should `convert_file` support remote URLs (non-HTML) or only local paths? — Decision: both, same as CLI (`_is_local_file` check).
