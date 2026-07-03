"""Fetch backends. `Fetcher` is a swappable interface (Protocol).

StaticFetcher is the default fast path. Later phases add CamoufoxFetcher
behind the same interface, so nothing downstream changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

import httpx

# Browser-like UA: some sites reject the default httpx UA. Full anti-bot = Phase 3.
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 20.0
RENDER_TIMEOUT = 30.0


@dataclass
class FetchResult:
    url: str          # final URL after redirects
    content: bytes    # raw bytes; charset handled downstream by trafilatura
    content_type: str


class Fetcher(Protocol):
    def fetch(self, url: str) -> FetchResult: ...


def _cookie_jar(cookies: list[dict] | None, fallback_domain: str = "") -> httpx.Cookies | None:
    """Build a domain/path-scoped jar so httpx only sends matching cookies.

    A cookie without a domain is scoped to `fallback_domain` (the request
    host): an empty-domain cookie would otherwise be sent to EVERY host,
    leaking the session to a cross-host redirect (e.g. a 302 to an SSO host).
    """
    if not cookies:
        return None
    jar = httpx.Cookies()
    for c in cookies:
        jar.set(c["name"], c["value"],
                domain=c.get("domain") or fallback_domain, path=c.get("path", "/"))
    return jar


class StaticFetcher:
    """httpx GET with timeout + a single retry.

    `headers`/`cookies` carry auth material for private/internal sites
    (see auth.py). A user-supplied User-Agent header overrides the default.
    """

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_UA,
        headers: dict[str, str] | None = None,
        cookies: list[dict] | None = None,
    ):
        self._timeout = timeout
        self._headers = {"User-Agent": user_agent, **(headers or {})}
        self._cookie_list = cookies

    def fetch(self, url: str) -> FetchResult:
        # jar is built per-fetch so domain-less cookies scope to THIS host only
        cookies = _cookie_jar(self._cookie_list, urlsplit(url).hostname or "")
        last_exc: Exception | None = None
        for _ in range(2):  # initial attempt + 1 retry (transient failures only)
            try:
                resp = httpx.get(
                    url,
                    follow_redirects=True,
                    timeout=self._timeout,
                    headers=self._headers,
                    cookies=cookies,
                )
                resp.raise_for_status()
                return FetchResult(
                    url=str(resp.url),
                    content=resp.content,
                    content_type=resp.headers.get("content-type", ""),
                )
            except httpx.HTTPStatusError as exc:
                # 4xx is the server's final answer — fail fast, don't hammer.
                if exc.response.status_code < 500:
                    raise RuntimeError(f"Failed to fetch {url}: {exc}") from exc
                last_exc = exc  # 5xx: retry once
            except httpx.TransportError as exc:
                last_exc = exc  # timeout / connection error: retry once
        raise RuntimeError(f"Failed to fetch {url}: {last_exc}")


class CamoufoxFetcher:
    """Stealth headless render tier (JS-heavy / anti-bot sites).

    Reuses ONE browser across fetches (cheap per-page during a crawl).
    Call close() when done — or use as a context manager. camoufox is imported
    lazily so static-only users never need it installed.
    """

    def __init__(
        self,
        timeout: float = RENDER_TIMEOUT,
        headers: dict[str, str] | None = None,
        cookies: list[dict] | None = None,
    ):
        self._timeout_ms = int(timeout * 1000)
        self._headers = headers or {}
        self._cookies = cookies or []
        self._cm = None
        self._browser = None

    def _cookies_for(self, url: str) -> list[dict]:
        """Playwright cookies need either domain+path or a url to scope them."""
        out = []
        for c in self._cookies:
            if c.get("domain"):
                out.append({"name": c["name"], "value": c["value"],
                            "domain": c["domain"], "path": c.get("path", "/")})
            else:
                out.append({"name": c["name"], "value": c["value"], "url": url})
        return out

    def _ensure(self):
        if self._browser is None:
            try:
                from camoufox.sync_api import Camoufox
            except ImportError as exc:
                from .doctor import missing_extra_message
                raise RuntimeError(missing_extra_message("render")) from exc
            # self-heal a Playwright driver crash on SPA page errors (see module)
            from .playwright_patch import ensure_driver_patched
            ensure_driver_patched()
            cm = Camoufox(headless=True)
            self._browser = cm.__enter__()  # assign _cm only after launch succeeds
            self._cm = cm
        return self._browser

    def fetch(self, url: str) -> FetchResult:
        browser = self._ensure()
        page = browser.new_page()
        try:
            if self._headers:
                page.set_extra_http_headers(self._headers)
            if self._cookies:
                page.context.add_cookies(self._cookies_for(url))
            # domcontentloaded first (fast, and avoids a Firefox-driver crash that
            # `wait_until="load"` triggers on SPAs which throw uncaught JS errors),
            # then wait for network to settle so client-rendered content is in the
            # DOM. networkidle is best-effort: a timeout still yields what rendered.
            page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=self._timeout_ms)
            except Exception:
                pass  # persistent connections never idle → use what we have
            html = page.content()
            final = page.url
        except Exception as exc:  # playwright raises its own error types
            raise RuntimeError(f"Render failed for {url}: {exc}") from exc
        finally:
            page.close()
        return FetchResult(url=final, content=html.encode("utf-8"), content_type="text/html")

    def close(self) -> None:
        if self._cm is not None:
            self._cm.__exit__(None, None, None)
            self._cm = self._browser = None

    def __enter__(self) -> "CamoufoxFetcher":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
