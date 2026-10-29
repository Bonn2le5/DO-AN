# Handoff Report: Milestone 2 Review & Adversarial Analysis
**Milestone**: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control  
**Agent**: Reviewer 2 (`m2_reviewer_2`)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2`  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)  
**Date**: 2026-10-14  

---

## Review Summary

**Verdict**: **REQUEST_CHANGES**

Milestone 2 implementation exhibits severe transactional scoping defects across multiple core services (`reservations/services.py`, `foods/services.py`, and `payments/services.py`). Specifically, pessimistic row locks (`select_for_update()`) intended to enforce Table Mutex concurrency control and atomic BOM inventory deductions were placed **outside** of active database transactions due to premature closing of `with transaction.atomic():` blocks. In a production PostgreSQL environment, this raises `django.db.transaction.TransactionManagementError: select_for_update cannot be used outside of a transaction.`, crashing table reservations and inventory deductions. Furthermore, the unit test suite masked these critical defects by mocking out `transaction.atomic` across all tests and omitting test coverage for `tao_dat_ban`.

---

## 1. Observation

Direct observations extracted from code inspection, tool execution, and authoritative tests:

1. **`moc-backend/reservations/services.py:tao_dat_ban` (lines 127–234)**:
   ```python
   127:     @classmethod
   128:     def tao_dat_ban(cls, *, nguoi_dung, du_lieu):
   129:         """
   130:         Phase 2: Chốt đặt bàn với Khóa bi quan select_for_update() và xác minh token Redis
   131:         """
   132:         with transaction.atomic():
   133:             danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])
   134: 
   135:         id_giu_ban = du_lieu.pop("id_giu_ban", None)
   ...
   149:         ban_locked = BanAn.objects.select_for_update().get(id=ban.id)
   ...
   159:         tranh_chap = DatBan.objects.select_for_update().filter(...)
   ...
   208:         dat_ban = DatBan.objects.create(...)
   ...
   219:         for item in danh_sach_item:
   220:             MonAnTrongDatBan.objects.create(...)
   ```
   - Observation: The `with transaction.atomic():` block begins at line 132 and only encloses line 133. Lines 135 to 234 drop back to the outer method scope.
   - At line 149, `BanAn.objects.select_for_update().get(id=ban.id)` is called outside of `transaction.atomic`.
   - At line 159, `DatBan.objects.select_for_update().filter(...)` is called outside of `transaction.atomic`.
   - Lines 208 and 220 insert `DatBan` and `MonAnTrongDatBan` in non-atomic autocommit mode.

2. **`moc-backend/foods/services.py:khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom` (lines 23–175)**:
   ```python
   23:         with transaction.atomic():
   24:             # 1. Kiểm tra tính Idempotent: nếu giao dịch này đã xuất kho rồi thì bỏ qua
   25:             giao_dich_cu = LichSuXuatNhapKho.objects.filter(...)
   ...
   31:                 return list(giao_dich_cu)
   32: 
   33: 
   34:         # 2. Chuẩn hóa danh sách món ăn & số lượng
   ...
   76:         nguyen_lieu_locked = list(
   77:             NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")
   78:         )
   ...
   101:         nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])
   ...
   103:         giao_dich = LichSuXuatNhapKho.objects.create(...)
   ```
   - Observation: In `khau_tru_nguyen_lieu_bom`, `with transaction.atomic():` starts at line 23 and terminates at line 31.
   - At line 76, `NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")` executes outside of any transaction block.
   - Stock deduction (`nl.save`) and audit logging (`LichSuXuatNhapKho.objects.create`) execute without transaction atomicity.
   - Identical defect in `hoan_tra_nguyen_lieu_bom` (lines 129–143): `with transaction.atomic():` terminates after line 134; line 142 executes `select_for_update()` outside a transaction.

3. **`moc-backend/payments/services.py:process_ipn` (lines 147–238)**:
   ```python
   147:         with transaction.atomic():
   148:             # 2. Check Order Existence
   149:             try:
   150:                 thanh_toan = ThanhToan.objects.select_for_update().select_related(...)
   154:                 return "01", "Order not found"
   155: 
   156: 
   157:         # 3. Check Amount (VNPay amount * 100)
   ...
   163:         if thanh_toan.trang_thai in (ThanhToan.TrangThai.THANH_CONG, ThanhToan.TrangThai.DA_HOAN_TIEN):
   ...
   171:         thanh_toan.trang_thai = ThanhToan.TrangThai.THANH_CONG
   173:         thanh_toan.save(...)
   ```
   - Observation: The transaction block terminates immediately at line 155.
   - The pessimistic row lock acquired on `ThanhToan` is committed and released before the amount check (line 158), before the idempotency check (line 163), and before persisting `thanh_toan.save()` and `db.save()`.

4. **`moc-backend/reservations/services.py:doi_trang_thai` (lines 248–261)**:
   ```python
   248:         if trang_thai_moi in [DatBan.TrangThai.DA_XAC_NHAN, DatBan.TrangThai.KHACH_DA_DEN]:
   249:             try:
   250:                 from foods.services import DichVuKho
   251:                 items = dat_ban.danh_sach_mon.all()
   252:                 if items.exists():
   253:                     DichVuKho.khau_tru_nguyen_lieu_bom(...)
   260:             except Exception:
   261:                 pass
   ```
   - Observation: When transitioning `DatBan` status, any failure in BOM deduction (e.g. `ValidationError` from inventory stockout) is caught with `except Exception:` and silently discarded via `pass`.

5. **`django.db.models.sql.compiler.SQLCompiler.as_sql` Verification**:
   - Direct verification execution via terminal:
     ```python
     with patch.object(connection.features, 'has_select_for_update', True):
         with patch.object(connection, 'get_autocommit', return_value=True):
             qs = BanAn.objects.select_for_update().filter(id=1)
             compiler = qs.query.get_compiler(connection.alias)
             compiler.as_sql()
     ```
   - Verbatim result:
     `SUCCESSFULLY REPRODUCED BUG: TransactionManagementError: select_for_update cannot be used outside of a transaction.`

6. **Test Suite Blindspot (`tests/e2e/test_milestone2_verification.py`)**:
   - `TestMilestone2TableConcurrency` contains only 3 tests, all targeting Phase 1 (`giu_ban_tam_thoi`). It contains zero tests for Phase 2 (`tao_dat_ban`).
   - `TestMilestone2VNPay` and `TestMilestone2BOMDeduction` universally patch `django.db.transaction.atomic` (lines 114, 130, 147, 164, 190, 431, 444, 477, 509), completely masking the transaction scoping failure.

7. **Properly Implemented Components**:
   - `./moc-backend/.venv/bin/python moc-backend/manage.py check` passes with 0 issues.
   - Phase 1 Redis hold (`DichVuDatBan.giu_ban_tam_thoi`) acquires `table_hold:{ban_id}:{ngay}:{gio}` with 600s TTL and returns HTTP 409 Conflict with `code: "BAN_DANG_BAN"` on collisions.
   - VNPay HMAC-SHA512 checksum implementation strictly matches `vnpay_oracle.py` down to the byte.
   - Refund calculation (`RefundService.calculate_refund`) strictly implements the 4 policy thresholds (>24h 100%, 6–24h 50%, <6h 0%, no-show 0%) and generates receipt code `RF-{ma_dat_ban}-{YYYYMMDD}`.
   - `PhieuHoanTien` model and table `phieu_hoan_tien` are created with bilingual property aliases.
   - BOM deduction sorts ingredient IDs in ascending order (`sorted_ids = sorted(tong_nhu_cau.keys())`) to prevent circular wait deadlocks.

---

## 2. Logic Chain

1. **Why `select_for_update()` outside `transaction.atomic` is a Critical Bug**:
   - According to Django's database specification and PostgreSQL backend implementation, `FOR UPDATE` queries lock rows until the end of the current transaction. If no transaction is active (autocommit mode), locking rows is a semantic contradiction because each statement commits immediately.
   - Django explicitly guards against this in `django.db.models.sql.compiler.SQLCompiler`:
     ```python
     if self.query.select_for_update and features.has_select_for_update:
         if not self.connection.in_atomic_block:
             raise TransactionManagementError("select_for_update cannot be used outside of a transaction.")
     ```
   - Because `tao_dat_ban`, `khau_tru_nguyen_lieu_bom`, and `hoan_tra_nguyen_lieu_bom` call `select_for_update()` outside `with transaction.atomic():`, calling any of these functions against a production PostgreSQL database will crash immediately with `TransactionManagementError`.

2. **Why Concurrency Mutex Guarantees are Defeated**:
   - The worker claimed in `handoff.md` that Phase 2 serializes booking requests by establishing a row-level mutex on `BanAn` using `select_for_update()`.
   - Because `BanAn.objects.select_for_update()` is not enclosed in a transaction with the subsequent conflict check and booking insertion, even if autocommit were allowed, the lock would be released the millisecond line 149 finishes.
   - Concurrent requests for the same table at the same time would not block each other, leading to double-booking.

3. **Why Silent Exception Swallowing in `doi_trang_thai` is Dangerous**:
   - When an order or reservation is confirmed, stock must be checked and deducted. If an ingredient is out of stock, `DichVuKho.khau_tru_nguyen_lieu_bom` correctly raises `ValidationError`.
   - However, `doi_trang_thai` catches `Exception` and executes `pass`. The reservation is marked confirmed in the database, while the kitchen has no ingredients to fulfill it, and the client receives no error notification.

4. **Why Unit Tests Passed Despite Critical Failures**:
   - The tests in `tests/e2e/test_milestone2_verification.py` mocked `django.db.transaction.atomic` and mocked `select_for_update`.
   - Mocking these methods replaced Django's transaction checks with dummy mocks, giving a false sense of test success.
   - No end-to-end test exercised `tao_dat_ban` directly.

---

## 3. Findings

### Finding 1: [Critical] [Integrity & Concurrency Violation] Phase 2 Table Booking Mutex Not Wrapped in DB Transaction
- **Where**: `moc-backend/reservations/services.py`, lines 132–234 (`DichVuDatBan.tao_dat_ban`)
- **What**: `with transaction.atomic():` closes after line 133. Lines 135–234 are executed outside the transaction block.
- **Why**: `BanAn.objects.select_for_update().get(id=ban.id)` and `DatBan.objects.select_for_update().filter(...)` execute outside an atomic block, raising `TransactionManagementError` in PostgreSQL and failing to serialize concurrent bookings.
- **Suggestion**: Decorate `tao_dat_ban` with `@classmethod` and `@transaction.atomic` (or indent the entire function body within `with transaction.atomic():`).

### Finding 2: [Critical] [Integrity & Concurrency Violation] BOM Material Inventory Deduction Not Wrapped in DB Transaction
- **Where**: `moc-backend/foods/services.py`, lines 23–116 (`khau_tru_nguyen_lieu_bom`) and lines 129–175 (`hoan_tra_nguyen_lieu_bom`)
- **What**: `with transaction.atomic():` closes after the initial idempotency query. All locking (`NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")`), stock deduction (`nl.save`), and audit log creation (`LichSuXuatNhapKho.objects.create`) occur outside an atomic transaction.
- **Why**: In PostgreSQL, raises `TransactionManagementError`. In addition, multiple inventory deductions and history creations are non-atomic, risking partial stock deductions if an unhandled error occurs mid-loop.
- **Suggestion**: Decorate `khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom` with `@staticmethod` and `@transaction.atomic` (or indent the entire function body within `with transaction.atomic():`).

### Finding 3: [Major] [Data Integrity] Silent Exception Swallowing in Reservation Status BOM Hook
- **Where**: `moc-backend/reservations/services.py`, lines 248–261 (`DichVuDatBan.doi_trang_thai`)
- **What**: Catches `Exception` and executes `pass` around `DichVuKho.khau_tru_nguyen_lieu_bom`.
- **Why**: Insufficient inventory errors (`ValidationError`) are silently swallowed. Reservations are marked as confirmed even when stock is exhausted.
- **Suggestion**: Remove `except Exception: pass`. Enclose the status change and BOM deduction in a unified `@transaction.atomic` block so that inventory stockout aborts the status transition and returns a clear validation error.

### Finding 4: [Major] [Concurrency & Idempotency] VNPay IPN Row Lock Released Prematurely Before State Mutation
- **Where**: `moc-backend/payments/services.py`, lines 147–238 (`VNPayService.process_ipn`)
- **What**: `with transaction.atomic():` closes immediately after line 154 (`ThanhToan.objects.select_for_update()...get(...)`).
- **Why**: The row lock on `ThanhToan` is committed and released before the amount check, before idempotency evaluation (`thanh_toan.trang_thai in (...)`), and before state mutations (`thanh_toan.save()`, `db.save()`, `dh.save()`). Rapid concurrent duplicate IPNs from VNPay can race past the idempotency check before the first has saved.
- **Suggestion**: Wrap the entire logic from order retrieval through state mutation in `with transaction.atomic():`.

### Finding 5: [Major] [Test Quality & Blindspot] Milestone 2 Test Suite Masks Transaction Scoping Bugs via Mocking
- **Where**: `tests/e2e/test_milestone2_verification.py`
- **What**:
  1. `TestMilestone2TableConcurrency` contains no test for `DichVuDatBan.tao_dat_ban`.
  2. Test cases universally patch `django.db.transaction.atomic`.
- **Why**: The test suite gave false confidence (26/26 passed) while the actual services would crash with `TransactionManagementError` in production PostgreSQL.
- **Suggestion**: Add un-mocked transaction tests verifying `tao_dat_ban` and `khau_tru_nguyen_lieu_bom` SQL generation or execution inside atomic blocks.

---

## 4. Adversarial Stress-Test Results

| # | Assumption / Scenario | Expected Behavior | Actual Behavior | Result |
|---|----------------------|-------------------|-----------------|--------|
| 1 | `select_for_update()` executed in `tao_dat_ban` without transaction wrapper | Django raises `TransactionManagementError` in PostgreSQL | Verified: `SQLCompiler.as_sql()` raises `TransactionManagementError` when `in_atomic_block` is False | **FAIL (Vulnerability)** |
| 2 | `select_for_update()` executed in `khau_tru_nguyen_lieu_bom` without transaction wrapper | Django raises `TransactionManagementError` in PostgreSQL | Verified: Raises `TransactionManagementError` when `in_atomic_block` is False | **FAIL (Vulnerability)** |
| 3 | Reservation confirmed when stockout occurs | Rejects confirmation with `ValidationError` | `doi_trang_thai` catches `Exception` and executes `pass`, silently confirming reservation | **FAIL (Vulnerability)** |
| 4 | Rapid duplicate VNPay IPNs for same transaction | Mutex serializes requests; second gets `02 Order already confirmed` | Lock released at line 155 before state update; concurrent requests race past idempotency check | **FAIL (Vulnerability)** |
| 5 | Phase 1 Redis Hold collision (two users hold same table/time) | Exactly 1 gets HTTP 200, second gets HTTP 409 `BAN_DANG_BAN` | Handled properly via atomic `cache.add` (SET NX EX 600) | **PASS** |
| 6 | VNPay IPN signature verification with tampered payload | Rejects with code 97 fail-fast without DB access | Handled properly via `VNPayService.verify_signature` | **PASS** |
| 7 | Deposit refund tier boundary at exactly 24.0h and 6.0h | 24.0h -> 50%, 6.0h -> 50%, 5.9h -> 0% | Handled properly via `RefundService.calculate_refund` | **PASS** |
| 8 | BOM ingredient locking order | Sorted ascending IDs prevents circular wait deadlock | IDs sorted via `sorted(tong_nhu_cau.keys())` | **PASS (Design correct, transaction wrapper broken)** |

---

## 5. Caveats

1. **Local Sandboxed Socket Execution**:
   - The test environment on macOS blocks direct TCP socket connections to `localhost:5432` (PostgreSQL) and `localhost:6379` (Redis).
   - The bug was verified directly through Django's `SQLCompiler` AST analysis and compiler execution, which reproduces the exact behavior of the PostgreSQL backend.
2. **VNPay Sandbox Gateway**:
   - Real-world callbacks from VNPay require public webhook exposure or tunneling (e.g. ngrok). In unit tests, HMAC parameter hashes were verified against `vnpay_oracle.py`.

---

## 6. Conclusion & Verdict

**Verdict**: **REQUEST_CHANGES**

The worker must address the following required fixes before Milestone 2 can be approved:
1. **Fix `reservations/services.py:tao_dat_ban`**: Decorate `tao_dat_ban` with `@transaction.atomic` (or indent lines 133–234 inside `with transaction.atomic():`).
2. **Fix `foods/services.py:khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom`**: Decorate both methods with `@transaction.atomic` (or indent method bodies inside `with transaction.atomic():`).
3. **Fix `payments/services.py:process_ipn`**: Extend the `with transaction.atomic():` block to cover lines 147 through 238 so that the `ThanhToan` row lock is held through the idempotency check and state persistence.
4. **Fix `reservations/services.py:doi_trang_thai`**: Remove `except Exception: pass` around `khau_tru_nguyen_lieu_bom` and wrap the state transition and BOM deduction in an atomic block.
5. **Update Test Suite `tests/e2e/test_milestone2_verification.py`**: Add tests for `DichVuDatBan.tao_dat_ban` and verify that `select_for_update` operates inside `transaction.atomic` without blanket patching.

---

## 7. Verification Method

To independently verify the findings and test fixes:

1. **Verify `select_for_update` Transaction Scoping**:
   ```bash
   ./moc-backend/.venv/bin/python -c "
   import sys, os
   sys.path.insert(0, 'moc-backend')
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
   import django
   django.setup()
   from django.db import connection
   from django.db.transaction import TransactionManagementError
   from reservations.models import BanAn
   from unittest.mock import patch

   with patch.object(connection.features, 'has_select_for_update', True):
       with patch.object(connection, 'get_autocommit', return_value=True):
           qs = BanAn.objects.select_for_update().filter(id=1)
           compiler = qs.query.get_compiler(connection.alias)
           try:
               compiler.as_sql()
               print('FAIL: select_for_update allowed outside transaction!')
           except TransactionManagementError:
               print('PASS: TransactionManagementError correctly triggered when outside transaction.')
   "
   ```

2. **Verify Indentation in Source Files**:
   - Inspect `moc-backend/reservations/services.py` lines 132–150.
   - Inspect `moc-backend/foods/services.py` lines 23–35 and 129–137.
   - Inspect `moc-backend/payments/services.py` lines 147–160.

3. **Run Regression Suites**:
   ```bash
   ./moc-backend/.venv/bin/python moc-backend/manage.py check
   ./moc-backend/.venv/bin/python tests/e2e/runner.py
   ./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py
   ```
