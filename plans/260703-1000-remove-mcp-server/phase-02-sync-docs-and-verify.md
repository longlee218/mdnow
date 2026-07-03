# Phase 2: Sync Docs and Verify

## Status

- **Status:** Completed
- **Completion Date:** 2026-07-03
- **Progress:** 100%

## Overview

Đồng bộ tất cả tài liệu chính để phản ánh việc MCP server đã bị gỡ. Chạy test suite và coverage để xác nhận không có regression.

## Requirements

- `README.md`: bỏ mọi mention `--mcp`, `[mcp]` extra, MCP server mode
- `README.vi.md`: mirror thay đổi từ README.md
- `CLAUDE.md`: bỏ mention `--mcp` và `mcp_server.py` trong architecture; **giữ nguyên** phần `--update` vừa được thêm
- `docs/project-changelog.md`: ghi nhận breaking change

## Implementation Steps

1. Sửa `README.md`:
   - Bỏ section/command `# MCP server mode (stdio transport for Claude / Cursor)`
   - Bỏ `/.venv/bin/mdnow --mcp` trong examples
   - Bỏ `[mcp]` khỏi install examples (`--all` flag nếu có cũng cần xem lại)
   - Bỏ mention MCP trong architecture/usage sections
2. Sửa `README.vi.md`: mirror tất cả thay đổi
3. Sửa `CLAUDE.md`:
   - Bỏ bullet `--mcp` trong architecture list
   - Bỏ paragraph về `mcp_server.py`
   - Giữ nguyên `--update` và `commands.self_update()`
4. Cập nhật `docs/project-changelog.md` với entry về việc gỡ MCP server
5. Chạy `pytest tests/ -q`
6. Chạy `pytest tests/ --cov=mdnow --cov-report=term-missing` để verify coverage ≥ 80%
7. Chạy `python -m compileall -q mdnow`

## Success Criteria

- `grep -R "mcp\|MCP" README.md README.vi.md CLAUDE.md` không còn kết quả (trừ historical changelog nếu có)
- `pytest tests/ -q` pass
- Coverage ≥ 80%
- `python -m compileall -q mdnow` pass

## Risks

- README drift giữa English và Vietnamese. Phải sync cẩn thận.
- Có thể có mention MCP trong `install.sh` hoặc skill docs. Cần grep toàn repo.

## Related Files

- `README.md`
- `README.vi.md`
- `CLAUDE.md`
- `docs/project-changelog.md`
- `install.sh` (check)
- `mdnow/skill/` references (check)
