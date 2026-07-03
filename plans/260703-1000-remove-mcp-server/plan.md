# Plan: Remove MCP Server from mdnow

## Context

MCP server là optional extra `[mcp]` trong mdnow, kích hoạt qua `--mcp`. Theo brainstorm report `plans/reports/brainstorm-260703-1000-mcp-removal.md`, MCP duplicate một phần pipeline và chưa có consumer rõ ràng. mdnow được thiết kế cho personal use, CLI đã đủ. Decision: gỡ hoàn toàn MCP server.

## Scope

- Xóa `mdnow/mcp_server.py`
- Xóa `tests/test_mcp_server.py`
- Sửa `mdnow/cli.py`: bỏ `--mcp` flag và import
- Sửa `mdnow/doctor.py`: bỏ check `[mcp]`
- Sửa `pyproject.toml`: bỏ `[mcp]` extra
- Sửa `tests/test_cli_main.py`: bỏ 3 tests MCP
- Sync docs: `README.md`, `README.vi.md`, `CLAUDE.md`
- Cập nhật changelog

## Status

- **Status:** Completed
- **Completion Date:** 2026-07-03
- **Progress:** 100% (2/2 phases completed)
- **Finalization Report:** [reports/mcp-removal-project-manager-260703-1140-finalization.md](./reports/mcp-removal-project-manager-260703-1140-finalization.md)

## Phases

1. [x] [Phase 1: Remove MCP code and tests](./phase-01-remove-mcp-code.md) — Completed
2. [x] [Phase 2: Sync docs and verify](./phase-02-sync-docs-and-verify.md) — Completed

## Success Criteria

- `mdnow --mcp` không còn tồn tại
- `pytest tests/ -q` pass
- Coverage ≥ 80%
- Không còn mention MCP trong docs chính
- `python -m compileall -q mdnow` pass

## Risks

- Docs drift: cần sync cả 3 file docs trong cùng PR
- Early adopter confusion: ghi changelog rõ ràng
- CLAUDE.md vừa được update thêm `--update`; cần giữ nguyên phần đó khi sync

## Next Steps

Sau khi plan approved, chạy `/ck:cook` với plan directory này.
