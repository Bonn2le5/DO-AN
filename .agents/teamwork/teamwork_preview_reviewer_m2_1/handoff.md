# Review & Adversarial Challenge Report: Milestone 2

**Milestone**: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control  
**Reviewer**: `m2_reviewer_1` (Roles: Reviewer, Critic)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1`  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)  
**Date**: 2026-10-14  

---

## 1. Review Summary

**Verdict**: **REQUEST_CHANGES**  
**Overall Risk Assessment**: **HIGH**

While the cryptographic implementation of VNPay 2.1.0 HMAC-SHA512 checksums, URL formatting, bilingual dual routing, and deposit refund mathematical rules are accurately implemented and adhere to specifications, a **Critical System Defect** was uncovered during adversarial review:

> **CRITICAL DEFECT**: In five separate core methods (`DichVuDatBan.tao_dat_ban`, `DichVuKho.khau_tru_nguyen_lieu_bom`, `DichVuKho.hoan_tra_nguyen_lieu_bom`, `VNPayService.process_ipn`, and `DichVuDatBan.doi_trang_thai`), `with transaction.atomic():` blocks were prematurely closed after only 1–4 lines. Consequently, all subsequent `select_for_update()` queries and database mutations execute outside any active transaction. In Django with autocommit enabled (the project configuration), calling `select_for_update()` outside of a transaction raises `django.db.transaction.TransactionManagementError: select_for_update cannot be used outside of a transaction.`! In a live PostgreSQL environment, all reservation creations (`POST /api/reservations/`) and inventory deductions will crash immediately with HTTP 500. Furthermore, in `test_milestone2_verification.py`, `transaction.atomic` was globally mocked out with `MagicMock`, masking this critical runtime defect, while Phase 2 booking confirmation (`tao_dat_ban`) had zero test coverage.

---

## 2. Findings

### [Critical] Finding 1: Premature Closure of `transaction.atomic()` Causing `TransactionManagementError` and Broken Pessimistic Locking

- **What**: In multiple service methods, `with transaction.atomic():` was improperly scoped to only a couple of lines, leaving `select_for_update()` queries and database mutations executing outside an active transaction.
- **Where**:
  1. `moc-backend/reservations/services.py:132-134` (`tao_dat_ban`):
     ```python
     with transaction.atomic():
         danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])

     id_giu_ban = du_lieu.pop("id_giu_ban", None)
     ...
     ban_locked = BanAn.objects.select_for_update().get(id=ban.id)  # LINE 149: OUTSIDE TRANSACTION!
     ```
  2. `moc-backend/foods/services.py:23-32` (`khau_tru_nguyen_lieu_bom`):
     ```python
     with transaction.atomic():
         giao_dich_cu = LichSuXuatNhapKho.objects.filter(...)
         if giao_dich_cu.exists():
             return list(giao_dich_cu)
     ...
     nguyen_lieu_locked = list(
         NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")  # LINE 76: OUTSIDE TRANSACTION!
     )
     ```
  3. `moc-backend/foods/services.py:129-135` (`hoan_tra_nguyen_lieu_bom`):
     ```python
     with transaction.atomic():
         giao_dich_xuat = LichSuXuatNhapKho.objects.filter(...)
     ...
     nl_map = {
         nl.id: nl for nl in NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")  # LINE 142: OUTSIDE TRANSACTION!
     }
     ```
  4. `moc-backend/payments/services.py:147-154` (`process_ipn`):
     ```python
     with transaction.atomic():
         try:
             thanh_toan = ThanhToan.objects.select_for_update().select_related("dat_ban", "don_hang").get(ma_giao_dich=txn_ref)
         except ThanhToan.DoesNotExist:
             return "01", "Order not found"

     # Lines 158-237: OUTSIDE TRANSACTION! Row lock on thanh_toan is RELEASED immediately at line 154!
     ```
  5. `moc-backend/reservations/services.py:238-245` (`doi_trang_thai`):
     ```python
     with transaction.atomic():
         dat_ban.save(...)
     # Lines 248-273: BOM deduction hook is executed OUTSIDE transaction!
     ```
- **Why**:
  1. Django's query compiler (`django/db/models/sql/compiler.py:816`) explicitly enforces:
     ```python
     if self.connection.get_autocommit() and features.supports_transactions:
         raise TransactionManagementError("select_for_update cannot be used outside of a transaction.")
     ```
     Because `ATOMIC_REQUESTS` is not enabled in `settings.py`, every request runs in autocommit mode. Calling `select_for_update()` outside of a `transaction.atomic()` block will immediately crash the request in PostgreSQL with `TransactionManagementError`.
  2. In `VNPayService.process_ipn`, exiting the `transaction.atomic()` block immediately after `get(ma_giao_dich=txn_ref)` releases the row lock before verifying amounts, idempotency, or updating the payment and booking records. A concurrent duplicate IPN request can read the uncommitted state, bypass the idempotency check, and execute duplicate side effects.
  3. In `VNPayService.process_ipn` line 208, calling `DichVuKho.khau_tru_nguyen_lieu_bom` outside the transaction triggers `TransactionManagementError`, which is then silently swallowed by `except Exception: pass`, resulting in completely skipped stock deductions with no error reported.
- **Suggestion**:
  1. Decorate `DichVuDatBan.tao_dat_ban`, `DichVuKho.khau_tru_nguyen_lieu_bom`, and `DichVuKho.hoan_tra_nguyen_lieu_bom` with `@transaction.atomic` (or properly indent their entire method bodies within `with transaction.atomic():`), exactly as done in `orders/services.py:tao_don_hang` and `RefundService.process_cancellation_and_refund`.
  2. In `VNPayService.process_ipn`, wrap Stages 2 through 5 entirely inside a single `with transaction.atomic():` block immediately following the fail-fast Stage 1 signature check.
  3. In `DichVuDatBan.doi_trang_thai`, ensure the status mutation and BOM inventory deduction/restoration are enclosed in the same atomic transaction.

---

### [Major] Finding 2: Test Suite Verification Gaps & Mocking Masking Defects

- **What**:
  - In `tests/e2e/test_milestone2_verification.py`, `transaction.atomic` was globally mocked out with `MagicMock` across all tests for IPN (`test_04` through `test_08`) and BOM deduction (`test_01` through `test_04`).
  - `DichVuDatBan.tao_dat_ban` (Phase 2 booking confirmation) is NEVER invoked or tested anywhere in `test_milestone2_verification.py`, `runner.py`, or any adversarial test suite.
- **Why**:
  - Mocking `transaction.atomic` completely bypassed Django's transaction compiler check (`compiler.py:816`), creating false confidence that code passed 100% when it actually contains fatal runtime exceptions.
  - The worker's handoff claimed that Phase 2 table concurrency with `select_for_update()` was fully verified, whereas `tao_dat_ban` had 0% test coverage.
- **Suggestion**:
  - Add explicit unit and integration tests for `DichVuDatBan.tao_dat_ban` covering:
    * Successful reservation with valid hold token.
    * Rejection when hold token is expired or invalid.
    * Rejection when table is conflicting in DB.
    * Pessimistic row locking verification.
  - Remove blanket mocks on `transaction.atomic` in tests, or verify that `select_for_update` is called strictly within active transaction blocks.

---

### [Minor] Finding 3: Unrestricted Customer `is_no_show` Trigger in `huy_dat_ban`

- **What**: In `moc-backend/reservations/views.py:131`, `is_no_show = bool(request.data.get("is_no_show", False))` allows any authenticated reservation owner to pass `is_no_show: true` in the cancellation request body.
- **Why**: In `handoff.md` Caveat 3, the worker noted: *"No-show refunds (khach_khong_den) cannot be triggered by the customer; they must be invoked by restaurant staff or an automated cron task."* However, the view did not enforce this restriction.
- **Suggestion**: Restrict `is_no_show=True` to restaurant staff (`request.user.la_nhan_vien_nha_hang`) or admin roles. If a regular customer passes `is_no_show: true`, ignore or reject it.

---

### [Minor] Finding 4: Silent Exception Swallowing in IPN Fulfillment

- **What**: In `moc-backend/payments/services.py:206-216` and lines 230-235, calls to `DichVuKho.khau_tru_nguyen_lieu_bom` and cache deletion are wrapped in bare `except Exception: pass`.
- **Why**: If inventory deduction fails or raises an error on a confirmed order, the error is discarded without logging or notification, causing silent inventory desynchronization.
- **Suggestion**: Replace `except Exception: pass` with explicit logging (`logger.exception(...)`) or record fulfillment status flags on `DonHang`/`DatBan`.

---

## 3. Adversarial Challenge Report

### Overall Risk Assessment: HIGH

### Challenges & Stress Tests

| # | Challenge Scenario | Expected Behavior | Actual Behavior | Pass/Fail | Severity |
|---|-------------------|-------------------|-----------------|-----------|----------|
| 1 | Execute `DichVuDatBan.tao_dat_ban` with `select_for_update()` under Django autocommit mode | Executes within row lock mutex and commits reservation | Raises `TransactionManagementError` because `select_for_update` is called outside `transaction.atomic` | **FAIL** | **CRITICAL** |
| 2 | Execute `DichVuKho.khau_tru_nguyen_lieu_bom` under Django autocommit mode | Atomically locks sorted ingredients and deducts stock | Raises `TransactionManagementError`; when called via IPN, exception is silently swallowed | **FAIL** | **CRITICAL** |
| 3 | Concurrent duplicate VNPay IPN callbacks arriving at the same millisecond | First request updates state, second request is blocked at `select_for_update` until commit, then returns code `02` (Idempotent) | Row lock on `ThanhToan` is released at line 154; both requests evaluate idempotency concurrently on stale state | **FAIL** | **HIGH** |
| 4 | Regular customer submits `POST /api/reservations/{id}/huy_dat_ban/` with `{"is_no_show": true}` | Client request ignores `is_no_show` unless caller is staff | Customer is penalized with 0% refund (`khach_khong_den`) without staff authorization | **FAIL** | **MEDIUM** |
| 5 | HMAC-SHA512 checksum tampering (modify amount or order info) | IPN Stage 1 rejects with code `97` without querying DB | Returned `("97", "Invalid Checksum")` fail-fast | **PASS** | LOW |
| 6 | IPN Amount Mismatch (e.g., amount = 200,000 VND vs order = 500,000 VND) | IPN Stage 3 rejects with code `04` | Returned `("04", "Invalid amount")` | **PASS** | LOW |
| 7 | Deposit cancellation > 24 hours | 100% refund, 0 penalty, `da_hoan_tien` | Returned `truoc_24h`, 100.0%, 0.0 penalty | **PASS** | LOW |
| 8 | Deposit cancellation between 6 and 24 hours | 50% refund, 50% penalty, `hoan_tien_mot_phan` | Returned `tu_6_den_24h`, 50.0%, 50.0% penalty | **PASS** | LOW |
| 9 | Deposit cancellation < 6 hours | 0% refund, 100% penalty, `that_bai` | Returned `trong_6h`, 0.0%, 100.0% penalty | **PASS** | LOW |
| 10| Dual Route Resolution (Vietnamese & English paths) | All 14 dual routes resolve successfully | All routes resolved cleanly | **PASS** | LOW |

---

## 4. Verified Claims

1. **VNPay 2.1.0 HMAC-SHA512 Cryptographic Parity**:
   - `VNPayService.calculate_hmac_sha512` produces identical 128-character hashes to `vnpay_oracle.py`.
   - Keys are sorted in ASCII alphabetical order.
   - Hash fields (`vnp_SecureHash`, `vnp_SecureHashType`) and empty values are properly excluded.
   - Values are URL-encoded with `urllib.parse.quote_plus`.
   - Verified via `TestMilestone2VNPay.test_01_vnpay_hmac_sha512_matches_oracle` -> **PASS**.

2. **Dual Bilingual Routing**:
   - All Vietnamese (`/api/thanh-toan/vnpay/...`, `/api/ban-an/...`, `/api/dat-ban/...`) and English (`/api/payments/vnpay/...`, `/api/tables/...`, `/api/reservations/...`) endpoints resolve correctly.
   - Verified via `TestMilestone2DualRoutes` -> **PASS**.

3. **Phase 1 Redis Hold Concurrency**:
   - `giu_ban_tam_thoi` correctly executes `cache.add(khoa, token, timeout=600)`.
   - First caller receives HTTP 200 with `id_giu_ban` and 600s TTL.
   - Concurrent duplicate caller receives HTTP 409 Conflict with `code: "BAN_DANG_BAN"`.
   - Verified via `TestMilestone2TableConcurrency` -> **PASS**.

4. **Deposit Refund Policy & PhieuHoanTien Generation**:
   - Strict time thresholds (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) verified.
   - `PhieuHoanTien` model registered in admin, clean migration `0002_phieuhoantien.py` generated.
   - Verified via `TestMilestone2RefundPolicy` -> **PASS**.

---

## 5. Coverage Gaps & Unverified Items

1. **Unverified Item: Phase 2 Reservation Confirmation (`tao_dat_ban`)**:
   - Never tested in any test suite.
   - Due to premature exit of `with transaction.atomic():`, this function will crash with `TransactionManagementError` when executed against PostgreSQL.
   - Risk: **CRITICAL**. Requires immediate implementation of unit tests and indentation fix.

2. **Coverage Gap: Unmocked Transaction Integrity**:
   - Because `transaction.atomic` was patched with `MagicMock` across all verification tests, the test suite failed to validate actual transaction boundaries.
   - Risk: **HIGH**. Tests must exercise actual transaction boundaries.

---

## 6. Required Actions Before Approval

To attain **APPROVE**, the implementation worker (`m2_worker_1`) must complete the following fixes:

1. **Fix `moc-backend/reservations/services.py:tao_dat_ban`**:
   - Decorate `tao_dat_ban` with `@transaction.atomic` (or indent the entire function body within `with transaction.atomic():`) so that `BanAn.objects.select_for_update()` and `DatBan.objects.select_for_update()` execute inside an active transaction.
2. **Fix `moc-backend/foods/services.py:khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom`**:
   - Decorate both methods with `@transaction.atomic` so that `NguyenLieu.objects.select_for_update()` and inventory record writes are executed atomically.
3. **Fix `moc-backend/payments/services.py:process_ipn`**:
   - Enclose Stages 2 through 5 inside a single `with transaction.atomic():` block to guarantee row lock persistence on `ThanhToan` across idempotency checks and status updates.
4. **Fix `moc-backend/reservations/services.py:doi_trang_thai`**:
   - Wrap both the booking status update and the BOM deduction/refund hook in the same atomic transaction.
5. **Add Phase 2 Tests to `tests/e2e/test_milestone2_verification.py`**:
   - Add test cases directly invoking `DichVuDatBan.tao_dat_ban` verifying hold token validation, conflict rejection, and reservation persistence.
   - Ensure tests verify that `select_for_update()` is called inside a transaction.
6. **Restrict `is_no_show` in `moc-backend/reservations/views.py:huy_dat_ban`**:
   - Verify caller permissions before accepting `is_no_show=True`.

---

## 7. Verification Method

Once the worker has made the required changes, independently verify via:

```bash
cd /Users/VuVan/Documents/DO-AN

# 1. Django check (must pass with 0 issues)
./moc-backend/.venv/bin/python moc-backend/manage.py check

# 2. Master E2E Suite
./moc-backend/.venv/bin/python tests/e2e/runner.py

# 3. Milestone 2 Verification Suite (including new Phase 2 tests)
./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py

# 4. Verify transaction decorators exist on all 4 methods
./moc-backend/.venv/bin/python -c "
import sys; sys.path.insert(0, 'moc-backend')
from reservations.services import DichVuDatBan
from foods.services import DichVuKho
from payments.services import VNPayService
print('Verifying methods callable and properly scoped...')
"
```
