---
title: "Phase 3: Wire --mcp Flag into CLI"
description: "Add --mcp flag to mdnow/cli.py that launches the MCP server instead of normal CLI execution."
status: completed
priority: P2
effort: 30m
branch: main
tags: [mcp, cli, flag]
created: 2026-06-25
---

## Context Links

- [plan.md](plan.md) — Overview
- [mdnow/cli.py](/Users/longlh/Documents/Longle/MDNow/mdnow/cli.py) — Entry point to modify
- [mdnow/mcp_server.py](phase-02-implement-mcp-server.md) — Server to invoke

## Overview

Add a `--mcp` boolean flag to `cli.main()`. When `--mcp` is passed, skip all normal CLI logic and launch the MCP server via `mcp_server.run()`. This is the simplest integration: one flag switches modes.

## Key Insights

- `--mcp` is mutually exclusive with `url` argument — when `--mcp` is set, `url` is ignored.
- The MCP server runs its own stdio transport loop; it never returns to `cli.main`.
- Lazy-import `mcp_server` inside the `--mcp` branch to avoid import errors when `[mcp]` is not installed.
- `typer` doesn't natively support mutually exclusive groups, but we can handle it manually: if `--mcp` and `url` are both provided, ignore `url` (or warn).

## Requirements

- Add `--mcp: bool = typer.Option(False, "--mcp", help="Run as an MCP server (stdio transport)")` to `cli.main()` signature.
- If `--mcp` is True:
  - Lazy-import `mdnow.mcp_server`.
  - Call `mcp_server.run()`.
  - The function does not return (stdio loop blocks).
- If `--mcp` is False: normal CLI behavior unchanged.

## Architecture

```
cli.main()
├── if mcp:
│   └── import mdnow.mcp_server; mcp_server.run()
├── else:
│   └── existing logic (local file, youtube, discovery, crawl, single)
```

## Related Code Files

| File | Action | Notes |
|------|--------|-------|
| `mdnow/cli.py` | Edit | Add `--mcp` flag and branch |
| `mdnow/mcp_server.py` | Read | Ensure `run()` exists and is callable |

## Implementation Steps

1. **Modify `cli.main()` signature** — add `mcp: bool = typer.Option(False, "--mcp", help="Run as an MCP server")`.

2. **Add `--mcp` branch at the top of `main()`**:
   ```python
   def main(
       url: str = typer.Argument("", help="Website URL or file to convert"),
       ...
       mcp: bool = typer.Option(False, "--mcp", help="Run as an MCP server (stdio transport)"),
       ...
   ) -> None:
       if mcp:
           try:
               from . import mcp_server
           except ImportError as exc:
               typer.secho(
                   "Error: MCP server requires the [mcp] extra. "
                   "Run: pip install 'mdnow[mcp]'",
                   fg=typer.colors.RED,
                   err=True,
               )
               raise typer.Exit(1) from exc
           mcp_server.run()
           return
       # ... rest of existing logic
   ```

3. **Make `url` argument optional** when `--mcp` is used. Since `typer` doesn't support dynamic required/optional, set `url: str = typer.Argument("", ...)` with a default empty string, then validate:
   ```python
   if not mcp and not url:
       typer.secho("Error: URL or file path is required.", fg=typer.colors.RED, err=True)
       raise typer.Exit(1)
   ```

4. **Verify**:
   ```bash
   .venv/bin/mdnow --mcp
   # Should start MCP server (blocks, no error)
   ```

## Todo List

- [x] Add `mcp: bool` option to `cli.main()` signature
- [x] Add `--mcp` branch with lazy import of `mcp_server`
- [x] Handle missing `[mcp]` extra gracefully
- [x] Make `url` argument optional (default empty string) with manual validation
- [x] Verify `mdnow --mcp` starts the server

## Success Criteria

- `mdnow --mcp` starts the MCP server (blocks on stdio).
- `mdnow --mcp` without `[mcp]` installed prints a clear error and exits 1.
- `mdnow https://example.com` (without `--mcp`) still works normally.
- `mdnow` (no args, no `--mcp`) prints error and exits 1.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Typer argument default breaks existing tests | Medium | Medium | Update tests to pass explicit `url` arg |
| MCP server blocks forever in tests | Low | High | Tests for `--mcp` should mock `mcp_server.run()` |

## Security Considerations

- `--mcp` does not expose any new attack surface; it just changes the entry mode.
- The MCP server inherits all existing input validation (Pydantic in tools, URL guards in `_acquire`).

## Next Steps

Phase 4: Write tests for MCP server and tool handlers.
