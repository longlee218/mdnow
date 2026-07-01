---
title: "Phase 5: README Sync + Demo Example"
description: "Update README.md with MCP usage instructions and provide a demo configuration snippet."
status: completed
priority: P2
effort: 1h
branch: main
tags: [mcp, docs, readme]
created: 2026-06-25
---

## Context Links

- [plan.md](plan.md) — Overview
- [README.md](/Users/longlh/Documents/Longle/MDNow/README.md) — Source of truth to update
- [CLAUDE.md](/Users/longlh/Documents/Longle/MDNow/CLAUDE.md) — Operating guidance (sync if architecture changes)

## Overview

Update `README.md` to document the new MCP server mode: install, configuration, and usage. Add a Claude Desktop configuration snippet as a demo. Keep `CLAUDE.md` in sync if any architecture or command changes are introduced.

## Key Insights

- README is the **source of truth** for behavior, flags, install, and usage. Any change to CLI flags or features must be reflected here.
- The MCP server is an **optional mode** — document it as a separate section, not the primary usage.
- Claude Desktop users need a `claude_desktop_config.json` snippet to add the server.
- The `--mcp` flag is the only new CLI surface; no other commands change.

## Requirements

### README Updates

1. **Install section**: Add `[mcp]` extra:
   ```bash
   pip install -e ".[mcp]"    # optional: expose mdnow as an MCP server
   ```

2. **New section: "MCP Server"** after "Usage" with:
   - What it is (expose mdnow tools to LLM clients).
   - How to run: `mdnow --mcp`.
   - Available tools table: `mdnow_fetch_url`, `mdnow_crawl_site`, `mdnow_convert_file`.
   - Claude Desktop configuration snippet.

3. **Flags table**: Add `--mcp` row.

4. **Behavior notes**: Mention that `--mcp` is mutually exclusive with normal URL/file input.

### CLAUDE.md Updates

- Add `mcp_server` to the architecture module list.
- Update the "Commands" section to mention `mdnow --mcp`.

## Architecture

No code architecture changes. Documentation-only phase.

## Related Code Files

| File | Action | Notes |
|------|--------|-------|
| `README.md` | Edit | Add MCP section, update install/flags |
| `CLAUDE.md` | Edit | Add `mcp_server` to module list, mention `--mcp` |

## Implementation Steps

1. **Edit `README.md` — Install section**:
   Add `[mcp]` to the install block:
   ```markdown
   # Only needed for MCP server mode:
   .venv/bin/pip install -e ".[mcp]"    # exposes mdnow tools to LLM clients
   ```

2. **Edit `README.md` — Add MCP Server section**:
   ```markdown
   ## MCP Server

   MDNow can run as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server, exposing its tools to compatible LLM clients (Claude Desktop, Claude Code, etc.).

   ```bash
   mdnow --mcp
   ```

   ### Tools

   | Tool | Description |
   |------|-------------|
   | `mdnow_fetch_url` | Fetch a single URL and return clean markdown |
   | `mdnow_crawl_site` | Crawl a site and return a summary of pages |
   | `mdnow_convert_file` | Convert a local file or remote file URL to markdown |

   ### Claude Desktop Configuration

   Add to your `claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "mdnow": {
         "command": "/path/to/.venv/bin/mdnow",
         "args": ["--mcp"]
       }
     }
   }
   ```
   ```

3. **Edit `README.md` — Flags table**:
   Add row:
   ```markdown
   | `--mcp` | Run as an MCP server (stdio transport) |
   ```

4. **Edit `CLAUDE.md` — Architecture**:
   Add `mcp_server` to the modules list:
   ```markdown
   Modules: `cli`, `discovery`/`llmstxt`, `fetcher`, `extractor`, `convert`, `crawler`, `urls`, `linkrewrite`, `guards`, `frontmatter`, `outline`, `artifacts`, `writer`, `mcp_server`.
   ```

5. **Edit `CLAUDE.md` — Commands**:
   Add:
   ```bash
   # MCP server mode
   .venv/bin/mdnow --mcp
   ```

6. **Verify README renders**:
   ```bash
   .venv/bin/python -c "import markdown; markdown.markdown(open('README.md').read())"
   # Or just eyeball it
   ```

## Todo List

- [x] Add `[mcp]` install instruction to README
- [x] Add "MCP Server" section with tools table
- [x] Add Claude Desktop config snippet
- [x] Add `--mcp` to flags table
- [x] Update CLAUDE.md module list
- [x] Update CLAUDE.md commands section
- [x] Verify no stale references remain

## Success Criteria

- README.md documents `--mcp`, `[mcp]` install, tools, and Claude Desktop config.
- CLAUDE.md mentions `mcp_server` in architecture and commands.
- No broken internal links or stale flags.
- README renders correctly as markdown.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| README becomes too long | Low | Low | Keep MCP section concise; link to spec for details |
| Config snippet has wrong path | Medium | Low | Use placeholder `/path/to/.venv/bin/mdnow` |

## Security Considerations

- No secrets in README snippets.
- Config snippet uses local path (no remote URLs).

## Next Steps

Implementation complete. Hand off to team lead for review.
