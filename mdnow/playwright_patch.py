"""Self-healing patch for a Playwright Firefox driver crash.

Playwright's bundled driver reads `pageError.location.url` without a null check
(coreBundle.js). SPA pages (e.g. Angular docs sites) throw uncaught JS errors
whose `location` is undefined, which crashes the whole Node driver process — and
because a crawl reuses one browser, one crash aborts the entire run.

We patch the two offending dereferences to be null-safe with schema-valid
defaults (the protocol requires `location.url` to be a string, so `undefined`
alone still fails validation). The patch is idempotent and best-effort: a
reinstall of playwright wipes it, so we re-apply it lazily before the browser
launches. Any failure here is swallowed — a failed patch must never block a
render that might have worked anyway.
"""
from __future__ import annotations

from pathlib import Path

# unpatched → patched (three dereferences, appearing twice in the bundle)
_REPLACEMENTS = (
    ("url: pageError.location.url,", 'url: pageError.location?.url ?? "",'),
    ("line: pageError.location.lineNumber,", "line: pageError.location?.lineNumber ?? 0,"),
    ("column: pageError.location.columnNumber", "column: pageError.location?.columnNumber ?? 0"),
)


def _core_bundle_path() -> Path | None:
    try:
        import playwright
    except ImportError:
        return None
    p = Path(playwright.__file__).parent / "driver" / "package" / "lib" / "coreBundle.js"
    return p if p.exists() else None


def ensure_driver_patched() -> bool:
    """Apply the null-safe pageError patch if needed. Returns True if patched now.

    Idempotent: a no-op when already patched or the file/package is absent.
    Never raises — render must proceed even if patching fails.
    """
    try:
        path = _core_bundle_path()
        if path is None:
            return False
        text = path.read_text(encoding="utf-8")
        if all(old not in text for old, _ in _REPLACEMENTS):
            return False  # already patched (or bundle changed) → nothing to do
        for old, new in _REPLACEMENTS:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        return True
    except Exception:
        return False  # best-effort — swallow and let the render attempt proceed
