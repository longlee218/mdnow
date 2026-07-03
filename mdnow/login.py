"""Interactive login capture: headed Camoufox → saved session cookies.

Opens a VISIBLE browser window at the target URL and lets the user log in
by hand (2FA/captcha included — it's a real person at a real browser).
mdnow never sees credentials: it only reads the cookies the site set,
and stores them via sessions.save_session for auto-reuse.

Cookie VALUES are secrets: never echoed or logged; they go straight to
the owner-only session file. Errors name the host, never a value.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from . import sessions, ui

LOGIN_GOTO_TIMEOUT_MS = 60_000


def run_login(url: str) -> Path:
    """Open a headed browser at *url*, wait for Enter, save the session.

    Returns the session file path. Raises RuntimeError if the [render]
    extra is missing or the login window closed before capture.
    """
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme not in ("http", "https") or not host:
        raise ValueError("--login needs a full http(s) URL (e.g. https://host/path).")
    try:
        from camoufox.sync_api import Camoufox
    except ImportError as exc:
        from .doctor import missing_extra_message
        raise RuntimeError(missing_extra_message("render")) from exc
    # self-heal a Playwright driver crash on SPA page errors (see module)
    from .playwright_patch import ensure_driver_patched
    ensure_driver_patched()

    with Camoufox(headless=False) as browser:
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=LOGIN_GOTO_TIMEOUT_MS)
        except Exception:
            pass  # best-effort: slow/anti-bot first paint — user can still navigate
        ui.note(f"Log in to {host} in the browser window that just opened.")
        input("Press Enter here when you are logged in... ")
        try:
            cookies = page.context.cookies()
        except Exception as exc:
            raise RuntimeError(
                f"Login window for {host} closed before capture — run --login again "
                "and press Enter before closing the browser."
            ) from exc
    return sessions.save_session(host, cookies)
