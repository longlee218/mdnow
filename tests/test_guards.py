import time

import mdnow.guards as guards
from mdnow.guards import RateLimiter, RobotsChecker

from conftest import FakeResp, router


def test_rate_limiter_enforces_min_delay():
    rl = RateLimiter(0.1)
    t0 = time.monotonic()
    rl.wait(); rl.wait(); rl.wait()
    assert time.monotonic() - t0 >= 0.2


def test_robots_allows_by_default_when_missing(monkeypatch):
    monkeypatch.setattr(guards.httpx, "get", router({}))  # robots.txt 404
    rc = RobotsChecker("https://s.com/")
    assert rc.allowed("https://s.com/anything")


def test_robots_disallow_respected(monkeypatch):
    robots = FakeResp(200, "User-agent: *\nDisallow: /private")
    monkeypatch.setattr(guards.httpx, "get", router({"/robots.txt": robots}))
    rc = RobotsChecker("https://s.com/")
    assert not rc.allowed("https://s.com/private/x")
    assert rc.allowed("https://s.com/public")
