---
title: "Phase 1: Add [mcp] Optional Dependency"
description: "Add mcp SDK as an optional extra in pyproject.toml."
status: completed
priority: P2
effort: 15m
branch: main
tags: [mcp, dependency, pyproject]
created: 2026-06-25
---

## Context Links

- [plan.md](plan.md) — Overview
- [pyproject.toml](/Users/longlh/Documents/Longle/MDNow/pyproject.toml) — Source of truth for dependencies
- [mdnow/cli.py](/Users/longlh/Documents/Longle/MDNow/mdnow/cli.py) — Entry point that will import mcp lazily

## Overview

Add the official MCP Python SDK as an optional dependency under the `[mcp]` extra in `pyproject.toml`. This mirrors the existing pattern for `[render]` (camoufox) and `[docs]` (markitdown).

## Key Insights

- The `mcp` package on PyPI is the official SDK: `mcp>=1.0.0`.
- Pin upper bound to `<2.0` to avoid breaking changes from major version churn.
- No code changes needed in this phase — just the dependency declaration.
- `fastmcp` is re-exported from `mcp.server.fastmcp` in the official SDK; no separate package needed.

## Requirements

- Add `mcp>=1.0.0,<2.0` to `[project.optional-dependencies]` under a new `mcp` key.
- Ensure `pip install -e ".[mcp]"` resolves correctly.
- Keep the base dependency list unchanged.

## Architecture

No architecture changes. This is a packaging-only phase.

## Related Code Files

| File | Action |
|------|--------|
| `pyproject.toml` | Add `[mcp]` extra |

## Implementation Steps

1. Open `pyproject.toml`.
2. Add the following under `[project.optional-dependencies]`:
   ```toml
   mcp = ["mcp>=1.0.0,<2.0"]
   ```
3. Verify with:
   ```bash
   .venv/bin/pip install -e ".[mcp]"
   .venv/bin/python -c "from mcp.server.fastmcp import FastMCP; print('OK')"
   ```

## Todo List

- [x] Add `mcp` extra to `pyproject.toml`
- [x] Verify install and import

## Success Criteria

- `pip install -e ".[mcp]"` succeeds.
- `python -c "from mcp.server.fastmcp import FastMCP"` prints `OK` without error.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| `mcp` package name collision | Low | High | Verify with `pip search mcp` or `pip install mcp` in a fresh venv first |
| Version incompatibility with Python 3.11 | Low | Medium | SDK requires >=3.10; we require >=3.11 — compatible |

## Security Considerations

None. This is a dependency declaration only.

## Next Steps

Phase 2: Implement `mdnow/mcp_server.py`.
