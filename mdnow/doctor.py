"""`mdnow --doctor` probes + the shared missing-extra hint helper.

Probes are best-effort and network-free: importlib.util.find_spec checks for
installed extras, and the Camoufox browser-binary check never triggers a
download (download_if_missing=False) or a network call.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import sys

# mdnow is distributed via git (not PyPI), so install hints use the direct-ref spec.
_GIT_URL = "git+https://github.com/longlee218/mdnow"
_EXTRAS = {"render": "render", "docs": "docs"}


def _install_hint(extra: str) -> str:
    return f'uv tool install "mdnow[{extra}] @ {_GIT_URL}"'


def missing_extra_message(feature: str) -> str:
    """Shared "feature X needs extra Y" hint, reused by render/docs call sites."""
    extra = _EXTRAS[feature]
    return f"{feature} requires the [{extra}] extra. Run: {_install_hint(extra)}"


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str
    fix: str | None = None  # copy-paste fix command, set when ok is False


def _extra_installed(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _check_render_browser() -> Check:
    if not _extra_installed("camoufox"):
        return Check("render browser", False, "not checked ([render] not installed)",
                      fix=_install_hint("render"))
    try:
        import camoufox.pkgman as pm

        pm.camoufox_path(download_if_missing=False)
        return Check("render browser", True, f"downloaded ({pm.installed_verstr()})")
    except Exception:
        # Camoufox's detection API may differ by version — best-effort only.
        return Check("render browser", False, "unknown — run: mdnow --fetch-browser",
                      fix="mdnow --fetch-browser")


def _check_extra(feature: str, module: str) -> Check:
    extra = _EXTRAS[feature]
    if _extra_installed(module):
        return Check(f"[{extra}] extra", True, "installed")
    return Check(f"[{extra}] extra", False, "not installed", fix=_install_hint(extra))


def _check_skill() -> Check:
    from .commands import DEFAULT_SKILL_DIR  # local import: avoids a circular import

    skill_md = DEFAULT_SKILL_DIR / "SKILL.md"
    if skill_md.exists():
        return Check("Claude skill", True, f"installed at {DEFAULT_SKILL_DIR}")
    return Check("Claude skill", False, "not installed", fix="mdnow --install-skill")


def _check_session_store() -> Check:
    from . import sessions  # local import: keeps doctor's top level stdlib-only

    if sessions.SESSION_DIR.is_dir():
        count = len(list(sessions.SESSION_DIR.glob("*.txt")))
    else:
        count = 0
    # informational only: count + dir, never the host list (avoid surprises)
    detail = f"{count} saved at {sessions.SESSION_DIR}" if count else "none"
    return Check("saved sessions", True, detail)


def run_checks() -> list[Check]:
    """All doctor checks, in report order."""
    py = sys.version_info
    checks = [
        Check("Python", True, f"{py.major}.{py.minor}.{py.micro}"),
        Check("base pipeline", True, "OK (httpx, trafilatura, typer)"),
        _check_extra("docs", "markitdown"),
        _check_extra("render", "camoufox"),
        _check_render_browser(),
        _check_skill(),
        _check_session_store(),
    ]
    return checks


def render_report(checks: list[Check]) -> str:
    """Human-readable report text for the CLI."""
    lines = ["mdnow doctor", "-" * 40]
    for c in checks:
        mark = "OK" if c.ok else "MISSING"
        lines.append(f"[{mark}] {c.name}: {c.detail}")
        if not c.ok and c.fix:
            lines.append(f"       fix: {c.fix}")
    return "\n".join(lines)
