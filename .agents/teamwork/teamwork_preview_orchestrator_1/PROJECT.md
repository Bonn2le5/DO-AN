# Project: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)

## Architecture
The system consists of a unified full-stack architecture:
1. **Frontend**: Vite SPA (React 19, TypeScript, Tailwind CSS v4, React Router v7, Zustand, Axios/Fetch).
   - Client Portal: Homepage, Menu & Dish Detail, Table Reservation Flow, Cart & Checkout, Order Tracking, Realtime Chat Widget.
   - Admin/Staff Portal: Dashboard, Order Management & FSM Transition, Table & Reservation Management, Menu & Inventory Management, Review Moderation, Staff Chat Support.
2. **Backend**: Django 4.x / Django REST Framework (Python 3.9) with 13 modular apps:
   - `accounts`: Authentication (JWT), Users (`NguoiDung`), Roles (`VaiTro`), Permissions (`QuyenHan`).
   - `foods`: Categories (`DanhMuc`), Dishes (`MonAn`), Ingredients (`NguyenLieu`), BOM (`DinhMucNguyenLieu`), Inventory History (`LichSuXuatNhapKho`).
   - `branches`: Branches (`ChiNhanh`) with PostGIS spatial geography point and GiST index.
   - `reservations`: Tables (`BanAn`), Deposit Policies (`ChinhSachDatCoc`, `QuyTacHuyDatCoc`), Bookings (`DatBan`), Booking Dishes (`MonAnTrongDatBan`).
   - `orders`: Orders (`DonHang`), Order Items (`ChiTietDonHang`), FSM History (`LichSuTrangThaiDon`).
   - `payments`: Payments (`ThanhToan`), VNPay Sandbox integration, Refund receipts (`PhieuHoanTien`).
   - `carts`: Carts (`GioHang`), Cart Items (`ChiTietGioHang`).
   - `promotions`: Promotions (`KhuyenMai`), Coupons (`MaKhuyenMai`), Usage (`LichSuDungKhuyenMai`).
   - `reviews`: Dish Reviews (`DanhGia`).
   - `chat`: Conversations (`HoiThoai`), Messages (`TinNhan`).
   - `recommendations`: Interactions (`TuongTacMonAn`), Cached Recommendations (`GoiYMonAn`), TF-IDF & Cosine similarity engine.
   - `analytics`: Dashboard metrics, Notifications (`ThongBao`).
   - `posts`: Blog Categories (`DanhMucBaiViet`), Posts (`BaiViet`).
3. **Data & Message Infrastructure**:
   - **PostgreSQL 14+ with PostGIS**: Authoritative relational data store matching `moc_schema_tieng_viet.sql`.
   - **Redis 6+**: Dual purpose:
     - Temporary 10-minute hold lock (`SET NX EX 600`) for table reservation concurrency.
     - Django Channels Channel Layer (`channels_redis`) for real-time WebSocket messaging.
   - **Django Channels (ASGI)**: Real-time 2-way staff-customer chat and order lifecycle push.
4. **External Services**:
   - VNPay Sandbox (Version 2.1.0, HMAC-SHA512 checksum, IPN webhook, Return URL).

---

## Feature Inventory
Every feature identified during the Survey phase mapped to its assigned milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Backend Model Schema Alignment | Chuẩn hóa toàn bộ model 13 Django apps theo `moc_schema_tieng_viet.sql`, cung cấp Model Aliases (`Food=MonAn`, `Order=DonHang`, etc.) | M1 | R1, Explorer 1 |
| 2 | Model Import & Django Check Resolution | Khắc phục 100% lỗi import gãy trong views, serializers, admin, settings (`AUTH_USER_MODEL`); `manage.py check` thoát mã 0 | M1 | R1, Explorer 1 |
| 3 | Clean Migrations Generation | Xóa migration lỗi cũ, tạo bộ migration `0001_initial.py` đồng nhất với 36 bảng CSDL tiếng Việt | M1 | R1, Explorer 1 |
| 4 | Test Data Seeding Command | Management command nạp 100 món, 5 danh mục, 4 thẻ từ `Du-lieu-test.txt` và tự động bổ sung chi nhánh, bàn ăn, chính sách cọc, user mẫu | M1 | R1, Explorer 1 |
| 5 | Dual API Route Support | Hỗ trợ router song ngữ tiếng Anh và tiếng Việt để tương thích mượt mà với frontend callers | M1 | R1, Explorer 1 |
| 6 | VNPay Sandbox URL Creation | Tạo URL thanh toán VNPay Sandbox có tham số chuẩn 2.1.0 và chữ ký HMAC-SHA512 | M2 | R2, Spec Miner |
| 7 | VNPay Return Callback | Xử lý redirect khách hàng, kiểm tra chữ ký HMAC-SHA512, trả về trạng thái thanh toán | M2 | R2, Spec Miner |
| 8 | VNPay IPN Webhook Verification | Webhook server-to-server xử lý thanh toán, kiểm tra checksum, idempotency, mã phản hồi 00, 01, 02, 04, 97 | M2 | R2, Spec Miner |
| 9 | Deposit Refund Evaluation | Tính tỷ lệ hoàn cọc theo thời gian hủy (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) | M2 | R2, Spec Miner |
| 10 | Refund Receipt Generation | Sinh phiếu hoàn tiền (`PhieuHoanTien`) chi tiết có mã định danh đối soát | M2 | R2, Spec Miner |
| 11 | Redis Table Hold (Phase 1) | Khóa giữ bàn tạm thời 10 phút trên Redis bằng `SET NX EX 600`, trả về HTTP 409 Conflict khi trùng | M2 | R2, Spec Miner |
| 12 | DB Pessimistic Lock (Phase 2) | Chốt đặt bàn trong Database Transaction với Khóa bi quan `select_for_update()`, đối soát token Redis | M2 | R2, Spec Miner |
| 13 | Material Inventory Deduction | Khấu trừ tồn kho nguyên liệu theo định mức (BOM) bằng khóa bi quan khi đơn được xác nhận | M2 | R2, Spec Miner |
| 14 | Django Channels & ASGI Setup | Kích hoạt Channels, cấu hình ASGI application và Redis Channel Layer | M3 | R3, Spec Miner |
| 15 | Order FSM Lifecycle Transitions | Quản lý máy trạng thái đơn hàng 6 bước (`cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat`/`da_huy`) có audit log | M3 | R3, Spec Miner |
| 16 | Realtime Order WebSocket Broadcast | Phát sự kiện chuyển đổi trạng thái đơn hàng tới kênh `order_{ma_don_hang}` và `staff_orders` | M3 | R3, Spec Miner |
| 17 | 2-Way Staff-Customer WebSocket Chat | WebSocket consumer kết nối `/ws/chat/<conversation_id>/` cho khách hàng và nhân viên | M3 | R3, Spec Miner |
| 18 | Chat Message DB Persistence | Lưu trữ tin nhắn vào PostgreSQL trước khi broadcast qua Channels | M3 | R3, Spec Miner |
| 19 | Content-Based Food Recommendation | Thuật toán TF-IDF và Cosine Similarity trên đặc trưng món ăn và hồ sơ tương tác của user | M4 | R4, Spec Miner |
| 20 | Interaction Weight Tracking | Ghi nhận tương tác với trọng số: xem=1, thích=2, giỏ=3, đặt=4, đánh giá=5 | M4 | R4, Spec Miner |
| 21 | Cold-Start Popularity Fallback | Gợi ý món phổ biến (số lượt đánh giá & điểm đánh giá cao nhất) cho user mới/chưa đăng nhập | M4 | R4, Spec Miner |
| 22 | Explainable Recommendation Tags | Sinh lý do giải thích gợi ý dễ hiểu ("Gợi ý vì bạn thích món cay/lẩu...") | M4 | R4, Spec Miner |
| 23 | PostGIS Nearest Branch Spatial Query | Truy vấn chi nhánh gần nhất theo tọa độ (lat, lng) dùng `ST_Distance` và GiST index | M4 | R4, Spec Miner |
| 24 | Frontend Type Adapter Layer | Cung cấp alias types hai chiều giải quyết dứt điểm 175 lỗi TypeScript; `npm run build` thành công 100% | M5 | R5, Explorer 2 |
| 25 | Frontend API Callers Alignment | Đồng bộ toàn bộ URL endpoint và data mapper của `moc-frontend` khớp 100% với REST API backend | M5 | R5, Explorer 2 |
| 26 | Admin Table & Reservation Portal | Trang quản lý sơ đồ bàn ăn, trạng thái bàn và lịch đặt bàn kèm thao tác duyệt/hủy | M5 | R5, Explorer 2 |
| 27 | Admin Menu & Inventory Portal | Trang quản lý món ăn, bật/tắt còn hàng, định mức và tồn kho nguyên liệu | M5 | R5, Explorer 2 |
| 28 | Admin Review Moderation Portal | Trang duyệt và ẩn/hiện đánh giá của khách hàng | M5 | R5, Explorer 2 |
| 29 | Staff Realtime Chat Portal | Màn hình chat trực tuyến của nhân viên hỗ trợ khách hàng | M5 | R5, Explorer 2 |
| 30 | Frontend WebSocket Chat & Tracking | Kết nối `ChatWidget.tsx` và tiến trình FSM theo dõi đơn hàng với WebSocket Channels | M5 | R5, Explorer 2 |
| 31 | Full E2E Integration & Verification | Kiểm thử toàn diện 4 tầng (Tier 1-4) đáp ứng 100% Acceptance Criteria của ORIGINAL_REQUEST.md | M6 | Acceptance, Orchestrator |
| 32 | Adversarial Hardening (Tier 5) | Thử nghiệm tải biên, race condition đặt bàn và kiểm toán tính toàn vẹn hệ thống | M6 | Project Pattern |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Schema Normalization & Migrations | Features 1–5: Khắc phục lỗi import model, chuẩn hóa Django apps theo `moc_schema_tieng_viet.sql`, tạo migrations sạch, script nạp dữ liệu mẫu từ `Du-lieu-test.txt` | None | PLANNED |
| M2 | VNPay Sandbox & Table Concurrency Control | Features 6–13: Module VNPay sandbox (URL, return, IPN), Concurrency Control 2 pha (Redis 10m TTL lock + DB pessimistic lock), tự động hóa hoàn cọc (>24h 100%, 6-24h 50%, <6h 0%), trừ kho nguyên liệu | M1 | PLANNED |
| M3 | Real-time Communication (Channels & Redis) | Features 14–18: Kích hoạt Django Channels, ASGI, Redis Channel Layer, WebSocket Consumer chat 2 chiều (lưu DB trước khi broadcast), FSM đơn hàng 6 trạng thái kèm broadcast | M1 | PLANNED |
| M4 | AI Recommendation Engine & PostGIS GIS | Features 19–23: Content-based filtering (TF-IDF + Cosine similarity), trọng số tương tác, Cold-start fallback, Explainable recommendation, PostGIS `ST_Distance` tìm chi nhánh gần nhất | M1 | PLANNED |
| M5 | Frontend Synchronization & Staff/Admin Portals | Features 24–30: Sửa 175 lỗi TypeScript (`npm run build` pass), đồng bộ API callers/mappers, hoàn thiện 4 trang Admin (Bàn, Menu/Kho, Đánh giá, Chat), nối WebSocket cho ChatWidget & Tracking | M1, M2, M3, M4 | PLANNED |
| M6 | End-to-End Testing & Adversarial Hardening | Features 31–32: Kiểm thử tự động E2E Tiers 1-4, kiểm tra race condition đặt bàn, kiểm tra IPN webhook, audit toàn vẹn | M1, M2, M3, M4, M5 | PLANNED |

---

## Interface Contracts

### 1. Table Concurrency Control Contract
- **Phase 1: Temporary Lock (Redis)**
  - Action: `POST /api/tables/{id}/giu_ban/`
  - Payload: `{"ngay": "YYYY-MM-DD", "gio": "HH:MM", "so_luong_khach": N}`
  - Success Response (HTTP 200): `{"id_giu_ban": "<uuid>", "thoi_han_giu_cho": "<iso-timestamp>", "thoi_gian_con_lai_giay": 600}`
  - Conflict Response (HTTP 409): `{"detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt", "code": "BAN_DANG_BAN"}`
- **Phase 2: Confirmation & Pessimistic DB Lock**
  - Action: `POST /api/reservations/`
  - Payload: `{"ban_an_id": N, "id_giu_ban": "<uuid>", "ngay_dat": "YYYY-MM-DD", "gio_bat_dau": "HH:MM", "so_luong_khach": N, ...}`
  - Logic: `@transaction.atomic` with `select_for_update()`. Verify Redis token matches, delete Redis key, insert `DatBan`.

### 2. VNPay Sandbox Payment Contract
- **Payment Initiation**:
  - Action: `POST /api/payments/vnpay/create/`
  - Payload: `{"loai_thanh_toan": "tien_coc" | "don_hang", "ma_tham_chieu_id": N, "so_tien": N, "ip_addr": "<client-ip>"}`
  - Response: `{"payment_url": "https://sandbox.vnpayment.vn/...", "txn_ref": "TT..."}`
- **IPN Webhook**:
  - Action: `GET /api/payments/vnpay/ipn/?vnp_Amount=...&vnp_SecureHash=...`
  - Response: `{"RspCode": "00", "Message": "Confirm Success"}` (or `"01"`, `"02"`, `"04"`, `"97"`)
- **Cancellation & Refund**:
  - Action: `POST /api/reservations/{id}/huy_dat_ban/`
  - Response: `{"trang_thai": "da_huy", "phan_tram_hoan_tien": 100 | 50 | 0, "so_tien_hoan": N, "phieu_hoan_tien": {...}}`

### 3. Realtime Channels WebSocket Contract
- **Order Lifecycle FSM**:
  - Valid transitions: `cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat`; cancellation to `da_huy` permitted from `cho_tiep_nhan` or `da_xac_nhan`.
  - Channel group: `order_{ma_don_hang}`
  - Payload: `{"type": "order.status_update", "order_id": N, "status": "<new_status>", "timestamp": "...", "note": "..."}`
- **Chat Consumer**:
  - Route: `/ws/chat/<conversation_id>/`
  - Receive payload: `{"noi_dung": "...", "loai_tin_nhan": "van_ban"}`
  - Action: Save to `tin_nhan` table in PostgreSQL -> Commit DB -> Broadcast `{"type": "chat.message", "message": {...}}` to group `chat_{conversation_id}`.

### 4. AI Recommendation & GIS Contract
- **Recommendation**:
  - Action: `GET /api/recommendations/?gioi_han=6`
  - Response: `{"data": [{"id": N, "ten": "...", "don_gia": N, "hinh_anh": "...", "diem_tuong_dong": 0.85, "ly_do_goi_y": "Gợi ý vì bạn thích món cay/lẩu", "is_cold_start": false}]}`
- **GIS Nearest Branch**:
  - Action: `GET /api/branches/nearest/?lat=10.7769&lng=106.7009`
  - Query: `ST_Distance(toa_do_gis, ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography)`
  - Response: `{"id": N, "ten": "Chi nhánh Quận 1", "dia_chi": "...", "distance_km": 1.25}`

---

## Code Layout & Ownership

```
/Users/VuVan/Documents/DO-AN/
├── moc-backend/                        <- Backend Worker Ownership (M1, M2, M3, M4)
│   ├── config/                         <- settings.py, urls.py, asgi.py, wsgi.py
│   ├── api/urls.py                     <- Central REST routers
│   ├── accounts/                       <- User auth, RBAC
│   ├── foods/                          <- Menu, ingredients, BOM inventory
│   ├── branches/                       <- Branches, PostGIS spatial queries
│   ├── reservations/                   <- Tables, bookings, Redis 10m lock
│   ├── orders/                         <- Orders, items, FSM transition logic
│   ├── payments/                       <- Payments, VNPay sandbox, refunds
│   ├── carts/                          <- Carts, items
│   ├── promotions/                     <- Discounts, vouchers
│   ├── reviews/                        <- Dish reviews
│   ├── chat/                           <- Realtime chat, consumers, routing
│   ├── recommendations/                <- TF-IDF & Cosine AI engine
│   ├── analytics/                      <- Dashboard stats, notifications
│   ├── posts/                          <- Blog posts
│   └── management/commands/            <- seed_data.py
│
├── moc-frontend/                       <- Frontend Worker Ownership (M5)
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── types/index.ts              <- Dual Type & Adapter definitions
│   │   ├── api/                        <- API service callers & mappers
│   │   ├── store/                      <- Zustand stores (authStore, cartStore)
│   │   ├── hooks/                      <- useReservationFlow, useWebSocket
│   │   ├── components/                 <- UI components, layout, chat/ChatWidget.tsx
│   │   └── pages/                      <- Client & Admin pages (AdminOrders, AdminReservations, AdminMenu, AdminReviews, AdminChat)
│
└── .agents/teamwork/                   <- Orchestrator metadata & reports ONLY
```
