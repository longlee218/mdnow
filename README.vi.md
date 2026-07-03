<div align="center">

[English](README.md) · [Tiếng Việt](README.vi.md)

<img src="https://raw.githubusercontent.com/longlee218/mdnow/main/assets/banner-2.png" alt="mdnow — biến mọi thứ thành Markdown" width="640">

# mdnow

### Mọi URL. Mọi website. Mọi tệp. Thư mục cục bộ. → Markdown sạch, sẵn sàng cho LLM.

**100% cục bộ. Không cần API key. Không gửi dữ liệu ra ngoài. Chỉ một câu lệnh.**

Biến một trang web, cả một website, một thư mục cục bộ, hay một tệp PDF/Office/âm thanh thành Markdown sạch mà LLM đọc được — mà không phải đẩy nội dung của bạn lên cloud của bên thứ ba.

[![Python](https://img.shields.io/badge/python-3.11%2B-3b82f6.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-3b82f6.svg)](LICENSE)
[![Install: git](https://img.shields.io/badge/install-via%20git-6f42c1.svg)](#cài-đặt)
[![Local-first](https://img.shields.io/badge/data%20egress-none%20by%20default-16a34a.svg)](#-tại-sao-cục-bộ)

**macOS / Linux**

```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
```

**Windows**

```powershell
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 | iex
```

**Đa nền tảng (uv)**

```bash
uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"
```

</div>

---

## Vấn đề

LLM chỉ tốt ngang với dữ liệu bạn đưa vào — nhưng web thì cản trở bạn ở mọi bước:

- **HTML thô toàn là nhiễu.** Menu, quảng cáo, banner cookie và một rừng `<div>` chôn vùi nội dung thật.
- **Scraper trên cloud khiến bạn trả giá hai lần.** Tính phí theo từng lần gọi _và_ gửi nội dung của bạn cho bên thứ ba.
- **Mỗi định dạng lại cần một công cụ khác nhau.** Một thứ cho trang web, thứ khác cho PDF, thứ khác cho âm thanh, thứ khác nữa cho cả một site tài liệu.

**mdnow gộp tất cả vào một câu lệnh chạy cục bộ** — trang đơn, cả website, và tệp — ra thẳng Markdown sạch, mà mặc định không có gì rời khỏi máy bạn.

```console
$ mdnow https://example.com/article -o out/
fetched: example-article.md (v1, 1234 words, ~247 tokens)

$ mdnow https://docs.example.com --crawl --max-pages 50 -o out/
Crawling https://docs.example.com ...
Done: 47 page(s) written, 0 failed → out/   (+ llms.txt, llms-full.txt, manifest.json)
```

<!-- TODO: replace with animated asciinema/vhs cast (assets/demo.svg) before launch -->

---

## ✨ Vì sao chọn mdnow

|                                    |     **mdnow**      | API scraper trên cloud | Công cụ cục bộ đơn mục đích |
| ---------------------------------- | :----------------: | :--------------------: | :-------------------------: |
| Chạy hoàn toàn cục bộ              |         ✅         |      ❌ chỉ cloud      |             ✅              |
| Không cần API key / đăng ký        |         ✅         |           ❌           |             ✅              |
| Nội dung của bạn được giữ riêng tư |  ✅ không gửi đi   |   ❌ vốn dĩ phải gửi   |             ✅              |
| Trang web → Markdown               |         ✅         |           ✅           |      ⚠️ chỉ trích xuất      |
| Crawl cả site → `llms.txt`         |         ✅         |       ⚠️ tùy nơi       |             ❌              |
| Render vượt JS / anti-bot          |         ✅         |           ✅           |             ❌              |
| Tệp: PDF, Office, âm thanh, ảnh…   |         ✅         |       ⚠️ tùy nơi       |   ⚠️ mỗi loại một công cụ   |
| Skill cho Claude                   |         ✅         |           ❌           |             ❌              |
| Chi phí                            | **Miễn phí (MIT)** |   💲 tính theo lượt    |          Miễn phí           |

> **Điểm khác biệt then chốt:** làm được mọi thứ một cloud scraper làm, nhưng ngay trên máy _của bạn_ — và làm được mọi thứ một công cụ trích xuất cục bộ làm, nhưng cho cả web _lẫn_ mọi loại tệp, đã được thiết kế sẵn cho LLM.

---

## 🚀 Bạn nhận được gì

|     | Khả năng                          | Ý nghĩa                                                                                                                     |
| --- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| ⚡  | **Static fetch**                  | `httpx` + `trafilatura`. Mặc định nhanh, không cần trình duyệt.                                                             |
| 🎭  | **Stealth render**                | Camoufox headless Firefox cho site nặng JS / anti-bot — tùy chọn bật, hoặc **tự động nâng cấp** khi nội dung tĩnh quá mỏng. |
| 🔗  | **Crawl + lập chỉ mục**           | Cây cả site → mỗi trang một `.md` + `llms.txt` + `llms-full.txt` + `manifest.json`.                                         |
| 📄  | **Chuyển đổi mọi tệp**            | PDF, Word, PowerPoint, Excel, EPub, ảnh (OCR), âm thanh, YouTube, CSV/JSON/XML, ZIP.                                        |
| 🔌  | **Skill đóng gói sẵn**            | `mdnow --install-skill` cài một skill dùng ngay vào Claude Code.                                                            |
| 🔒  | **Cục bộ trước tiên**             | Không key, không telemetry, mặc định không gửi dữ liệu đi. Nội dung là của bạn.                                             |
| 🧾  | **Kết quả bất biến (idempotent)** | Versioning theo content-hash — chạy lại chỉ tăng `version` khi nội dung thực sự đổi.                                        |

---

## Mục lục

- [Bắt đầu nhanh](#bắt-đầu-nhanh)
- [Cài đặt](#cài-đặt)
- [Cách dùng](#cách-dùng)
- [Dành cho trợ lý AI](#-dành-cho-trợ-lý-ai)
- [Cơ chế hoạt động](#cơ-chế-hoạt-động)
- [Định dạng đầu ra](#định-dạng-đầu-ra)
- [Hành vi](#hành-vi)
- [Vì sao cục bộ](#-tại-sao-cục-bộ)
- [Phát triển](#phát-triển)
- [Giấy phép](#giấy-phép)

---

## Bắt đầu nhanh

| Nền tảng         | Một dòng lệnh                                                                         |
| :--------------- | :------------------------------------------------------------------------------------ |
| macOS / Linux    | `curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh \| sh` |
| Windows          | `irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 \| iex`      |
| Đa nền tảng (uv) | `uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"`                   |

Sau đó:

```bash
mdnow https://example.com -o out/
```

> **Phân phối qua git, không qua PyPI** — cài thẳng từ repo này. Không registry, không bước publish.

Không chắc đã cài những gì? Chạy **`mdnow --doctor`** — nó liệt kê từng extra và câu lệnh chính xác để cài phần còn thiếu.

---

## Cài đặt

### Chọn nền tảng

| Nền tảng         | Cài đặt cơ bản                                                                        |
| :--------------- | :------------------------------------------------------------------------------------ |
| macOS / Linux    | `curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh \| sh` |
| Windows          | `irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 \| iex`      |
| Đa nền tảng (uv) | `uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"`                   |
| Từ mã nguồn      | xem bên dưới                                                                          |

> **Phân phối qua git, không qua PyPI** — cài thẳng từ repo này. Không registry, không bước publish.

### Thêm extras

Bản nền `mdnow` lấy **HTML tĩnh** và chuyển đổi **tệp cục bộ** bằng logic nhẹ. Chỉ thêm extras khi cần:

| Extra      | Bổ sung                                                                                 |
| ---------- | --------------------------------------------------------------------------------------- |
| `[render]` | Trình duyệt stealth headless (Camoufox, tải ~300MB một lần) cho site nặng JS / anti-bot |
| `[docs]`   | Chuyển đổi mọi tệp: PDF, Office, ảnh/OCR, âm thanh, YouTube                             |

**macOS / Linux**

```bash
# chỉ render
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --render
# chỉ docs
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --docs
# render + docs + skill
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --all
```

**Windows**

```powershell
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 -o install.ps1
# chỉ render
.\install.ps1 -Render
# chỉ docs
.\install.ps1 -Docs
# render + docs + skill
.\install.ps1 -All
```

**uv (mọi nền tảng)**

```bash
uv tool install "mdnow[render] @ git+https://github.com/longlee218/mdnow"
uv tool install "mdnow[docs] @ git+https://github.com/longlee218/mdnow"
uv tool install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"
```

Sau khi cài `[render]`, tải trình duyệt:

```bash
mdnow --fetch-browser
```

> Không có uv? Bạn cũng có thể dùng `pipx install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"`.

### Nâng cấp bằng `--update`

Cài lại phiên bản mới nhất từ git, giữ nguyên các extras đã cài:

```bash
mdnow --update
```

Lệnh này làm gì:

1. Phát hiện các extras bạn đang có (`render`, `docs`, v.v.)
2. Chạy `uv tool install --force "mdnow[<extras>] @ git+https://github.com/longlee218/mdnow"`
3. Nếu `uv` không có trên PATH, nó sẽ in câu lệnh thủ công tương đương

Nếu `uv` không có trên PATH, chạy thủ công tương đương:

```bash
uv tool install --force "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"
```

Thay `[render,docs]` bằng extras bạn thực sự dùng, hoặc bỏ extras đi nếu không cần. Không có uv? Cài lại bằng một dòng lệnh phía trên kèm cờ bạn cần (`--render`, `--docs`, hoặc `--all`).

### Từ mã nguồn

```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,docs]"
```

---

## Cách dùng

### Website: trang đơn

```bash
mdnow https://example.com/article -o out/
```

### Website: crawl cả site

```bash
mdnow https://example.com --crawl -o out/                 # tối đa 100 trang (mặc định)
mdnow https://example.com --crawl --all -o out/           # không giới hạn
mdnow https://example.com --crawl --max-pages 50 -o out/  # giới hạn tùy chỉnh
```

Đầu ra: mỗi trang một `.md` + `llms.txt` + `llms-full.txt` + `manifest.json`.

### Website: site nặng JS hoặc anti-bot

```bash
mdnow https://example.com/spa --render -o out/   # ép dùng trình duyệt stealth (cần [render])
mdnow https://example.com --crawl -o out/        # tự động nâng cấp render cho trang mỏng/rỗng
```

### Tệp: PDF, Office, ảnh, âm thanh cục bộ, …

```bash
mdnow ./report.pdf -o out/
mdnow ./slides.pptx -o out/
mdnow ./screenshot.png -o out/         # OCR
mdnow ./talk.m4a --allow-remote -o out/ # phiên âm âm thanh (cần [docs] + --allow-remote)
```

### Tệp: URL từ xa

```bash
mdnow https://example.com/paper.pdf -o out/
mdnow "https://www.youtube.com/watch?v=abc123" --allow-remote -o out/  # transcript YouTube, có mốc thời gian (gửi ra cloud)
```

### Thư mục: chuyển đổi hàng loạt thư mục cục bộ

```bash
mdnow ./docs -o out/                  # chuyển đổi tất cả tệp trong thư mục, bảo toàn cấu trúc thư mục con
mdnow ./docs -o out/ --all -max-pages 1000  # giới hạn cao hơn nếu cần (mặc định dựa theo tệp)
```

Đầu ra: mỗi tệp một `.md` + `llms.txt` + `llms-full.txt` + `manifest.json` (tương tự chế độ crawl).

Hành vi:
- **Bảo toàn cấu trúc thư mục con**: `docs/guide/setup.pdf` → `out/guide/setup.md`
- **Bỏ qua dotfiles và dotdirs** (`.git`, `.venv`, `.DS_Store`, v.v.)
- **Cô lập lỗi từng tệp**: tệp không thể chuyển đổi (ví dụ: âm thanh mà không có `--allow-remote`) bị bỏ qua, phần còn lại tiếp tục
- **Các cờ fetch-tier bị bỏ qua**: `--render`, `-H`, `--cookie-file`, `--no-llms` không áp dụng cho tệp cục bộ và được bỏ qua im lặng

Lưu ý: `--crawl` trên thư mục bị từ chối (chế độ thư mục luôn xây dựng chỉ mục); dùng đầu vào thư mục trực tiếp để chuyển đổi hàng loạt.

### Bỏ qua discovery, ép fetch/crawl

```bash
# Mặc định, nếu site có công bố /llms.txt, mdnow dùng luôn. Ép lấy mới bằng:
mdnow https://example.com --crawl --no-llms -o out/
```

### Site riêng tư / nội bộ

Cho các site đòi yêu cầu xác thực (session cookies, bearer tokens, v.v.):

**Bearer token (API key, OAuth)**

```bash
mdnow https://internal.example.com/docs -H "Authorization: Bearer $TOKEN" -o out/
```

**Session cookies** (xuất từ trình duyệt, ví dụ: [Cookie-Editor](https://chrome.google.com/webstore/detail/cookie-editor/iphcomtajlahbettdcakbotja27ijehe))

```bash
# Định dạng Netscape (.txt file, các browser extension xuất format này)
mdnow https://internal.example.com/wiki --cookie-file ~/cookies.txt -o out/

# Định dạng JSON: [{"name", "value", "domain", "path"}, ...]
mdnow https://internal.example.com/wiki --cookie-file ~/cookies.json -o out/
```

**Nhiều header** (có thể lặp)

```bash
mdnow https://api.example.com -H "Authorization: Bearer $TOKEN" -H "X-API-Key: $KEY" -o out/
```

**Bảo vệ secrets:** Cookie files và tokens **không bao giờ được logged, echoed, hoặc ghi vào đầu ra**. Khuyến cáo dùng `chmod 600` cho cookie files và inject tokens qua env vars. Custom header sẽ được gửi tiếp nếu site redirect sang origin khác (httpx chỉ tự bỏ `Authorization`) — hãy trỏ mdnow vào đúng host bạn tin cậy. Lưu ý: discovery probes `llms.txt` không xác thực (dùng `--no-llms` nếu chúng làm confuse private site); discovery tĩnh khi crawl (sitemap/BFS) cũng không xác thực; per-page fetches và render-based discovery có mang xác thực.

### Các cờ (flags)

| Cờ                | Ý nghĩa                                                                         |
| ----------------- | ------------------------------------------------------------------------------- |
| `-o, --out`       | Thư mục đầu ra (mặc định `.`)                                                   |
| `--crawl`         | Crawl cả site thành cây (chỉ website)                                           |
| `--max-pages N`   | Số trang tối đa để crawl (mặc định 100)                                         |
| `--all`           | Crawl tất cả các trang (bỏ qua `--max-pages`)                                   |
| `--render`        | Dùng trình duyệt stealth Camoufox (site JS/anti-bot); cần `[render]`            |
| `--no-llms`       | Bỏ qua discovery `llms.txt`; ép fetch/crawl                                     |
| `--allow-remote`  | Cho phép API cloud: phiên âm âm thanh/video, YouTube (gửi dữ liệu ra, tùy chọn) |
| `-H, --header`    | Thêm HTTP header (có thể lặp); ví dụ: `-H "Authorization: Bearer $TOKEN"`       |
| `--cookie-file`   | Đường dẫn tới tệp cookies Netscape hoặc JSON để xác thực                        |
| `--doctor`        | Báo cáo extras đã cài/còn thiếu (kèm cách khắc phục) rồi thoát                  |
| `--fetch-browser` | Tải trình duyệt Camoufox cho `--render` rồi thoát                               |
| `--install-skill` | Cài skill Claude Code đóng gói sẵn vào `~/.claude/skills/mdnow`                 |
| `--update`        | Nâng cấp mdnow lên phiên bản mới nhất từ git                                    |

---

## 🧠 Dành cho trợ lý AI

### Skill cho Claude Code

```bash
mdnow --install-skill                                   # → ~/.claude/skills/mdnow
mdnow --install-skill --skill-dir ~/.claude/skills/foo  # vị trí tùy chỉnh
mdnow --install-skill --force                           # ghi đè bản cũ
```

Skill này giúp Claude Code lấy một URL, crawl một site, hoặc chuyển đổi một tệp — ngay trong trình soạn thảo.

---

## Cơ chế hoạt động

Một **phễu ưu tiên đường rẻ nhất trước** — mỗi tầng chỉ chạy nếu tầng trước chưa tạo ra Markdown sạch:

1. **Discovery** — nếu site có công bố `/llms.txt`, `/llms-full.txt` (hoặc biến thể, hoặc bản `<url>.md` song sinh), dùng luôn và bỏ qua mọi thứ còn lại.
2. **Static fetch** — `httpx` + `trafilatura`. Mặc định nhanh; không cần trình duyệt.
3. **Render** — trình duyệt stealth Camoufox cho site nặng JS / anti-bot. Bật qua `--render`, hoặc tự động nâng cấp khi static trả về nội dung rỗng, mỏng, hoặc toàn boilerplate (ví dụ: farms của navigation/footer links).

---

## Định dạng đầu ra

Mỗi trang được ghi kèm YAML frontmatter và **versioning** theo content-hash — chạy lại chỉ tăng `version` khi nội dung thực sự đổi:

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
outline:
  - "## Getting Started"
  - "### Installation"
  - "## API Reference"
---
```

Khóa `outline` liệt kê các heading strings (hữu ích cho AI agents để nhanh chóng xác định các section).

Chế độ crawl còn ghi thêm ba tệp:

- **`llms.txt`** — chỉ mục theo chuẩn [llmstxt.org](https://llmstxt.org): tiêu đề `# <host>`, blockquote `> <summary>`, và danh sách `## Pages` gồm `- [title](path): summary`.
- **`llms-full.txt`** — toàn bộ Markdown của mọi trang đã crawl, mỗi trang có tiền tố `## <title>` + `Source: <url>`.
- **`manifest.json`** — metadata dạng máy đọc được: host, số trang, hash/summary/số token của từng trang. Mỗi trang bao gồm `sections`: một danh sách `{slug, heading, level, word_count, token_estimate}` theo thứ tự xuất hiện trong tài liệu, với `_intro` cho nội dung trước heading đầu tiên (hữu ích cho AI agents để chọn sections theo kích thước).

---

## Hành vi

- **Ảnh** — bị loại bỏ nhưng giữ lại alt-text (HTML); hoặc trích bằng OCR (tệp ảnh, `[docs]`).
- **Tệp** — non-HTML cục bộ/từ xa được tự nhận diện và chuyển đổi qua markitdown (PDF, Word, PowerPoint, Excel, EPub, ảnh, CSV/JSON/XML, ZIP).
- **Âm thanh/video & YouTube** — cần `--allow-remote` (phiên âm qua cloud). Không có nó, sẽ báo lỗi rõ ràng.
- **Transcript YouTube** — được gom thành các đoạn thô (~45 giây), mỗi đoạn có tiền tố mốc thời gian `[mm:ss]` liên kết sâu (deep-link) về đúng thời điểm đó trong video. YouTube thường giới hạn tần suất hoặc chặn yêu cầu transcript từ IP cloud/VPN/trung tâm dữ liệu; khi bị chặn, bạn nhận được một thông báo ngắn gọn, rõ ràng (không phải stack trace) — hãy chờ vài phút rồi thử lại.
- **Lỗi** — mọi lỗi đều in một dòng `Error: …` gọn gàng và thoát với mã khác 0; CLI không bao giờ đổ (dump) traceback Python. Đặt `MDNOW_DEBUG=1` để khôi phục traceback đầy đủ khi cần gỡ lỗi.
- **Thư mục** — chuyển đổi tất cả tệp trong thư mục, bảo toàn cấu trúc thư mục con; dotfiles/dotdirs bị bỏ qua; cô lập lỗi từng tệp (một lỗi không làm dừng lệnh); phát hành các tệp artifacts kiểu crawl (`llms.txt`, `llms-full.txt`, `manifest.json`).
- **`--crawl`** — không hợp lệ cho đầu vào là tệp / thư mục (chỉ fetch trang đơn hoặc thư mục hàng loạt); báo lỗi rõ ràng.
- **Crawl** — tìm qua `sitemap.xml` trước, quay về BFS; tôn trọng `robots.txt`, giới hạn tốc độ, cô lập lỗi từng trang.
- **SPA render bằng JS** (tài liệu React/Angular, v.v.) — tự nâng cấp trong chế độ crawl: nếu discovery tĩnh không thấy link, trang gốc được render; trang mỏng tự render. Cần `[render]` + `mdnow --fetch-browser`.
- **Cloudflare / anti-bot** — vượt qua bằng `--render` là nỗ lực tốt nhất có thể (best-effort).
- **Output terminal** — trạng thái có màu, spinner khi fetch, progress bar trực tiếp cho `--crawl` hoặc chuyển đổi thư mục, kèm gợi ý bước tiếp theo. Tự động chuyển về text thuần khi pipe hoặc trên non-tty / `NO_COLOR`, nên script không bị ảnh hưởng.

---

## 🔒 Tại sao cục bộ?

**Hoàn toàn cục bộ theo mặc định là một ràng buộc nền tảng, không phải một cờ tính năng.**

- Nội dung của bạn **không bao giờ rời khỏi máy** — ngoại lệ duy nhất là âm thanh/video/YouTube, và đó là tùy chọn qua `--allow-remote`.
- **Không API key, không đăng ký, không giới hạn tốc độ, không khóa chặt vào nhà cung cấp.**
- **Zero telemetry** — không gửi tín hiệu về nhà, không analytics. Đọc mã nguồn; không có lời gọi cloud ẩn.
- Dùng như một CLI, trong script, hay nhúng vào LLM IDE của bạn — bạn toàn quyền kiểm soát.

---

## Phát triển

```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,docs]"
.venv/bin/pytest          # 106 test, ~88% coverage
```

**Kiến trúc** — mỗi module dưới 200 dòng, một trách nhiệm: `cli`, `discovery`/`llmstxt`, `fetcher` (`StaticFetcher`/`CamoufoxFetcher` sau một interface `Fetcher` duy nhất), `playwright_patch` (bản vá tự phục hồi driver render), `extractor`, `convert` (bọc markitdown), `crawler`, `urls`, `linkrewrite`, `guards`, `frontmatter`, `outline`, `artifacts`, `writer`, `commands`, `doctor`.

---

## Giấy phép

[MIT](LICENSE) © Long Le. Hoan nghênh đóng góp — mở issue hoặc PR.

<div align="center"><sub>Dành cho những người đưa web vào LLM và muốn giữ dữ liệu của mình cho riêng mình.</sub></div>
