# BRIEFING — 2026-10-14T03:15:00Z

## Mission
Thực hiện điều tra khảo sát toàn diện backend Django (moc-backend), lược đồ CSDL (moc_schema_tieng_viet.sql), dữ liệu test (Du-lieu-test.txt), và xác định chi tiết toàn bộ xung đột tên model/bảng/trường, migration, cấu hình DB để phục vụ chuẩn hóa theo R1-R5.

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend & Database Schema Explorer
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_1
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: survey

## 🔒 Key Constraints
- Read-only investigation — do NOT implement code changes in the source code
- Document exact file paths, line numbers, discrepancies, and actionable remediation steps
- Output complete report to handoff.md and notify parent agent via send_message

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: not yet

## Investigation State
- **Explored paths**:
  * `moc_schema_tieng_viet.sql`: 36 bảng CSDL chuẩn, 17 ENUM types, PostGIS, pgcrypto.
  * `Du-lieu-test.txt`: 5 categories, 100 foods (20 món/danh mục), 4 tags theo tên tiếng Anh. Thiếu bàn ăn và chi nhánh.
  * `moc-backend/config/`: settings.py, asgi.py, wsgi.py, urls.py, .env.
  * 13 Django apps: `accounts`, `foods`, `branches`, `reservations`, `orders`, `payments`, `promotions`, `chat`, `recommendations`, `carts`, `reviews`, `posts`, `analytics`, kèm thư mục `api`.
  * `moc-frontend/`: router, api client, mappers.ts, build errors (175 TS errors do dang dở rename).
- **Key findings**:
  * Đang có sự phân mảnh nghiêm trọng: 9 apps đã đổi sang tên tiếng Việt (nhưng view/serializer hoặc admin chưa đồng bộ hoàn toàn), trong khi 4 apps (`carts`, `reviews`, `posts`, `analytics`) vẫn giữ code tiếng Anh và import model tiếng Anh cũ (`Food`, `Order`, `OrderItem`).
  * `manage.py check` gãy ngay tại `carts/models.py:4` (`cannot import name 'Food' from 'foods.models'`).
  * Toàn bộ migrations (`0001_initial.py`) là tàn dư từ đợt khởi tạo tiếng Anh (07/09/2026), không khớp với model tiếng Việt hiện tại.
  * GDAL và GEOS đã sẵn sàng trên macOS (`/opt/homebrew/opt/gdal/lib/libgdal.dylib` và `libgeos_c.dylib`).
  * Redis và Channels đã cài trong `.venv` nhưng chưa cấu hình trong `settings.py` / `asgi.py`.
- **Unexplored areas**: None for backend survey.

## Key Decisions Made
- Lập lộ trình khắc phục theo chiến lược Model Alias & Schema Unification: vừa chuẩn hóa 100% db_table và class tiếng Việt theo `moc_schema_tieng_viet.sql`, vừa cung cấp alias tiếng Anh (`Food = MonAn`, `Order = DonHang`, ...) để bảo đảm an toàn cho các module chưa kịp refactor và hỗ trợ dual endpoint cho frontend.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_1/handoff.md — Báo cáo điều tra đầy đủ 5 phần
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_1/progress.md — Nhật ký tiến độ và heartbeat
