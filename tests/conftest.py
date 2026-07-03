"""Shared test helpers — a minimal fake httpx response + URL router."""
from __future__ import annotations

import httpx
import pytest

from mdnow import sessions as _sessions


@pytest.fixture(autouse=True)
def _isolate_session_store(tmp_path_factory, monkeypatch):
    """Keep tests hermetic: never read/write the real ~/.mdnow/sessions."""
    monkeypatch.setattr(_sessions, "SESSION_DIR", tmp_path_factory.mktemp("sessions"))


class FakeResp:
    def __init__(self, status=200, text="", content_type="text/plain", url=None, content=None):
        self.status_code = status
        self.text = text
        self.headers = {"content-type": content_type}
        self.url = url or "https://example.com/"
        self._content = content if content is not None else text.encode("utf-8")

    @property
    def content(self) -> bytes:
        return self._content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=httpx.Request("GET", self.url), response=self
            )


def router(routes: dict, default_status: int = 404):
    """Return a fake httpx.get that matches by URL suffix."""
    def _get(url, **_kw):
        for suffix, resp in routes.items():
            if url.endswith(suffix):
                return resp
        return FakeResp(status=default_status)
    return _get
