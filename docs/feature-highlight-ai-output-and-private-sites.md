# Tính năng: Xác thực site nội bộ & Xuất liệu cho AI agents

## Vấn đề cần giải quyết

**AI agents cần truy vấn nhanh từng section**: Khi crawl một site lớn (~50+ trang), agent cần chọn section liên quan mà không cần đọc toàn bộ file Markdown.

**Site nội bộ (wiki, docs) thường yêu cầu session tokens**: Cookie hoặc bearer tokens để xác thực, nhưng hiện tại mdnow không hỗ trợ.

## Giải pháp

### 1. Xác thực site nội bộ

**Flags mới:**
- `--header/-H "Name: Value"` (lặp được) — thêm HTTP headers (OAuth, API keys)
- `--cookie-file PATH` — tệp cookies Netscape hoặc JSON

**Bearer token:**
```bash
mdnow https://internal.example.com -H "Authorization: Bearer $GITHUB_TOKEN" -o out/
```

**Session cookies (xuất từ browser via Cookie-Editor):**
```bash
mdnow https://internal-wiki.com --cookie-file ~/Downloads/cookies.txt -o out/
```

**Cookies JSON:**
```json
[
  {"name": "session_id", "value": "abc123", "domain": ".example.com", "path": "/"}
]
```

### 2. Xuất liệu cho AI agents

**Frontmatter `outline`** — danh sách heading trong mỗi trang:
```yaml
outline:
  - "## Getting Started"
  - "### Installation"
  - "## API Reference"
```

**Manifest `sections`** (crawl mode):
```json
{
  "local_path": "getting-started.md",
  "sections": [
    {"slug": "_intro", "heading": "", "level": 0, "word_count": 250, "token_estimate": 330},
    {"slug": "getting-started", "heading": "Getting Started", "level": 2, "word_count": 1200, "token_estimate": 1580},
    {"slug": "installation", "heading": "Installation", "level": 3, "word_count": 500, "token_estimate": 660}
  ]
}
```

Agent chọn sections theo kích thước trước khi đọc file, giảm context overhead.

## Bảo vệ secrets

⚠️ **Quy tắc vàng:**
- Cookie files: `chmod 600` (only owner reads)
- Tokens: inject qua env vars (`$GITHUB_TOKEN`, `$API_KEY`)
- **Không bao giờ** log/echo values vào output

```bash
# GOOD
export AUTH_TOKEN="secret..."
mdnow https://site.com -H "Authorization: Bearer $AUTH_TOKEN" -o out/

# AVOID
mdnow https://site.com -H "Authorization: Bearer $(cat token.txt)" -o out/
```

**Redirect cross-origin:** custom header (ví dụ `X-API-Key`) được gửi tiếp nếu site
redirect sang origin khác — httpx chỉ tự loại `Authorization`. Cookie thiếu `domain`
được tự scope vào host của URL đang fetch (không bao giờ gửi sang host khác).

## Giới hạn đã biết

1. **Discovery probes unauthenticated**: `llms.txt` được probe mà không có auth. Dùng `--no-llms` nếu confuse private site.
2. **Crawl discovery không có auth**: Sitemap / BFS discovery không mang headers/cookies — chỉ per-page fetches có.
3. **No SSO/OAuth flow**: Không tự động handle OAuth login. Dùng token hoặc cookie đã export.
4. **trafilatura link headings**: Một số site có link-style headings — `outline` có thể rỗng. Kiểm tra frontmatter để confirm.

## Tường lai

- [ ] SSO login flow (OAuth auto-redirect)
- [ ] Header inference từ `--render` (detect auth từ browser)
- [ ] Cookie jar sync với browser profiles
