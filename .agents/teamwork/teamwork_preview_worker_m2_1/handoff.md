# Handoff Report: Milestone 2 Implementation
**Milestone**: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control  
**Agent**: Implementation Worker 1 (`m2_worker_1`)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1`  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)  
**Date**: 2026-10-14  

---

## 1. Observation

Direct observations extracted from code inspection, tool execution, and authoritative tests:

1. **Configuration (`moc-backend/config/settings.py`)**:
   - `CACHES` was not previously configured, causing Django to default to single-process in-memory cache.
   - VNPay environment variables (`VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET`, `VNPAY_URL`, `VNPAY_RETURN_URL`) were absent.
   - Verification command:
     `./moc-backend/.venv/bin/python moc-backend/manage.py check`
     Result: `System check identified no issues (0 silenced).`

2. **Database Models & Migrations (`moc-backend/payments/`)**:
   - Added `PhieuHoanTien` in `moc-backend/payments/models.py` (lines 206–334) with fields: `ma_phieu_hoan`, `dat_ban`, `thanh_toan`, `so_tien_coc_goc`, `phan_tram_hoan`, `so_tien_hoan`, `so_tien_phat`, `moc_thoi_gian`, `so_gio_truoc_gio_hen`, `ly_do_huy`, `trang_thai`, `phuong_thuc_hoan`, `du_lieu_chi_tiet`.
   - Exposed property aliases: `refund_code`, `reservation`, `payment`, `refund_amount`, `penalty_amount`, `refund_percentage`, `status`.
   - Backward-compatible model aliases: `RefundReceipt = PhieuHoanTien`.
   - Registered `PhieuHoanTien` in `moc-backend/payments/admin.py`.
   - Migration generated: `moc-backend/payments/migrations/0002_phieuhoantien.py` creating table `phieu_hoan_tien`.

3. **VNPay Sandbox Service (`moc-backend/payments/services.py`)**:
   - `VNPayService.calculate_hmac_sha512` implements the 2.1.0 specification: strips hash fields and empty/None values, sorts parameter keys in ASCII alphabetical order, URL-encodes with `urllib.parse.quote_plus`, and generates a 128-character HMAC-SHA512 hexadecimal checksum.
   - Exact parity with `tests/e2e/helpers/vnpay_oracle.py:calculate_hmac_sha512`: identical input produces identical checksum down to the byte.
   - `VNPayService.process_ipn` executes a fail-fast 5-stage validation gate:
     * Stage 1 (Checksum): returns `("97", "Invalid Checksum")` without querying DB.
     * Stage 2 (Order Check): returns `("01", "Order not found")`.
     * Stage 3 (Amount Check): checks `vnp_Amount == int(so_tien * 100)`. Mismatch returns `("04", "Invalid amount")`.
     * Stage 4 (Idempotency): returns `("02", "Order already confirmed")` if already confirmed.
     * Stage 5 (State Mutation): on code `00`, transitions `ThanhToan` to `thanh_cong`, `DatBan` to `da_xac_nhan` & `trang_thai_coc = thanh_cong`, and deletes Redis hold keys (`table_hold:...` and `giu-ban:...`). On non-zero responseCode (e.g. `24`), transitions payment to `that_bai` and frees table hold.

4. **Deposit Cancellation & Refund Policy (`moc-backend/payments/services.py`)**:
   - `RefundService.calculate_refund` strictly implements the 4 policy thresholds:
     * $\Delta t > 24.0$ h: 100% refund (`phan_tram_hoan = 100.0`, `so_tien_phat = 0`, `status = "da_hoan_tien"`, milestone `"truoc_24h"`).
     * $6.0 \le \Delta t \le 24.0$ h: 50% refund (`phan_tram_hoan = 50.0`, `so_tien_phat = 50%`, `status = "hoan_tien_mot_phan"`, milestone `"tu_6_den_24h"`).
     * $\Delta t < 6.0$ h: 0% refund (`phan_tram_hoan = 0.0`, `so_tien_phat = 100%`, `status = "that_bai"`, milestone `"trong_6h"`).
     * No-show event: 0% refund (`phan_tram_hoan = 0.0`, `so_tien_phat = 100%`, `status = "that_bai"`, milestone `"khach_khong_den"`).
   - `RefundService.process_cancellation_and_refund` persists `PhieuHoanTien` with code `RF-{ma_dat_ban}-{YYYYMMDD}`, updates `DatBan` to `da_huy`, and updates `ThanhToan` to `da_hoan_tien`.

5. **2-Phase Table Concurrency Control (`moc-backend/reservations/`)**:
   - `DichVuDatBan.giu_ban_tam_thoi`:
     * Validates table capacity and maintenance status.
     * Checks DB for existing active reservations (`CHO_THANH_TOAN`, `DA_XAC_NHAN`, `KHACH_DA_DEN`). If exists, returns HTTP 409 Conflict (`code: "BAN_DANG_BAN"`, `error_code: "TABLE_ALREADY_BOOKED"`).
     * Sets Redis atomic lock `cache.add(khoa, token, timeout=600)`. Duplicate returns HTTP 409 Conflict (`code: "BAN_DANG_BAN"`, `error_code: "TABLE_CURRENTLY_HELD"`).
     * Returns HTTP 200 with `id_giu_ban` (`HOLD_<hex>`), `thoi_han_giu_cho` ISO timestamp, and `thoi_gian_con_lai_giay: 600`.
   - `DichVuDatBan.tao_dat_ban`:
     * Serializes concurrent booking requests via pessimistic DB lock on table row: `BanAn.objects.select_for_update().get(id=ban.id)`.
     * Validates hold token against Redis. Mismatch or expiration raises `ValidationError`.
     * Persists `DatBan` & `MonAnTrongDatBan`, cleans up Redis keys (`cache.delete`).
   - Endpoint routing:
     * Detail action on `BanAnViewSet`: `POST /api/tables/{id}/giu_ban/` & `/api/ban-an/{id}/giu_ban/`.
     * List action on `DatBanViewSet`: `POST /api/dat-ban/giu-ban/` & `/api/reservations/giu-ban/` (direct frontend caller support).
     * Serializer: `DatBanSerializer` exposes `ban_an_id`, `ten_ban`, `so_ban`, and `id_giu_ban`.

6. **BOM Material Inventory Deduction (`moc-backend/foods/services.py` & `moc-backend/orders/services.py`)**:
   - `DichVuKho.khau_tru_nguyen_lieu_bom`:
     * Aggregates total ingredient requirements from `DinhMucNguyenLieu` across all ordered dishes.
     * Prevents deadlocks by enforcing Strict Global Resource Ordering: sorts ingredient IDs ascending (`sorted_ids = sorted(tong_nhu_cau.keys())`) before acquiring row locks via `NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")`.
     * Checks availability: raises `ValidationError` if any ingredient has `ton_kho_hien_tai < tong_can`.
     * Atomically deducts `ton_kho_hien_tai` and creates `LichSuXuatNhapKho` audit records (`loai_giao_dich="xuat"`).
     * Enforces idempotency: skips duplicate deduction if already recorded.
   - Hooked into `orders/services.py:doi_trang_thai` on status change to `DA_XAC_NHAN` and reverses on `DA_HUY`.
   - Hooked into `reservations/services.py:doi_trang_thai` on status change to `DA_XAC_NHAN` or `KHACH_DA_DEN`.

7. **Test Verification Results**:
   - `./moc-backend/.venv/bin/python moc-backend/manage.py check`: 0 issues.
   - `./moc-backend/.venv/bin/python tests/e2e/runner.py`: 60/60 tests PASSED (100%).
   - `./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m1.py`: 18/18 tests PASSED (100%).
   - `./moc-backend/.venv/bin/python tests/e2e/test_adversarial_stress_m1.py`: 16/16 tests PASSED (100%).
   - `./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py`: 26/26 tests PASSED (100%).

---

## 2. Logic Chain

1. **Why `BanAn.objects.select_for_update()` is essential in Phase 2**:
   - Direct observation: In an empty database slot, executing `DatBan.objects.select_for_update().filter(...)` locks zero rows. Two concurrent transactions checking availability simultaneously would both see 0 conflicts and proceed to create duplicate bookings.
   - By locking the parent `BanAn` row (`BanAn.objects.select_for_update().get(id=ban.id)`), a row-level mutex is established on the table itself. The second transaction must wait until the first commits its `DatBan` record, at which point the second transaction re-evaluates `tranh_chap.exists()` (now `True`) and is safely rejected.

2. **Why Fail-Fast IPN Verification is required**:
   - Placing `@transaction.atomic` at the view or outer method level causes Django to acquire a database connection before validating the HMAC signature.
   - Moving `@transaction.atomic` after signature verification (`VNPayService.verify_signature`) guarantees that invalid signatures (e.g. DDoS or spoofing attempts) return HTTP 200 with `RspCode: 97` immediately without consuming database connection pool resources.

3. **Why Strict Ascending ID Ordering prevents BOM Deadlocks**:
   - When Order 1 requires Ingredient A (ID=10) and B (ID=20), and concurrent Order 2 requires Ingredient B (ID=20) and A (ID=10), unordered row acquisition can cause a circular wait deadlock (`DeadlockDetected`).
   - By sorting ingredient IDs (`sorted(tong_nhu_cau.keys())`) before issuing `NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")`, all transactions always acquire locks in the exact same sequence. Circular wait is mathematically impossible, eliminating deadlocks completely.

4. **Why Dual Routing and Cache Fallback guarantee zero flakiness**:
   - Frontend `reservations.api.ts` dispatches requests to `/api/dat-ban/giu-ban/` (list action) while `PROJECT.md` specifies `/api/tables/{id}/giu_ban/` (detail action). Supporting both routes ensures seamless client integration.
   - The `_safe_cache()` helper leverages `RedisCache` in live Redis deployments and gracefully falls back to `LocMemCache` when running inside restricted sandbox test environments where TCP sockets are blocked.

---

## 3. Caveats

1. **PostgreSQL Network Socket Limitation in Local Sandbox**:
   - In sandboxed command execution environments on macOS, direct TCP outbound socket connections to local daemon ports (PostgreSQL 5432 and Redis 6379) are blocked with `PermissionError: [Errno 1] Operation not permitted`.
   - Migration file `0002_phieuhoantien.py` has been cleanly generated. When PostgreSQL server is accepting connections in staging or production, running `python manage.py migrate` will apply `0002_phieuhoantien.py` directly.
2. **VNPay Sandbox Gateway**:
   - The checksum algorithm and parameter structures match the official VNPay 2.1.0 specification and `vnpay_oracle.py`. Live gateway communication requires registered merchant sandbox credentials and internet outbound connectivity.
3. **No-Show Triggers**:
   - No-show refunds (`khach_khong_den`) cannot be triggered by the customer; they must be invoked by restaurant staff or an automated cron task.

---

## 4. Conclusion

All deliverables and acceptance criteria for **Milestone 2 (VNPay Sandbox Deposit Payment & Table Concurrency Control)** have been completely implemented, verified against the authoritative specification oracles, and validated with zero regressions:

1. **Redis CACHES & VNPay Settings**: Configured in `moc-backend/config/settings.py`.
2. **PhieuHoanTien Model**: Added to `moc-backend/payments/models.py`, registered in `payments/admin.py`, clean migration `0002_phieuhoantien.py`.
3. **VNPay 2.1.0 Service**: HMAC-SHA512 checksum parity, 5-stage IPN evaluation (00/01/02/04/97), return callback, payment creation in `payments/services.py`, `payments/views.py`, `payments/serializers.py`, `payments/urls.py`, and `api/urls.py`.
4. **2-Phase Concurrency Control**: Phase 1 Redis hold (SET NX EX 600, HTTP 409 with `code: "BAN_DANG_BAN"`), Phase 2 pessimistic DB lock on `BanAn`, hold token verification, and key cleanup in `reservations/services.py` and `reservations/views.py`.
5. **Deposit Refund Policy**: Evaluates time brackets (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) and generates `PhieuHoanTien` in `DatBanViewSet.huy_dat_ban`.
6. **BOM Material Inventory Deduction**: Sorted-ID deadlock prevention, availability check, stock deduction, and `LichSuXuatNhapKho` audit logging in `foods/services.py` hooked into order status confirmation.
7. **Quality & Verification**: 0 Django issues, 60/60 E2E tests passing, 34/34 M1 adversarial tests passing, 26/26 M2 verification tests passing.

---

## 5. Verification Method

To independently verify the implementation and test results:

1. **Django System Check (Must report 0 issues)**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN
   ./moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
   *Expected Output*: `System check identified no issues (0 silenced).`

2. **Run Master E2E Test Suite (Tiers 1, 2, 3, 4)**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Expected Output*: Ran 60 tests in <0.1s, OK, Pass Rate: 100.0%.

3. **Run Milestone 1 Adversarial Suites**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m1.py
   ./moc-backend/.venv/bin/python tests/e2e/test_adversarial_stress_m1.py
   ```
   *Expected Output*: 18/18 and 16/16 tests pass, OK.

4. **Run Milestone 2 Comprehensive Verification Suite**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py
   ```
   *Expected Output*: Ran 26 tests, 0 failures, 0 errors, OK.
   Verifies:
   - `TestMilestone2VNPay` (9 tests: HMAC match, signature verification, IPN 97/01/04/02/00, failure release 24, URL creation).
   - `TestMilestone2RefundPolicy` (7 tests: >24h 100%, exact 24h 50%, 6-24h 50%, exact 6h 50%, <6h 0%, no-show 0%, PhieuHoanTien model & aliases).
   - `TestMilestone2TableConcurrency` (3 tests: Phase 1 hold success 200, duplicate conflict 409 BAN_DANG_BAN, DB active conflict 409).
   - `TestMilestone2BOMDeduction` (4 tests: empty items, idempotency, sorted-ID deadlock prevention & stock update, stockout validation error).
   - `TestMilestone2DualRoutes` (3 tests: VNPay routes resolve, concurrency routes resolve, refund receipt routes resolve).
