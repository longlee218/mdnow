---
title: "Phase 4: Write Tests for MCP Server"
description: "Write unit and integration tests for MCP server, tool handlers, and CLI --mcp flag."
status: completed
priority: P2
effort: 2h
branch: main
tags: [mcp, testing, pytest]
created: 2026-06-25
---

## Context Links

- [plan.md](plan.md) — Overview
- [mdnow/mcp_server.py](phase-02-implement-mcp-server.md) — Server to test
- [mdnow/cli.py](/Users/longlh/Documents/Longle/MDNow/mdnow/cli.py) — CLI to test
- [tests/](/Users/longlh/Documents/Longle/MDNow/tests/) — Existing test suite (72 tests, ~86% coverage)

## Overview

Add tests for the MCP server and the `--mcp` CLI flag. Tests must be network-free (mock external I/O), fast, and maintain the existing ~86% coverage target.

## Key Insights

- **Network-free**: The existing test suite monkeypatches `httpx` and avoids real browser calls. Follow the same pattern.
- **Mock `mcp_server` tools**: Test tool logic by mocking `_acquire`, `crawl_site`, and `convert.from_path`.
- **Test `--mcp` flag in CLI**: Mock `mcp_server.run()` to avoid blocking on stdio.
- **Pydantic validation**: Test invalid inputs (bad URLs, negative max_pages) to verify FastMCP schema rejection.
- **Character limit**: Test truncation logic with a large markdown string.
- **Import guard**: Test behavior when `[mcp]` is not installed (mock `ImportError`).

## Requirements

### Test Coverage Targets

| Component | Tests | Coverage Goal |
|-----------|-------|---------------|
| `mcp_server.py` module import | 2 | 100% |
| `fetch_url` tool | 4 | 100% |
| `crawl_site` tool | 3 | 100% |
| `convert_file` tool | 3 | 100% |
| `_truncate` helper | 2 | 100% |
| `_format_result` helper | 1 | 100% |
| `cli --mcp` flag | 3 | 100% |
| **Total** | **18** | **~90% of mcp_server.py** |

### Test Cases

1. **`test_mcp_server_import`** — `from mdnow.mcp_server import mcp` succeeds when `[mcp]` installed.
2. **`test_mcp_server_import_missing`** — `ImportError` with correct hint when `mcp` not installed.
3. **`test_fetch_url_success`** — Mock `_acquire` returning `FetchResult` + `Extracted`; verify JSON output contains markdown and metadata.
4. **`test_fetch_url_truncation`** — Mock `_acquire` returning >25k chars; verify truncation message appended.
5. **`test_fetch_url_error`** — Mock `_acquire` raising `RuntimeError`; verify error JSON.
6. **`test_fetch_url_invalid_input`** — Pydantic rejects empty URL or invalid type.
7. **`test_crawl_site_success`** — Mock `crawl_site` returning `(2, 0)`; verify summary JSON has 2 pages.
8. **`test_crawl_site_with_failures`** — Mock `crawl_site` returning `(1, 1)`; verify failure count in output.
9. **`test_crawl_site_invalid_max_pages`** — Pydantic rejects `max_pages=0` or `max_pages=2000`.
10. **`test_convert_file_local_success`** — Mock `convert.from_path`; verify JSON output.
11. **`test_convert_file_remote_success`** — Mock `_acquire` for remote URL; verify JSON output.
12. **`test_convert_file_error`** — Mock raising `RuntimeError`; verify error JSON.
13. **`test_truncate_under_limit`** — String <25k returned unchanged.
14. **`test_truncate_over_limit`** — String >25k truncated with notice.
15. **`test_format_result`** — Verify JSON structure with title, word_count, markdown.
16. **`test_cli_mcp_flag_starts_server`** — Mock `mcp_server.run`; verify called once.
17. **`test_cli_mcp_flag_missing_extra`** — Mock `ImportError` on `mcp_server` import; verify exit code 1 and error message.
18. **`test_cli_mcp_flag_ignores_url`** — Pass both `--mcp` and `url`; verify `mcp_server.run()` is called, normal logic skipped.

## Architecture

Test files:
- `tests/test_mcp_server.py` — All MCP server tests (tools, helpers, import guard).
- `tests/test_cli.py` — Add `--mcp` flag tests to existing CLI test file.

## Related Code Files

| File | Action | Notes |
|------|--------|-------|
| `tests/test_mcp_server.py` | Create | New test file, ~150 lines |
| `tests/test_cli.py` | Edit | Add 3 `--mcp` tests |
| `mdnow/mcp_server.py` | Read | Mock targets |
| `mdnow/cli.py` | Read | Mock targets |

## Implementation Steps

1. **Create `tests/test_mcp_server.py`**:
   ```python
   """Tests for mdnow.mcp_server."""
   import json
   import sys
   from pathlib import Path
   from unittest.mock import MagicMock, patch

   import pytest

   from mdnow.extractor import Extracted
   from mdnow.fetcher import FetchResult


   @pytest.fixture
   def mock_acquire():
       with patch("mdnow.mcp_server._acquire") as m:
           yield m


   @pytest.fixture
   def mock_crawl():
       with patch("mdnow.mcp_server.crawl_site") as m:
           yield m


   class TestFetchUrl:
       def test_success(self, mock_acquire):
           mock_acquire.return_value = (
               FetchResult(url="https://example.com", content=b"<html></html>", content_type="text/html"),
               Extracted(markdown="# Hello", title="Hello", published_date=None),
           )
           from mdnow.mcp_server import fetch_url, FetchUrlInput
           result = fetch_url(FetchUrlInput(url="https://example.com"))
           data = json.loads(result)
           assert data["title"] == "Hello"
           assert data["markdown"] == "# Hello"

       def test_truncation(self, mock_acquire):
           long_md = "word " * 20000  # > 25000 chars
           mock_acquire.return_value = (
               FetchResult(url="https://example.com", content=b"", content_type="text/html"),
               Extracted(markdown=long_md, title="Long", published_date=None),
           )
           from mdnow.mcp_server import fetch_url, FetchUrlInput
           result = fetch_url(FetchUrlInput(url="https://example.com"))
           assert "truncated" in result
           assert len(result) <= 25000 + 100

       def test_error(self, mock_acquire):
           mock_acquire.side_effect = RuntimeError("blocked")
           from mdnow.mcp_server import fetch_url, FetchUrlInput
           result = fetch_url(FetchUrlInput(url="https://example.com"))
           assert "error" in json.loads(result)

   class TestCrawlSite:
       def test_success(self, mock_crawl, tmp_path):
           mock_crawl.return_value = (2, 0)
           from mdnow.mcp_server import crawl_site, CrawlSiteInput
           # ... setup temp dir mock ...
           result = crawl_site(CrawlSiteInput(url="https://example.com"))
           data = json.loads(result)
           assert data["pages_crawled"] == 2

   class TestConvertFile:
       def test_local_success(self):
           with patch("mdnow.mcp_server.convert.from_path") as m:
               m.return_value = Extracted(markdown="# File", title="File", published_date=None)
               from mdnow.mcp_server import convert_file, ConvertFileInput
               result = convert_file(ConvertFileInput(path="/tmp/test.pdf"))
               data = json.loads(result)
               assert data["title"] == "File"

   class TestTruncate:
       def test_under_limit(self):
           from mdnow.mcp_server import _truncate
           assert _truncate("short") == "short"

       def test_over_limit(self):
           from mdnow.mcp_server import _truncate, CHARACTER_LIMIT
           long = "a" * (CHARACTER_LIMIT + 100)
           result = _truncate(long)
           assert result.endswith("chars omitted]")
           assert len(result) <= CHARACTER_LIMIT + 100
   ```

2. **Add `--mcp` tests to `tests/test_cli.py`**:
   ```python
   class TestMcpFlag:
       def test_mcp_starts_server(self, runner):
           with patch("mdnow.cli.mcp_server") as mock_mcp:
               result = runner.invoke(app, ["--mcp"])
               mock_mcp.run.assert_called_once()

       def test_mcp_missing_extra(self, runner):
           with patch.dict("sys.modules", {"mdnow.mcp_server": None}):
               result = runner.invoke(app, ["--mcp"])
               assert result.exit_code == 1
               assert "[mcp]" in result.output

       def test_mcp_ignores_url(self, runner):
           with patch("mdnow.cli.mcp_server") as mock_mcp:
               result = runner.invoke(app, ["--mcp", "https://example.com"])
               mock_mcp.run.assert_called_once()
   ```

3. **Run tests**:
   ```bash
   .venv/bin/python -m pytest tests/test_mcp_server.py tests/test_cli.py -q
   ```

4. **Check coverage**:
   ```bash
   .venv/bin/python -m pytest tests/ --cov=mdnow --cov-report=term-missing
   ```

## Todo List

- [x] Create `tests/test_mcp_server.py` with tool tests
- [x] Add `--mcp` tests to `tests/test_cli.py`
- [x] Mock all external I/O (network, browser, file system)
- [x] Run tests and verify pass
- [x] Check coverage stays >= 80%

## Success Criteria

- All 18 new tests pass.
- Overall coverage remains >= 80% (target: 86%+).
- No network calls during test execution.
- Test execution time < 5 seconds for all MCP tests.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| FastMCP requires async test runner | Medium | Medium | Use `pytest-asyncio` or call `asyncio.run()` in tests |
| `mcp_server` import fails in CI if `[mcp]` not installed | Medium | High | Add `[mcp]` to dev install in CI or mock the import |
| Tests block on `mcp.run()` | Low | High | Always mock `mcp_server.run()` in CLI tests |

## Security Considerations

- Tests use mock data only — no real URLs fetched.
- Temp directories cleaned up via `tmp_path` fixture.
- No secrets in test code.

## Next Steps

Phase 5: README sync + demo example.
