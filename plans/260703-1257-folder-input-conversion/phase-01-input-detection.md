# Phase 01 — Input detection: `is_local_dir`

## Context Links
- `mdnow/inputs.py` (existing `is_local_file`, `is_youtube`)
- `tests/test_cli_main.py` (existing input-routing tests) — no dedicated `test_inputs.py` today
- CLAUDE.md → "Input-type fork at CLI entry"

## Overview
- **Priority:** P2 (foundation for Phase 03 routing)
- **Status:** ✅ done
- **Description:** Add a directory-detection predicate mirroring `is_local_file`.

## Key Insights
- `is_local_file` already excludes `http`/`https` schemes via `urlparse` before the FS check — copy that exact shape so a URL is never mistaken for a path.
- `Path(arg).is_dir()` is the only differing line vs `is_local_file`.
- `inputs.py` is tiny; adding one function keeps it well under 200 lines.

## Requirements
- Functional: `is_local_dir("./docs")` → `True` when the dir exists; `False` for files, non-existent paths, and `http(s)` URLs. Malformed input → `False` (never raise).
- Non-functional: network-free, pure, deterministic.

## Architecture
Pure predicate in `inputs.py`. No state, no I/O beyond a `Path.is_dir()` stat.

```python
def is_local_dir(arg: str) -> bool:
    """True if arg is a path to an existing local directory (not an http(s) URL)."""
    try:
        scheme = urlparse(arg).scheme
    except ValueError:
        return False
    return scheme not in ("http", "https") and Path(arg).is_dir()
```

## Related Code Files
- **Modify:** `mdnow/inputs.py` (add `is_local_dir`)
- **Create:** `tests/test_inputs.py` (new — covers `is_local_dir`; may also fold in a couple `is_local_file`/`is_youtube` assertions if not covered elsewhere, but keep scope tight per YAGNI)

## Implementation Steps
1. (RED) Write `tests/test_inputs.py` with cases: existing dir → True (use `tmp_path`); existing file → False; non-existent path → False; `https://x.com` → False; `""` → False.
2. Run tests → expect failure (`is_local_dir` undefined).
3. (GREEN) Add `is_local_dir` to `inputs.py`.
4. Run tests → pass.
5. `python -m compileall -q mdnow`.

## Todo List
- [ ] Write `tests/test_inputs.py` (RED)
- [ ] Add `is_local_dir` to `inputs.py`
- [ ] Tests pass (GREEN)
- [ ] compileall clean

## Success Criteria
- `is_local_dir` returns correct bool for dir / file / URL / missing / empty inputs.
- New tests pass; no regression in existing suite.

## Risk Assessment
- Low. A path that is both a valid URL-ish string and a local dir is not a real scenario (URL scheme check guards it).

## Security Considerations
- Read-only `stat`; no traversal or writes here. No secrets involved.

## Next Steps
- Phase 02 consumes `is_local_dir` indirectly (Phase 03 wires it into `cli.main`).
