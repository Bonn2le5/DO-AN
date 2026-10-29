# Original User Request

## 2026-10-14T03:03:18Z

Xây dựng và hoàn thiện toàn diện hệ thống Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering) tích hợp AI gợi ý món ăn (Content-Based Filtering TF-IDF & Cosine Similarity), Concurrency Control đặt bàn và trừ kho nguyên liệu, Realtime Chat & Order Tracking qua WebSocket (Django Channels + Redis), GIS tìm chi nhánh gần nhất và Thanh toán đặt cọc VNPay Sandbox kèm chính sách hoàn tiền theo mốc thời gian.

Working directory: /Users/VuVan/Documents/DO-AN
Integrity mode: demo

## Requirements

### R1. Chuẩn hóa Backend & Khắc phục xung đột mô hình dữ liệu
- Đồng bộ nhất quán toàn bộ các app trong Django backend (`accounts`, `foods`, `orders`, `reservations`, `payments`, `carts`, `reviews`, `promotions`, `chat`, `analytics`, `branches`, `recommendations`) theo chuẩn schema tiếng Việt đã thiết kế tại `moc_schema_tieng_viet.sql`.
- Khắc phục triệt để lỗi import model (như `Food` vs `MonAn`, `Order` vs `DonHang`, `Payment` vs `ThanhToan`) để `python manage.py check` và migrate cơ sở dữ liệu thành công 100%.
- Cung cấp script nạp dữ liệu mẫu từ `Du-lieu-test.txt` vào PostgreSQL.

### R2. Tích hợp Thanh toán Cọc VNPay Sandbox & Kiểm soát Tranh chấp Đặt bàn
- Xây dựng module thanh toán VNPay Sandbox hoàn chỉnh: tạo URL thanh toán có mã hóa checksum HMAC-SHA512, xử lý IPN webhook và return URL callback.
- Thực hiện cơ chế Concurrency Control 2 giai đoạn: giữ chỗ tạm 10 phút trên Redis với TTL (`SET NX`) và chốt đơn trong Database Transaction với Khóa bi quan (`select_for_update()`).
- Tự động hóa chính sách phạt/hoàn cọc theo đề cương (>24h hoàn 100%, 6-24h hoàn 50%, <6h không hoàn) và sinh phiếu hoàn tiền.

### R3. Hệ thống Giao tiếp Thời gian thực (Real-time Communication)
- Kích hoạt Django Channels, cấu hình ASGI và Redis Channel Layer.
- Xây dựng WebSocket consumer cho:
  1. Chat trực tiếp giữa Khách hàng và Nhân viên nhà hàng (lưu trữ tin nhắn vào PostgreSQL trước khi broadcast).
  2. Cập nhật trạng thái vòng đời đơn hàng theo FSM (`cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat`/`da_huy`) trực tiếp tới màn hình khách hàng mà không cần reload trang.

### R4. Module AI Gợi ý Món ăn & Xử lý GIS
- Hoàn thiện thuật toán Content-Based Filtering dùng TF-IDF và Cosine Similarity dựa trên đặc trưng món (nguyên liệu, thể loại, độ cay) và lịch sử tương tác có trọng số của người dùng (xem, yêu thích, thêm giỏ, đặt hàng, đánh giá).
- Cung cấp tính năng Explainable Recommendation ("Gợi ý cho bạn vì bạn thích món cay/lẩu...") và giải pháp Cold-Start dựa trên độ phổ biến cho khách hàng mới.
- Hoàn thiện truy vấn không gian GIS (`ST_Distance`, `GiST Index`) tìm chi nhánh gần nhất theo tọa độ của người dùng.

### R5. Đồng bộ Frontend & Hoàn thiện Giao diện Quản trị (Admin/Staff)
- Đồng bộ toàn bộ URL endpoint và data mapper của `moc-frontend` khớp 100% với REST API của backend.
- Hoàn thiện các trang quản trị còn để trống: Quản lý Bàn ăn & Đặt bàn, Quản lý Thực đơn & Kho nguyên liệu, Quản lý Đánh giá, và Giao diện Chat của nhân viên.
- Kết nối `ChatWidget.tsx` và trang theo dõi đơn hàng với WebSocket backend.

## Acceptance Criteria

### Tính toàn vẹn & Ổn định hệ thống
- [ ] Lệnh `python manage.py check` chạy không có lỗi import hay model mapping nào.
- [ ] `npm run build` trên `moc-frontend` biên dịch thành công không có lỗi TypeScript.
- [ ] Database PostgreSQL nạp đầy đủ danh mục, 100+ món ăn, bàn ăn, chi nhánh từ file dữ liệu test.

### Nghiệp vụ Đặt bàn & Thanh toán VNPay
- [ ] Khi khách chọn bàn, hệ thống tạo khóa Redis với TTL đếm ngược 10 phút; bàn khác truy cập cùng lúc bị báo bận (HTTP 409).
- [ ] Tạo URL thanh toán VNPay Sandbox chuyển hướng chính xác, checksum hợp lệ và cập nhật trạng thái `da_xac_nhan` khi nhận IPN thành công.
- [ ] Thử nghiệm hủy đặt bàn tính đúng tỷ lệ hoàn cọc theo mốc thời gian quy định.

### Realtime & AI
- [ ] Mở 2 trình duyệt (1 Khách hàng, 1 Nhân viên), tin nhắn chat gửi qua WebSocket hiển thị tức thời cả 2 bên và được lưu vào DB.
- [ ] Thay đổi trạng thái đơn hàng ở trang Admin phản ánh tức thời trên giao diện khách hàng.
- [ ] API `/api/recommendations/` trả về Top-N món ăn kèm trường giải thích lý do gợi ý hợp lý theo tương tác của user.


## 2026-10-14T15:10:21Z

tiếp tục triển khai các agents tiến trình đã bị ngưng


## 2026-10-14T23:45:11Z

tiếp tục phần đang bị dừng
