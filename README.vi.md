[English](README.md) | [Tiếng Việt](README.vi.md)

# mdnow

**Chuyển đổi bất kỳ trang web hoặc tệp nào thành markdown sạch, thân thiện với AI.**

Hoàn toàn cục bộ theo mặc định — không cần API key, không dữ liệu rò rỉ. Trang web đơn hoặc crawl toàn bộ trang (→ llms.txt + llms-full.txt), chuyển đổi bất kỳ tệp nào (PDF, Office, ảnh, âm thanh), hoặc máy chủ MCP cho Claude / Cursor. Chọn tầng của bạn: tìm nạp tĩnh nhanh, render JS tinh vi, hoặc kỹ năng Claude gói.

[![PyPI version](https://img.shields.io/pypi/v/mdnow.svg)](https://pypi.org/project/mdnow/)
[![Python versions](https://img.shields.io/pypi/pyversions/mdnow.svg)](https://pypi.org/project/mdnow/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub Actions](https://github.com/longlee218/mdnow/actions/workflows/publish.yml/badge.svg)](https://github.com/longlee218/mdnow/actions)

## Bắt đầu nhanh

```bash
# One-liner (macOS / Linux)
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh

# Hoặc với uv (khuyến nghị)
uv tool install mdnow

# Hoặc với pipx
pipx install mdnow

# Sau đó:
mdnow https://example.com -o out/
```

<!-- TODO: replace with animated asciinema/vhs cast (assets/demo.svg) before launch -->

```
$ mdnow https://example.com/article -o out/
fetched: example-article.md (v1, from https://example.com/article, 1234 words, ~247 tokens)

$ mdnow https://example.com --crawl --max-pages 50 -o out/
Crawling https://example.com ...
Done: 47 page(s) written, 0 failed → out/
```

## Tính năng

| Tính năng | Mô tả |
|---------|-------------|
| ⚡ **Tìm nạp tĩnh** | `httpx` + `trafilatura`: nhanh, không cần render JS |
| 🎭 **Render tinh vi** | Trình duyệt Firefox không đầu Camoufox cho các trang web JS-nặng / chống bot (tùy chọn hoặc tự động leo thang) |
| 🔗 **Crawl + index** | Cây toàn bộ trang: `.md` mỗi trang + `llms.txt` + `llms-full.txt` + `manifest.json` |
| 📄 **Chuyển đổi bất kỳ tệp nào** | PDF, Office, EPub, ảnh (OCR), âm thanh, YouTube, CSV/JSON/XML, ZIP |
| 🧠 **Máy chủ MCP** | Hiển thị công cụ cho Claude Desktop, Claude Code, Cursor và các máy khách LLM khác |
| 🔌 **Kỹ năng gói** | `mdnow --install-skill` → cài đặt vào `~/.claude/skills/mdnow` |

## Cài đặt

### 1. Cài đặt cơ bản (tất cả người dùng)

Chọn một cách:

**Qua shell one-liner** (macOS / Linux):
```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
```

**Qua uv** (khuyến nghị, đa nền tảng):
```bash
uv tool install mdnow
```

**Qua pipx** (chỉ Python, không cần uv):
```bash
pipx install mdnow
```

**Từ mã nguồn** (những người đóng góp):
```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 2. Extras (tùy chọn, cài đặt cùng nhau)

Cơ sở `mdnow` tìm nạp **HTML tĩnh chỉ** và chuyển đổi **tệp cục bộ** qua logic gói nhẹ. Chọn vào các phụ thuộc nặng hơn khi cần:

**`[render]`** — Trình duyệt không đầu tinh vi (Camoufox Firefox, tải xuống một lần ~300MB):
```bash
# Shell one-liner: thêm cờ --render
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --render

# uv / pipx
uv tool install "mdnow[render]"
pipx install "mdnow[render]"

# Sau đó tải xuống trình duyệt (một lần):
mdnow --fetch-browser
```

**`[docs]`** — Chuyển đổi bất kỳ tệp nào: PDF, Word, PowerPoint, Excel, EPub, ảnh (OCR), âm thanh, YouTube (markitdown + ML deps nặng):
```bash
# Shell: --docs
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --docs

# uv / pipx
uv tool install "mdnow[docs]"
pipx install "mdnow[docs]"
```

**`[mcp]`** — Chế độ máy chủ MCP cho Claude / Cursor:
```bash
# Shell: --mcp
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --mcp

# uv / pipx
uv tool install "mdnow[mcp]"
pipx install "mdnow[mcp]"
```

**`--all`** — Tất cả extras cùng một lúc:
```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --all
```

### Windows

Người dùng Windows: sử dụng **PowerShell** (không có shell one-liner). Cài đặt uv hoặc pipx trước, sau đó:

```powershell
uv tool install "mdnow[render,docs,mcp]"
```

Để tải xuống trình duyệt Camoufox trên Windows:
```powershell
mdnow --fetch-browser
```

## Sử dụng

### Trang web: trang đơn

```bash
mdnow https://example.com/article -o out/
```

### Trang web: crawl toàn bộ trang

```bash
# Max 100 trang (mặc định)
mdnow https://example.com --crawl -o out/

# Không có giới hạn trang
mdnow https://example.com --crawl --all -o out/

# Giới hạn tùy chỉnh
mdnow https://example.com --crawl --max-pages 50 -o out/
```

Đầu ra: các tệp `.md` mỗi trang + `llms.txt` + `llms-full.txt` + `manifest.json`.

### Trang web: các trang JS-nặng hoặc chống bot

```bash
# Bắt buộc trình duyệt tinh vi (yêu cầu extra [render])
mdnow https://example.com/spa --render -o out/

# Tự động leo thang: nếu HTML tĩnh mỏng hoặc rỗng, render được kích hoạt tự động
mdnow https://example.com --crawl -o out/
```

### Tệp: PDF cục bộ, Office, ảnh, âm thanh, v.v.

```bash
mdnow ./report.pdf -o out/
mdnow ./slides.pptx -o out/
mdnow ./document.docx -o out/
mdnow ./screenshot.png -o out/        # OCR
mdnow ./talk.m4a -o out/              # cloud transcription (yêu cầu --allow-remote + [docs] extra)
```

### Tệp: URL từ xa

```bash
mdnow https://example.com/paper.pdf -o out/
mdnow https://youtu.be/watch?v=abc123 --allow-remote -o out/  # YouTube transcript (cloud egress)
```

### Bỏ qua khám phá, bắt buộc tìm nạp/crawl

```bash
# Thông thường: nếu /llms.txt tồn tại trên trang web, hãy sử dụng nó trực tiếp và bỏ qua tìm nạp
# Sử dụng --no-llms để bắt buộc tìm nạp/crawl thay thế
mdnow https://example.com --crawl --no-llms -o out/
```

### Các cờ

| Cờ | Ý nghĩa |
|------|---------|
| `-o, --out` | Thư mục đầu ra (mặc định `.`) |
| `--crawl` | Crawl toàn bộ trang vào một cây (chỉ trang web) |
| `--max-pages N` | Số trang tối đa để crawl (mặc định 100) |
| `--all` | Crawl tất cả các trang (bỏ qua `--max-pages`) |
| `--render` | Sử dụng trình duyệt tinh vi Camoufox (các trang JS/chống bot); yêu cầu extra `[render]` |
| `--no-llms` | Bỏ qua khám phá llms.txt; bắt buộc tìm nạp/crawl (chỉ trang web) |
| `--allow-remote` | Cho phép API đám mây: âm thanh/video transcription, YouTube (egress dữ liệu tùy chọn) |
| `--doctor` | Báo cáo extras được cài đặt/bị thiếu (và cách khắc phục) rồi thoát |
| `--fetch-browser` | Tải xuống trình duyệt Camoufox cho `--render` rồi thoát |
| `--install-skill` | Cài đặt kỹ năng Claude Code gói vào `~/.claude/skills/mdnow` |
| `--mcp` | Chạy như một máy chủ MCP (stdio transport) cho Claude / Cursor |

## Cho những trợ lý AI

### Kỹ năng Claude Code

Cài đặt kỹ năng Claude Code gói:

```bash
mdnow --install-skill
```

Kỹ năng này hiển thị đường ống chuyển đổi mdnow cho Claude Code: tìm nạp URL, crawl trang, hoặc chuyển đổi tệp — tất cả từ trình chỉnh sửa Claude Code.

Để chỉ định điểm đến tùy chỉnh:

```bash
mdnow --install-skill --skill-dir ~/.claude/skills/my-mdnow
mdnow --install-skill --force    # ghi đè nếu đã được cài đặt
```

### Máy chủ MCP

Hiển thị mdnow như một máy chủ [MCP (Model Context Protocol)](https://modelcontextprotocol.io) cho Claude Desktop, Claude Code hoặc Cursor:

```bash
mdnow --mcp
```

**Cấu hình Claude Desktop** (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mdnow": {
      "command": "/path/to/mdnow",
      "args": ["--mcp"]
    }
  }
}
```

**Công cụ được hiển thị:**
- `mdnow_fetch_url`: Tìm nạp một URL → markdown với metadata
- `mdnow_crawl_site`: Crawl một trang → tóm tắt các chuyển đổi mỗi trang
- `mdnow_convert_file`: Chuyển đổi tệp cục bộ hoặc từ xa → markdown

## Nó hoạt động như thế nào

Một đường ống chi phí rẻ nhất-đầu tiên — mỗi tầng chỉ chạy nếu tầng trước không đã tạo ra markdown sạch:

1. **Khám phá** — nếu trang web xuất bản `/llms.txt`, `/llms-full.txt` (hoặc biến thể, hoặc sinh đôi `<url>.md`), hãy sử dụng nó trực tiếp và bỏ qua mọi thứ khác.
2. **Tìm nạp tĩnh** — trích xuất `httpx` + `trafilatura`. Mặc định nhanh; không cần trình duyệt.
3. **Render** — Trình duyệt Firefox không đầu Camoufox cho các trang JS-nặng / chống bot. Tùy chọn qua `--render`, hoặc tự động leo thang khi tìm nạp tĩnh trả về nội dung rỗng/mỏng.

## Đầu ra

Mỗi trang được viết với lưỡng chữ YAML phía trước và **versioning** dựa trên hash nội dung — chạy lại chỉ bumps `version` khi nội dung thực sự thay đổi:

```yaml
---
source_url: https://example.com/article
title: Example Article
published_date: 2026-01-01
fetched_date: 2026-06-21
version: 1
content_hash: <sha256>
word_count: 1234
token_estimate: 247
summary: "The world as we have created it is a process of our thinking."
---
```

Chế độ crawl cũng viết ba hiện tượng:

- **`llms.txt`** — chỉ mục theo [llmstxt.org](https://llmstxt.org): tiêu đề `# <host>`, blockquote `> <summary>`, `## Pages` với danh sách `- [title](path): summary`.
- **`llms-full.txt`** — markdown nối tiếp từ mỗi trang crawled, mỗi cái được tiền tố với `## <title>` và `Source: <url>`.
- **`manifest.json`** — Metadata có thể đọc máy: máy chủ lưu trữ, số trang và hashes mỗi trang, tóm tắt, số lượng token.

## Hành vi

- **Ảnh** được loại bỏ nhưng văn bản thay thế được bảo tồn (HTML); hoặc được trích xuất qua OCR (tệp ảnh, `[docs]` extra).
- **Tệp** (cục bộ hoặc từ xa không phải HTML) được phát hiện tự động và chuyển đổi qua markitdown. Hỗ trợ: PDF, Word, PowerPoint, Excel, EPub, ảnh, CSV/JSON/XML, lưu trữ ZIP.
- **Âm thanh/video** và **YouTube** yêu cầu `--allow-remote` (API transcription đám mây). Nếu không, chúng lỗi rõ ràng.
- **`--crawl`** không hợp lệ cho đầu vào tệp (chỉ tệp đơn); lỗi rõ ràng.
- **Hoàn toàn cục bộ theo mặc định** — chỉ egress âm thanh/video/YouTube là tùy chọn qua `--allow-remote`. Không có khóa LLM hoặc telemetry.
- **Crawl** phát hiện qua `sitemap.xml` trước, quay trở lại BFS; tôn trọng `robots.txt`, giới hạn tốc độ và cô lập các lỗi mỗi trang.
- **SPAs được render JS** (tài liệu React/Angular, v.v.) tự động leo thang ở chế độ crawl: nếu khám phá tĩnh không tìm thấy liên kết, trang bắt đầu được render và các trang mỏng tự động render. Yêu cầu `[render]` extra + `mdnow --fetch-browser`.
- **Cloudflare / chống bot** bypass qua `--render` là nỗ lực tốt nhất.

## Tại sao cục bộ?

**mdnow hoàn toàn cục bộ theo mặc định** — không API key, không egress dữ liệu, không telemetry. Đây là một ràng buộc sáng lập.

- Nội dung trang web của bạn không bao giờ rời khỏi máy của bạn (ngoại trừ âm thanh/video/YouTube, đó là tùy chọn qua `--allow-remote`).
- Không phụ thuộc mạng sau lần cài đặt đầu tiên (ngoại trừ tìm nạp trang web thực tế, tất nhiên).
- Không khóa vendor bên thứ ba hoặc giới hạn tốc độ API.
- Không telemetry — không ping về nhà, không phân tích.
- Minh bạch: đọc mã nguồn; không có cuộc gọi đám mây ẩn.

Sử dụng mdnow như một CLI, trong một tập lệnh hoặc nhúng trong IDE LLM của bạn — nó là của bạn để kiểm soát.

## Develop

```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,docs,mcp]"
.venv/bin/pytest          # 95 tests, ~88% coverage
```

## Kiến trúc

Kế hoạch & tài liệu giai đoạn: `plans/260621-0714-website-to-markdown-cli/`. Các mô-đun (mỗi <200 dòng): `cli`, `discovery`/`llmstxt`, `fetcher` (`StaticFetcher`/`CamoufoxFetcher` phía sau một giao diện `Fetcher`), `playwright_patch` (bản sửa tự chữa render-driver), `extractor`, `convert` (wrapper markitdown), `crawler`, `urls`, `linkrewrite`, `guards`, `frontmatter`, `outline`, `artifacts`, `writer`, `mcp_server`.

## Giấy phép

MIT
