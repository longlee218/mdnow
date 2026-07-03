---
name: project-optional-extras
description: mdnow's optional-dependency guarding convention and the ImportError-vs-RuntimeError exception-type gotcha at CLI call sites
metadata:
  type: project
---

mdnow declares 2 optional extras: `[render]` (camoufox) and `[docs]` (markitdown). All are imported lazily. `doctor.missing_extra_message(feature)` is the single source for the "feature X needs extra Y" hint (reused by convert.py, fetcher.py, commands.py).

**Why:** founding constraint is fully-local base install; optional heavy deps must never break `pip install mdnow`.

**How to apply / gotcha:** call sites that import an optional module must catch the RIGHT exception type. Each optional module raises `ImportError` when missing; callers should catch that and surface a friendly hint via `missing_extra_message()`. When reviewing new optional-extra call sites, verify the except clause matches what actually propagates.
