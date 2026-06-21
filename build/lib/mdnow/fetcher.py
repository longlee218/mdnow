"""Fetch backends. `Fetcher` is a swappable interface (Protocol).

StaticFetcher is the default fast path. Later phases add CamoufoxFetcher
behind the same interface, so nothing downstream changes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

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


class StaticFetcher:
    """httpx GET with timeout + a single retry."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT, user_agent: str = DEFAULT_UA):
        self._timeout = timeout
        self._ua = user_agent

    def fetch(self, url: str) -> FetchResult:
        last_exc: Exception | None = None
        for _ in range(2):  # initial attempt + 1 retry (transient failures only)
            try:
                resp = httpx.get(
                    url,
                    follow_redirects=True,
                    timeout=self._timeout,
                    headers={"User-Agent": self._ua},
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

    def __init__(self, timeout: float = RENDER_TIMEOUT):
        self._timeout_ms = int(timeout * 1000)
        self._cm = None
        self._browser = None

    def _ensure(self):
        if self._browser is None:
            try:
                from camoufox.sync_api import Camoufox
            except ImportError as exc:
                raise RuntimeError(
                    "Camoufox not installed. Run: pip install camoufox "
                    "&& python -m camoufox fetch"
                ) from exc
            cm = Camoufox(headless=True)
            self._browser = cm.__enter__()  # assign _cm only after launch succeeds
            self._cm = cm
        return self._browser

    def fetch(self, url: str) -> FetchResult:
        browser = self._ensure()
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self._timeout_ms)
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
