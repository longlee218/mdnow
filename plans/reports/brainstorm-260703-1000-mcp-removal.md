# Brainstorm Report: Remove MCP Server from mdnow

## Executive Summary

MCP server trong `mdnow` hiện là optional extra `[mcp]` kích hoạt qua `--mcp`, nhưng nó duplicate một phần pipeline (fetch/crawl/convert) và chưa có consumer rõ ràng. Với positioning "personal, fully-local, built for one user" của mdnow, CLI đã đủ. **Khuyến nghị: gỡ hoàn toàn MCP server trong release tiếp theo.** Đây là thởi điểm tốt nhất vì project còn beta, chưa có public API commitment. Effort ước tính 4-8 giờ bao gồm code, tests, và docs sync.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| User đang dùng `--mcp` thực tế | Low | High | Xác nhận trước khi gỡ; nếu có, cân nhắc deprecation cycle ngắn |
| Docs drift sau khi gỡ | Medium | Medium | Sync `README.md`, `README.vi.md`, `CLAUDE.md` trong cùng PR |
| Test coverage giảm | Low | Low | Xóa `test_mcp_server.py`; coverage còn lại vẫn >80% nếu baseline đúng |
| Breaking change cho early adopters | Low | Medium | Ghi changelog, bump minor version |
| Phải rewrite lại sau này nếu cần MCP | Medium | Low | Git history giữ lại implementation; rewrite dễ hơn maintain dead code |

## Strategic Options

| Approach | Effort | Risk | Flexibility | Fit với mdnow |
|----------|--------|------|-------------|---------------|
| **A. Gỡ hoàn toàn** | 4-8h | Low | Medium | **Tốt nhất** — giảm surface, đúng YAGNI/KISS |
| B. Giữ nhưng không advertise | 1h | Medium | High | Không giải quyết maintenance burden thực sự |
| C. Giữ nguyên | 0h | Medium | High | Tích lũy technical debt cho feature chưa dùng |

**Recommendation:** Option A.

## Recommended Approach

Gỡ MCP server hoàn toàn khỏi codebase:

1. **Xóa files:**
   - `mdnow/mcp_server.py`
   - `tests/test_mcp_server.py`

2. **Sửa files:**
   - `mdnow/cli.py`: bỏ `--mcp` flag, bỏ import `mcp_server`, bỏ branch `if mcp:`
   - `mdnow/doctor.py`: bỏ `"mcp"` khỏi `_EXTRAS`, bỏ `_check_extra("mcp", "mcp")`
   - `pyproject.toml`: bỏ `[mcp]` extra dòng 45
   - `tests/test_cli_main.py`: bỏ 3 tests MCP-related

3. **Sync docs:**
   - `README.md`, `README.vi.md`: bỏ section MCP / `--mcp`
   - `CLAUDE.md`: cập nhật architecture description

## Operational Considerations

- **Testing:** Chạy full test suite sau khi xóa. Không được ignore failing tests.
- **Changelog:** Ghi rõ breaking change trong `docs/project-changelog.md`.
- **Versioning:** Nếu đang ở `0.1.0`, bump lên `0.2.0` vì xóa public flag.
- **Rollback:** Nếu sau này cần MCP, revert commit hoặc rewrite từ git history.

## Business Impact

- **Effort:** 4-8 giờ senior engineer.
- **Value delivered:** Giảm maintenance surface, đơn giản hóa install story, giảm cognitive load cho contributors, tránh public API commitment sớm.
- **Dependencies:** Cần xác nhận không có user/tool nào đang dùng `--mcp`.

## Decisions Needed

1. **Có consumer thực tế nào đang dùng `--mcp` không?** Nếu có, cần deprecation thay vì xóa đột ngột.
2. **Có muốn thay thế MCP bằng skill-based integration không?** Skill `mdnow/skill/` đã cung cấp Claude Code integration qua CLI, có thể đủ thay thế.
3. **Version bump?** Xóa flag là breaking change — bump minor (0.2.0) hay patch tùy semantic-versioning policy.

## Unresolved Questions

- Có AI assistant / IDE nào đang kết nối với `mdnow --mcp` không?
- Có kế hoạch tích hợp Cursor / other MCP clients trong tương lai gần không?
