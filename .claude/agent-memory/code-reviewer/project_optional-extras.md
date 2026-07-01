---
name: project-optional-extras
description: mdnow's optional-dependency guarding convention and the ImportError-vs-RuntimeError exception-type gotcha at CLI call sites
metadata:
  type: project
---

mdnow declares 3 optional extras: `[render]` (camoufox), `[docs]` (markitdown), `[mcp]` (mcp). All are imported lazily. `doctor.missing_extra_message(feature)` is the single source for the "feature X needs extra Y" hint (reused by convert.py, fetcher.py, commands.py, mcp_server.py).

**Why:** founding constraint is fully-local base install; optional heavy deps must never break `pip install mdnow`.

**How to apply / gotcha:** call sites that import an optional module must catch the RIGHT exception type. `mcp_server.py` converts the inner `ImportError` (missing `mcp`) into a `RuntimeError` at *module import time* (top-level `_ensure_fastmcp()` call). So `from . import mcp_server` raises `RuntimeError`, not `ImportError`. Any caller catching only `ImportError` will leak an ugly traceback. When reviewing new optional-extra call sites, verify the except clause matches what actually propagates.
