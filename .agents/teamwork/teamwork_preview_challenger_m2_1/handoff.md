# Adversarial Challenge Report: Milestone 2 Verification

**Milestone**: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control  
**Challenger**: `m2_challenger_1` (Empirical Challenger)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m2_1`  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)  
**Verdict**: **REQUEST_CHANGES**  
**Overall Risk Assessment**: **HIGH**  

---

## 1. Observation

Direct observations obtained by executing test harnesses, inspecting source code, and analyzing runtime outputs:

### Observation 1: Public Webhook & Callback Endpoints return HTTP 401 Unauthorized
- **Location**: `moc-backend/payments/views.py` (lines 21–23, 114–142) and `moc-backend/api/urls.py` (lines 112–119).
- **Code**:
  ```python
  class ThanhToanViewSet(viewsets.ModelViewSet):
      serializer_class = ThanhToanSerializer
      permission_classes = [IsAuthenticated]
  ```
  `ThanhToanViewSet` does not define `get_permissions()`. When mapped via `path("payments/vnpay/ipn/", PaymentViewSet.as_view({"get": "vnpay_ipn"}))`, DRF applies class-level `permission_classes = [IsAuthenticated]`.
- **Runtime Output**:
  ```bash
  APIRequestFactory().get('/api/payments/vnpay/ipn/') -> 401 Unauthorized
  {"detail": "Authentication credentials were not provided."}
  APIRequestFactory().get('/api/payments/vnpay/return/') -> 401 Unauthorized
  APIRequestFactory().post('/api/payments/vnpay/create/', {}) -> 401 Unauthorized
  ```

### Observation 2: Valid VNPay IPN rejected with Code 97 on Django `QueryDict`
- **Location**: `moc-backend/payments/services.py` (lines 123, 40–54).
- **Code**:
  ```python
  params = dict(query_params)
  ```
  When `query_params` is a Django `QueryDict` (from `request.query_params`), `dict(query_params)` converts values into Python lists (`{'vnp_Amount': ['20000000'], ...}`).
  In `calculate_hmac_sha512`:
  ```python
  hash_data = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items)
  ```
  `str(['20000000'])` formats as `"%5B%2720000000%27%5D"` instead of `"20000000"`.
- **Runtime Output**:
  ```
  VNPayService.process_ipn(QueryDict('vnp_Amount=20000000&...&vnp_SecureHash=<valid_hash>'))
  Result: ('97', 'Invalid Checksum')
  ```

### Observation 3: Premature `transaction.atomic()` exit in `process_ipn` releasing row lock
- **Location**: `moc-backend/payments/services.py` (lines 147–173).
- **Code**:
  ```python
  with transaction.atomic():
      try:
          thanh_toan = ThanhToan.objects.select_for_update().select_related("dat_ban", "don_hang").get(ma_giao_dich=txn_ref)
      except ThanhToan.DoesNotExist:
          return "01", "Order not found"

  # Unindented outside transaction.atomic()!
  expected_amount = int(Decimal(str(thanh_toan.so_tien)) * 100)
  if amount != expected_amount:
      return "04", "Invalid amount"

  if thanh_toan.trang_thai in (ThanhToan.TrangThai.THANH_CONG, ThanhToan.TrangThai.DA_HOAN_TIEN):
      return "02", "Order already confirmed"

  if response_code == "00":
      thanh_toan.trang_thai = ThanhToan.TrangThai.THANH_CONG
      thanh_toan.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])
  ```
  The row-level lock acquired by `select_for_update()` is released at line 155 upon exiting the `with` block, leaving the idempotency check and `thanh_toan.save()` completely unguarded against concurrent race conditions.

### Observation 4: Customer Cancellation (Code 24) leaves `DatBan` blocking table in DB
- **Location**: `moc-backend/payments/services.py` (lines 223–227) and `moc-backend/reservations/services.py` (lines 64–73).
- **Code**:
  ```python
  # payments/services.py line 223
  if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
      db = thanh_toan.dat_ban
      db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
      db.save(update_fields=["trang_thai_coc", "cap_nhat_luc"])
  ```
  `db.trang_thai` is NOT transitioned to `DA_HUY`. It remains `CHO_THANH_TOAN`.
  In `reservations/services.py`:
  ```python
  da_dat_db = DatBan.objects.filter(
      ban_an=ban, ngay_dat=ngay_str, gio_bat_dau__startswith=gio_str,
      trang_thai__in=[DatBan.TrangThai.CHO_THANH_TOAN, DatBan.TrangThai.DA_XAC_NHAN, DatBan.TrangThai.KHACH_DA_DEN]
  ).exists()
  ```
  Since `trang_thai` is `CHO_THANH_TOAN`, `da_dat_db` returns `True`, permanently blocking all future reservations for that table slot with HTTP 409 `BAN_DANG_BAN`.

### Observation 5: Primary Table Hold Endpoint `/api/tables/{id}/giu_ban/` blocks Customers
- **Location**: `moc-backend/reservations/views.py` (lines 15–17, 39–41) and `moc-backend/api/permissions.py` (lines 12–14).
- **Code**:
  ```python
  class BanAnViewSet(viewsets.ModelViewSet):
      serializer_class = BanAnSerializer
      permission_classes = [LaNhanVienHoacChiDoc]
  ```
  `LaNhanVienHoacChiDoc` restricts all non-safe methods (such as `POST`) to staff users only (`is_staff` or `la_nhan_vien_nha_hang`). `BanAnViewSet` does not implement `get_permissions()`.
- **Runtime Output**:
  ```bash
  Anonymous POST /api/tables/1/giu_ban/ -> 401 Unauthorized
  Normal Customer POST /api/tables/1/giu_ban/ -> 403 Forbidden
  ```

### Observation 6: Premature `transaction.atomic()` exits in `tao_dat_ban` and `khau_tru_nguyen_lieu_bom`
- **Location**: `moc-backend/reservations/services.py` (lines 132–150) and `moc-backend/foods/services.py` (lines 23–77).
- **Code**:
  In `tao_dat_ban`:
  ```python
  with transaction.atomic():
      danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])

  # Line 135 is outside atomic block!
  ban_locked = BanAn.objects.select_for_update().get(id=ban.id)
  ```
  In `khau_tru_nguyen_lieu_bom`:
  ```python
  with transaction.atomic():
      giao_dich_cu = LichSuXuatNhapKho.objects.filter(...)
      if giao_dich_cu.exists(): return list(giao_dich_cu)

  # Line 34 is outside atomic block!
  nguyen_lieu_locked = list(NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id"))
  ```

---

## 2. Logic Chain

1. **Failure of Webhook Ingestion (Observation 1)**:
   - External gateways (VNPay) connect anonymously over HTTP without an `Authorization: Bearer <JWT>` header.
   - Because `ThanhToanViewSet` enforces `[IsAuthenticated]` without overriding `get_permissions()` for actions `vnpay_ipn`, `vnpay_return`, and `vnpay_create`, DRF halts processing at the permission check layer and returns HTTP 401.
   - Therefore, no IPN payment confirmation can ever reach `VNPayService.process_ipn` in production.

2. **Failure of Checksum Verification on Real Payloads (Observation 2)**:
   - When an HTTP GET request hits `/api/payments/vnpay/ipn/`, Django provides query arguments via `request.query_params`, an instance of `QueryDict`.
   - Calling `dict(QueryDict)` does not flatten single values; it wraps every value in a list (`{'vnp_Amount': ['20000000']}`).
   - Hashing stringified lists produces `%5B%2720000000%27%5D` instead of `20000000`, causing `hmac.compare_digest` to evaluate to `False`.
   - Therefore, all authentic VNPay IPN requests fail fail-fast verification with code 97 ("Invalid Checksum").

3. **Loss of Concurrency Mutual Exclusion (Observation 3, 6)**:
   - In PostgreSQL, row-level locks acquired with `SELECT FOR UPDATE` are held only until the enclosing database transaction terminates.
   - Because `with transaction.atomic():` is closed before evaluating idempotency and persisting the state changes, the row lock is released immediately.
   - Two concurrent IPN deliveries or two concurrent bookings can acquire locks sequentially, release them, evaluate non-terminal states simultaneously, and commit duplicate mutations.

4. **Table Denial-of-Service on Payment Cancellation (Observation 4)**:
   - If a customer cancels payment at the VNPay payment gateway (code 24), the reservation's deposit status is set to `THAT_BAI`, but the reservation status (`trang_thai`) remains `CHO_THANH_TOAN`.
   - `DichVuDatBan.giu_ban_tam_thoi` checks if any reservation exists with `trang_thai__in=[CHO_THANH_TOAN, DA_XAC_NHAN, KHACH_DA_DEN]`.
   - The canceled booking matches this filter, causing all subsequent customer requests for that table and time slot to be rejected with HTTP 409 Conflict (`BAN_DANG_BAN`).

5. **Client Blocking on Table Hold (Observation 5)**:
   - The contract in `PROJECT.md` defines `POST /api/tables/{id}/giu_ban/` as the Phase 1 temporary reservation hold.
   - `BanAnViewSet` uses `LaNhanVienHoacChiDoc`, which forbids POST requests from anonymous users (HTTP 401) and normal authenticated customers (HTTP 403).
   - Only staff can invoke this endpoint, breaking the customer table booking flow.

---

## 3. Caveats

1. **Robust Areas Verified**:
   - The core mathematical engine of `RefundService.calculate_refund` is 100% correct across all exact boundary conditions (`24.00000001h` -> 100%, `24.0h` -> 50%, `6.0h` -> 50%, `5.99999h` -> 0%, `0.0h` -> 0%, negative delta -> 0%, no-show -> 0%).
   - Financial conservation (`so_tien_hoan + so_tien_phat == so_tien_coc_goc`) is mathematically preserved across 500 randomized trials with zero rounding leakage.
   - HMAC-SHA512 tampering resistance is verified: altering a single character in any parameter or in the hash correctly triggers rejection.
   - Unicode Vietnamese diacritics and special characters are handled identically to the authoritative specification oracle.
2. **Local PostgreSQL Socket Constraint**:
   - As documented by Worker 1, direct TCP connections to localhost 5432 are restricted in sandboxed environments without bypass. Tests were constructed using DRF test client, `APIRequestFactory`, and mocked DB queries without relying on live network daemons.

---

## 4. Conclusion & Actionable Mitigations

### Verdict: **REQUEST_CHANGES**

The implementation demonstrates solid core algorithms (HMAC calculation, refund formula, sorted BOM IDs), but contains **2 Critical** and **4 High** architectural defects that prevent successful end-to-end payment processing, table reservation, and webhook reception.

### Concrete Action Items for Worker:

1. **Fix `ThanhToanViewSet` Permissions (`moc-backend/payments/views.py`)**:
   Add `get_permissions(self)` to `ThanhToanViewSet`:
   ```python
   def get_permissions(self):
       if self.action in {"vnpay_create", "vnpay_tao_phien", "vnpay_return", "vnpay_ipn"}:
           return [AllowAny()]
       return super().get_permissions()
   ```

2. **Fix `QueryDict` Parameter Unpacking in `VNPayService.process_ipn` (`moc-backend/payments/services.py`)**:
   Unpack `query_params` to scalar strings before computing hash or calling `verify_signature`:
   ```python
   if hasattr(query_params, "dict"):
       params = query_params.dict()
   else:
       params = {k: (v[0] if isinstance(v, list) else v) for k, v in query_params.items()}
   ```

3. **Expand `transaction.atomic()` Scope in `process_ipn` (`moc-backend/payments/services.py`)**:
   Enclose the order lookup, idempotency evaluation, and status save inside a single `with transaction.atomic():` block so that `select_for_update()` lock is held until the transaction commits.

4. **Transition `DatBan` to `DA_HUY` on Customer Payment Failure (`moc-backend/payments/services.py`)**:
   In `process_ipn` under `else` (non-zero response code like 24):
   ```python
   if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
       db = thanh_toan.dat_ban
       db.trang_thai = DatBan.TrangThai.DA_HUY
       db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
       db.save(update_fields=["trang_thai", "trang_thai_coc", "cap_nhat_luc"])
   ```

5. **Fix `BanAnViewSet` Permissions (`moc-backend/reservations/views.py`)**:
   Add `get_permissions(self)` to `BanAnViewSet`:
   ```python
   def get_permissions(self):
       if self.action in {"giu_ban", "giu_ban_hyphen"}:
           return [AllowAny()]
       return super().get_permissions()
   ```

6. **Fix Transaction Indentation in `tao_dat_ban` and `khau_tru_nguyen_lieu_bom`**:
   Indent the entire booking creation (`select_for_update`, verification, and DB creates) and inventory deduction logic under `with transaction.atomic():`.

---

## 5. Verification Method

To independently reproduce all 6 findings and verify the stress test suite:

1. **Run the Milestone 2 Adversarial Challenger Suite**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   ./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py
   ```
   *Expected Output*:
   - Ran 16 tests in ~0.07s.
   - All 16 tests PASS (each test empirically catches and displays the confirmed findings).

2. **Run Master Verification Suite**:
   ```bash
   ./moc-backend/.venv/bin/python -m unittest tests/e2e/test_milestone2_verification.py tests/e2e/test_adversarial_challenger_m2.py
   ```
   *Expected Output*: Ran 42 tests in ~0.25s, OK.
