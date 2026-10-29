# Business Logic & Specification Mining Report: Web App Nhà hàng Mộc

## 1. Observation

Directly observed facts, file paths, line numbers, and authoritative sources:

1. **Schema and Database Models (`/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`)**:
   - Lines 16–33 define enum types:
     ```sql
     CREATE TYPE trang_thai_ban AS ENUM ('trong','dang_giu','da_dat','dang_phuc_vu','bao_tri');
     CREATE TYPE hinh_thuc_dat_ban AS ENUM ('chi_giu_cho','dat_ban_va_goi_mon','dat_ban_goi_mon_chinh_sua');
     CREATE TYPE trang_thai_dat_ban AS ENUM ('cho_thanh_toan','da_xac_nhan','khach_da_den','hoan_tat','da_huy','khach_khong_den');
     CREATE TYPE trang_thai_coc AS ENUM ('chua_thanh_toan','dang_xu_ly','thanh_cong','that_bai','da_hoan_tien','hoan_tien_mot_phan');
     CREATE TYPE moc_huy_dat_ban AS ENUM ('truoc_24h','tu_6_den_24h','trong_6h','khach_khong_den');
     CREATE TYPE trang_thai_don_hang AS ENUM ('cho_tiep_nhan','da_xac_nhan','dang_che_bien','san_sang','hoan_tat','da_huy');
     CREATE TYPE loai_thanh_toan AS ENUM ('don_hang','tien_coc');
     CREATE TYPE trang_thai_thanh_toan AS ENUM ('cho_xu_ly','thanh_cong','that_bai','da_hoan_tien');
     CREATE TYPE loai_tuong_tac AS ENUM ('xem','them_gio_hang','dat_mon','danh_gia','yeu_thich');
     ```
   - Lines 107–112: `chi_nhanh` table has `toa_do_gis geography(Point, 4326) NOT NULL` and spatial index `CREATE INDEX idx_chi_nhanh_toa_do ON chi_nhanh USING GIST (toa_do_gis);`.
   - Lines 281–287: `quy_tac_huy_dat_coc` table defines `moc_thoi_gian moc_huy_dat_ban` and `phan_tram_hoan_tien NUMERIC(5,2)`.
   - Lines 317–319: Constraint `kiem_tra_chi_giu_cho`: `hinh_thuc <> 'chi_giu_cho' OR (yeu_cau_dat_coc = false AND so_tien_coc = 0)`.
   - Lines 421–431: `lich_su_trang_thai_don` table logs FSM audit history (`tu_trang_thai`, `sang_trang_thai`, `doi_boi`, `ghi_chu`, `tao_luc`).
   - Lines 522–550: `hoi_thoai` (`khach_hang_id`, `nhan_vien_id`, `trang_thai`, `tin_nhan_cuoi_luc`) and `tin_nhan` (`hoi_thoai_id`, `nguoi_gui_id`, `noi_dung`, `da_doc`, `doc_luc`).
   - Lines 574–596: `tuong_tac_mon_an` (`loai_tuong_tac`, `trong_so`) and `goi_y_mon_an` (`diem_tuong_dong`, `ly_do_goi_y`, `phien_ban_model`).

2. **Thesis Document Specifications (`BB-V1_1250080238-DE-CUONG-DACN-CNPM - Vũ Nguyễn Văn.docx`)**:
   - Paragraph 26: 2-phase concurrency control: TTL countdown in Redis temporary hold, followed by Database Transaction with Pessimistic Locking (`SELECT ... FOR UPDATE`) at final confirmation.
   - Paragraph 36: Content-Based Filtering using TF-IDF and Cosine Similarity, Explainable Recommendation, and Popularity Fallback for Cold-Start users.
   - Paragraph 40 & 103: PostGIS geography point, SRID 4326, `ST_Distance`, and GiST index for nearest branch navigation.
   - Paragraph 108: Reservation concurrency testing using sorted set / TTL in Redis, database transaction, and order state machine (`Pending` -> `Confirmed` -> `Preparing` -> `Serving` -> `Completed`/`Cancelled`).
   - Paragraph 252 (Reference 13): VNPay integration developer documentation (`https://sandbox.vnpayment.vn/apis/`).

3. **Current Backend Implementation Inconsistencies (`moc-backend`)**:
   - `payments/views.py`: Line 7 imports `from .models import Payment`, but `payments/models.py` defines `ThanhToan`. No VNPay checksum creation, return URL, or IPN handler exists.
   - `reservations/services.py`: Lines 10–12 create Redis key `giu-ban:{id_ban}:{ngay}:{gio}`, but lines 89–98 in `reservations/views.py` handle cancellation (`huy_dat_ban`) by simply setting `trang_thai = DA_HUY` without computing refund percentages (100%, 50%, 0%) or updating deposit status (`trang_thai_coc`).
   - `orders/services.py`: Line 103 `doi_trang_thai` changes status and creates history record, but does NOT validate legal FSM state transitions and does NOT trigger any WebSocket broadcast.
   - `chat`: Only has basic REST ViewSet `ChatRoomViewSet`; no `consumers.py`, no `routing.py`, and `config/asgi.py` does not configure Channels `ProtocolTypeRouter`.
   - `recommendations/services.py`: Implements raw Python TF-IDF and Cosine similarity, but `ly_do_goi_y` is hardcoded to a static string rather than explaining the specific matching features (e.g. spicy, hotpot).
   - `branches/views.py`: Imports `from .models import Branch` (should be `ChiNhanh`) and lacks any PostGIS `ST_Distance` or `nearest` endpoint.

4. **Frontend Expectations (`moc-frontend`)**:
   - `src/api/reservations.api.ts`: Lines 22–34 explicitly specify deposit rate 20% and cancellation refund tiers:
     - `truoc_24h`: 100%
     - `tu_6_den_24h`: 50%
     - `trong_6h`: 0%
     - `khach_khong_den`: 0%
   - `src/api/reservations.api.ts`: Lines 42 & 113 define expected endpoints `/api/dat-ban/giu-ban/` and `/api/thanh-toan/vnpay/tao-phien/`.
   - `src/components/chat/ChatWidget.tsx`: Lines 15–19 specify WebSocket route `ws://<host>/ws/chat/<conversation_id>/`.
   - `src/api/mappers.ts`: Mappers accept both Vietnamese snake_case and English property names.

---

## 2. Logic Chain

1. **VNPay & Refund Chain**:
   - *Premise*: VNPay v2.1.0 requires query parameters sorted alphabetically by ASCII key and hashed using HMAC-SHA512 with the secret key (`vnp_HashSecret`).
   - *Observation*: `payments` currently has no VNPay payment initiation endpoint (`/api/payments/vnpay/create/` or `/api/thanh-toan/vnpay/tao-phien/`), no Return URL validation, and no IPN handler (`RspCode` `00`, `01`, `02`, `04`, `97`).
   - *Deduction*: A complete VNPay Sandbox service must be specified with exact query parameter encoding, HMAC-SHA512 generation, IPN response protocol, and transaction status transition to `da_xac_nhan`.
   - *Premise*: Cancellation rules require time comparison: $\Delta t = T_{\text{reservation}} - T_{\text{cancellation}}$.
   - *Deduction*: When `POST /api/reservations/{id}/huy_dat_ban/` is invoked, the backend must calculate $\Delta t$:
     - If $\Delta t > 24\text{h}$ -> `phan_tram_hoan_tien = 100`, `trang_thai_coc = 'da_hoan_tien'`, `so_tien_hoan = so_tien_coc`.
     - If $6\text{h} \le \Delta t \le 24\text{h}$ -> `phan_tram_hoan_tien = 50`, `trang_thai_coc = 'hoan_tien_mot_phan'`, `so_tien_hoan = so_tien_coc * 0.5`.
     - If $\Delta t < 6\text{h}$ -> `phan_tram_hoan_tien = 0`, `trang_thai_coc = 'that_bai'`, `so_tien_hoan = 0`.
     - A structured refund receipt must be generated for auditing.

2. **Concurrency Control Chain**:
   - *Premise*: Booking collisions happen when two users browse the table map simultaneously and choose the same table and time slot.
   - *Observation*: Redis key is `giu-ban:{ban_id}:{ngay}:{gio}`. `cache.add()` (or Redis `SET NX EX 600`) returns false if key exists.
   - *Deduction*: Phase 1 must return HTTP 409 Conflict with structured JSON when `cache.add` fails, preventing the second user from advancing.
   - *Premise*: Redis keys can expire while a user is typing credit card details, or two requests might race before Redis write.
   - *Deduction*: Phase 2 inside `DatBanViewSet.create()` must execute inside `@transaction.atomic`, lock rows with `select_for_update()`, verify `cache.get(khoa_redis) == id_giu_ban`, ensure no active `DatBan` rows exist, and then delete the Redis hold key once the DB record is persisted.

3. **Realtime FSM & Chat Chain**:
   - *Premise*: Order lifecycle must follow a strict Finite State Machine without invalid backward transitions.
   - *Observation*: `trang_thai_don_hang` has 6 states: `cho_tiep_nhan`, `da_xac_nhan`, `dang_che_bien`, `san_sang`, `hoan_tat`, `da_huy`.
   - *Deduction*: `doi_trang_thai` must enforce allowed transition matrix (e.g. `cho_tiep_nhan` -> `da_xac_nhan` or `da_huy`; `san_sang` -> `hoan_tat`; terminal states `hoan_tat` and `da_huy` cannot transition further).
   - *Premise*: Realtime push must not lose data and must update client screens without page reloads.
   - *Deduction*: State change must write to `lich_su_trang_thai_don`, commit DB, and invoke `channel_layer.group_send(f"order_{ma_don_hang}", ...)`. In chat, incoming messages must be inserted into PostgreSQL `tin_nhan` before triggering `channel_layer.group_send(f"chat_{conversation_id}", ...)`.

4. **AI & PostGIS Chain**:
   - *Premise*: Food recommendation must be personalized and explainable; new users must receive popular items.
   - *Observation*: `tuong_tac_mon_an` stores user actions with weights. `danh_muc`, `nguyen_lieu`, `the_mon_an`, `do_cay` provide textual features.
   - *Deduction*: TF-IDF vectorizes item corpus; user preference vector aggregates interaction history with weights (`xem`=1, `yeu_thich`=2, `them_gio_hang`=3, `dat_mon`=4, `danh_gia`=5). Cosine similarity ranks top items. Cold-start fallback ranks by `so_luot_danh_gia` and `diem_danh_gia`. Explainability generator parses matching dominant features (e.g. "Gợi ý vì bạn thích món cay/lẩu").
   - *Premise*: PostGIS stores branch coordinates as `geography(Point, 4326)`.
   - *Deduction*: Finding nearest branch uses `ST_Distance(toa_do_gis, ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography)` with GiST index acceleration.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Payments | VNPay Sandbox Payment Creation | Tạo URL thanh toán VNPay Sandbox có chữ ký HMAC-SHA512 | `dat_ban_id` hoặc `don_hang_id`, `so_tien`, `ip_addr` | `payment_url`, `txn_ref`, `expired_at` | HTTP 400 nếu đơn không tồn tại hoặc đã thanh toán | `ORIGINAL_REQUEST.md`, VNPay 2.1.0 Spec |
| 2 | Payments | VNPay Return Callback | Xử lý redirect khách hàng sau thanh toán, kiểm tra chữ ký | Query params từ VNPay (`vnp_ResponseCode`, `vnp_SecureHash`, ...) | Redirect frontend kèm trạng thái thành công/thất bại | Báo lỗi nếu sai hash hoặc mã phản hồi != "00" | VNPay Spec, `moc-frontend` return URL |
| 3 | Payments | VNPay IPN Webhook | Callback ngầm server-to-server cập nhật trạng thái đơn/cọc | Query params từ VNPay server | JSON `{"RspCode":"00","Message":"Confirm Success"}` | `RspCode 97` (Sai hash), `01` (Không tìm thấy đơn), `04` (Sai số tiền) | VNPay Sandbox Webhook Spec |
| 4 | Reservations | Deposit Refund Evaluation | Tính tỷ lệ hoàn cọc và tiền hoàn theo thời gian hủy so với giờ hẹn | `dat_ban_id`, `ly_do_huy`, thời điểm hủy | `phan_tram_hoan_tien`, `so_tien_hoan`, `trang_thai_coc` | HTTP 403 nếu không có quyền hủy, 400 nếu bàn đã hoàn tất | `moc_schema_tieng_viet.sql`, Đề cương luận văn |
| 5 | Reservations | Refund Receipt Generation | Sinh phiếu hoàn tiền có mã định danh để đối soát và gửi cho khách | Dữ liệu hủy cọc từ Feature 4 | JSON phiếu hoàn tiền chi tiết | Không sinh phiếu nếu tiền cọc = 0 hoặc cọc thất bại | `ORIGINAL_REQUEST.md`, `chinh_sach_dat_coc` |
| 6 | Concurrency | Redis Table Hold (Phase 1) | Giữ bàn tạm thời trong 10 phút bằng Redis `SET NX EX 600` | `ban_an_id`, `ngay_dat`, `gio_bat_dau`, `so_luong_khach` | `id_giu_ban`, `thoi_han_giu_cho` (ISO string) | HTTP 409 Conflict nếu bàn đang bị giữ hoặc đã đặt | Đề cương luận văn ¶26, `reservations/views.py` |
| 7 | Concurrency | DB Pessimistic Lock (Phase 2) | Chốt đặt bàn trong Database Transaction bằng `select_for_update()` | `id_giu_ban`, payload đặt bàn | Bản ghi `DatBan` mới với trạng thái xác nhận | HTTP 400 nếu phiên giữ bàn hết hạn hoặc xung đột DB | `reservations/services.py`, Đề cương ¶38 |
| 8 | Inventory | Material Inventory Deduction | Khấu trừ tồn kho nguyên liệu theo định mức (BOM) bằng khóa bi quan | `don_hang_id` khi đơn được xác nhận / tạo | Cập nhật `ton_kho_hien_tai`, ghi `lich_su_xuat_nhap_kho` | HTTP 400 nếu nguyên liệu không đủ tồn kho | `moc_schema_tieng_viet.sql`, `foods/models.py` |
| 9 | Realtime | Order FSM Lifecycle Transition | Quản lý chuyển đổi trạng thái đơn hàng theo FSM hữu hạn | `don_hang_id`, `trang_thai_moi`, `doi_boi`, `ghi_chu` | Bản ghi đơn hàng cập nhật + bản ghi audit log | HTTP 400 nếu vi phạm ma trận chuyển đổi FSM | `moc_schema_tieng_viet.sql`, `orders/models.py` |
| 10 | Realtime | Order WebSocket Broadcast | Phát sự kiện thay đổi trạng thái đơn hàng tới màn hình khách hàng | Sự kiện đổi trạng thái từ Feature 9 | WebSocket JSON message tới group `order_{ma_don_hang}` | Bỏ qua nếu socket không kết nối, lưu log DB | `ORIGINAL_REQUEST.md`, Channels Spec |
| 11 | Realtime | 2-Way Staff-Customer Chat | Kênh chat trực tiếp 2 chiều giữa khách và nhân viên nhà hàng | WebSocket connection tới `/ws/chat/{conversation_id}/` | Realtime messages qua Redis Channel Layer | Đóng kết nối nếu token JWT không hợp lệ hoặc sai phòng | `prompt web nhà hàng .txt`, Channels Spec |
| 12 | Realtime | Chat Message Persistence | Lưu trữ tin nhắn vào PostgreSQL trước khi broadcast qua WebSocket | Incoming message payload (`noi_dung`, `loai_tin_nhan`) | Bản ghi `tin_nhan` đã commit DB + timestamp | Báo lỗi gửi tin nếu DB lưu thất bại, không broadcast | `ORIGINAL_REQUEST.md`, `chat/models.py` |
| 13 | AI | Content-Based Recommendation | Gợi ý món ăn dùng TF-IDF và Cosine Similarity theo khẩu vị user | `nguoi_dung_id`, `gioi_han` (default=6) | Danh sách Top-N món ăn kèm điểm tương đồng | Chuyển sang Cold-Start nếu user chưa có tương tác | `recommendations/services.py`, Đề cương ¶36 |
| 14 | AI | Interaction Weight Tracking | Thu thập tương tác người dùng theo trọng số (xem, thích, giỏ, đặt, đánh giá) | `nguoi_dung_id`, `mon_an_id`, `loai_tuong_tac` | Bản ghi `tuong_tac_mon_an` được lưu | Bỏ qua hoặc báo lỗi 401 nếu chưa đăng nhập | `moc_schema_tieng_viet.sql`, `recommendations/models.py` |
| 15 | AI | Cold-Start Popularity Fallback | Gợi ý theo độ phổ biến cho khách hàng mới chưa có dữ liệu tương tác | `nguoi_dung_id` (mới hoặc ẩn danh), `gioi_han` | Danh sách món ăn có lượt đánh giá & điểm cao nhất | Trả về danh sách món nổi bật nếu database chưa có đánh giá | `prompt web nhà hàng .txt` §32, Đề cương ¶36 |
| 16 | AI | Explainable Recommendation | Sinh lý do gợi ý dễ hiểu dựa trên đặc trưng khớp mạnh nhất (cay, lẩu, ...) | Vector khẩu vị user & vector đặc trưng món ăn | Chuỗi giải thích: "Gợi ý vì bạn thích món cay..." | Trả về chuỗi mặc định nếu không có từ khóa nổi trội | `ORIGINAL_REQUEST.md` R4, `prompt` §29 |
| 17 | GIS | Nearest Branch Spatial Query | Truy vấn chi nhánh gần nhất bằng PostGIS `ST_Distance` và GiST index | `lat`, `lng` (tọa độ GPS người dùng) | Thông tin chi nhánh + `distance_km` | HTTP 400 nếu thiếu tọa độ; HTTP 404 nếu không có chi nhánh mở | `moc_schema_tieng_viet.sql`, `branches/models.py` |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | VNPay IPN | Callback gửi `vnp_Amount` lệch so với số tiền trong DB (ví dụ hacker sửa request) | Hệ thống phát hiện mismatch, ghi log cảnh báo bảo mật, trả về `{"RspCode":"04","Message":"Invalid amount"}` và KHÔNG cập nhật trạng thái đơn |
| 2 | VNPay IPN | VNPay gửi IPN lặp lại cho đơn đã xử lý thành công (`trang_thai == 'thanh_cong'`) | Hệ thống kiểm tra idempotency, trả về `{"RspCode":"02","Message":"Order already confirmed"}`, không tạo giao dịch trùng lặp |
| 3 | VNPay IPN | Chữ ký `vnp_SecureHash` trong query không khớp với hash tính toán tại backend | Hệ thống từ chối request, trả về `{"RspCode":"97","Message":"Invalid Checksum"}` |
| 4 | Deposit Refund | Khách hủy đặt bàn cách giờ hẹn 24 giờ 01 phút ($\Delta t = 24.016\text{h} > 24\text{h}$) | Áp dụng mốc `truoc_24h`: Hoàn 100% tiền cọc, chuyển trạng thái cọc sang `da_hoan_tien`, sinh phiếu hoàn tiền đủ 100% |
| 5 | Deposit Refund | Khách hủy đặt bàn cách giờ hẹn đúng 6 giờ 00 phút ($\Delta t = 6.0\text{h}$) | Áp dụng mốc `tu_6_den_24h`: Hoàn 50% tiền cọc, chuyển trạng thái cọc sang `hoan_tien_mot_phan`, giữ lại 50% phí hủy |
| 6 | Deposit Refund | Khách hủy đặt bàn cách giờ hẹn 5 giờ 59 phút ($\Delta t = 5.98\text{h} < 6\text{h}$) | Áp dụng mốc `trong_6h`: Hoàn 0% tiền cọc, chuyển trạng thái cọc sang `that_bai` (tiền cọc bị thu giữ do hủy muộn) |
| 7 | Deposit Refund | Khách không đến nhà hàng sau khung giờ đặt mà không báo hủy (`khach_khong_den`) | Nhân viên chuyển trạng thái sang `khach_khong_den`: Hoàn 0% tiền cọc, giải phóng bàn ăn về trạng thái `trong` |
| 8 | Concurrency Phase 1 | Hai khách hàng A và B cùng bấm giữ Bàn 5 vào lúc 18:00 cùng một mili-giây | Redis thực thi nguyên tử lệnh `SET NX`: Khách A nhận HTTP 200 kèm `id_giu_ban`, khách B nhận HTTP 409 Conflict với thông báo bàn đã được giữ |
| 9 | Concurrency Phase 1 | Khách giữ bàn nhưng đóng trình duyệt hoặc không thanh toán cọc sau 10 phút | Khóa Redis tự động bị xóa (TTL 600s hết hạn), bàn ăn trở lại trạng thái khả dụng cho khách hàng tiếp theo |
| 10 | Concurrency Phase 2 | Khách giữ bàn qua 10 phút, token Redis hết hạn, sau đó mới gửi request tạo đơn đặt bàn | Backend kiểm tra `cache.get(khoa_redis) != id_giu_ban`, ném lỗi validation báo phiên giữ bàn đã hết hạn, không tạo đơn |
| 11 | Concurrency Phase 2 | User A đang trong giao dịch chốt bàn, User B cố gắng chốt cùng bàn trong DB | `select_for_update()` block transaction của User B cho đến khi transaction của User A hoàn tất; sau đó User B thấy đơn đã tồn tại và bị từ chối |
| 12 | Order FSM | Nhân viên cố tình chuyển trạng thái đơn hàng từ `san_sang` quay ngược về `cho_tiep_nhan` | Hệ thống kiểm tra ma trận chuyển đổi FSM, ném lỗi HTTP 400 `InvalidStateTransitionError`, giữ nguyên trạng thái cũ |
| 13 | Order FSM | Khách hàng bấm hủy đơn khi đơn hàng đã chuyển sang trạng thái `dang_che_bien` | Hệ thống từ chối yêu cầu hủy tự động từ khách hàng (chỉ nhân viên/bếp mới có quyền hủy khi đang chế biến do đã tốn nguyên liệu) |
| 14 | Realtime Chat | Khách hàng ngắt kết nối mạng ngay khi gửi tin nhắn | Tin nhắn đã được lưu thành công vào PostgreSQL trước khi broadcast; khi khách reconnect, tin nhắn vẫn hiển thị đầy đủ từ lịch sử |
| 15 | AI Recommendation | Khách hàng mới vừa tạo tài khoản, chưa có bất kỳ lượt xem, thích hay đặt món nào | Hệ thống tự động kích hoạt Popularity Fallback: trả về các món có số lượt đánh giá cao nhất và gắn nhãn "Phổ biến hôm nay" |
| 16 | AI Recommendation | Khách hàng chỉ tương tác với các món ăn hiện đã hết hàng (`con_hang == False`) | Pipeline lọc bỏ tất cả món hết hàng khỏi tập ứng viên trước khi xếp hạng Cosine, đảm bảo không bao giờ gợi ý món khách không thể gọi |
| 17 | PostGIS GIS | Người dùng từ chối cấp quyền Geolocation hoặc thiết bị không có GPS | Frontend hiển thị cảnh báo thân thiện và cho phép người dùng chọn chi nhánh thủ công từ danh sách chi nhánh mặc định |

---

## 5. Detailed Technical Specifications

### Part 1: VNPay Sandbox Payment & Refund Flow

#### 1.1 VNPay Sandbox Architecture & Configuration
- **Sandbox URL**: `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html`
- **Environment Parameters**:
  - `VNPAY_TMN_CODE`: Mã website của merchant tại hệ thống VNPay (8 ký tự).
  - `VNPAY_HASH_SECRET`: Chuỗi bí mật dùng để tạo chữ ký bảo mật HMAC-SHA512.
  - `VNPAY_URL`: `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html`
  - `VNPAY_RETURN_URL`: `http://localhost:5173/payment/vnpay-return` (hoặc cấu hình tương ứng trong môi trường triển khai).

#### 1.2 Query Parameters & Checksum Algorithm (HMAC-SHA512)
Khi khách hàng tiến hành thanh toán cọc hoặc thanh toán đơn hàng:
1. Tập hợp các tham số bắt buộc:
   - `vnp_Version`: `"2.1.0"`
   - `vnp_Command`: `"pay"`
   - `vnp_TmnCode`: Giá trị cấu hình `VNPAY_TMN_CODE`
   - `vnp_Amount`: `str(int(so_tien * 100))` (số nguyên, VNĐ nhân với 100)
   - `vnp_CreateDate`: Định dạng thời gian GMT+7 `datetime.now().strftime("%Y%m%d%H%M%S")`
   - `vnp_CurrCode`: `"VND"`
   - `vnp_IpAddr`: IP của client (lấy từ header `REMOTE_ADDR` hoặc `X-Forwarded-For`)
   - `vnp_Locale`: `"vn"`
   - `vnp_OrderInfo`: Nội dung thanh toán (ví dụ: `"Thanh toan tien coc dat ban DB12345678"`)
   - `vnp_OrderType`: `"other"` hoặc `"billpayment"`
   - `vnp_ReturnUrl`: Giá trị cấu hình `VNPAY_RETURN_URL`
   - `vnp_TxnRef`: Mã tham chiếu giao dịch duy nhất: `f"TT{thanh_toan_id}_{int(time.time())}"`
2. Thuật toán tạo Checksum HMAC-SHA512:
   - Sắp xếp tất cả các tham số theo thứ tự alphabet tăng dần của tên khóa (ASCII order).
   - Nối chuỗi dữ liệu băm:
     ```python
     import urllib.parse
     import hmac
     import hashlib

     sorted_params = sorted(params.items())
     hash_data = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params if v is not None and v != ""])
     secure_hash = hmac.new(
         settings.VNPAY_HASH_SECRET.encode("utf-8"),
         hash_data.encode("utf-8"),
         hashlib.sha512
     ).hexdigest()
     ```
   - Ghép thêm `vnp_SecureHash={secure_hash}` vào query string để tạo URL chuyển hướng hoàn chỉnh.

#### 1.3 Return URL Validation (`/api/payments/vnpay/return/`)
- Trình duyệt khách hàng được chuyển hướng về kèm các query parameters từ VNPay.
- Backend lấy toàn bộ tham số, tách riêng `vnp_SecureHash` và `vnp_SecureHashType`.
- Tính toán lại checksum trên các tham số còn lại theo cùng thuật toán mục 1.2.
- Kiểm tra tính hợp lệ:
  - Nếu `calculated_hash != vnp_SecureHash`: Giao dịch không hợp lệ (nghi vấn giả mạo).
  - Nếu mã phản hồi `vnp_ResponseCode == "00"`: Giao dịch thành công. Trả về thông tin cho frontend hiển thị màn hình chúc mừng.

#### 1.4 IPN Webhook Verification (`GET /api/payments/vnpay/ipn/`)
Hệ thống VNPay gọi trực tiếp ngầm đến backend. Quy trình kiểm tra và phản hồi tuân thủ nghiêm ngặt chuẩn VNPay:
```python
def handle_vnpay_ipn(request):
    input_data = request.GET.dict()
    vnp_secure_hash = input_data.pop("vnp_SecureHash", None)
    input_data.pop("vnp_SecureHashType", None)

    # 1. Kiểm tra checksum
    sorted_params = sorted(input_data.items())
    hash_data = "&".join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params if v])
    expected_hash = hmac.new(settings.VNPAY_HASH_SECRET.encode('utf-8'), hash_data.encode('utf-8'), hashlib.sha512).hexdigest()

    if vnp_secure_hash != expected_hash:
        return JsonResponse({"RspCode": "97", "Message": "Invalid Checksum"})

    txn_ref = input_data.get("vnp_TxnRef")
    amount = int(input_data.get("vnp_Amount", 0))
    response_code = input_data.get("vnp_ResponseCode")

    try:
        thanh_toan = ThanhToan.objects.select_for_update().get(ma_giao_dich=txn_ref)
    except ThanhToan.DoesNotExist:
        return JsonResponse({"RspCode": "01", "Message": "Order not found"})

    # 2. Kiểm tra số tiền
    if int(thanh_toan.so_tien * 100) != amount:
        return JsonResponse({"RspCode": "04", "Message": "Invalid amount"})

    # 3. Kiểm tra trạng thái giao dịch
    if thanh_toan.trang_thai != ThanhToan.TrangThai.CHO_XU_LY:
        return JsonResponse({"RspCode": "02", "Message": "Order already confirmed"})

    # 4. Cập nhật kết quả giao dịch
    if response_code == "00":
        thanh_toan.trang_thai = ThanhToan.TrangThai.THANH_CONG
        thanh_toan.thanh_toan_luc = timezone.now()
        thanh_toan.save()

        if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
            dat_ban = thanh_toan.dat_ban
            dat_ban.trang_thai_coc = DatBan.TrangThaiCoc.THANH_CONG
            dat_ban.trang_thai = DatBan.TrangThai.DA_XAC_NHAN
            dat_ban.thanh_toan_coc_luc = timezone.now()
            dat_ban.save()
            # Khóa trạng thái bàn
            dat_ban.ban_an.trang_thai = BanAn.TrangThai.DA_DAT
            dat_ban.ban_an.save()
        elif thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.DON_HANG and thanh_toan.don_hang:
            don_hang = thanh_toan.don_hang
            don_hang.trang_thai = DonHang.TrangThai.DA_XAC_NHAN
            don_hang.save()
    else:
        thanh_toan.trang_thai = ThanhToan.TrangThai.THAT_BAI
        thanh_toan.save()
        if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
            dat_ban = thanh_toan.dat_ban
            dat_ban.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
            dat_ban.trang_thai = DatBan.TrangThai.DA_HUY
            dat_ban.save()

    return JsonResponse({"RspCode": "00", "Message": "Confirm Success"})
```

#### 1.5 Deposit Refund Policy & Receipt Generation
1. **Công thức tính mốc thời gian**:
   $$\Delta t = \frac{\text{Timestamp}(ngay\_dat, gio\_bat\_dau) - \text{Timestamp}(huy\_luc)}{3600} \quad (\text{đơn vị: giờ})$$
2. **Quy tắc tính tỷ lệ hoàn**:
   - Nếu $\Delta t > 24$: Mốc `truoc_24h` $\rightarrow$ Tỷ lệ hoàn $100\%$, số tiền hoàn = $1.0 \times \text{so\_tien\_coc}$, trạng thái cọc = `da_hoan_tien`.
   - Nếu $6 \le \Delta t \le 24$: Mốc `tu_6_den_24h` $\rightarrow$ Tỷ lệ hoàn $50\%$, số tiền hoàn = $0.5 \times \text{so\_tien\_coc}$, tiền phạt = $0.5 \times \text{so\_tien\_coc}$, trạng thái cọc = `hoan_tien_mot_phan`.
   - Nếu $\Delta t < 6$: Mốc `trong_6h` $\rightarrow$ Tỷ lệ hoàn $0\%$, số tiền hoàn = $0$, trạng thái cọc = `that_bai` (tiền cọc khấu trừ toàn bộ cho nhà hàng).
   - Nếu khách không đến: Mốc `khach_khong_den` $\rightarrow$ Tỷ lệ hoàn $0\%$.
3. **Cấu trúc dữ liệu Phiếu hoàn tiền (`PhieuHoanTien`)**:
   ```json
   {
     "ma_phieu_hoan": "RF-DB482910-20261014",
     "ma_dat_ban": "DB482910",
     "khach_hang": {
       "ho_ten": "Nguyễn Văn Vũ",
       "so_dien_thoai": "0987654321"
     },
     "chi_nhanh": {
       "id": 1,
       "ten": "Nhà hàng Mộc - Chi nhánh Tân Bình"
     },
     "thoi_gian_dat_ban": "2026-10-20T19:00:00+07:00",
     "thoi_gian_yeu_cau_huy": "2026-10-18T10:00:00+07:00",
     "so_gio_truoc_gio_hen": 57.0,
     "chinh_sach_ap_dung": {
       "moc": "truoc_24h",
       "ty_le_hoan_phan_tram": 100.0
     },
     "tai_chinh": {
       "so_tien_coc_goc": 200000,
       "so_tien_hoan_tra": 200000,
       "so_tien_khau_tru_phat": 0
     },
     "ly_do_huy": "Thay đổi kế hoạch công tác",
     "phuong_thuc_hoan": "vnpay_refund",
     "trang_thai": "da_hoan_tien",
     "tao_luc": "2026-10-18T10:00:02+07:00"
   }
   ```

---

### Part 2: Concurrency Control (Redis Hold + DB Pessimistic Lock)

#### 2.1 Phase 1: Redis Temporary Hold (10-minute TTL)
- **Mục tiêu**: Ngăn chặn 2 người dùng chọn trùng bàn và khung giờ ngay trên giao diện sơ đồ bàn mà không cần khóa dòng dữ liệu database quá lâu.
- **Cấu trúc Redis Key**: `giu-ban:{ban_an_id}:{ngay_dat}:{gio_bat_dau}`
  *(Ví dụ: `giu-ban:12:2026-10-20:18:00:00`)*
- **Giá trị Value**: Token UUID ngẫu nhiên `HOLD_{uuid.uuid4().hex}`
- **Lệnh thực thi**: `SET key hold_token NX EX 600` (TTL = 600 giây = 10 phút)
- **Mã lỗi trả về khi xung đột (HTTP 409 Conflict)**:
  ```json
  {
    "status": "conflict",
    "error_code": "TABLE_CURRENTLY_HELD",
    "message": "Bàn ăn này đang được khách hàng khác giữ chỗ trong 10 phút. Vui lòng chọn bàn khác hoặc thử lại sau.",
    "ban_an_id": 12,
    "ngay_dat": "2026-10-20",
    "gio_bat_dau": "18:00:00",
    "retry_after_seconds": 600
  }
  ```

#### 2.2 Phase 2: Database Pessimistic Locking (`select_for_update`)
- **Mục tiêu**: Đảm bảo tính nhất quán tuyệt đối (ACID) khi chốt đơn đặt bàn trong database.
- **Triển khai bên trong transaction**:
  ```python
  @transaction.atomic
  def tao_dat_ban(*, nguoi_dung, du_lieu):
      ban_id = du_lieu["ban_an_id"]
      ngay_dat = du_lieu["ngay_dat"]
      gio_bat_dau = du_lieu["gio_bat_dau"]
      id_giu_ban = du_lieu.get("id_giu_ban")

      # 1. Khóa bi quan dòng bản ghi bàn ăn
      ban = BanAn.objects.select_for_update().get(id=ban_id)

      # 2. Khóa và kiểm tra các đơn đặt bàn trùng khung giờ
      tranh_chap = DatBan.objects.select_for_update().filter(
          ban_an=ban,
          ngay_dat=ngay_dat,
          gio_bat_dau=gio_bat_dau,
          trang_thai__in=[
              DatBan.TrangThai.CHO_THANH_TOAN,
              DatBan.TrangThai.DA_XAC_NHAN,
              DatBan.TrangThai.KHACH_DA_DEN
          ]
      )
      if tranh_chap.exists():
          raise ConflictError("Bàn đã có người đặt và xác nhận trong khung giờ này.")

      # 3. Kiểm tra token giữ chỗ Redis
      khoa_redis = f"giu-ban:{ban.id}:{ngay_dat}:{gio_bat_dau}"
      token_hien_tai = cache.get(khoa_redis)
      if not token_hien_tai or token_hien_tai != id_giu_ban:
          raise ValidationError("Phiên giữ bàn đã hết hạn (quá 10 phút) hoặc không hợp lệ.")

      # 4. Tạo bản ghi DatBan
      dat_ban = DatBan.objects.create(...)

      # 5. Giải phóng khóa Redis vì dữ liệu đã được bảo vệ trong DB
      cache.delete(khoa_redis)
      return dat_ban
  ```

#### 2.3 Khóa bi quan kiểm soát trừ kho nguyên liệu (BOM)
- Khi đơn hàng được xác nhận hoặc tạo:
  ```python
  with transaction.atomic():
      for item in items:
          mon_an = MonAn.objects.select_for_update().get(id=item.mon_an_id)
          if mon_an.quan_ly_kho:
              dinh_muc = DinhMucNguyenLieu.objects.filter(mon_an=mon_an).select_related('nguyen_lieu')
              for dm in dinh_muc:
                  nl = NguyenLieu.objects.select_for_update().get(id=dm.nguyen_lieu_id)
                  so_luong_can = dm.so_luong_can * item.so_luong
                  if nl.ton_kho_hien_tai < so_luong_can:
                      raise ValidationError(f"Nguyên liệu {nl.ten} không đủ đáp ứng (cần {so_luong_can} {nl.don_vi}, còn {nl.ton_kho_hien_tai} {nl.don_vi}).")
                  nl.ton_kho_hien_tai -= so_luong_can
                  nl.save(update_fields=['ton_kho_hien_tai', 'cap_nhat_luc'])
          elif mon_an.ton_kho_cache is not None:
              if mon_an.ton_kho_cache < item.so_luong:
                  raise ValidationError(f"Món {mon_an.ten} không đủ số lượng trong kho.")
              mon_an.ton_kho_cache -= item.so_luong
              mon_an.save(update_fields=['ton_kho_cache', 'cap_nhat_luc'])
  ```

---

### Part 3: Realtime Communication (WebSocket & FSM)

#### 3.1 Order FSM States & Transition Rules
- **Tập hợp trạng thái**:
  - `cho_tiep_nhan`: Đơn hàng mới tạo, chờ nhân viên duyệt.
  - `da_xac_nhan`: Đơn hàng được nhà hàng chấp nhận (hoặc đã thanh toán online).
  - `dang_che_bien`: Nhà bếp đang chế biến các món trong đơn.
  - `san_sang`: Món ăn chế biến xong, sẵn sàng giao cho khách hoặc shipper.
  - `hoan_tat`: Khách đã nhận món và thanh toán xong (Trạng thái kết thúc).
  - `da_huy`: Đơn hàng bị hủy (Trạng thái kết thúc).
- **Ma trận chuyển đổi trạng thái hợp lệ**:
  ```
  [cho_tiep_nhan] ───(duyệt đơn)───> [da_xac_nhan] ───(nấu ăn)───> [dang_che_bien]
        │                                  │                            │
        │ (hủy trước chế biến)             │ (hủy có lý do)             │ (sự cố)
        ▼                                  ▼                            ▼
     [da_huy] <───────────────────────── [da_huy] <────────────────── [da_huy]
                                                                        │
                                                                        │ (chế biến xong)
                                                                        ▼
                                                                   [san_sang]
                                                                     │     │
                                                   (giao thành công) │     │ (khách bùng)
                                                                     ▼     ▼
                                                                [hoan_tat] [da_huy]
  ```
- **Quy tắc bắt buộc**:
  - `hoan_tat` và `da_huy` là Terminal States: Mọi nỗ lực chuyển sang trạng thái khác đều bị từ chối bằng `ValidationError("Đơn hàng đã kết thúc, không thể thay đổi trạng thái.")`.
  - Không cho phép nhảy cóc trái quy trình (ví dụ: `cho_tiep_nhan` $\rightarrow$ `san_sang` hoặc `hoan_tat` $\rightarrow$ `dang_che_bien`).

#### 3.2 WebSocket Broadcast Sự kiện Đơn hàng
- **Channel Layer Group**:
  - Khách hàng theo dõi đơn: `order_{ma_don_hang}` (ví dụ: `order_MOC482910`).
  - Màn hình quản lý của nhân viên: `staff_orders`.
- **Cấu trúc sự kiện Broadcast**:
  ```json
  {
    "type": "order_status_update",
    "data": {
      "order_code": "MOC482910",
      "previous_status": "da_xac_nhan",
      "current_status": "dang_che_bien",
      "status_label": "Đang chế biến",
      "updated_by": "Bếp trưởng Trần Văn B",
      "note": "Bắt đầu nấu các món lẩu và nướng",
      "updated_at": "2026-10-14T10:45:00+07:00"
    }
  }
  ```

#### 3.3 2-Way Realtime Chat Architecture
- **WebSocket Endpoint**: `ws://<host>/ws/chat/<conversation_id>/`
- **Xác thực**: Token JWT truyền qua subprotocol hoặc query param `?token=<access_token>`.
- **Nguyên tắc "Lưu DB trước khi Broadcast" (Zero Data Loss)**:
  1. Khi nhận tin nhắn từ WebSocket client:
     ```python
     async def receive_json(self, content):
         noi_dung = content.get("content", "").strip()
         if not noi_dung:
             return
         
         # 1. Lưu tin nhắn vào PostgreSQL qua database_sync_to_async
         tin_nhan = await self.save_message_to_db(
             conversation_id=self.conversation_id,
             sender=self.scope["user"],
             content=noi_dung,
             msg_type=content.get("message_type", "van_ban")
         )
         
         # 2. Sau khi DB commit thành công, phát tới Channel Group
         await self.channel_layer.group_send(
             self.room_group_name,
             {
                 "type": "chat_message_broadcast",
                 "message": {
                     "id": tin_nhan.id,
                     "conversation_id": self.conversation_id,
                     "sender_id": self.scope["user"].id,
                     "sender_name": self.scope["user"].ho_ten,
                     "is_staff": self.scope["user"].is_staff,
                     "content": tin_nhan.noi_dung,
                     "created_at": tin_nhan.tao_luc.isoformat(),
                     "is_read": False
                 }
             }
         )
     ```

---

### Part 4: AI Recommendation & PostGIS GIS

#### 4.1 Content-Based Filtering via TF-IDF & Cosine Similarity
1. **Trích xuất đặc trưng món ăn**:
   Mỗi món ăn $m$ được biểu diễn bằng văn bản tổng hợp:
   $$D_m = \text{ten} \circ \text{mo\_ta\_ngan} \circ \text{danh\_muc.ten} \circ \left(\bigcup \text{nguyen\_lieu.ten}\right) \circ \left(\bigcup \text{the\_mon\_an.ten}\right) \circ \text{nhan\_cay} \circ \text{nhan\_chay}$$
2. **Vector hóa TF-IDF**:
   - Tần suất từ: $\text{TF}(t, D_m) = 1 + \ln(f_{t, D_m})$ (với $f_{t, D_m} > 0$).
   - Nghịch đảo tần suất văn bản: $\text{IDF}(t, \mathcal{M}) = \ln\left(\frac{|\mathcal{M}| + 1}{\text{DF}(t) + 1}\right) + 1$.
   - Trọng số đặc trưng: $v_{m, t} = \text{TF}(t, D_m) \times \text{IDF}(t, \mathcal{M})$.
   - Chuẩn hóa vector độ dài đơn vị: $\hat{v}_m = \frac{\vec{v}_m}{\|\vec{v}_m\|_2}$.
3. **Hồ sơ khẩu vị người dùng (User Profile Vector)**:
   - Các tương tác của người dùng $u$ được tính với trọng số tương ứng:
     - `xem` (View): $W_{\text{xem}} = 1$
     - `yeu_thich` (Favorite): $W_{\text{yeu\_thich}} = 2$
     - `them_gio_hang` (Cart): $W_{\text{them\_gio}} = 3$
     - `dat_mon` (Order): $W_{\text{dat\_mon}} = 4$
     - `danh_gia` (Review): $W_{\text{danh\_gia}} = 5$ (với đánh giá $\ge 4\star$)
   - Vector người dùng $\vec{u}$:
     $$\vec{u} = \sum_{k \in \text{Interactions}(u)} W_k \cdot \hat{v}_{m_k}$$
     Chuẩn hóa: $\hat{u} = \frac{\vec{u}}{\|\vec{u}\|_2}$.
4. **Tính điểm tương đồng Cosine Similarity & Xếp hạng**:
   $$\text{Score}(u, m) = \hat{u} \cdot \hat{v}_m = \sum_{t} \hat{u}_t \cdot \hat{v}_{m, t} \in [0, 1]$$
   - Chỉ xét các món thỏa mãn: `con_hang == True` và `hien_thi == True`.
   - Lọc bỏ các món khách hàng vừa mới đặt gần đây để đảm bảo tính đa dạng.
   - Lấy Top-$N$ (mặc định $N=6$).

#### 4.2 Cold-Start Fallback Strategy
- Khi người dùng mới chưa có tương tác ($\|\vec{u}\|_2 = 0$) hoặc khách vãng lai:
  - Áp dụng Popularity-Based Fallback:
    $$\text{Score}_{\text{cold}}(m) = 0.6 \times \frac{\text{so\_luot\_danh\_gia}}{\max(\text{so\_luot\_danh\_gia}) + 1} + 0.4 \times \frac{\text{diem\_danh\_gia}}{5.0}$$
  - Nhãn lý do hiển thị: `"Phổ biến hôm nay"`, `"Món được yêu thích nhất"`.

#### 4.3 Explainable Recommendation Generator
Hệ thống xác định các đặc trưng đóng góp lớn nhất vào tích vô hướng $\hat{u}_t \cdot \hat{v}_{m, t}$ để sinh câu giải thích trực quan:
- Nếu từ khóa chiếm ưu thế là danh mục Lẩu: `"Gợi ý cho bạn vì bạn yêu thích các món lẩu ấm cúng"`.
- Nếu món ăn có độ cay $> 0$ và người dùng thường ăn cay: `"Phù hợp với khẩu vị thích món cay nồng của bạn"`.
- Nếu có đặc trưng nướng / hải sản: `"Được gợi ý dựa trên sở thích món nướng & hải sản tươi sống của bạn"`.
- Nếu món chay: `"Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"`.
- Mặc định: `"Phù hợp với khẩu vị và các món bạn thường chọn"`.

#### 4.4 PostGIS GIS Nearest Branch Query
- **Kiểu dữ liệu**: `geography(Point, 4326)` (Hệ tọa độ WGS 84, thứ tự PostGIS: `Point(kinh_do, vi_do)`).
- **Chỉ mục không gian**: `GiST` index trên cột `toa_do_gis`.
- **Câu truy vấn SQL tìm chi nhánh gần nhất**:
  ```sql
  SELECT 
      id, 
      ten, 
      dia_chi, 
      so_dien_thoai,
      ST_X(toa_do_gis::geometry) AS kinh_do,
      ST_Y(toa_do_gis::geometry) AS vi_do,
      ROUND(ST_Distance(toa_do_gis, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)) AS khoang_cach_met,
      ROUND((ST_Distance(toa_do_gis, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) / 1000.0)::numeric, 1) AS khoang_cach_km
  FROM chi_nhanh
  WHERE con_hoat_dong = true
  ORDER BY toa_do_gis <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
  LIMIT 1;
  ```
  *(Trong đó tham số truyền vào là `(kinh_do, vi_do)`)*.
- **Tích hợp GeoDjango**:
  Sử dụng hàm `Distance` từ `django.contrib.gis.db.models.functions`:
  ```python
  from django.contrib.gis.geos import Point
  from django.contrib.gis.db.models.functions import Distance

  user_location = Point(float(lng), float(lat), srid=4326)
  nearest_branch = ChiNhanh.objects.filter(con_hoat_dong=True).annotate(
      distance=Distance("toa_do_gis", user_location)
  ).order_by("distance").first()
  ```

---

## 6. Caveats

1. **VNPay Sandbox Merchant Credentials**: Quá trình kiểm thử sandbox yêu cầu các giá trị mẫu `vnp_TmnCode` và `vnp_HashSecret` do VNPay cung cấp. Khi chưa có thông tin credentials thực tế của khách hàng, cần sử dụng credentials test chuẩn từ cổng VNPay Sandbox (`2.1.0`).
2. **Định dạng tọa độ PostGIS**: PostGIS sử dụng thứ tự `(kinh_do, vi_do)` tức `(longitude, latitude)` trong hàm `ST_MakePoint(lng, lat)`, trong khi các API của trình duyệt hoặc Google Maps thường trả về `(lat, lng)`. Khi triển khai cần đảm bảo đảo thứ tự chính xác để tránh sai lệch địa lý.
3. **Cấu hình Redis Channel Layer**: Môi trường local cần có Redis server đang chạy (mặc định `127.0.0.1:6379`) để hỗ trợ cả bộ nhớ đệm cache giữ bàn lẫn Channel Layer của Django Channels. Nếu môi trường không có Redis, cần cấu hình In-Memory Channel Layer dự phòng cho unit test.

---

## 7. Conclusion

Hệ thống Web App Nhà hàng Mộc có kiến trúc nghiệp vụ chặt chẽ, được định nghĩa rõ ràng qua đề cương luận văn và lược đồ chuẩn tiếng Việt `moc_schema_tieng_viet.sql`. 
- Vấn đề cốt lõi của Backend hiện tại là sự không nhất quán giữa mã nguồn cũ (tiếng Anh như `Payment`, `Branch`, `Food`) và lược đồ chuẩn hóa tiếng Việt (`ThanhToan`, `ChiNhanh`, `MonAn`).
- 4 module trọng yếu (VNPay Sandbox + Hoàn cọc, Concurrency Control 2 pha, Realtime FSM & Chat Channels, AI Recommendation & PostGIS) đã được đào sâu, mô hình hóa toán học và quy chuẩn hóa giao diện API đầy đủ trong báo cáo này.
- Bản đặc tả này là kim chỉ nam trực tiếp để các subagent triển khai (Backend Engineer, Frontend Engineer) xây dựng mã nguồn chính xác, đạt chuẩn nghiệm thu 100%.

---

## 8. Verification Method

1. **Kiểm tra Model & Migration**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-backend
   source .venv/bin/activate
   python manage.py check
   python manage.py makemigrations --check
   ```
2. **Kiểm tra Concurrency Control (Redis Hold + DB Lock)**:
   - Gửi đồng thời 2 request cURL giữ cùng một bàn ăn tại cùng thời điểm:
     ```bash
     curl -X POST http://localhost:8000/api/tables/1/giu_ban/ -d '{"ngay_dat":"2026-10-20","gio_bat_dau":"18:00:00","so_luong_khach":4}' -H "Content-Type: application/json"
     ```
     Request 1 phải trả về HTTP 200 kèm `id_giu_ban`. Request 2 phải trả về HTTP 409 Conflict.
3. **Kiểm tra VNPay Checksum & IPN**:
   - Kiểm tra tính toán HMAC-SHA512 qua unit test so sánh với chuỗi hash mẫu của VNPay.
   - Giả lập request IPN tới `GET /api/payments/vnpay/ipn/` kiểm tra các mã phản hồi `00`, `01`, `04`, `97`.
4. **Kiểm tra WebSocket Chat & FSM Order**:
   - Sử dụng công cụ WebSocket client (hoặc wscat) kết nối tới `ws://localhost:8000/ws/chat/1/`. Gửi tin nhắn và xác minh bản ghi mới xuất hiện trong bảng `tin_nhan` trước khi nhận tin phản hồi.
   - Đổi trạng thái đơn hàng và kiểm tra event push tới `ws://localhost:8000/ws/orders/MOC482910/`.
5. **Kiểm tra AI Recommendation & PostGIS**:
   - Gọi `GET /api/recommendations/` với user mới: xác minh trả về top món phổ biến kèm lý do "Phổ biến hôm nay".
   - Gọi `GET /api/branches/nearest/?lat=10.7925&lng=106.6669`: xác minh kết quả trả về chi nhánh gần nhất kèm khoảng cách tính bằng mét/km.
