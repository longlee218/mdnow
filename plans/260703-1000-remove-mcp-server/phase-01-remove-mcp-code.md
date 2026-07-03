# Phase 1: Remove MCP Code and Tests

## Overview

Xóa toàn bộ MCP server implementation, bỏ `--mcp` flag khỏi CLI, và loại bỏ các tests liên quan. Đảm bảo codebase vẫn compile và các tests còn lại pass.

## Requirements

- Xóa `mdnow/mcp_server.py`
- Xóa `tests/test_mcp_server.py`
- Sửa `mdnow/cli.py`: bỏ `mcp: bool = typer.Option(...)` parameter, bỏ `if mcp:` branch, bỏ import `mcp_server`
- Sửa `mdnow/doctor.py`: bỏ `"mcp": "mcp"` khỏi `_EXTRAS`, bỏ `_check_extra("mcp", "mcp")` trong `run_checks()`
- Sửa `pyproject.toml`: bỏ dòng `[mcp]` extra
- Sửa `tests/test_cli_main.py`: bỏ 3 tests MCP (`test_mcp_flag_starts_server`, `test_mcp_flag_ignores_url_argument`, `test_mcp_missing_extra_is_friendly`)

## Implementation Steps

1. Xóa file `mdnow/mcp_server.py`
2. Xóa file `tests/test_mcp_server.py`
3. Sửa `mdnow/cli.py`:
   - Bỏ parameter `mcp: bool = typer.Option(False, "--mcp", ...)`
   - Bỏ toàn bộ `if mcp:` branch (dòng 72-85)
4. Sửa `mdnow/doctor.py`:
   - `_EXTRAS = {"render": "render", "docs": "docs"}`
   - Bỏ `_check_extra("mcp", "mcp")` trong `run_checks()`
5. Sửa `pyproject.toml`: xóa dòng `mcp = ["mcp>=1.0.0,<2.0", "pydantic>=2"]`
6. Sửa `tests/test_cli_main.py`: xóa 3 tests liên quan đến MCP
7. Chạy `python -m compileall -q mdnow`
8. Chạy `pytest tests/ -q`

## Success Criteria

- `grep -R "mcp_server\|--mcp\|\[mcp\]" mdnow/ tests/ pyproject.toml` không còn kết quả
- `pytest tests/ -q` pass
- `python -m compileall -q mdnow` pass

## Risks

- Có thể còn reference đến `mcp_server` ở nơi khác (vd. `commands.py`?). Cần grep toàn repo.
- `missing_extra_message("mcp")` trong `mcp_server.py` sẽ bị xóa; `doctor.py` vẫn giữ helper.

## Related Files

- `mdnow/cli.py`
- `mdnow/doctor.py`
- `mdnow/mcp_server.py` (delete)
- `pyproject.toml`
- `tests/test_mcp_server.py` (delete)
- `tests/test_cli_main.py`
