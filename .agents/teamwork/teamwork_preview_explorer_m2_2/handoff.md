# BÁO CÁO NGHIÊN CỨU & KIẾN TRÚC KỸ THUẬT MILESTONE 2 (TECHNICAL EXPLORER 2 HANDOFF)
**Nhiệm vụ**: VNPay Sandbox Payment Module, IPN & Return URL Callback, Dual API Route Mapping, và Tự động hóa Hoàn cọc (Refund & Cancellation Policy).  
**Agent**: Technical Explorer 2 (`teamwork_preview_explorer_m2_2`)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_2`  
**Ngày báo cáo**: 2026-10-14T08:15:00Z  

---

## 1. Observation (Các quan sát trực tiếp & Bằng chứng thực nghiệm)

### 1.1. Hiện trạng Module Payments (`moc-backend/payments/`)
1. **Model `ThanhToan` (`moc-backend/payments/models.py:6-65`)**:
   - Trường dữ liệu: `id`, `nguoi_dung`, `don_hang` (nullable, `on_delete=CASCADE`), `dat_ban` (nullable, `on_delete=CASCADE`), `loai_thanh_toan` (choices `don_hang`, `tien_coc`), `phuong_thuc` (max_length=30), `so_tien` (numeric 12,2), `ma_giao_dich` (max_length=100), `trang_thai` (choices `cho_xu_ly`, `thanh_cong`, `that_bai`, `da_hoan_tien`), `thanh_toan_luc`, `hoan_tien_luc`.
   - Ràng buộc CheckConstraint `kiem_tra_muc_tieu_thanh_toan`:
     ```python
     models.Q(loai_thanh_toan="don_hang", don_hang__isnull=False, dat_ban__isnull=True) |
     models.Q(loai_thanh_toan="tien_coc", dat_ban__isnull=False, don_hang__isnull=True)
     ```
   - Model Aliases đã được thiết lập: `Payment = ThanhToan`, `PaymentType = ThanhToan.LoaiThanhToan`, `PaymentStatus = ThanhToan.TrangThai`.
   - **Chưa có model hoặc logic cho `PhieuHoanTien`** trong `payments/models.py`.

2. **Serializer `ThanhToanSerializer` (`moc-backend/payments/serializers.py:6-37`)**:
   - Kế thừa `DualPayloadMixin`.
   - Đã hỗ trợ ánh xạ `FIELD_ALIASES` song ngữ (payment_type, method, amount, order, reservation, transaction_id).
   - Chưa có các serializer chuyên dụng cho VNPay: tạo payment URL (`VNPayCreatePaymentSerializer`), kết quả IPN (`VNPayIPNResponseSerializer`), return URL callback, và `PhieuHoanTienSerializer`.

3. **Views `ThanhToanViewSet` (`moc-backend/payments/views.py:11-45`)**:
   - Hiện chỉ có 2 action mẫu cho nhân viên: `xac_nhan_thanh_cong` và `mark_success` (dòng 23-42).
   - **Hoàn toàn chưa có** các endpoint xử lý VNPay:
     - `POST /api/payments/vnpay/create/` và `/api/thanh-toan/vnpay/create/` (hoặc `tao-phien/`).
     - `GET /api/payments/vnpay/return/` và `/api/thanh-toan/vnpay/return/`.
     - `GET /api/payments/vnpay/ipn/` và `/api/thanh-toan/vnpay/ipn/`.
   - Thiếu file service `payments/services.py` để tách biệt business logic mã hóa chữ ký, kiểm tra checksum, gọi cổng thanh toán, và tính toán hoàn tiền.

### 1.2. Hiện trạng Cấu hình Settings (`moc-backend/config/settings.py`)
- Lệnh kiểm tra hệ thống với môi trường virtualenv:
  ```bash
  /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python manage.py check
  ```
  Kết quả: `System check identified no issues (0 silenced)` (Mã thoát 0).
- Trong `config/settings.py`: **Chưa khai báo các biến môi trường VNPay Sandbox**:
  - `VNPAY_TMN_CODE`
  - `VNPAY_HASH_SECRET`
  - `VNPAY_URL`
  - `VNPAY_RETURN_URL`

### 1.3. Hiện trạng Router API Song ngữ (`moc-backend/api/urls.py`)
- Dòng 63-64:
  ```python
  router.register("payments", PaymentViewSet, basename="payment")
  router.register("thanh-toan", PaymentViewSet, basename="thanh-toan")
  ```
- Dòng 55-56:
  ```python
  router.register("reservations", DatBanViewSet, basename="reservation")
  router.register("dat-ban", DatBanViewSet, basename="dat-ban")
  ```
- Dòng 59-60:
  ```python
  router.register("orders", DonHangViewSet, basename="order")
  router.register("don-hang", DonHangViewSet, basename="don-hang")
  ```
- Cần bổ sung route action rõ ràng trên `PaymentViewSet` và `DatBanViewSet` hoặc ánh xạ đường dẫn URL trực tiếp trong `urlpatterns` để đảm bảo tương thích 100% với frontend caller (`/api/thanh-toan/vnpay/tao-phien/`) và backend contract (`/api/payments/vnpay/create/`, `/api/thanh-toan/vnpay/create/`, `/api/payments/vnpay/return/`, `/api/payments/vnpay/ipn/`, `/api/reservations/{id}/huy_dat_ban/`, `/api/dat-ban/{id}/huy_dat_ban/`).

### 1.4. Hiện trạng Nghiệp vụ Hủy Đặt bàn & Hoàn cọc (`reservations/views.py:89-98`)
- Hiện tại method `huy_dat_ban` trong `DatBanViewSet` chỉ thực hiện:
  ```python
  dat_ban.trang_thai = DatBan.TrangThai.DA_HUY
  dat_ban.huy_luc = timezone.now()
  dat_ban.ly_do_huy = request.data.get("ly_do", "")
  dat_ban.phien_ban += 1
  dat_ban.save()
  return Response(self.get_serializer(dat_ban).data)
  ```
- **Chưa thực hiện**:
  - Tính khoảng thời gian đến giờ hẹn: `delta_hours = (thoi_gian_dat - thoi_gian_huy).total_seconds() / 3600.0`.
  - Phân loại tỷ lệ hoàn tiền theo 4 mốc:
    * `delta_hours > 24.0`: hoàn 100% cọc (`phan_tram_hoan_tien = 100.0`), `trang_thai_coc = "da_hoan_tien"`.
    * `6.0 <= delta_hours <= 24.0`: hoàn 50% cọc (`phan_tram_hoan_tien = 50.0`), `trang_thai_coc = "hoan_tien_mot_phan"`.
    * `delta_hours < 6.0`: hoàn 0% cọc (`phan_tram_hoan_tien = 0.0`), `trang_thai_coc = "that_bai"`.
    * No-show (`is_no_show=True`): hoàn 0% cọc (`phan_tram_hoan_tien = 0.0`), `trang_thai_coc = "that_bai"`.
  - Cập nhật trạng thái `ThanhToan` liên kết sang `da_hoan_tien`.
  - Sinh chứng từ đối soát hoàn tiền `PhieuHoanTien` có mã định danh `RF-{ma_dat_ban}-{YYYYMMDD}` và cấu trúc tài chính chi tiết.
  - Trả về payload khớp Interface Contract 2 của `PROJECT.md`:
    `{"trang_thai": "da_huy", "phan_tram_hoan_tien": N, "so_tien_hoan": N, "phieu_hoan_tien": {...}}`.

### 1.5. Bộ kiểm thử Tham chiếu & Oracle có sẵn
1. `tests/e2e/helpers/vnpay_oracle.py`:
   - Hàm `calculate_hmac_sha512(params, hash_secret)`: Loại bỏ `vnp_SecureHash`, `vnp_SecureHashType`, loại bỏ rỗng/None, sắp xếp key theo ASCII, mã hóa URL bằng `urllib.parse.quote_plus`, băm HMAC-SHA512 trả về chuỗi hex 128 ký tự chữ thường.
   - Hàm `verify_vnpay_signature(params, secure_hash, hash_secret)`: So sánh chữ ký an toàn `hmac.compare_digest`.
   - Hàm `build_vnpay_payment_url(...)`: Tạo URL sandbox với 13 tham số chuẩn v2.1.0 (`vnp_Version=2.1.0`, `vnp_Command=pay`, `vnp_TmnCode`, `vnp_Amount` nhân 100, `vnp_CreateDate`, `vnp_CurrCode=VND`, `vnp_IpAddr`, `vnp_Locale=vn`, `vnp_OrderInfo`, `vnp_OrderType=billpayment`, `vnp_ReturnUrl`, `vnp_TxnRef`, `vnp_SecureHash`).
   - Hàm `evaluate_vnpay_ipn(...)`: Trả mã RspCode chuẩn:
     * `'00'`: Xác nhận thành công (Confirm Success).
     * `'01'`: Không tìm thấy đơn hàng / giao dịch (Order not found).
     * `'02'`: Đơn hàng đã được xác nhận trước đó (Order already confirmed - Idempotent).
     * `'04'`: Số tiền không khớp (Invalid amount).
     * `'97'`: Chữ ký không hợp lệ (Invalid Checksum).
2. `tests/e2e/helpers/refund_calculator.py`:
   - Hàm `calculate_refund(thoi_gian_dat, thoi_gian_huy, so_tien_coc, is_no_show)`
   - Hàm `generate_refund_receipt(...)` trả về đối tượng dict chứng từ hoàn cọc `PhieuHoanTien`.
3. `tests/e2e/tier1/test_t1_vnpay.py` & `tests/e2e/tier2/test_t2_vnpay.py` & `tests/e2e/tier2/test_t2_refund.py`:
   - Toàn bộ 60 tests trong `tests/e2e/runner.py` đã chạy đạt 100% pass với `./moc-backend/.venv/bin/python tests/e2e/runner.py`.

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới giải pháp)

1. **Chuẩn hóa giá trị Enum trong CSDL PostgreSQL vs Mã nguồn**:
   - Từ Quan sát 1.1 và schema CSDL (`moc_schema_tieng_viet.sql:25`):
     Cột `trang_thai` trong bảng `thanh_toan` dùng ENUM `trang_thai_thanh_toan` gồm các giá trị:
     `'cho_xu_ly'`, `'thanh_cong'`, `'that_bai'`, `'da_hoan_tien'`.
   - Trong `DISPATCH.md` có ghi chú: *"updating ThanhToan.trang_thai = 'da_thanh_toan'"*. Tuy nhiên, CSDL PostgreSQL thực tế không có giá trị enum `'da_thanh_toan'` mà giá trị chuẩn là `'thanh_cong'`. Nếu gán chuỗi `'da_thanh_toan'` vào CSDL sẽ gây lỗi ngoại lệ `DataError: invalid input value for enum`.
   - **Giải pháp suy luận**: CSDL lưu chuẩn `trang_thai = 'thanh_cong'`, đồng thời model/serializer cung cấp property alias `is_paid = (trang_thai == 'thanh_cong')` và ánh xạ đầu ra nếu client yêu cầu `'da_thanh_toan'`. Bảng `dat_ban` cập nhật `trang_thai = 'da_xac_nhan'`, `trang_thai_coc = 'thanh_cong'`, và `thanh_toan_coc_luc = now()`.

2. **Kiến trúc phân tầng chuyên trách (Service Layer Pattern)**:
   - Thay vì nhồi nhét thuật toán băm HMAC, kiểm tra chữ ký, và đối soát hoàn tiền vào trong Views, cần tổ chức:
     - `payments/services.py`:
       - `class VNPayService`: Đóng gói logic tạo URL sandbox, băm HMAC-SHA512, trích xuất IP client, kiểm tra IPN webhook (idempotency, amount, checksum), và xử lý return callback.
       - `class RefundService`: Đóng gói logic tính toán delta giờ, phân loại tỷ lệ hoàn tiền, sinh chứng từ đối soát `PhieuHoanTien`, và cập nhật bản ghi trong transaction atomic.
     - `payments/views.py`: Kế thừa `ThanhToanViewSet` với các extra action:
       - `POST vnpay/create/`: Khởi tạo phiên thanh toán và trả về payment URL.
       - `POST vnpay/tao-phien/`: Alias trực tiếp cho frontend `reservations.api.ts`.
       - `GET vnpay/return/`: Khách hàng redirect về từ VNPay.
       - `GET vnpay/ipn/`: Cổng webhook server-to-server xử lý IPN và phản hồi `{"RspCode": "...", "Message": "..."}`.
     - `reservations/views.py`: Nâng cấp method `@action huy_dat_ban` gọi `RefundService.process_cancellation_and_refund`.

3. **Hỗ trợ Song ngữ Dual API Routing và Tương thích Frontend**:
   - Frontend `moc-frontend/src/api/reservations.api.ts:113` gọi:
     `POST /api/thanh-toan/vnpay/tao-phien/` với body `{ dat_ban_id, so_tien }` và mong đợi nhận `{ duongDanThanhToan, maGiaoDich, soTien, hetHanLuc }`.
   - Backend test và tài liệu yêu cầu:
     `POST /api/payments/vnpay/create/` và `POST /api/thanh-toan/vnpay/create/` với `{ loai_thanh_toan, ma_tham_chieu_id, so_tien }`.
   - **Giải pháp suy luận**: Payload serializer `VNPayCreatePaymentSerializer` chấp nhận linh hoạt cả hai cách gọi:
     - `dat_ban_id` hoặc `reservation_id` hoặc `ma_tham_chieu_id`.
     - `don_hang_id` hoặc `order_id`.
     - Tự động suy luận `so_tien` từ `dat_ban.so_tien_coc` hoặc `don_hang.tong_tien` nếu client không gửi.
     - Kết quả trả về chứa cả hai bộ khóa tiếng Anh (`payment_url`, `txn_ref`, `amount`, `expires_at`) và tiếng Việt (`duong_dan_thanh_toan`, `ma_giao_dich`, `so_tien`, `het_han_luc`).

4. **Bảo mật & Tính toàn vẹn IPN Webhook (Corner Cases)**:
   - Các trường hợp biên đã được kiểm chứng qua `test_t2_vnpay.py`:
     1. Chữ ký sai hoặc bị sửa đổi tham số URL: Ngay lập tức trả mã `97` ("Invalid Checksum"), không chạm vào CSDL.
     2. Giao dịch không tồn tại: Trả mã `01` ("Order not found").
     3. Khách hàng gian lận số tiền (ví dụ gửi 10.000 thay vì 200.000): Trả mã `04` ("Invalid amount").
     4. Gọi IPN lặp lại khi giao dịch đã thành công (Idempotency): Trả mã `02` ("Order already confirmed") và giữ nguyên trạng thái cũ, không sinh log trùng lặp.
     5. Tiếng Việt có dấu trong `vnp_OrderInfo`: Phải dùng `urllib.parse.quote_plus` đồng nhất khi tính HMAC và khi ghép query string để không bị sai lệch chữ ký.

---

## 3. Caveats (Các giả định & Lưu ý biên)

1. **Chế độ Sandbox VNPay**:
   - VNPay Sandbox không gọi IPN thật nếu server chạy `localhost`. Do đó, endpoint `GET /api/payments/vnpay/ipn/` phục vụ cho cả webhook giả lập (từ test suite / cURL / Postman) và webhook thật từ VNPay cổng thanh toán khi triển khai môi trường staging/production có public IP hoặc tunneling (ngrok/Cloudflare Tunnel).
2. **Giá trị múi giờ khi tính giờ hủy đặt bàn**:
   - `ngay_dat` và `gio_bat_dau` lưu trữ theo giờ địa phương (Việt Nam UTC+7). Khi ghép thành `datetime`, cần đảm bảo tính toán `total_seconds()` với `timezone.now()` cùng hệ quy chiếu (timezone-aware) để tránh sai số giờ dẫn đến nhảy sai tỷ lệ hoàn cọc (100% vs 50% vs 0%).
3. **Mốc thời gian đúng 24.0h**:
   - Theo chuẩn kiểm thử `test_t2_refund_02_cancellation_exactly_24h_50_percent`, tại mốc thời gian **chính xác 24.0 giờ**, tỷ lệ hoàn tiền là **50%** (thuộc khoảng `6.0 <= delta_hours <= 24.0`), chỉ khi `delta_hours > 24.0` (ví dụ 24 giờ 1 phút hoặc 25 giờ) mới được tính là 100%.

---

## 4. Conclusion (Kiến trúc & Thiết kế Kỹ thuật Chi tiết)

Toàn bộ giải pháp bao gồm 4 thành phần cụ thể sau:

### 4.1. Cấu hình Settings (`moc-backend/config/settings.py`)
Bổ sung cấu hình VNPay Sandbox vào cuối file:
```python
# ==============================================================================
# VNPay Sandbox Payment Gateway Settings
# ==============================================================================
VNPAY_TMN_CODE = env("VNPAY_TMN_CODE", default="MOCREST1")
VNPAY_HASH_SECRET = env("VNPAY_HASH_SECRET", default="VNPAYSECRETKEY2026MOCRESTAURANT")
VNPAY_URL = env("VNPAY_URL", default="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
VNPAY_RETURN_URL = env(
    "VNPAY_RETURN_URL", default="http://localhost:5173/payment/vnpay-return"
)
```

### 4.2. Lớp Dịch vụ `payments/services.py`
Tạo file mới `/Users/VuVan/Documents/DO-AN/moc-backend/payments/services.py`:
```python
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import ThanhToan
from reservations.models import DatBan
from orders.models import DonHang


class VNPayService:
    @staticmethod
    def get_client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "127.0.0.1")

    @staticmethod
    def calculate_hmac_sha512(params: Dict[str, Any], hash_secret: str) -> str:
        clean_params = {}
        for k, v in params.items():
            if k in ("vnp_SecureHash", "vnp_SecureHashType"):
                continue
            if v is not None and str(v) != "":
                clean_params[k] = str(v)

        sorted_items = sorted(clean_params.items())
        hash_data = "&".join(
            f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items
        )
        return hmac.new(
            hash_secret.encode("utf-8"),
            hash_data.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()

    @staticmethod
    def verify_signature(params: Dict[str, Any], secure_hash: str, hash_secret: str) -> bool:
        if not secure_hash:
            return False
        expected_hash = VNPayService.calculate_hmac_sha512(params, hash_secret)
        return hmac.compare_digest(expected_hash.lower(), secure_hash.lower())

    @classmethod
    def create_payment_url(
        cls,
        *,
        thanh_toan: ThanhToan,
        ip_addr: str = "127.0.0.1",
        order_info: Optional[str] = None,
        locale: str = "vn",
    ) -> Tuple[str, Dict[str, Any]]:
        tmn_code = getattr(settings, "VNPAY_TMN_CODE", "MOCREST1")
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        base_url = getattr(settings, "VNPAY_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
        return_url = getattr(settings, "VNPAY_RETURN_URL", "http://localhost:5173/payment/vnpay-return")

        now = timezone.now()
        create_date = now.strftime("%Y%m%d%H%M%S")
        amount_vnd = int(Decimal(thanh_toan.so_tien) * 100)

        if not thanh_toan.ma_giao_dich:
            thanh_toan.ma_giao_dich = f"TT{thanh_toan.id}_{int(now.timestamp())}"
            thanh_toan.save(update_fields=["ma_giao_dich", "cap_nhat_luc"])

        if not order_info:
            if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                order_info = f"Thanh toan dat coc ban {thanh_toan.dat_ban.ma_dat_ban}"
            elif thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.DON_HANG and thanh_toan.don_hang:
                order_info = f"Thanh toan don hang {thanh_toan.don_hang.ma_don_hang}"
            else:
                order_info = f"Thanh toan giao dich {thanh_toan.ma_giao_dich}"

        params: Dict[str, Any] = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": tmn_code,
            "vnp_Amount": str(amount_vnd),
            "vnp_CreateDate": create_date,
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ip_addr,
            "vnp_Locale": locale,
            "vnp_OrderInfo": order_info,
            "vnp_OrderType": "billpayment",
            "vnp_ReturnUrl": return_url,
            "vnp_TxnRef": thanh_toan.ma_giao_dich,
        }

        checksum = cls.calculate_hmac_sha512(params, hash_secret)
        params["vnp_SecureHash"] = checksum

        sorted_items = sorted(params.items())
        query_string = "&".join(
            f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items
        )
        payment_url = f"{base_url}?{query_string}"
        return payment_url, params

    @classmethod
    @transaction.atomic
    def process_ipn(cls, query_params: Dict[str, Any]) -> Tuple[str, str]:
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        params = dict(query_params)
        vnp_secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        if isinstance(vnp_secure_hash, list):
            vnp_secure_hash = vnp_secure_hash[0]

        # 1. Verify Checksum
        if not vnp_secure_hash or not cls.verify_signature(params, str(vnp_secure_hash), hash_secret):
            return "97", "Invalid Checksum"

        txn_ref = params.get("vnp_TxnRef")
        if isinstance(txn_ref, list):
            txn_ref = txn_ref[0]

        raw_amount = params.get("vnp_Amount", 0)
        if isinstance(raw_amount, list):
            raw_amount = raw_amount[0]
        amount = int(raw_amount)

        response_code = params.get("vnp_ResponseCode")
        if isinstance(response_code, list):
            response_code = response_code[0]

        # 2. Check Order Existence
        try:
            thanh_toan = ThanhToan.objects.select_for_update().select_related(
                "dat_ban", "don_hang"
            ).get(ma_giao_dich=txn_ref)
        except ThanhToan.DoesNotExist:
            return "01", "Order not found"

        # 3. Check Amount (VNPay amount * 100)
        expected_amount = int(Decimal(thanh_toan.so_tien) * 100)
        if amount != expected_amount:
            return "04", "Invalid amount"

        # 4. Idempotency Check
        if thanh_toan.trang_thai in (ThanhToan.TrangThai.THANH_CONG, ThanhToan.TrangThai.DA_HOAN_TIEN):
            return "02", "Order already confirmed"

        # 5. Process Confirmation or Failure
        now = timezone.now()
        if response_code == "00":
            thanh_toan.trang_thai = ThanhToan.TrangThai.THANH_CONG
            thanh_toan.thanh_toan_luc = now
            thanh_toan.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])

            # Link DatBan
            if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                db = thanh_toan.dat_ban
                db.trang_thai = DatBan.TrangThai.DA_XAC_NHAN
                db.trang_thai_coc = DatBan.TrangThaiCoc.THANH_CONG
                db.thanh_toan_coc_luc = now
                db.phien_ban += 1
                db.save(update_fields=["trang_thai", "trang_thai_coc", "thanh_toan_coc_luc", "phien_ban", "cap_nhat_luc"])

            # Link DonHang
            elif thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.DON_HANG and thanh_toan.don_hang:
                dh = thanh_toan.don_hang
                dh.trang_thai = DonHang.TrangThai.DA_XAC_NHAN
                dh.save(update_fields=["trang_thai", "cap_nhat_luc"])
                from orders.models import LichSuTrangThaiDon
                LichSuTrangThaiDon.objects.create(
                    don_hang=dh,
                    tu_trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
                    sang_trang_thai=DonHang.TrangThai.DA_XAC_NHAN,
                    doi_boi=thanh_toan.nguoi_dung,
                    ghi_chu="VNPay IPN confirmed payment"
                )

            return "00", "Confirm Success"
        else:
            thanh_toan.trang_thai = ThanhToan.TrangThai.THAT_BAI
            thanh_toan.save(update_fields=["trang_thai", "cap_nhat_luc"])

            if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                db = thanh_toan.dat_ban
                db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
                db.save(update_fields=["trang_thai_coc", "cap_nhat_luc"])

            return "00", "Confirm Failure"


class RefundService:
    POLICY_THRESHOLDS = {
        "TRUOC_24H": ("truoc_24h", Decimal("100.0"), "da_hoan_tien"),
        "TU_6_DEN_24H": ("tu_6_den_24h", Decimal("50.0"), "hoan_tien_mot_phan"),
        "TRONG_6H": ("trong_6h", Decimal("0.0"), "that_bai"),
        "KHACH_KHONG_DEN": ("khach_khong_den", Decimal("0.0"), "that_bai"),
    }

    @classmethod
    def calculate_refund(
        cls,
        thoi_gian_dat: datetime,
        thoi_gian_huy: datetime,
        so_tien_coc: Decimal,
        is_no_show: bool = False,
    ) -> Tuple[str, Decimal, Decimal, Decimal, str]:
        if is_no_show:
            moc, pct, status = cls.POLICY_THRESHOLDS["KHACH_KHONG_DEN"]
            return moc, pct, Decimal("0.0"), so_tien_coc, status

        delta_seconds = (thoi_gian_dat - thoi_gian_huy).total_seconds()
        delta_hours = delta_seconds / 3600.0

        if delta_hours > 24.0:
            moc, pct, status = cls.POLICY_THRESHOLDS["TRUOC_24H"]
            so_tien_hoan = Decimal(str(so_tien_coc))
            so_tien_phat = Decimal("0.0")
        elif 6.0 <= delta_hours <= 24.0:
            moc, pct, status = cls.POLICY_THRESHOLDS["TU_6_DEN_24H"]
            so_tien_hoan = round(Decimal(str(so_tien_coc)) * Decimal("0.5"), 2)
            so_tien_phat = round(Decimal(str(so_tien_coc)) - so_tien_hoan, 2)
        else:
            moc, pct, status = cls.POLICY_THRESHOLDS["TRONG_6H"]
            so_tien_hoan = Decimal("0.0")
            so_tien_phat = Decimal(str(so_tien_coc))

        return moc, pct, so_tien_hoan, so_tien_phat, status

    @classmethod
    @transaction.atomic
    def process_cancellation_and_refund(
        cls,
        dat_ban: DatBan,
        user,
        ly_do: str = "Khách hàng yêu cầu hủy",
        is_no_show: bool = False,
    ) -> Dict[str, Any]:
        now = timezone.now()
        naive_dt = datetime.combine(dat_ban.ngay_dat, dat_ban.gio_bat_dau)
        if timezone.is_aware(now):
            thoi_gian_dat = timezone.make_aware(naive_dt, timezone.get_current_timezone())
        else:
            thoi_gian_dat = naive_dt

        so_tien_coc = Decimal(str(dat_ban.so_tien_coc))
        delta_seconds = (thoi_gian_dat - now).total_seconds()
        delta_hours = max(0.0, delta_seconds / 3600.0)

        moc, pct, so_tien_hoan, so_tien_phat, status_coc = cls.calculate_refund(
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=now,
            so_tien_coc=so_tien_coc,
            is_no_show=is_no_show,
        )

        dat_ban.trang_thai = DatBan.TrangThai.DA_HUY
        dat_ban.trang_thai_coc = status_coc
        dat_ban.huy_luc = now
        dat_ban.ly_do_huy = ly_do
        dat_ban.phien_ban += 1
        dat_ban.save(update_fields=["trang_thai", "trang_thai_coc", "huy_luc", "ly_do_huy", "phien_ban", "cap_nhat_luc"])

        # Update ThanhToan if exists
        tt = dat_ban.danh_sach_thanh_toan.filter(loai_thanh_toan=ThanhToan.LoaiThanhToan.TIEN_COC).first()
        if tt:
            if so_tien_hoan > Decimal("0.0"):
                tt.trang_thai = ThanhToan.TrangThai.DA_HOAN_TIEN
            tt.hoan_tien_luc = now
            tt.save(update_fields=["trang_thai", "hoan_tien_luc", "cap_nhat_luc"])

        receipt_code = f"RF-{dat_ban.ma_dat_ban}-{now.strftime('%Y%m%d')}"
        phieu_hoan_tien = {
            "ma_phieu_hoan": receipt_code,
            "ma_dat_ban": dat_ban.ma_dat_ban,
            "khach_hang": {
                "id": dat_ban.nguoi_dung_id,
                "ho_ten": dat_ban.ten_khach,
                "so_dien_thoai": dat_ban.sdt_khach,
            },
            "chi_nhanh": {
                "id": dat_ban.chi_nhanh_id,
                "ten": dat_ban.chi_nhanh.ten if dat_ban.chi_nhanh else "",
            },
            "thoi_gian_dat_ban": thoi_gian_dat.isoformat(),
            "thoi_gian_yeu_cau_huy": now.isoformat(),
            "so_gio_truoc_gio_hen": round(delta_hours, 2),
            "chinh_sach_ap_dung": {
                "moc": moc,
                "ty_le_hoan_phan_tram": float(pct),
            },
            "tai_chinh": {
                "so_tien_coc_goc": float(so_tien_coc),
                "so_tien_hoan_tra": float(so_tien_hoan),
                "so_tien_khau_tru_phat": float(so_tien_phat),
            },
            "ly_do_huy": ly_do,
            "phuong_thuc_hoan": "vnpay_refund",
            "trang_thai": status_coc,
            "tao_luc": now.isoformat(),
        }

        return {
            "trang_thai": "da_huy",
            "phan_tram_hoan_tien": float(pct),
            "so_tien_hoan": float(so_tien_hoan),
            "so_tien_phat": float(so_tien_phat),
            "moc_thoi_gian": moc,
            "phieu_hoan_tien": phieu_hoan_tien,
        }
```

### 4.3. Nâng cấp Serializers `payments/serializers.py`
Bổ sung các serializer sau vào `payments/serializers.py`:
```python
class VNPayCreatePaymentSerializer(serializers.Serializer):
    loai_thanh_toan = serializers.ChoiceField(
        choices=[("tien_coc", "Tiền cọc"), ("don_hang", "Đơn hàng")],
        default="tien_coc",
        required=False
    )
    payment_type = serializers.CharField(required=False, write_only=True)
    dat_ban_id = serializers.IntegerField(required=False, allow_null=True)
    reservation_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    don_hang_id = serializers.IntegerField(required=False, allow_null=True)
    order_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    ma_tham_chieu_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    so_tien = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, write_only=True)
    order_info = serializers.CharField(max_length=255, required=False, default="")

    def validate(self, attrs):
        # Resolve aliases
        loai = attrs.get("payment_type") or attrs.get("loai_thanh_toan") or "tien_coc"
        attrs["loai_thanh_toan"] = loai
        
        dat_ban_id = attrs.get("dat_ban_id") or attrs.get("reservation_id")
        don_hang_id = attrs.get("don_hang_id") or attrs.get("order_id")
        ma_ref = attrs.get("ma_tham_chieu_id")

        if loai == "tien_coc":
            target_id = dat_ban_id or ma_ref
            if not target_id:
                raise serializers.ValidationError("Cần cung cấp dat_ban_id cho thanh toán tiền cọc.")
            attrs["dat_ban_id"] = target_id
        elif loai == "don_hang":
            target_id = don_hang_id or ma_ref
            if not target_id:
                raise serializers.ValidationError("Cần cung cấp don_hang_id cho thanh toán đơn hàng.")
            attrs["don_hang_id"] = target_id

        so_tien = attrs.get("amount") or attrs.get("so_tien")
        if so_tien:
            attrs["so_tien"] = so_tien

        return attrs
```

### 4.4. Nâng cấp Views `payments/views.py`
Bổ sung các action VNPay vào `ThanhToanViewSet`:
```python
    @action(detail=False, methods=["post"], url_path="vnpay/create", permission_classes=[AllowAny])
    def vnpay_create(self, request):
        ser = VNPayCreatePaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user if request.user.is_authenticated else None
        loai = data["loai_thanh_toan"]
        dat_ban = don_hang = None

        if loai == "tien_coc":
            dat_ban = get_object_or_404(DatBan, id=data["dat_ban_id"])
            if not user:
                user = dat_ban.nguoi_dung
            so_tien = data.get("so_tien") or dat_ban.so_tien_coc
        else:
            don_hang = get_object_or_404(DonHang, id=data["don_hang_id"])
            if not user:
                user = don_hang.khach_hang
            so_tien = data.get("so_tien") or don_hang.tong_tien

        if not user:
            from django.contrib.auth import get_user_model
            user = get_user_model().objects.filter(is_active=True).first()

        thanh_toan, _ = ThanhToan.objects.get_or_create(
            dat_ban=dat_ban,
            don_hang=don_hang,
            loai_thanh_toan=loai,
            phuong_thuc="vnpay",
            trang_thai=ThanhToan.TrangThai.CHO_XU_LY,
            defaults={"so_tien": so_tien, "nguoi_dung": user}
        )
        if thanh_toan.so_tien != so_tien:
            thanh_toan.so_tien = so_tien
            thanh_toan.save(update_fields=["so_tien", "cap_nhat_luc"])

        client_ip = VNPayService.get_client_ip(request)
        payment_url, params = VNPayService.create_payment_url(
            thanh_toan=thanh_toan,
            ip_addr=client_ip,
            order_info=data.get("order_info")
        )

        expires_at = (timezone.now() + timedelta(minutes=15)).isoformat()
        return Response({
            "payment_url": payment_url,
            "duong_dan_thanh_toan": payment_url,
            "txn_ref": thanh_toan.ma_giao_dich,
            "ma_giao_dich": thanh_toan.ma_giao_dich,
            "amount": float(thanh_toan.so_tien),
            "so_tien": float(thanh_toan.so_tien),
            "expires_at": expires_at,
            "het_han_luc": expires_at,
            "thanh_toan_id": thanh_toan.id,
        })

    @action(detail=False, methods=["post"], url_path="vnpay/tao-phien", permission_classes=[AllowAny])
    def vnpay_tao_phien(self, request):
        return self.vnpay_create(request)

    @action(detail=False, methods=["get"], url_path="vnpay/return", permission_classes=[AllowAny])
    def vnpay_return(self, request):
        params = request.query_params.dict()
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        vnp_secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        is_valid = VNPayService.verify_signature(params, vnp_secure_hash, hash_secret)
        rsp_code = params.get("vnp_ResponseCode", "")
        is_success = is_valid and rsp_code == "00"
        raw_amount = params.get("vnp_Amount", 0)
        amount_vnd = float(raw_amount) / 100.0 if raw_amount else 0.0

        return Response({
            "status": "success" if is_success else "failed",
            "ma_giao_dich": params.get("vnp_TxnRef", ""),
            "txn_ref": params.get("vnp_TxnRef", ""),
            "ma_phan_hoi": rsp_code,
            "response_code": rsp_code,
            "so_tien": amount_vnd,
            "amount": amount_vnd,
            "message": "Giao dịch thành công" if is_success else "Giao dịch không thành công hoặc chữ ký không hợp lệ"
        })

    @action(detail=False, methods=["get"], url_path="vnpay/ipn", permission_classes=[AllowAny])
    def vnpay_ipn(self, request):
        rsp_code, message = VNPayService.process_ipn(request.query_params)
        return Response({"RspCode": rsp_code, "Message": message})
```

### 4.5. Nâng cấp Hủy Đặt bàn & Hoàn cọc (`reservations/views.py`)
Cập nhật action `huy_dat_ban` trong `DatBanViewSet`:
```python
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def huy_dat_ban(self, request, pk=None):
        dat_ban = self.get_object()
        if dat_ban.nguoi_dung_id != request.user.id and not getattr(request.user, "la_nhan_vien_nha_hang", False):
            return Response({"chi_tiet": "Không có quyền hủy đặt bàn này."}, status=403)

        if dat_ban.trang_thai in [DatBan.TrangThai.DA_HUY, DatBan.TrangThai.HOAN_TAT]:
            return Response({"chi_tiet": f"Đặt bàn này đã ở trạng thái {dat_ban.get_trang_thai_display()}."}, status=400)

        from payments.services import RefundService
        ly_do = request.data.get("ly_do", "Khách hàng yêu cầu hủy")
        is_no_show = request.data.get("is_no_show", False)

        result = RefundService.process_cancellation_and_refund(
            dat_ban=dat_ban,
            user=request.user,
            ly_do=ly_do,
            is_no_show=is_no_show,
        )
        result["dat_ban"] = self.get_serializer(dat_ban).data
        return Response(result)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        return self.huy_dat_ban(request, pk=pk)
```

---

## 5. Verification Method (Phương pháp Kiểm thử & Độc lập Xác minh)

Người nhận bàn giao hoặc kiểm thử viên có thể kiểm tra độc lập qua các bước:

1. **Kiểm tra cú pháp & Import Django**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python manage.py check
   ```
   *Điều kiện thành công*: Trả về `System check identified no issues (0 silenced)` với exit code 0.

2. **Chạy toàn bộ 60 Test E2E hiện có**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Điều kiện thành công*: 60/60 test vượt qua 100%.

3. **Kiểm tra các Test chuyên biệt cho VNPay và Hoàn tiền**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -m unittest tests.e2e.tier1.test_t1_vnpay
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -m unittest tests.e2e.tier2.test_t2_vnpay
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -m unittest tests.e2e.tier2.test_t2_refund
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -m unittest tests.e2e.tier3.test_t3_combinations
   ```

4. **Kiểm tra cURL / API Integration (sau khi Implementer áp dụng code)**:
   - Tạo URL thanh toán cọc:
     ```bash
     curl -X POST http://localhost:8000/api/payments/vnpay/create/ \
       -H "Content-Type: application/json" \
       -d '{"loai_thanh_toan": "tien_coc", "dat_ban_id": 1, "so_tien": 200000}'
     ```
   - Gọi IPN webhook xác nhận giao dịch:
     ```bash
     curl -X GET "http://localhost:8000/api/payments/vnpay/ipn/?vnp_TxnRef=TT...&vnp_Amount=20000000&vnp_ResponseCode=00&vnp_SecureHash=..."
     ```
     Kỳ vọng nhận: `{"RspCode": "00", "Message": "Confirm Success"}`.
   - Thử nghiệm hủy đặt bàn:
     ```bash
     curl -X POST http://localhost:8000/api/reservations/1/huy_dat_ban/ \
       -H "Content-Type: application/json" \
       -d '{"ly_do": "Khách hủy trước 25 tiếng"}'
     ```
     Kỳ vọng nhận: `{"trang_thai": "da_huy", "phan_tram_hoan_tien": 100.0, "so_tien_hoan": 200000.0, "phieu_hoan_tien": {...}}`.

---
*Báo cáo đã hoàn tất và sẵn sàng bàn giao cho Orchestrator và Implementation Workers.*
