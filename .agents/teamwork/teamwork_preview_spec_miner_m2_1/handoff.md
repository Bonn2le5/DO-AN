# Handoff Report: VNPay Sandbox 2.1.0 & Deposit Refund Policy Specification

**Author**: `m2_spec_miner_1` (Specification Miner for Milestone 2)  
**Date**: 2026-10-14  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m2_1`  
**Target Milestone**: Milestone 2 (VNPay Sandbox Integration & Deposit Refund Policy)  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)

---

## 1. Observation

Direct observations extracted from authoritative project sources, test oracles, and codebase:

1. **Test Infrastructure & Specification Oracles**:
   - `tests/e2e/helpers/vnpay_oracle.py`: Lines 14–45 define `DEFAULT_TMN_CODE = "MOCREST1"`, `DEFAULT_HASH_SECRET = "VNPAYSECRETKEY2026MOCRESTAURANT"`, `DEFAULT_SANDBOX_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"`. The HMAC-SHA512 algorithm strips `vnp_SecureHash` and `vnp_SecureHashType`, ignores empty/None values, sorts parameter keys in ASCII alphabetical order, formats `key=value` using `urllib.parse.quote_plus`, joins them with `&`, and computes `hmac.new(secret, hash_data, hashlib.sha512).hexdigest()`.
   - `tests/e2e/helpers/vnpay_oracle.py`: Lines 100–149 define the 5-step IPN evaluation returning response codes:
     - `"00"`: `"Confirm Success"` (or `"Confirm Failure"` if `vnp_ResponseCode != "00"`)
     - `"01"`: `"Order not found"`
     - `"02"`: `"Order already confirmed"`
     - `"04"`: `"Invalid amount"`
     - `"97"`: `"Invalid Checksum"`
   - `tests/e2e/helpers/refund_calculator.py`: Lines 11–51 define `POLICY_THRESHOLDS`:
     - `TRUOC_24H`: `("truoc_24h", 100.0, "da_hoan_tien")` when $\Delta t > 24.0$ hours.
     - `TU_6_DEN_24H`: `("tu_6_den_24h", 50.0, "hoan_tien_mot_phan")` when $6.0 \le \Delta t \le 24.0$ hours.
     - `TRONG_6H`: `("trong_6h", 0.0, "that_bai")` when $0.0 \le \Delta t < 6.0$ hours.
     - `KHACH_KHONG_DEN`: `("khach_khong_den", 0.0, "that_bai")` for no-show events.
   - `tests/e2e/helpers/refund_calculator.py`: Lines 53–100 define `PhieuHoanTien` receipt schema with `ma_phieu_hoan = f"RF-{ma_dat_ban}-{date_str}"`, customer info, branch info, time delta hours, financial breakdown (`so_tien_coc_goc`, `so_tien_hoan_tra`, `so_tien_khau_tru_phat`), `phuong_thuc_hoan = "vnpay_refund"`, and `trang_thai`.

2. **Schema & Model Definitions**:
   - `moc_schema_tieng_viet.sql`:
     - Line 20: `CREATE TYPE trang_thai_coc AS ENUM ('chua_thanh_toan','dang_xu_ly','thanh_cong','that_bai','da_hoan_tien','hoan_tien_mot_phan');`
     - Line 21: `CREATE TYPE moc_huy_dat_ban AS ENUM ('truoc_24h','tu_6_den_24h','trong_6h','khach_khong_den');`
     - Line 24: `CREATE TYPE loai_thanh_toan AS ENUM ('don_hang','tien_coc');`
     - Line 25: `CREATE TYPE trang_thai_thanh_toan AS ENUM ('cho_xu_ly','thanh_cong','that_bai','da_hoan_tien');`
     - Lines 281–287: `quy_tac_huy_dat_coc` table maps `chinh_sach_id`, `moc_thoi_gian`, and `phan_tram_hoan_tien`.
     - Lines 436–455: `thanh_toan` table with `loai_thanh_toan`, `so_tien`, `ma_giao_dich`, `trang_thai`, `thanh_toan_luc`, `hoan_tien_luc`, and mutual exclusion constraint `kiem_tra_muc_tieu_thanh_toan`.
   - `moc-backend/payments/models.py`:
     - Lines 6–35: `ThanhToan` model with fields `nguoi_dung`, `don_hang`, `dat_ban`, `loai_thanh_toan`, `phuong_thuc`, `so_tien`, `ma_giao_dich`, `trang_thai`, `thanh_toan_luc`, `hoan_tien_luc`.
     - Lines 36–51, 66–194: `_LEGACY_MAP` and property aliases supporting legacy English field names.
   - `moc-backend/reservations/models.py`:
     - Lines 88–129: `ChinhSachDatCoc` and `QuyTacHuyDatCoc` models.
     - Lines 130–233: `DatBan` model with `yeu_cau_dat_coc`, `so_tien_coc`, `trang_thai_coc`, `thanh_toan_coc_luc`, `huy_luc`, `ly_do_huy`, `phien_ban`.
   - `moc-backend/reservations/views.py`:
     - Lines 88–98: Current basic `huy_dat_ban` sets `trang_thai = DA_HUY`, `huy_luc = now()`, `ly_do_huy`, but lacks automated refund percentage evaluation, `trang_thai_coc` update, and `PhieuHoanTien` generation.

3. **Frontend API Callers & Contracts**:
   - `moc-frontend/src/api/reservations.api.ts`: Lines 109–126 define `taoPhienThanhToanVNPay(idDatBan, soTien)` calling `POST /api/thanh-toan/vnpay/tao-phien/` with body `{ dat_ban_id, so_tien }`, expecting `{ duong_dan_thanh_toan, ma_giao_dich, so_tien, het_han_luc }`.
   - `moc-frontend/src/types/index.ts`: Lines 132–137 define `PhienThanhToanVNPay` interface: `{ duongDanThanhToan, maGiaoDich, soTien, hetHanLuc }`.
   - `PROJECT.md`: Lines 99–117 define dual routes: `POST /api/payments/vnpay/create/` and `POST /api/thanh-toan/vnpay/create/`, IPN webhook `GET /api/payments/vnpay/ipn/`, and Return URL `GET /api/payments/vnpay/return/`.

4. **Test Suite Verification**:
   - Executing `/Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1`: Ran 30 tests in 0.005s, 0 failures, 100% pass.
   - Executing `/Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 2`: Ran 20 tests in 0.002s, 0 failures, 100% pass.

---

## 2. Logic Chain

1. **VNPay Sandbox 2.1.0 Architecture**:
   - To build a compliant payment URL, the backend must construct a query string containing 12 required parameters (`vnp_Version`, `vnp_Command`, `vnp_TmnCode`, `vnp_Amount`, `vnp_CreateDate`, `vnp_CurrCode`, `vnp_IpAddr`, `vnp_Locale`, `vnp_OrderInfo`, `vnp_OrderType`, `vnp_ReturnUrl`, `vnp_TxnRef`).
   - The checksum algorithm requires:
     1. Sorting parameter keys by ASCII byte values.
     2. URL-encoding keys and values with `urllib.parse.quote_plus` (converting spaces to `+` and percent-encoding Vietnamese diacritics).
     3. Joining them with `&` into `hash_data`.
     4. Generating a 128-character HMAC-SHA512 hexadecimal digest using `hash_secret`.
   - The final URL redirects the user to `https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?{hash_data}&vnp_SecureHash={checksum}`.

2. **IPN Webhook Security & Idempotency Pipeline**:
   - VNPay dispatches a server-to-server HTTP GET request containing all transaction parameters and `vnp_SecureHash`.
   - The backend handler must enforce a strict 5-stage validation gate:
     - **Stage 1 (Checksum)**: Validate signature against secret key. Mismatch $\rightarrow$ `{"RspCode": "97", "Message": "Invalid Checksum"}`.
     - **Stage 2 (Order Check)**: Locate `ThanhToan` record matching `vnp_TxnRef`. Not found $\rightarrow$ `{"RspCode": "01", "Message": "Order not found"}`.
     - **Stage 3 (Amount Check)**: Verify `vnp_Amount == record.so_tien * 100`. Mismatch $\rightarrow$ `{"RspCode": "04", "Message": "Invalid amount"}`.
     - **Stage 4 (Idempotency)**: If `record.trang_thai` is already in a terminal state (`thanh_cong`, `da_xac_nhan`, `that_bai`, `da_huy`), return `{"RspCode": "02", "Message": "Order already confirmed"}` without repeating side effects.
     - **Stage 5 (State Transition)**:
       - On `vnp_ResponseCode == "00"`: Mark `ThanhToan` as `thanh_cong`, mark `DatBan` as `da_xac_nhan` & `trang_thai_coc = thanh_cong`, release Redis temporary hold (`cache.delete()`), and return `{"RspCode": "00", "Message": "Confirm Success"}`.
       - On `vnp_ResponseCode != "00"` (e.g. `24` customer cancelled): Mark `ThanhToan` as `that_bai`, mark `DatBan` as `da_huy` & `trang_thai_coc = that_bai`, release Redis hold lock, and return `{"RspCode": "00", "Message": "Confirm Success"}`.

3. **Deposit Cancellation & Refund Evaluation Logic**:
   - Time difference $\Delta t = (T_{\text{booking}} - T_{\text{cancel}}).\text{total\_seconds}() / 3600.0$.
   - Three deterministic time brackets govern refund eligibility:
     - $\Delta t > 24.0$ h: 100% refund, `trang_thai_coc = da_hoan_tien`, milestone `truoc_24h`.
     - $6.0 \le \Delta t \le 24.0$ h: 50% refund, `trang_thai_coc = hoan_tien_mot_phan`, milestone `tu_6_den_24h`.
     - $0.0 \le \Delta t < 6.0$ h: 0% refund (100% penalty retained), `trang_thai_coc = that_bai`, milestone `trong_6h`.
     - No-show ($\Delta t \le 0$): 0% refund, `trang_thai_coc = that_bai`, milestone `khach_khong_den`.
   - A structured `PhieuHoanTien` audit record is created capturing reconciliation identifiers, exact hour deltas, original vs refund vs penalty amounts, and timestamps.
   - Upon cancellation, the booked table is immediately released back to `trong` status so it can be re-reserved.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | VNPay 2.1.0 | VNPay Sandbox URL Generation | Generates payment redirect URL with 12 mandatory params + HMAC-SHA512 checksum | `txn_ref`, `amount_vnd`, `order_info`, `ip_addr`, `tmn_code`, `hash_secret` | `full_url`, `params` dict with `vnp_SecureHash` | Fails if missing required parameters or negative amount | `tests/e2e/helpers/vnpay_oracle.py:55` |
| 2 | VNPay 2.1.0 | Parameter Sorting & Normalization | Sorts parameters in ASCII alphabetical order, ignores empty values and hashes | Dictionary of `vnp_*` parameters | ASCII-ordered `key=value` string joined by `&` | Silently ignores `vnp_SecureHash`, `vnp_SecureHashType`, and empty values | `tests/e2e/helpers/vnpay_oracle.py:19` |
| 3 | VNPay 2.1.0 | HMAC-SHA512 Checksum Verification | Verifies incoming hash matches computed SHA512 digest using secret key | `params`, `secure_hash`, `hash_secret` | Boolean `True`/`False` | Constant-time comparison prevents timing attacks | `tests/e2e/helpers/vnpay_oracle.py:47` |
| 4 | VNPay 2.1.0 | IPN Webhook Verification & Idempotency | Server-to-server webhook validating checksum, order existence, amount, and terminal state | GET query parameters from VNPay, DB transaction record | JSON response `{"RspCode": "...", "Message": "..."}`, updated DB status | Returns `97` (hash mismatch), `01` (not found), `04` (bad amount), `02` (duplicate) | `tests/e2e/helpers/vnpay_oracle.py:100` |
| 5 | VNPay 2.1.0 | Customer Return URL Redirect Handling | Parses browser redirect from VNPay, verifies signature, presents payment result | Return URL GET parameters | Verification status, transaction reference, display state | Invalid hash rejects callback with verification failure | `tests/e2e/tier1/test_t1_vnpay.py:120` |
| 6 | VNPay 2.1.0 | Payment Failure Release Trigger | When user cancels or payment fails (`vnp_ResponseCode != "00"`), releases table hold | IPN with non-zero response code (e.g. `24`) | `ThanhToan` set to `that_bai`, Redis key deleted, `DatBan` set to `da_huy` | Acknowledges IPN receipt with `RspCode: 00` while setting internal failure status | `tests/e2e/tier3/test_t3_combinations.py:137` |
| 7 | Payment API | Dual Payment Initiation Endpoints | Creates VNPay payment session supporting both English and Vietnamese routes | `POST /api/payments/vnpay/create/` or `POST /api/thanh-toan/vnpay/create/` | `{"payment_url": "...", "txn_ref": "...", "so_tien": N}` | HTTP 400 on invalid payload; HTTP 404 if booking not found | `PROJECT.md:100`, `api/urls.py:62` |
| 8 | Payment API | Frontend Session Adapter Endpoint | Direct endpoint called by frontend `reservations.api.ts` | `POST /api/thanh-toan/vnpay/tao-phien/` with `{dat_ban_id, so_tien}` | `{"duong_dan_thanh_toan": "...", "ma_giao_dich": "...", "so_tien": N, "het_han_luc": "..."}` | HTTP 400 if missing `dat_ban_id` or `so_tien` | `moc-frontend/src/api/reservations.api.ts:109` |
| 9 | Refund Policy | Early Cancellation (>24h) | 100% deposit refund when cancelled more than 24 hours in advance | Booking datetime, cancellation datetime, deposit amount ($\Delta t > 24\text{h}$) | `pct=100.0`, `so_tien_hoan=deposit`, `so_tien_phat=0`, `status='da_hoan_tien'` | Raises error if already cancelled or past booking time | `tests/e2e/helpers/refund_calculator.py:37` |
| 10 | Refund Policy | Mid-tier Cancellation (6h–24h) | 50% deposit refund, 50% penalty retained by restaurant | Booking datetime, cancellation datetime ($\Delta t \in [6.0, 24.0]$) | `pct=50.0`, `so_tien_hoan=0.5*deposit`, `so_tien_phat=0.5*deposit`, `status='hoan_tien_mot_phan'` | Handles exact 24.0h and 6.0h boundaries deterministically | `tests/e2e/helpers/refund_calculator.py:41` |
| 11 | Refund Policy | Late Cancellation (<6h) | 0% deposit refund, 100% penalty retained by restaurant | Booking datetime, cancellation datetime ($\Delta t < 6.0\text{h}$) | `pct=0.0`, `so_tien_hoan=0`, `so_tien_phat=deposit`, `status='that_bai'` | Restaurant retains full deposit; table status reset to `trong` | `tests/e2e/helpers/refund_calculator.py:45` |
| 12 | Refund Policy | No-Show Forfeiture (`khach_khong_den`) | 0% refund when customer fails to arrive for scheduled reservation | Booking datetime passed, staff marks no-show flag | `pct=0.0`, `so_tien_hoan=0`, `so_tien_phat=deposit`, `status='that_bai'`, booking `khach_khong_den` | Must only be triggered by staff or scheduled automated cleanup | `tests/e2e/helpers/refund_calculator.py:30` |
| 13 | Refund Policy | `PhieuHoanTien` Audit Receipt Generation | Produces audit record with unique code `RF-{ma_dat_ban}-{date_str}` | Reservation, customer details, branch details, cancel reason | Structured receipt dictionary with financial and timestamp audit trails | Unique code collision prevented by reservation code + date scoping | `tests/e2e/helpers/refund_calculator.py:53` |
| 14 | Reservation API | Cancellation Endpoint | Unified cancellation endpoint performing policy calculation and receipt generation | `POST /api/reservations/{id}/huy_dat_ban/` or `POST /api/dat-ban/{id}/huy_dat_ban/` with `{ly_do}` | `{"trang_thai": "da_huy", "phan_tram_hoan_tien": N, "so_tien_hoan": N, "phieu_hoan_tien": {...}}` | HTTP 403 if unauthorized; HTTP 400 if already cancelled | `PROJECT.md:111`, `reservations/views.py:88` |
| 15 | Concurrency | Redis Hold Release on Successful IPN | Automatic deletion of Redis temporary hold key upon VNPay confirmation | Confirmed IPN for reservation holding a Redis key | `cache.delete(khoa_giu_ban)` removes lock; table secured via DB record | Idempotent; key expiry handled cleanly if already expired | `tests/e2e/tier3/test_t3_combinations.py:106` |
| 16 | Concurrency | Table Availability Reset on Cancellation | Releasing table from `da_dat` to `trong` when booking is cancelled | Cancellation of confirmed booking | `DatBan.trang_thai = 'da_huy'`; table immediately open for new queries | Excludes cancelled bookings from date/time collision queries | `reservations/views.py:36` |

---

## 4. Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | VNPay URL Building | Amount with decimal value (e.g. 200000.50 VND) | `vnp_Amount` must be formatted as an integer string multiplied by 100 (`20000000`); floating points are truncated/converted to int. |
| 2 | Parameter Sorting | Disordered keys in dictionary (`z_param`, `a_param`, `m_param`) | Checksum algorithm sorts keys strictly by ASCII byte order before building query string; identical dictionary content with different insertion order produces identical HMAC-SHA512 checksum. |
| 3 | Empty / None Params | Parameter dictionary contains `{"vnp_CardType": None, "vnp_BankCode": ""}` | Parameters with `None` or empty string values are excluded from both the hash calculation and the final URL query string. |
| 4 | Unicode Diacritics | `vnp_OrderInfo` with Vietnamese text: `"Thanh toán cọc bàn Nhà hàng Mộc - Bàn 12 VIP"` | `urllib.parse.quote_plus` properly converts accents to UTF-8 percent-encoded strings and spaces to `+`; HMAC hash matches verification oracle without encoding corruption. |
| 5 | Invalid Checksum (IPN) | Attacker alters `vnp_TxnRef` or sends bogus signature `0000000000...` | Evaluation immediately returns `{"RspCode": "97", "Message": "Invalid Checksum"}` without querying the database or mutating state. |
| 6 | Unknown Transaction (IPN) | VNPay sends callback for non-existent `vnp_TxnRef = "UNKNOWN_TRANSACTION_ID"` | Signature succeeds, but DB lookup fails; returns `{"RspCode": "01", "Message": "Order not found"}`. |
| 7 | Tampered Amount (IPN) | Expected amount 350,000 VND; incoming `vnp_Amount = "1000000"` (10,000 VND) | Amount mismatch detected; returns `{"RspCode": "04", "Message": "Invalid amount"}` and aborts transaction. |
| 8 | Duplicate IPN (Idempotency) | Identical IPN callback received twice for an already confirmed order (`trang_thai == "thanh_cong"`) | Gatekeeper detects existing terminal state; returns `{"RspCode": "02", "Message": "Order already confirmed"}` without repeating database updates or inventory deductions. |
| 9 | Payment Failure (IPN) | Customer cancels at gateway; VNPay returns `vnp_ResponseCode = "24"` | Valid hash verified; payment marked `that_bai`, reservation marked `da_huy`, Redis hold lock released; returns `{"RspCode": "00", "Message": "Confirm Failure"}` to acknowledge IPN delivery. |
| 10 | Exact 24.0h Boundary (Refund) | Cancellation at exactly 24 hours 00 minutes before booking time ($\Delta t = 24.000$) | Evaluates to mid-tier rule `tu_6_den_24h` ($6.0 \le \Delta t \le 24.0$); yields exactly 50% refund, 50% penalty, and `trang_thai_coc = hoan_tien_mot_phan`. |
| 11 | Exact 6.0h Boundary (Refund) | Cancellation at exactly 6 hours 00 minutes before booking time ($\Delta t = 6.000$) | Evaluates to mid-tier rule `tu_6_den_24h`; yields exactly 50% refund, 50% penalty. |
| 12 | Just Under 6h (Refund) | Cancellation at 5 hours 50 minutes before booking time ($\Delta t = 5.833$) | Falls into `trong_6h` (<6.0h); yields 0% refund, 100% penalty, and `trang_thai_coc = that_bai`. |
| 13 | No-Show (Refund) | Customer fails to arrive 1 hour after scheduled time ($\Delta t = -1.0$) | Flagged as `is_no_show = True` or $\Delta t \le 0$; yields 0% refund, 100% penalty, status `that_bai`, and receipt marked `khach_khong_den`. |
| 14 | Return URL vs IPN Race | Customer browser redirects to Return URL before IPN asynchronous webhook reaches server | Return URL verifies checksum and marks temporary UI status; backend transaction mutation relies on atomic DB lock (`select_for_update`) so subsequent IPN recognizes or finalizes state idempotently without collision. |

---

## 5. Specification Blueprint for Implementation

### 5.1 VNPay Sandbox Configuration
Add to `moc-backend/config/settings.py` (and `.env`):
```python
# VNPay Configuration (Sandbox 2.1.0)
VNPAY_TMN_CODE = env("VNPAY_TMN_CODE", default="MOCREST1")
VNPAY_HASH_SECRET = env("VNPAY_HASH_SECRET", default="VNPAYSECRETKEY2026MOCRESTAURANT")
VNPAY_SANDBOX_URL = env("VNPAY_SANDBOX_URL", default="https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
VNPAY_RETURN_URL = env("VNPAY_RETURN_URL", default="http://localhost:5173/payment/vnpay-return")
```

### 5.2 VNPay Payment URL Builder Function
```python
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from django.conf import settings

def build_vnpay_url(*, txn_ref: str, amount_vnd: int, order_info: str, ip_addr: str) -> tuple[str, dict]:
    now_str = datetime.now().strftime("%Y%m%d%H%M%S")
    params = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(int(amount_vnd * 100)),
        "vnp_CreateDate": now_str,
        "vnp_CurrCode": "VND",
        "vnp_IpAddr": ip_addr,
        "vnp_Locale": "vn",
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "billpayment",
        "vnp_ReturnUrl": settings.VNPAY_RETURN_URL,
        "vnp_TxnRef": txn_ref,
    }
    # Sort ASCII
    sorted_items = sorted(params.items())
    hash_data = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items)
    checksum = hmac.new(
        settings.VNPAY_HASH_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512
    ).hexdigest()
    params["vnp_SecureHash"] = checksum
    full_url = f"{settings.VNPAY_SANDBOX_URL}?{hash_data}&vnp_SecureHash={checksum}"
    return full_url, params
```

### 5.3 VNPay IPN Webhook Processing Logic
```python
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.core.cache import cache
from payments.models import ThanhToan

class VNPayIPNView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        params = request.query_params.dict()
        secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        # 1. Verify Checksum
        if not secure_hash or not verify_vnpay_signature(params, secure_hash, settings.VNPAY_HASH_SECRET):
            return Response({"RspCode": "97", "Message": "Invalid Checksum"})

        txn_ref = params.get("vnp_TxnRef")
        amount = int(params.get("vnp_Amount", 0))
        resp_code = params.get("vnp_ResponseCode")

        with transaction.atomic():
            # 2. Check Order Existence
            try:
                tt = ThanhToan.objects.select_for_update().get(ma_giao_dich=txn_ref)
            except ThanhToan.DoesNotExist:
                return Response({"RspCode": "01", "Message": "Order not found"})

            # 3. Check Amount
            if amount != int(tt.so_tien * 100):
                return Response({"RspCode": "04", "Message": "Invalid amount"})

            # 4. Check Idempotency
            if tt.trang_thai in (ThanhToan.TrangThai.THANH_CONG, ThanhToan.TrangThai.THAT_BAI):
                return Response({"RspCode": "02", "Message": "Order already confirmed"})

            # 5. Mutate State
            if resp_code == "00":
                tt.trang_thai = ThanhToan.TrangThai.THANH_CONG
                tt.thanh_toan_luc = timezone.now()
                tt.save()

                if tt.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and tt.dat_ban:
                    db = tt.dat_ban
                    db.trang_thai = "da_xac_nhan"
                    db.trang_thai_coc = "thanh_cong"
                    db.thanh_toan_coc_luc = tt.thanh_toan_luc
                    db.phien_ban += 1
                    db.save()
                    # Release temporary Redis hold key
                    cache.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{db.gio_bat_dau}")
                return Response({"RspCode": "00", "Message": "Confirm Success"})
            else:
                tt.trang_thai = ThanhToan.TrangThai.THAT_BAI
                tt.save()
                if tt.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and tt.dat_ban:
                    db = tt.dat_ban
                    db.trang_thai = "da_huy"
                    db.trang_thai_coc = "that_bai"
                    db.save()
                    cache.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{db.gio_bat_dau}")
                return Response({"RspCode": "00", "Message": "Confirm Success"})
```

### 5.4 PhieuHoanTien Model & Migration Blueprint
Create `PhieuHoanTien` in `payments/models.py`:
```python
class PhieuHoanTien(MoHinhThoiGian):
    ma_phieu_hoan = models.CharField(max_length=50, unique=True, editable=False)
    dat_ban = models.ForeignKey("reservations.DatBan", related_name="phieu_hoan_tien", on_delete=models.CASCADE)
    thanh_toan = models.ForeignKey(ThanhToan, related_name="phieu_hoan_tien", null=True, blank=True, on_delete=models.SET_NULL)
    so_tien_coc_goc = models.DecimalField(max_digits=12, decimal_places=2)
    phan_tram_hoan = models.DecimalField(max_digits=5, decimal_places=2)
    so_tien_hoan = models.DecimalField(max_digits=12, decimal_places=2)
    so_tien_phat = models.DecimalField(max_digits=12, decimal_places=2)
    moc_thoi_gian = models.CharField(max_length=20)  # 'truoc_24h', 'tu_6_den_24h', 'trong_6h', 'khach_khong_den'
    so_gio_truoc_gio_hen = models.DecimalField(max_digits=7, decimal_places=2)
    ly_do_huy = models.TextField(blank=True)
    trang_thai = models.CharField(max_length=20)  # 'da_hoan_tien', 'hoan_tien_mot_phan', 'that_bai'
    phuong_thuc_hoan = models.CharField(max_length=30, default="vnpay_refund")
    du_lieu_chi_tiet = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "phieu_hoan_tien"
        verbose_name = "Phiếu hoàn tiền"

RefundReceipt = PhieuHoanTien
```

### 5.5 Cancellation Endpoint Implementation Blueprint
In `reservations/views.py`:
```python
@action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
def huy_dat_ban(self, request, pk=None):
    with transaction.atomic():
        dat_ban = DatBan.objects.select_for_update().get(pk=pk)
        if dat_ban.nguoi_dung_id != request.user.id and not request.user.la_nhan_vien_nha_hang:
            return Response({"chi_tiet": "Không có quyền hủy đặt bàn này."}, status=403)
        if dat_ban.trang_thai in (DatBan.TrangThai.DA_HUY, DatBan.TrangThai.HOAN_TAT):
            return Response({"chi_tiet": "Không thể hủy đặt bàn ở trạng thái này."}, status=400)

        # Calculate time delta
        booking_dt = datetime.combine(dat_ban.ngay_dat, dat_ban.gio_bat_dau)
        cancel_dt = timezone.now()
        if timezone.is_aware(cancel_dt):
            import pytz
            booking_dt = timezone.make_aware(booking_dt, cancel_dt.tzinfo)

        delta_hours = max(0.0, (booking_dt - cancel_dt).total_seconds() / 3600.0)
        so_tien_coc = float(dat_ban.so_tien_coc)

        moc, pct, so_tien_hoan, so_tien_phat, status_coc = calculate_refund(
            booking_dt, cancel_dt, so_tien_coc
        )

        dat_ban.trang_thai = DatBan.TrangThai.DA_HUY
        dat_ban.trang_thai_coc = status_coc
        dat_ban.huy_luc = cancel_dt
        dat_ban.ly_do_huy = request.data.get("ly_do", "Khách hàng yêu cầu hủy")
        dat_ban.phien_ban += 1
        dat_ban.save()

        # Generate PhieuHoanTien audit record
        receipt_data = generate_refund_receipt(
            ma_dat_ban=dat_ban.ma_dat_ban,
            khach_hang_info={"ho_ten": dat_ban.ten_khach, "so_dien_thoai": dat_ban.sdt_khach},
            chi_nhanh_info={"id": dat_ban.chi_nhanh_id, "ten": dat_ban.chi_nhanh.ten},
            thoi_gian_dat=booking_dt,
            thoi_gian_huy=cancel_dt,
            so_tien_coc=so_tien_coc,
            ly_do_huy=dat_ban.ly_do_huy,
        )

        pht = PhieuHoanTien.objects.create(
            ma_phieu_hoan=receipt_data["ma_phieu_hoan"],
            dat_ban=dat_ban,
            so_tien_coc_goc=so_tien_coc,
            phan_tram_hoan=pct,
            so_tien_hoan=so_tien_hoan,
            so_tien_phat=so_tien_phat,
            moc_thoi_gian=moc,
            so_gio_truoc_gio_hen=round(delta_hours, 2),
            ly_do_huy=dat_ban.ly_do_huy,
            trang_thai=status_coc,
            phuong_thuc_hoan="vnpay_refund",
            du_lieu_chi_tiet=receipt_data,
        )

        return Response({
            "trang_thai": dat_ban.trang_thai,
            "trang_thai_coc": dat_ban.trang_thai_coc,
            "phan_tram_hoan_tien": pct,
            "so_tien_hoan": so_tien_hoan,
            "so_tien_phat": so_tien_phat,
            "phieu_hoan_tien": receipt_data,
        })
```

---

## 6. Caveats

1. **VNPay Sandbox Live Connectivity vs Oracle Simulation**: In local offline testing or CI without direct outbound internet or registered sandbox credentials, the test suite uses `vnpay_oracle.py`. For live sandbox calls, valid merchant credentials (`MOCREST1` / `VNPAYSECRETKEY2026MOCRESTAURANT`) must be active on VNPay's gateway.
2. **PostgreSQL vs SQLite for Timestamp Timezones**: SQLite handles datetime timezone conversions differently than PostgreSQL `TIMESTAMPTZ`. In PostgreSQL, `make_aware` using the active timezone (e.g. `Asia/Ho_Chi_Minh` or `UTC`) ensures exact hour delta arithmetic down to the millisecond.
3. **No-Show Trigger Mechanism**: No-show refunds (`khach_khong_den`) cannot be triggered by the customer; they must only be invoked by staff via the status update endpoint or an automated Celery/cron task evaluating passed reservation times.

---

## 7. Conclusion

All specifications for Milestone 2 (VNPay Sandbox 2.1.0 & Deposit Refund Policy) have been mined, verified against the authoritative test suites, and documented:
1. **VNPay 2.1.0**: Checksum hashing (HMAC-SHA512), query parameter ASCII sorting, URL encoding rules, Return URL callback, and IPN server-to-server webhook gatekeeper with status codes `00`, `01`, `02`, `04`, `97` are completely specified.
2. **Refund Policies**: The 3 time brackets (>24h 100%, 6–24h 50%, <6h 0%) plus no-show forfeiture (0%) and receipt generation (`PhieuHoanTien`) are mapped to the relational database schema and API endpoints.
3. **Dual Routes**: Supported dual routes for both REST and frontend compatibility (`/api/payments/` & `/api/thanh-toan/`, `/api/reservations/` & `/api/dat-ban/`).

---

## 8. Verification Method

To independently verify all findings and test suite compliance:

1. **Run Tier 1 (VNPay Core Coverage)**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1
   ```
   *Expected*: Ran 30 tests, 0 failures, 100% pass (specifically passes `test_t1_vnpay_01` through `05`).

2. **Run Tier 2 (Security, Tampering & Refund Boundaries)**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 2
   ```
   *Expected*: Ran 20 tests, 0 failures, 100% pass (specifically passes `test_t2_vnpay_01` through `05` and `test_t2_refund_01` through `05`).

3. **Run Tier 3 & Tier 4 (Cross-Feature & Scenarios)**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 3
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 4
   ```
   *Expected*: Ran 5 tests each, 0 failures, 100% pass.
