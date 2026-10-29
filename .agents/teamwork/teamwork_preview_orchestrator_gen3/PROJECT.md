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
| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|--------|
| 1 | Backend Model Schema Alignment | Chuẩn hóa toàn bộ model 13 Django apps theo `moc_schema_tieng_viet.sql` | M1 | DONE |
| 2 | Model Import & Django Check Resolution | 0 check issues, model aliases | M1 | DONE |
| 3 | Clean Migrations Generation | Migration ban đầu sạch 13 apps | M1 | DONE |
| 4 | Test Data Seeding Command | `seed_data.py` nạp CSDL đầy đủ | M1 | DONE |
| 5 | Dual API Route Support | Router song ngữ EN và VI | M1 | DONE |
| 6 | VNPay Sandbox URL Creation | URL 2.1.0 + HMAC-SHA512 | M2 | DONE |
| 7 | VNPay Return Callback | Return callback kiểm tra chữ ký | M2 | DONE |
| 8 | VNPay IPN Webhook Verification | 5-stage IPN validation (00/01/02/04/97) | M2 | DONE |
| 9 | Deposit Refund Evaluation | >24h 100%, 6-24h 50%, <6h 0%, no-show 0% | M2 | DONE |
| 10 | Refund Receipt Generation | `PhieuHoanTien` RF-{ma_dat_ban}-{YYYYMMDD} | M2 | DONE |
| 11 | Redis Table Hold (Phase 1) | `SET NX EX 600` HTTP 409 BAN_DANG_BAN | M2 | DONE |
| 12 | DB Pessimistic Lock (Phase 2) | Table mutex `select_for_update` | M2 | DONE |
| 13 | Material Inventory Deduction | Sorted-ID BOM deduction deadlock-free | M2 | DONE |
| 14 | Django Channels & ASGI Setup | Kích hoạt Channels, ASGI, Redis Channel Layer | M3 | IN_PROGRESS |
| 15 | Order FSM Lifecycle Transitions | 6 trạng thái FSM đơn hàng có audit log | M3 | IN_PROGRESS |
| 16 | Realtime Order WebSocket Broadcast | Broadcast sự kiện trạng thái đơn hàng | M3 | IN_PROGRESS |
| 17 | 2-Way Staff-Customer WebSocket Chat | WebSocket consumer `/ws/chat/<conv_id>/` | M3 | IN_PROGRESS |
| 18 | Chat Message DB Persistence | Lưu PostgreSQL trước khi broadcast | M3 | IN_PROGRESS |
| 19 | Content-Based Food Recommendation | Thuật toán TF-IDF và Cosine Similarity | M4 | PLANNED |
| 20 | Interaction Weight Tracking | Trọng số: xem=1, thích=2, giỏ=3, đặt=4, đánh giá=5 | M4 | PLANNED |
| 21 | Cold-Start Popularity Fallback | Gợi ý món phổ biến cho user mới | M4 | PLANNED |
| 22 | Explainable Recommendation Tags | Lý do giải thích gợi ý | M4 | PLANNED |
| 23 | PostGIS Nearest Branch Spatial Query | `ST_Distance` và GiST index tìm chi nhánh | M4 | PLANNED |
| 24 | Frontend Type Adapter Layer | Alias types giải quyết lỗi TypeScript | M5 | PLANNED |
| 25 | Frontend API Callers Alignment | Đồng bộ REST API endpoints | M5 | PLANNED |
| 26 | Admin Table & Reservation Portal | Quản lý sơ đồ bàn & đặt bàn | M5 | PLANNED |
| 27 | Admin Menu & Inventory Portal | Quản lý món & kho nguyên liệu | M5 | PLANNED |
| 28 | Admin Review Moderation Portal | Duyệt đánh giá khách hàng | M5 | PLANNED |
| 29 | Staff Realtime Chat Portal | Chat trực tuyến nhân viên | M5 | PLANNED |
| 30 | Frontend WebSocket Chat & Tracking | Nối ChatWidget & Order Tracking WebSocket | M5 | PLANNED |
| 31 | Full E2E Integration & Verification | Kiểm thử toàn diện Tiers 1-4 | M6 | PLANNED |
| 32 | Adversarial Hardening (Tier 5) | Thử nghiệm tải biên & audit toàn vẹn | M6 | PLANNED |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Backend Schema Normalization & Migrations | Features 1–5 | None | **DONE** |
| M2 | VNPay Sandbox & Table Concurrency Control | Features 6–13 | M1 | **DONE** |
| M3 | Real-time Communication (Channels & Redis) | Features 14–18 | M1, M2 | **IN_PROGRESS** |
| M4 | AI Recommendation Engine & PostGIS GIS | Features 19–23 | M1 | PLANNED |
| M5 | Frontend Synchronization & Staff/Admin Portals | Features 24–30 | M1, M2, M3, M4 | PLANNED |
| M6 | End-to-End Testing & Adversarial Hardening | Features 31–32 | M1, M2, M3, M4, M5 | PLANNED |

---

## Code Layout & Ownership
```
/Users/VuVan/Documents/DO-AN/
├── moc-backend/                        <- Backend Worker Ownership (M1, M2, M3, M4)
│   ├── config/                         <- settings.py (Redis, Channels, VNPay), urls.py, asgi.py
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
│   ├── chat/                           <- Realtime chat, consumers, routing (M3)
│   ├── recommendations/                <- TF-IDF & Cosine AI engine (M4)
│   ├── analytics/                      <- Dashboard stats, notifications
│   ├── posts/                          <- Blog posts
│   └── management/commands/            <- seed_data.py
│
├── moc-frontend/                       <- Frontend Worker Ownership (M5)
└── .agents/teamwork/                   <- Orchestrator metadata & reports ONLY
```
