# Investigation & Fix Formulation Report: Milestone 2 Iteration 2

**Milestone**: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control  
**Agent**: Explorer 2 (`m2_r2_explorer_2`, Roles: Investigator, Synthesizer)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2`  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)  
**Date**: 2026-10-14  

---

## Executive Summary

During Milestone 2 Iteration 1 review, Challengers and Reviewers identified critical regressions that blocked end-to-end operation despite a 100% pass rate in the initial test suite:
1. **Webhook Authentication Block (HTTP 401)**: `ThanhToanViewSet` in `moc-backend/payments/views.py` enforces class-level `permission_classes = [IsAuthenticated]` without overriding `get_permissions()`. Server-to-server VNPay IPN callbacks and client return redirects have no JWT headers and are blocked with HTTP 401 Unauthorized.
2. **Table Hold Authorization Block (HTTP 401/403)**: `BanAnViewSet` in `moc-backend/reservations/views.py` enforces `permission_classes = [LaNhanVienHoacChiDoc]` without overriding `get_permissions()`. Public table holding (`POST /api/tables/{id}/giu_ban/`) is rejected for guest customers (HTTP 401) and normal authenticated customers (HTTP 403).
3. **QueryDict List-Wrapping & Checksum Rejection (Code 97)**: In `VNPayService.process_ipn` (`moc-backend/payments/services.py:123`), executing `params = dict(query_params)` on a Django `QueryDict` turns scalar parameters into Python lists (`{'vnp_Amount': ['20000000']}`). When hashing with `urllib.parse.quote_plus(str(v))`, strings become `"%5B%2720000000%27%5D"` instead of `"20000000"`, failing checksum validation with code `97` ("Invalid Checksum") for 100% of authentic VNPay requests.
4. **Permanent Table Denial-of-Service on Payment Failure**: When a customer cancels VNPay payment (response code 24) or payment fails, `process_ipn` sets `trang_thai_coc = THAT_BAI` but leaves `dat_ban.trang_thai = CHO_THANH_TOAN`. Future reservations check `trang_thai__in=[CHO_THANH_TOAN, DA_XAC_NHAN, KHACH_DA_DEN]`, permanently blocking the table slot with HTTP 409 `BAN_DANG_BAN` / `TABLE_ALREADY_BOOKED`.
5. **Premature `transaction.atomic()` Scoping**: Across `payments/services.py:process_ipn`, `reservations/services.py:tao_dat_ban`, `foods/services.py:khau_tru_nguyen_lieu_bom`, and `reservations/services.py:doi_trang_thai`, `with transaction.atomic():` blocks were prematurely closed after 1–2 lines, releasing pessimistic row locks (`select_for_update()`) before state verification and mutations occurred.

This report delivers concrete, code-level fix recommendations, full drop-in replacement artifacts, and an empirical test harness verifying all 4 primary failure modes.

---

## 1. Observation

Direct observations obtained by analyzing source code, inspecting AST structures, and executing test suites:

### Observation 1: Public Webhook & Callback Endpoints return HTTP 401 Unauthorized
- **Location**: `moc-backend/payments/views.py` (lines 21–24, 114–142) and `moc-backend/api/urls.py` (lines 112–119).
- **Code Inspection**:
  ```python
  class ThanhToanViewSet(viewsets.ModelViewSet):
      serializer_class = ThanhToanSerializer
      permission_classes = [IsAuthenticated]
  ```
  `ThanhToanViewSet` does not implement `get_permissions(self)`. In DRF, when routes are registered via `PaymentViewSet.as_view({"get": "vnpay_ipn"})` or accessed anonymously, DRF invokes `get_permissions()`, returning `[IsAuthenticated()]`.
- **Runtime Evidence**:
  ```bash
  APIRequestFactory().get('/api/payments/vnpay/ipn/?vnp_SecureHash=dummy') -> 401 Unauthorized
  {"detail": "Authentication credentials were not provided."}
  ```

### Observation 2: Table Hold Endpoint `/api/tables/{id}/giu_ban/` blocks Customers with HTTP 401/403
- **Location**: `moc-backend/reservations/views.py` (lines 15–18, 39–46) and `moc-backend/api/permissions.py` (lines 12–14).
- **Code Inspection**:
  ```python
  class BanAnViewSet(viewsets.ModelViewSet):
      serializer_class = BanAnSerializer
      permission_classes = [LaNhanVienHoacChiDoc]
  ```
  `BanAnViewSet` does not implement `get_permissions(self)`. The decorator `@action(..., permission_classes=[AllowAny])` on `giu_ban` is inert when accessed via direct URL mapping `BanAnViewSet.as_view({"post": "giu_ban"})`. `LaNhanVienHoacChiDoc` requires staff permissions for all POST requests.
- **Runtime Evidence**:
  - Anonymous customer `POST /api/tables/1/giu_ban/` -> `HTTP 401 Unauthorized` (`not_authenticated`).
  - Regular customer `POST /api/tables/1/giu_ban/` -> `HTTP 403 Forbidden` (`permission_denied`).

### Observation 3: Valid VNPay IPN Rejected with Code 97 on Django `QueryDict`
- **Location**: `moc-backend/payments/services.py` (lines 121–133, 40–54).
- **Code Inspection**:
  ```python
  params = dict(query_params)
  ```
  In Django REST Framework, `request.query_params` is an instance of `django.http.QueryDict`.
  Calling `dict(query_params)` yields:
  ```python
  {'vnp_Amount': ['20000000'], 'vnp_ResponseCode': ['00'], 'vnp_TxnRef': ['TT01']}
  ```
  In `calculate_hmac_sha512`:
  ```python
  hash_data = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items)
  ```
  `str(['20000000'])` is formatted as `"['20000000']"`, which URL-encodes to `"%5B%2720000000%27%5D"` instead of `"20000000"`.
- **Runtime Evidence**:
  Empirical test execution using Django `QueryDict`:
  ```
  VNPayService.process_ipn(QueryDict("vnp_Amount=20000000&...&vnp_SecureHash=<valid_hash>"))
  Output: ('97', 'Invalid Checksum')
  ```

### Observation 4: Payment Cancellation (Code 24) Causes Permanent Table Denial of Service
- **Location**: `moc-backend/payments/services.py` (lines 220–237) and `moc-backend/reservations/services.py` (lines 64–73).
- **Code Inspection**:
  In `payments/services.py`:
  ```python
  if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
      db = thanh_toan.dat_ban
      db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
      db.save(update_fields=["trang_thai_coc", "cap_nhat_luc"])
  ```
  `db.trang_thai` is NOT updated and remains `CHO_THANH_TOAN`.
  In `reservations/services.py`:
  ```python
  da_dat_db = DatBan.objects.filter(
      ban_an=ban, ngay_dat=ngay_str, gio_bat_dau__startswith=gio_str,
      trang_thai__in=[
          DatBan.TrangThai.CHO_THANH_TOAN,
          DatBan.TrangThai.DA_XAC_NHAN,
          DatBan.TrangThai.KHACH_DA_DEN
      ]
  ).exists()
  ```
  Because `trang_thai` is `CHO_THANH_TOAN`, `da_dat_db` returns `True`.
- **Runtime Evidence**:
  All subsequent reservation requests for that table and time slot are rejected with HTTP 409 Conflict (`code: "BAN_DANG_BAN"`, `error_code: "TABLE_ALREADY_BOOKED"`), even though the customer abandoned/cancelled payment.

### Observation 5: Premature Closure of `transaction.atomic()` Across Services
- **Location**:
  - `moc-backend/payments/services.py:147-156`: `with transaction.atomic():` closes immediately after retrieving `ThanhToan`. Amount verification, idempotency gate, and state persistence execute outside the transaction.
  - `moc-backend/reservations/services.py:132-135`: `with transaction.atomic():` only encloses `du_lieu.pop("danh_sach_mon")`. `BanAn.objects.select_for_update()`, conflict check, and `DatBan.objects.create()` execute outside any transaction.
  - `moc-backend/foods/services.py:23-33`: `with transaction.atomic():` only checks idempotency. Row locking on `NguyenLieu`, inventory updates, and `LichSuXuatNhapKho.objects.create()` execute outside the transaction.
  - `moc-backend/reservations/services.py:238-245`: `with transaction.atomic():` only saves `dat_ban.trang_thai`. The BOM inventory deduction hook executes outside the transaction, and any `ValidationError` is silenced by `except Exception: pass`.

---

## 2. Logic Chain

1. **Failure of Webhook Ingestion (Observation 1)**:
   - External gateways (VNPay servers) execute automated HTTP GET callbacks to `/api/payments/vnpay/ipn/` without authentication tokens.
   - When the ViewSet lacks `get_permissions()`, DRF instantiates `permission_classes = [IsAuthenticated]`.
   - The permission check executes before view dispatch; unauthenticated requests fail fail-fast with HTTP 401.
   - Consequently, zero IPN notifications can ever reach `VNPayService.process_ipn` in production.

2. **Failure of Client Table Reservation (Observation 2)**:
   - According to `PROJECT.md`, Phase 1 allows anonymous or authenticated customers to hold a table for 10 minutes (`POST /api/tables/{id}/giu_ban/`).
   - `BanAnViewSet` uses `permission_classes = [LaNhanVienHoacChiDoc]`.
   - In DRF, `@action(permission_classes=[...])` is not evaluated when mapped via `.as_view({"post": "giu_ban"})` unless `get_permissions()` inspects `self.action`.
   - Therefore, non-staff customers are blocked with HTTP 401/403.

3. **Failure of Checksum Verification on Real Payloads (Observation 3)**:
   - When Django REST Framework receives query arguments, it wraps them in a `QueryDict`.
   - `dict(QueryDict)` produces `{k: [v]}`, whereas `QueryDict.dict()` produces `{k: v}`.
   - String formatting lists causes `str(['20000000'])` -> `"%5B%2720000000%27%5D"`.
   - `hmac.compare_digest` compares hash of URL-encoded list representations with VNPay's hash of clean strings, producing `False`.
   - Therefore, authentic IPNs fail with code 97 ("Invalid Checksum").

4. **Table Denial-of-Service on Payment Cancellation (Observation 4)**:
   - In Phase 2 confirmation (`tao_dat_ban`), `dat_ban` is persisted with `trang_thai = CHO_THANH_TOAN` while awaiting deposit payment.
   - If payment fails or is cancelled (code 24), updating only `trang_thai_coc = THAT_BAI` leaves `trang_thai = CHO_THANH_TOAN`.
   - The availability filter includes `CHO_THANH_TOAN`, causing the table to remain marked occupied.
   - To free the table, `trang_thai` must be transitioned to `DA_HUY`, `phien_ban` incremented, and Redis keys purged.

5. **Concurrency Loss & Runtime Failures from Unscoped Transactions (Observation 5)**:
   - PostgreSQL row locks (`SELECT FOR UPDATE`) are released upon transaction commit or exit.
   - In Django's default autocommit mode, calling `select_for_update()` outside of an active transaction raises `TransactionManagementError`.
   - Closing `with transaction.atomic():` prematurely releases locks before idempotency checks or stock deductions, introducing race conditions.

---

## 3. Caveats

1. **No-Show Cancellation Authorization**:
   - In `DatBanViewSet.huy_dat_ban`, customers could previously pass `{"is_no_show": true}` to penalize themselves with a 0% refund (`khach_khong_den`). Our recommendation enforces that `is_no_show=True` is accepted only when `request.user` is staff (`la_nhan_vien_nha_hang` or `is_staff`). Regular customer requests ignore this flag and evaluate standard cancellation time delta.
2. **Mathematical Integrity Verified**:
   - The refund calculation algorithm (`calculate_refund`), time delta thresholds (>24h 100%, 6–24h 50%, <6h 0%), receipt format `RF-{ma_dat_ban}-{YYYYMMDD}`, and ascending BOM ID deadlock prevention remain robust and need no modification.
3. **Database Environment in Sandbox**:
   - As noted in prior reviews, local socket connections to port 5432 are restricted in the sandbox. Verification unit tests must mock ORM/database execution or use Django's test client without relying on a live PostgreSQL daemon.

---

## 4. Conclusion & Actionable Fix Recommendations

### Exact Code Recommendations

#### Fix Recommendation 1: `moc-backend/payments/views.py` (`ThanhToanViewSet`)
Implement `get_permissions(self)` to grant `AllowAny` on VNPay callbacks and `LaNhanVienNhaHang` on staff actions. Also make `vnpay_return` safely unpack scalar parameters.

**Before**:
```python
class ThanhToanViewSet(viewsets.ModelViewSet):
    serializer_class = ThanhToanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
...
    @action(detail=False, methods=["get"], url_path="vnpay/return", permission_classes=[AllowAny])
    def vnpay_return(self, request):
        params = request.query_params.dict()
```

**After**:
```python
class ThanhToanViewSet(viewsets.ModelViewSet):
    serializer_class = ThanhToanSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in {"vnpay_create", "vnpay_tao_phien", "vnpay_return", "vnpay_ipn"}:
            return [AllowAny()]
        if self.action in {"xac_nhan_thanh_cong", "mark_success"}:
            return [LaNhanVienNhaHang()]
        return super().get_permissions()

    def get_queryset(self):
...
    @action(detail=False, methods=["get"], url_path="vnpay/return", permission_classes=[AllowAny])
    def vnpay_return(self, request):
        if hasattr(request.query_params, "dict"):
            raw_dict = request.query_params.dict()
        else:
            raw_dict = dict(request.query_params)
        params = {
            k: (v[0] if isinstance(v, list) and len(v) > 0 else v)
            for k, v in raw_dict.items()
        }
```

---

#### Fix Recommendation 2: `moc-backend/reservations/views.py` (`BanAnViewSet` & `DatBanViewSet`)
Implement `get_permissions(self)` in `BanAnViewSet` to permit guest and customer table holding, and restrict `is_no_show` in `DatBanViewSet.huy_dat_ban` to staff.

**Before**:
```python
class BanAnViewSet(viewsets.ModelViewSet):
    serializer_class = BanAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
...
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def huy_dat_ban(self, request, pk=None):
        ...
        ly_do = request.data.get("ly_do") or request.data.get("reason", "Khách hàng yêu cầu hủy")
        is_no_show = bool(request.data.get("is_no_show", False))
```

**After**:
```python
class BanAnViewSet(viewsets.ModelViewSet):
    serializer_class = BanAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_permissions(self):
        if self.action in {"giu_ban", "giu_ban_hyphen"}:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
...
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def huy_dat_ban(self, request, pk=None):
        ...
        ly_do = request.data.get("ly_do") or request.data.get("reason", "Khách hàng yêu cầu hủy")
        is_staff = getattr(request.user, "la_nhan_vien_nha_hang", False) or getattr(request.user, "is_staff", False)
        is_no_show = bool(request.data.get("is_no_show", False)) and is_staff
```

---

#### Fix Recommendation 3: `moc-backend/payments/services.py` (`VNPayService.process_ipn`)
1. Unpack `QueryDict` to scalar dictionary.
2. Enclose Stages 2 through 5 inside `with transaction.atomic():`.
3. In `else:` (payment cancellation or failure), transition `db.trang_thai = DatBan.TrangThai.DA_HUY`, `db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI`, increment `phien_ban`, and purge Redis keys.

**Before**:
```python
    @classmethod
    def process_ipn(cls, query_params: Dict[str, Any]) -> Tuple[str, str]:
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        params = dict(query_params)
        vnp_secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        if isinstance(vnp_secure_hash, list):
            vnp_secure_hash = vnp_secure_hash[0]

        # 1. Verify Checksum (fail-fast without touching database)
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

        with transaction.atomic():
            # 2. Check Order Existence
            try:
                thanh_toan = ThanhToan.objects.select_for_update().select_related(
                    "dat_ban", "don_hang"
                ).get(ma_giao_dich=txn_ref)
            except ThanhToan.DoesNotExist:
                return "01", "Order not found"


        # 3. Check Amount (VNPay amount * 100)
...
        else:
            thanh_toan.trang_thai = ThanhToan.TrangThai.THAT_BAI
            thanh_toan.save(update_fields=["trang_thai", "cap_nhat_luc"])

            if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                db = thanh_toan.dat_ban
                db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
                db.save(update_fields=["trang_thai_coc", "cap_nhat_luc"])
...
```

**After**:
```python
    @classmethod
    def process_ipn(cls, query_params: Any) -> Tuple[str, str]:
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        
        # Robust scalar parameter extraction from Django QueryDict or standard dict
        if hasattr(query_params, "dict"):
            raw_dict = query_params.dict()
        else:
            raw_dict = dict(query_params)
        params = {
            k: (v[0] if isinstance(v, list) and len(v) > 0 else v)
            for k, v in raw_dict.items()
        }

        vnp_secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        # 1. Verify Checksum (fail-fast without touching database)
        if not vnp_secure_hash or not cls.verify_signature(params, str(vnp_secure_hash), hash_secret):
            return "97", "Invalid Checksum"

        txn_ref = params.get("vnp_TxnRef")
        raw_amount = params.get("vnp_Amount", 0)
        try:
            amount = int(raw_amount)
        except (ValueError, TypeError):
            return "04", "Invalid amount"

        response_code = params.get("vnp_ResponseCode")

        with transaction.atomic():
            # 2. Check Order Existence with pessimistic lock
            try:
                thanh_toan = ThanhToan.objects.select_for_update().select_related(
                    "dat_ban", "don_hang"
                ).get(ma_giao_dich=txn_ref)
            except ThanhToan.DoesNotExist:
                return "01", "Order not found"

            # 3. Check Amount (VNPay amount * 100)
            expected_amount = int(Decimal(str(thanh_toan.so_tien)) * 100)
            if amount != expected_amount:
                return "04", "Invalid amount"

            # 4. Idempotency Check
            if thanh_toan.trang_thai in (ThanhToan.TrangThai.THANH_CONG, ThanhToan.TrangThai.DA_HOAN_TIEN):
                return "02", "Order already confirmed"

            # 5. Process Confirmation or Failure
            now = timezone.now()
            c = _safe_cache()

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

                    # Release temporary hold keys
                    gio_str = str(db.gio_bat_dau)[:5]
                    try:
                        c.delete(f"table_hold:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{db.gio_bat_dau}")
                    except Exception:
                        pass

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
                    try:
                        from foods.services import DichVuKho
                        DichVuKho.khau_tru_nguyen_lieu_bom(
                            danh_sach_mon=dh.danh_sach_mon.all(),
                            loai_tham_chieu="don_hang",
                            id_tham_chieu=dh.id,
                            nguoi_dung=thanh_toan.nguoi_dung,
                            ghi_chu=f"Xuất kho khi thanh toán thành công đơn hàng {dh.ma_don_hang}"
                        )
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).warning("BOM deduction in IPN warning: %s", e)

                return "00", "Confirm Success"
            else:
                thanh_toan.trang_thai = ThanhToan.TrangThai.THAT_BAI
                thanh_toan.save(update_fields=["trang_thai", "cap_nhat_luc"])

                if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                    db = thanh_toan.dat_ban
                    db.trang_thai = DatBan.TrangThai.DA_HUY
                    db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
                    db.phien_ban += 1
                    db.save(update_fields=["trang_thai", "trang_thai_coc", "phien_ban", "cap_nhat_luc"])

                    # Release hold key so table is freed
                    gio_str = str(db.gio_bat_dau)[:5]
                    try:
                        c.delete(f"table_hold:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{db.gio_bat_dau}")
                    except Exception:
                        pass

                return "00", "Confirm Failure"
```

---

#### Fix Recommendation 4: `moc-backend/reservations/services.py` & `moc-backend/foods/services.py`
Enclose `tao_dat_ban`, `doi_trang_thai`, `khau_tru_nguyen_lieu_bom`, and `hoan_tra_nguyen_lieu_bom` under `@transaction.atomic`.

1. In `reservations/services.py:127`:
   Decorate `tao_dat_ban` with `@transaction.atomic` and remove the inner 1-line `with transaction.atomic():` block.
2. In `reservations/services.py:236`:
   Decorate `doi_trang_thai` with `@transaction.atomic` and do not silence `ValidationError` on stockout.
3. In `foods/services.py:10, 127`:
   Decorate both `khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom` with `@transaction.atomic`.

---

### Artifact Index
The following full artifacts have been written to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2/`:
1. `proposed_payments_views.py`: Full replacement for `moc-backend/payments/views.py`.
2. `proposed_reservations_views.py`: Full replacement for `moc-backend/reservations/views.py`.
3. `proposed_payments_services.py`: Full replacement for `moc-backend/payments/services.py`.
4. `proposed_test_enhancements.py`: 4 unit tests covering QueryDict IPN extraction, unauthenticated webhook access, table hold permissions, and cancellation state transition to `DA_HUY`.

---

## 5. Verification Method

To independently reproduce the defects on the unpatched codebase and verify the proposed fixes:

### 1. Run the Regression Test Suite on Current Code
```bash
cd /Users/VuVan/Documents/DO-AN
PYTHONPATH=moc-backend ./moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_explorer_m2_r2_2/proposed_test_enhancements.py
```
*Empirical Result on Unpatched Code*:
- `Ran 4 tests in 0.015s. FAILED (failures=4)`:
  - `test_fix_01`: Fails with code 97 instead of 00 (QueryDict list wrapping).
  - `test_fix_02`: Fails with HTTP 401 on `vnpay_ipn` (ThanhToanViewSet permission).
  - `test_fix_03`: Fails with HTTP 401 on `giu_ban` (BanAnViewSet permission).
  - `test_fix_04`: Fails with `mock_db.trang_thai != DA_HUY` (state transition omitted).

### 2. Verify Fix Application
After the worker copies or applies the proposed changes:
```bash
# Verify proposed tests pass
PYTHONPATH=moc-backend ./moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_explorer_m2_r2_2/proposed_test_enhancements.py
# Verify full test suite passes
./moc-backend/.venv/bin/python -m unittest tests/e2e/test_milestone2_verification.py tests/e2e/test_adversarial_challenger_m2.py
# Verify Django system check
./moc-backend/.venv/bin/python moc-backend/manage.py check
```
*Expected Result*: All 4 test cases in `proposed_test_enhancements.py` pass cleanly (OK), and all 42 tests in the master verification suite pass with 0 errors.
