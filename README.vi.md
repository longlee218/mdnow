<div align="center">

[English](README.md) · [Tiếng Việt](README.vi.md)

<img src="https://raw.githubusercontent.com/longlee218/mdnow/main/assets/banner.png" alt="mdnow — biến mọi thứ thành Markdown" width="640">

# mdnow

### Mọi URL. Mọi website. Mọi tệp. → Markdown sạch, sẵn sàng cho LLM.

**100% cục bộ. Không cần API key. Không gửi dữ liệu ra ngoài. Chỉ một câu lệnh.**

Biến một trang web, cả một website, hay một tệp PDF/Office/âm thanh thành Markdown sạch mà LLM đọc được — mà không phải đẩy nội dung của bạn lên cloud của bên thứ ba.

[![Python](https://img.shields.io/badge/python-3.11%2B-3b82f6.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-3b82f6.svg)](LICENSE)
[![Install: git](https://img.shields.io/badge/install-via%20git-6f42c1.svg)](#cài-đặt)
[![Local-first](https://img.shields.io/badge/data%20egress-none%20by%20default-16a34a.svg)](#-tại-sao-cục-bộ)

```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
```

<sub>macOS / Linux · hoặc <code>uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"</code></sub>

</div>

---

## Vấn đề

LLM chỉ tốt ngang với dữ liệu bạn đưa vào — nhưng web thì cản trở bạn ở mọi bước:

- **HTML thô toàn là nhiễu.** Menu, quảng cáo, banner cookie và một rừng `<div>` chôn vùi nội dung thật.
- **Scraper trên cloud khiến bạn trả giá hai lần.** Tính phí theo từng lần gọi *và* gửi nội dung của bạn cho bên thứ ba.
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

|  | **mdnow** | API scraper trên cloud | Công cụ cục bộ đơn mục đích |
|---|:---:|:---:|:---:|
| Chạy hoàn toàn cục bộ | ✅ | ❌ chỉ cloud | ✅ |
| Không cần API key / đăng ký | ✅ | ❌ | ✅ |
| Nội dung của bạn được giữ riêng tư | ✅ không gửi đi | ❌ vốn dĩ phải gửi | ✅ |
| Trang web → Markdown | ✅ | ✅ | ⚠️ chỉ trích xuất |
| Crawl cả site → `llms.txt` | ✅ | ⚠️ tùy nơi | ❌ |
| Render vượt JS / anti-bot | ✅ | ✅ | ❌ |
| Tệp: PDF, Office, âm thanh, ảnh… | ✅ | ⚠️ tùy nơi | ⚠️ mỗi loại một công cụ |
| Skill cho Claude | ✅ | ❌ | ❌ |
| Chi phí | **Miễn phí (MIT)** | 💲 tính theo lượt | Miễn phí |

> **Điểm khác biệt then chốt:** làm được mọi thứ một cloud scraper làm, nhưng ngay trên máy *của bạn* — và làm được mọi thứ một công cụ trích xuất cục bộ làm, nhưng cho cả web *lẫn* mọi loại tệp, đã được thiết kế sẵn cho LLM.

---

## 🚀 Bạn nhận được gì

| | Khả năng | Ý nghĩa |
|---|---|---|
| ⚡ | **Static fetch** | `httpx` + `trafilatura`. Mặc định nhanh, không cần trình duyệt. |
| 🎭 | **Stealth render** | Camoufox headless Firefox cho site nặng JS / anti-bot — tùy chọn bật, hoặc **tự động nâng cấp** khi nội dung tĩnh quá mỏng. |
| 🔗 | **Crawl + lập chỉ mục** | Cây cả site → mỗi trang một `.md` + `llms.txt` + `llms-full.txt` + `manifest.json`. |
| 📄 | **Chuyển đổi mọi tệp** | PDF, Word, PowerPoint, Excel, EPub, ảnh (OCR), âm thanh, YouTube, CSV/JSON/XML, ZIP. |
| 🔌 | **Skill đóng gói sẵn** | `mdnow --install-skill` cài một skill dùng ngay vào Claude Code. |
| 🔒 | **Cục bộ trước tiên** | Không key, không telemetry, mặc định không gửi dữ liệu đi. Nội dung là của bạn. |
| 🧾 | **Kết quả bất biến (idempotent)** | Versioning theo content-hash — chạy lại chỉ tăng `version` khi nội dung thực sự đổi. |

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

```bash
# Một dòng (macOS / Linux)
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh

# Hoặc với uv (khuyến nghị)
uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"

# Hoặc với pipx
pipx install "git+https://github.com/longlee218/mdnow"

# Sau đó:
mdnow https://example.com -o out/
```

> **Phân phối qua git, không qua PyPI** — cài thẳng từ repo này. Không registry, không bước publish.

Không chắc đã cài những gì? Chạy **`mdnow --doctor`** — nó liệt kê từng extra và câu lệnh chính xác để cài phần còn thiếu.

---

## Cài đặt

### 1. Cài bản nền (cho mọi người)

Chọn một cách:

**Một dòng lệnh shell** (macOS / Linux):
```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh
```

**uv** (khuyến nghị, đa nền tảng):
```bash
uv tool install "mdnow @ git+https://github.com/longlee218/mdnow"
```

**pipx** (chỉ Python, không cần uv):
```bash
pipx install "git+https://github.com/longlee218/mdnow"
```

**Từ mã nguồn** (cho người đóng góp):
```bash
git clone https://github.com/longlee218/mdnow.git
cd mdnow
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 2. Extras (tùy chọn)

Bản nền `mdnow` lấy **HTML tĩnh** và chuyển đổi **tệp cục bộ** bằng logic nhẹ. Chỉ bật thêm khả năng nặng hơn khi bạn cần:

| Extra | Bổ sung | Cài đặt |
|-------|---------|---------|
| `[render]` | Trình duyệt stealth headless (Camoufox, tải ~300MB một lần) | `uv tool install "mdnow[render] @ git+https://github.com/longlee218/mdnow"` rồi `mdnow --fetch-browser` |
| `[docs]` | Chuyển đổi mọi tệp (PDF, Office, ảnh/OCR, âm thanh, YouTube) | `uv tool install "mdnow[docs] @ git+https://github.com/longlee218/mdnow"` |

Với trình cài đặt shell, truyền cờ thay thế:
```bash
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --render --docs
# hoặc tất cả cùng lúc:
curl -LsSf https://raw.githubusercontent.com/longlee218/mdnow/main/install.sh | sh --all
```

`pipx` cũng dùng tương tự: `pipx install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"`.

### Nâng cấp

Cài lại phiên bản mới nhất từ git, giữ nguyên các extras đã cài:

```bash
mdnow --update
```

Lệnh này chạy `uv tool install --force "mdnow[<extras>] @ git+https://github.com/longlee218/mdnow"`. Nếu `uv` không có trên PATH, nó sẽ in câu lệnh thủ công tương đương.

### Windows

**Một dòng lệnh PowerShell**:

```powershell
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 | iex
```

Với cờ (lưu trước, rồi chạy):

```powershell
irm https://raw.githubusercontent.com/longlee218/mdnow/main/install.ps1 -o install.ps1
.\install.ps1 -Render -Docs
# hoặc tất cả cùng lúc:
.\install.ps1 -All -Skill
```

Hoặc cài uv / pipx thủ công:

```powershell
uv tool install "mdnow[render,docs] @ git+https://github.com/longlee218/mdnow"
mdnow --fetch-browser   # nếu dùng [render]
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
mdnow "https://youtu.be/watch?v=abc123" --allow-remote -o out/   # transcript YouTube (gửi ra cloud)
```

### Bỏ qua discovery, ép fetch/crawl
```bash
# Mặc định, nếu site có công bố /llms.txt, mdnow dùng luôn. Ép lấy mới bằng:
mdnow https://example.com --crawl --no-llms -o out/
```

### Các cờ (flags)

| Cờ | Ý nghĩa |
|------|---------|
| `-o, --out` | Thư mục đầu ra (mặc định `.`) |
| `--crawl` | Crawl cả site thành cây (chỉ website) |
| `--max-pages N` | Số trang tối đa để crawl (mặc định 100) |
| `--all` | Crawl tất cả các trang (bỏ qua `--max-pages`) |
| `--render` | Dùng trình duyệt stealth Camoufox (site JS/anti-bot); cần `[render]` |
| `--no-llms` | Bỏ qua discovery `llms.txt`; ép fetch/crawl |
| `--allow-remote` | Cho phép API cloud: phiên âm âm thanh/video, YouTube (gửi dữ liệu ra, tùy chọn) |
| `--doctor` | Báo cáo extras đã cài/còn thiếu (kèm cách khắc phục) rồi thoát |
| `--fetch-browser` | Tải trình duyệt Camoufox cho `--render` rồi thoát |
| `--install-skill` | Cài skill Claude Code đóng gói sẵn vào `~/.claude/skills/mdnow` |
| `--update` | Nâng cấp mdnow lên phiên bản mới nhất từ git |

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
3. **Render** — trình duyệt stealth Camoufox cho site nặng JS / anti-bot. Bật qua `--render`, hoặc tự động nâng cấp khi static trả về nội dung rỗng/mỏng.

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
---
```

Chế độ crawl còn ghi thêm ba tệp:

- **`llms.txt`** — chỉ mục theo chuẩn [llmstxt.org](https://llmstxt.org): tiêu đề `# <host>`, blockquote `> <summary>`, và danh sách `## Pages` gồm `- [title](path): summary`.
- **`llms-full.txt`** — toàn bộ Markdown của mọi trang đã crawl, mỗi trang có tiền tố `## <title>` + `Source: <url>`.
- **`manifest.json`** — metadata dạng máy đọc được: host, số trang, hash/summary/số token của từng trang.

---

## Hành vi

- **Ảnh** — bị loại bỏ nhưng giữ lại alt-text (HTML); hoặc trích bằng OCR (tệp ảnh, `[docs]`).
- **Tệp** — non-HTML cục bộ/từ xa được tự nhận diện và chuyển đổi qua markitdown (PDF, Word, PowerPoint, Excel, EPub, ảnh, CSV/JSON/XML, ZIP).
- **Âm thanh/video & YouTube** — cần `--allow-remote` (phiên âm qua cloud). Không có nó, sẽ báo lỗi rõ ràng.
- **`--crawl`** — không hợp lệ cho đầu vào là tệp (chỉ một tệp); báo lỗi rõ ràng.
- **Crawl** — tìm qua `sitemap.xml` trước, quay về BFS; tôn trọng `robots.txt`, giới hạn tốc độ, cô lập lỗi từng trang.
- **SPA render bằng JS** (tài liệu React/Angular, v.v.) — tự nâng cấp trong chế độ crawl: nếu discovery tĩnh không thấy link, trang gốc được render; trang mỏng tự render. Cần `[render]` + `mdnow --fetch-browser`.
- **Cloudflare / anti-bot** — vượt qua bằng `--render` là nỗ lực tốt nhất có thể (best-effort).

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
