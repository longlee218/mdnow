"""Crawl guards: polite rate limiting + robots.txt.

robots.txt here covers the sitemap branch and is allow-by-default if the file
is missing/unreachable. The BFS branch (focused_crawler) already enforces
robots internally, so we never double-check it (single source of truth).
"""
from __future__ import annotations

import time
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx

from .fetcher import DEFAULT_UA

ROBOTS_TIMEOUT = 8.0


class RateLimiter:
    """Enforce a minimum delay between successive calls to wait()."""

    def __init__(self, delay: float):
        self._delay = delay
        self._last = 0.0

    def wait(self) -> None:
        gap = self._delay - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()


class RobotsChecker:
    """Fetch robots.txt once; allow-by-default when absent/unreachable."""

    def __init__(self, start_url: str, user_agent: str = DEFAULT_UA):
        self._ua = user_agent
        self._rp: RobotFileParser | None = None
        p = urlsplit(start_url)
        robots_url = urlunsplit((p.scheme, p.netloc, "/robots.txt", "", ""))
        try:
            resp = httpx.get(
                robots_url, follow_redirects=True, timeout=ROBOTS_TIMEOUT,
                headers={"User-Agent": self._ua},
            )
        except httpx.HTTPError:
            return
        if resp.status_code == 200:
            rp = RobotFileParser()
            rp.parse(resp.text.splitlines())
            self._rp = rp

    def allowed(self, url: str) -> bool:
        # Match the BFS path, which checks the "*" group — keeps both branches identical.
        return self._rp is None or self._rp.can_fetch("*", url)
