# Handoff Report: Milestone 2 Iteration 2 Independent Verification

**Agent**: `m2_r2_reviewer_2` (Reviewer 2 & Adversarial Critic)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_r2_2`  
**Recipient**: Parent Orchestrator (`3b4ac039-b543-49a4-9b3d-21e996771d3e`)  
**Timestamp**: 2026-10-14T10:19:00Z  
**Verdict**: **APPROVE**  
**Adversarial Risk Assessment**: **LOW (Robust)**

---

## 1. Observation

Direct observations obtained during code inspection, AST parsing, empirical security validation, and test execution:

### Observation 1: Elimination of `MagicMock` on `transaction.atomic`
- In `tests/e2e/test_milestone2_verification.py`, regex search `patch.*atomic` across the entire codebase confirmed **0 occurrences** of patching `django.db.transaction.atomic`.
- `AuthenticTransactionTestCase` (lines 84–122) sets up authentic Django transaction context:
  ```python
  patch.object(connection, "ensure_connection", return_value=None),
  patch.object(connection, "connection", self.mock_raw_conn),
  patch.object(connection.features, "has_select_for_update", True),
  patch.object(connection, "get_autocommit", side_effect=lambda: not connection.in_atomic_block),
  ```
- Genuine Django `Atomic` enters and exits during test executions, accurately updating `connection.atomic_blocks` and `connection.in_atomic_block`.
- Calling `compiler.as_sql()` on `select_for_update()` outside an active transaction raises `TransactionManagementError`, verified in `test_09_phase2_select_for_update_enforces_active_transaction` (lines 739–753).

### Observation 2: Authentic Phase 2 Booking Coverage (9 Tests)
- `tests/e2e/test_milestone2_verification.py:TestMilestone2Phase2PessimisticLock` contains exactly 9 comprehensive test methods (lines 507–753):
  1. `test_01_phase2_success_with_valid_token_and_deposit`: Valid hold token, ordered dishes, verifies 30% deposit calculation (`so_tien_coc=Decimal("60000.00")`), creates `MonAnTrongDatBan`, deletes Redis hold key on commit.
  2. `test_02_phase2_success_table_only_zero_deposit`: Table-only reservation requires zero deposit (`so_tien_coc=Decimal("0")`) and transitions immediately to `trang_thai="da_xac_nhan"`, `trang_thai_coc="thanh_cong"`.
  3. `test_03_phase2_rejects_expired_or_missing_hold_token`: Missing or expired Redis hold key raises `ValidationError({"id_giu_ban": ...})`, preventing database persistence.
  4. `test_04_phase2_rejects_mismatch_hold_token`: Mismatched hold token raises `ValidationError({"id_giu_ban": "Phiên giữ bàn đã hết hạn hoặc không hợp lệ."})`.
  5. `test_05_phase2_rejects_direct_booking_when_table_is_held`: Direct booking without token fails with `ValidationError({"ban_an": "Bàn hiện đang được giữ chỗ tạm thời bởi khách hàng khác."})` when Redis hold key exists.
  6. `test_06_phase2_rejects_database_pre_booking_conflict`: Existing conflicting booking in PostgreSQL raises `ValidationError({"ban_an": "Bàn đã có người đặt trong khung giờ này."})`.
  7. `test_07_phase2_rejects_table_in_maintenance`: Table with `trang_thai=BAO_TRI` raises `ValidationError({"ban_an": "Bàn đang trong trạng thái bảo trì."})`.
  8. `test_08_phase2_rejects_capacity_overflow`: Guest count exceeding `suc_chua` raises `ValidationError({"so_luong_khach": ...})`.
  9. `test_09_phase2_select_for_update_enforces_active_transaction`: Confirms that `select_for_update` fails outside an active transaction with `TransactionManagementError`, and succeeds with `FOR UPDATE` SQL compilation inside atomic blocks.

### Observation 3: Role Restriction on `is_no_show` in `DatBanViewSet.huy_dat_ban`
- In `moc-backend/reservations/views.py` (lines 141–142):
  ```python
  is_staff = getattr(request.user, "la_nhan_vien_nha_hang", False) or getattr(request.user, "is_staff", False)
  is_no_show = bool(request.data.get("is_no_show", False)) and is_staff
  ```
- Empirical validation with APIRequestFactory confirmed:
  - Customer request submitting `{"is_no_show": True}` yields `is_no_show=False` passed to `RefundService.process_cancellation_and_refund`.
  - Staff request submitting `{"is_no_show": True}` yields `is_no_show=True` passed to `RefundService.process_cancellation_and_refund`.

### Observation 4: AST Verification of Transaction Scoping
- AST parsing of backend service methods verified:
  - `reservations.services.DichVuDatBan.tao_dat_ban`: Decorated with `@classmethod` and `@transaction.atomic`.
  - `reservations.services.DichVuDatBan.doi_trang_thai`: Decorated with `@staticmethod` and `@transaction.atomic`. Stockout `ValidationError` is allowed to bubble up without exception swallowing.
  - `foods.services.DichVuKho.khau_tru_nguyen_lieu_bom`: Decorated with `@staticmethod` and `@transaction.atomic`.
  - `foods.services.DichVuKho.hoan_tra_nguyen_lieu_bom`: Decorated with `@staticmethod` and `@transaction.atomic`.
  - `payments.services.VNPayService.process_ipn`: Checksum verified fail-fast outside transaction; Stages 2 through 5 enclosed in unified `with transaction.atomic():` covering order lookup (`select_for_update()`), amount matching, idempotency guard, and mutations.

### Observation 5: Empirical Verification Test Suite Runs
1. **Django System Check**:
   ```bash
   ./moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
   *Output*: `System check identified no issues (0 silenced).` (Exit code 0)

2. **Master E2E Runner (Tiers 1–4)**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Output*:
   ```
   Ran 60 tests in 0.028s
   OK
   Total Tests Run : 60 | Passed : 60 | Failed : 0 | Errors : 0 | Pass Rate : 100.0%
   ```
   (Exit code 0)

3. **Milestone 2 Verification Suite (35 tests)**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py
   ```
   *Output*:
   ```
   Ran 35 tests in 0.548s
   OK
   ```
   (Exit code 0)

4. **Milestone 2 Adversarial Stress Suite (16 tests)**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py
   ```
   *Output*:
   ```
   Ran 16 tests in 1.243s
   OK
   ```
   (Exit code 0)

5. **Combined Milestone 2 Unittest (51 tests)**:
   ```bash
   ./moc-backend/.venv/bin/python -m unittest tests/e2e/test_milestone2_verification.py tests/e2e/test_adversarial_challenger_m2.py
   ```
   *Output*:
   ```
   Ran 51 tests in 1.419s
   OK
   ```
   (Exit code 0)

### Observation 6: Integrity Audit
- Scanned for integrity violations:
  - Hardcoded test results / expected outputs embedded in source code: **None found**.
  - Dummy or facade implementations: **None found**; models, serializers, services, and transactions execute authentic application logic.
  - Shortcuts bypassing intended requirements: **None found**.
  - Fabricated verification outputs: **None found**; all outputs directly reproduced and verified in real time.
  - Self-certifying without genuine verification: **None found**; AST and live execution tests conducted independently.

---

## 2. Logic Chain

1. **Transaction Scope Integrity**:
   - In production PostgreSQL autocommit mode, calling `select_for_update()` outside an active transaction raises `TransactionManagementError`, while executing it inside a 1-line block releases the lock immediately upon exit.
   - By decorating `tao_dat_ban`, `doi_trang_thai`, `khau_tru_nguyen_lieu_bom`, and `hoan_tra_nguyen_lieu_bom` with `@transaction.atomic`, and enclosing Stages 2 through 5 of `process_ipn` in `with transaction.atomic():`, row locks on `BanAn`, `DatBan`, `NguyenLieu`, and `ThanhToan` are held continuously until the operation commits or encounters an error.
   - The test harness accurately validates this by raising `TransactionManagementError` whenever `select_for_update()` is triggered while `connection.in_atomic_block` is `False`.

2. **Phase 2 Concurrency Handshake**:
   - Phase 1 creates a temporary 10-minute hold token in Redis via `SET NX EX 600`.
   - Phase 2 acquires a pessimistic lock on `BanAn`, validates table status, capacity, and branch, and verifies that the provided `id_giu_ban` matches the token currently residing in Redis.
   - Direct booking requests without tokens are rejected if another user has acquired a temporary hold.
   - Redis hold key cleanup is deferred via `transaction.on_commit(_xoa_khoa_redis)`, ensuring that temporary hold locks remain intact if a database transaction aborts or rolls back.

3. **Access Control & Penalty Protection**:
   - `is_no_show` induces a strict 0% deposit refund policy penalty.
   - By evaluating `is_staff = getattr(request.user, "la_nhan_vien_nha_hang", False) or getattr(request.user, "is_staff", False)` and forcing `is_no_show = bool(request.data.get("is_no_show", False)) and is_staff`, customers cannot trigger no-show penalties maliciously or manipulate refund logic.
   - Conversely, authorized restaurant staff retain full capability to flag no-shows during table management operations.

4. **Deadlock Elimination**:
   - BOM material deduction locks multiple `NguyenLieu` rows concurrently.
   - If two orders require overlapping ingredients in reverse order (e.g. Order A: [10, 20] and Order B: [20, 10]), concurrent transactions could trigger database deadlocks.
   - Sorting ingredient IDs ascending (`sorted(tong_nhu_cau.keys())`) guarantees strict global acquisition ordering, mathematically eliminating lock cycles.

---

## 3. Caveats

1. **macOS Sandbox TCP Socket Restriction**:
   - The macOS sandbox environment blocks raw TCP socket bindings to `localhost:5432`.
   - Consequently, unit and integration suites execute Django's ORM compiler, state machines, and transaction managers using `AuthenticTransactionTestCase`, which exercises authentic Django transaction logic without issuing live raw TCP calls.
2. **VNPay Gateway Sandbox**:
   - Webhook testing uses the HMAC-SHA512 test oracle conforming strictly to VNPay 2.1.0 specifications.

---

## 4. Conclusion

All 5 Milestone 2 Iteration 2 remediation objectives have been verified with complete fidelity:
1. `MagicMock` patching of `transaction.atomic` is completely eliminated across all test suites.
2. `AuthenticTransactionTestCase` enforces authentic Django transaction state machines and verifies `select_for_update()` lock scoping.
3. `DichVuDatBan.tao_dat_ban` is covered by 9 comprehensive tests verifying tokens, deposit math, conflict handling, capacity overflow, and transaction boundaries.
4. `is_no_show` role authorization in `DatBanViewSet.huy_dat_ban` strictly blocks customer privilege escalation while empowering staff.
5. All test suites pass cleanly with 100% success rate:
   - `python manage.py check`: 0 issues
   - `runner.py`: 60/60 passing
   - `test_milestone2_verification.py`: 35/35 passing
   - `test_adversarial_challenger_m2.py`: 16/16 passing
   - Combined test run: 51/51 passing
6. No integrity violations or cheating patterns were identified.

**Verdict**: **APPROVE**

---

## 5. Verification Method

To independently verify this evaluation, execute the following commands in order:

### Step 1: Check AST Transaction Scoping
```bash
cd /Users/VuVan/Documents/DO-AN
./moc-backend/.venv/bin/python -c '
import ast, inspect, textwrap, os, sys
sys.path.insert(0, "moc-backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
from reservations.services import DichVuDatBan
from foods.services import DichVuKho
from payments.services import VNPayService

assert any("atomic" in ast.dump(d) for d in ast.parse(textwrap.dedent(inspect.getsource(DichVuDatBan.tao_dat_ban))).body[0].decorator_list)
assert any("atomic" in ast.dump(d) for d in ast.parse(textwrap.dedent(inspect.getsource(DichVuDatBan.doi_trang_thai))).body[0].decorator_list)
assert any("atomic" in ast.dump(d) for d in ast.parse(textwrap.dedent(inspect.getsource(DichVuKho.khau_tru_nguyen_lieu_bom))).body[0].decorator_list)
assert any("atomic" in ast.dump(d) for d in ast.parse(textwrap.dedent(inspect.getsource(DichVuKho.hoan_tra_nguyen_lieu_bom))).body[0].decorator_list)
print("AST transaction scoping: PASSED")
'
```

### Step 2: Run Django System Check
```bash
./moc-backend/.venv/bin/python moc-backend/manage.py check
```
*Expected*: `System check identified no issues (0 silenced).`

### Step 3: Run Master E2E Runner (60 tests)
```bash
./moc-backend/.venv/bin/python tests/e2e/runner.py
```
*Expected*: `Ran 60 tests in ... OK ... Pass Rate : 100.0%`

### Step 4: Run Milestone 2 Verification Suite (35 tests)
```bash
./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py
```
*Expected*: `Ran 35 tests in ... OK`

### Step 5: Run Milestone 2 Adversarial Stress Suite (16 tests)
```bash
./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py
```
*Expected*: `Ran 16 tests in ... OK`

### Step 6: Invalidation Conditions
- Any occurrence of `patch("django.db.transaction.atomic")` or `patch.object(transaction, "atomic")` reappearing in tests.
- Re-introduction of `except Exception: pass` concealing stockout errors in `doi_trang_thai`.
- Allowing unauthenticated or non-staff callers to set `is_no_show: true`.
- Any failure in the 51 tests of Milestone 2.
