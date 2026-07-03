# AI-Grade Output & Private-Site Access

Branch: `feat/ai-output-and-private-sites` | Status: ✅ complete

Progress: Phase 1 ✅ (auth, verified live vs httpbingo echo) · Phase 2 ✅ (sections/outline,
verified on PEP 8 + quotes.toscrape crawl) · Phase 3 ✅ (quality.py) · Phase 4 ✅ (141 tests,
88% cov) · Phase 5 ✅ (README/README.vi/CLAUDE.md/docs highlight + changelog)

Code review: 3 security findings (empty-domain cookie leak, cross-origin header egress,
header-error value leak) — all fixed + regression-tested; egress documented as accepted
behavior for a personal CLI.

## Goal

1. Output chất lượng cao hơn, cấu trúc tốt hơn cho AI-agent retrieval (section-level metadata).
2. Trích xuất được trang private nội bộ (wiki/Jira/Confluence sau auth wall) qua header/cookie injection.
3. Bắt trang boilerplate (link-farm) mà heuristic đếm-từ hiện tại bỏ lọt.

Out of scope (YAGNI, chờ demand): per-vendor API connectors (Confluence/Notion REST),
persistent-browser SSO login flow, chunk full-text trong manifest.

## Phases

### Phase 1 — Auth injection (private sites)
- New module `mdnow/auth.py`: parse `--header "Name: Value"` strings; load cookie file
  (Netscape cookies.txt **and** JSON list) → list of cookie dicts.
- `StaticFetcher(headers=..., cookies=...)` — merge vào httpx call.
- `CamoufoxFetcher(headers=..., cookies=...)` — `page.set_extra_http_headers` +
  `page.context.add_cookies` trước khi goto.
- CLI: `--header` (repeatable), `--cookie-file PATH`. Thread qua runner/crawler.
- Secret hygiene: header/cookie values không bao giờ được echo/log hay ghi vào output.
- Verify: unit tests (fetcher nhận headers/cookies; cookie parser cả 2 format; CLI wiring).

### Phase 2 — Section-level output cho AI retrieval
- `outline.sections(markdown)` → `[{slug, heading, level, word_count, token_estimate}]`
  (nội dung mỗi section = từ heading đến heading kế tiếp; preamble → slug `_intro`).
- `manifest.json` pages thêm key `sections` (thay `headings` bằng superset? Không —
  giữ `headings` cho backward-compat, thêm `sections`).
- Frontmatter mỗi page thêm `outline:` (list chuỗi `"## Heading"`) — anchor rẻ cho agent.
- Verify: unit tests outline/artifacts/frontmatter; hash versioning không bị bump khi body không đổi.

### Phase 3 — Link-density thin detection
- New module `mdnow/quality.py`: move `THIN_WORDS`; add `link_density(md)` +
  `is_thin(md)` = word_count < 50 **or** (link_density > 0.7 and word_count < 200).
- runner `_acquire` + crawler dùng `is_thin` thay vì so word count trực tiếp.
  `runner.THIN_WORDS` giữ re-export để không gãy import cũ.
- Verify: unit tests với trang link-farm giả; suite cũ vẫn pass.

### Phase 4 — Real-data verification
- Chạy trên site thực: 1 trang docs tĩnh, 1 crawl nhỏ; inspect manifest sections + outline.
- Nếu network bị chặn trong sandbox → dùng fixture HTML thực (lưu sẵn) qua monkeypatch.

### Phase 5 — Docs sync + highlight
- README.md + README.vi.md: flags mới, mục "Private / internal sites", manifest schema mới.
- CLAUDE.md: cập nhật commands + architecture (auth seam, quality.py).
- `docs/`: highlight doc cho feature này + changelog entry.

## Success Criteria
- Toàn bộ suite (106+ mới) pass; coverage không giảm dưới mức hiện tại (~88%).
- `mdnow <url> --header/--cookie-file` fetch được trang yêu cầu auth (test giả lập).
- `manifest.json` có `sections` với token_estimate đúng; frontmatter có `outline`.
- Trang >50 từ nhưng toàn link được escalate sang render.
- README/README.vi/CLAUDE.md đồng bộ trong cùng nhánh.

## Risks
- Camoufox cookie API khác playwright thuần → test lazy-import path, không test browser thật.
- Frontmatter thêm `outline` làm mọi file re-write lần đầu (status updated, version giữ nguyên
  nếu body không đổi) — chấp nhận được, ghi chú trong docs.
