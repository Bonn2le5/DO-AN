# Dispatch: Milestone 1 Explorer 1 (Models & Aliases Strategy)

## Mission
Analyze all 13 Django apps in `moc-backend/` to provide the exact, unambiguous code changes required for models, serializers, views, and settings:
1. Standardize models to Vietnamese schema (`NguoiDung`, `MonAn`, `DonHang`, `DatBan`, `ThanhToan`, `GioHang`, `ChiTietGioHang`, `DanhGia`, `ChiNhanh`, `KhuyenMai`, `HoiThoai`, `TinNhan`, `ThongBao`, `BaiViet`).
2. Add backward-compatible model aliases in each app's `models.py` (`Food = MonAn`, `Category = DanhMuc`, `Order = DonHang`, `OrderItem = ChiTietDonHang`, `Payment = ThanhToan`, `Branch = ChiNhanh`, `Cart = GioHang`, `CartItem = ChiTietGioHang`, `Review = DanhGia`, `ChatRoom = HoiThoai`, `ChatMessage = TinNhan`, `Notification = ThongBao`, `Promotion = KhuyenMai`, etc.).
3. Fix `config/settings.py` (`AUTH_USER_MODEL = "accounts.NguoiDung"`).
4. Fix `accounts/admin.py` and other admin files importing nonexistent English models.
5. Fix serializers and views in `branches`, `payments`, `promotions`, `chat`, `recommendations`, `carts`, `reviews`, `posts`, `analytics` that currently import English names.

## Mandatory Files to Read
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_1/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_1/handoff.md`
- `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`

## Deliverables
Write your strategy report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1/handoff.md`
and notify Orchestrator via `send_message`.


## 2026-10-14T03:17:58Z
You are Milestone 1 Explorer 1 (Models & Aliases Strategy) for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1/DISPATCH.md.
Analyze all 13 Django apps models, serializers, views, admin, and settings to provide the complete strategy for standardizing to Vietnamese schema while maintaining backward-compatible aliases (Food=MonAn, etc.).
Write your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1/handoff.md and notify me via send_message when done.
