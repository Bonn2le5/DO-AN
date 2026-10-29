# Forensic Audit Report: Milestone 2 Implementation

**Work Product**: Milestone 2: VNPay Sandbox Deposit Payment & Table Concurrency Control  
**Auditor**: Forensic Auditor (`m2_auditor_1`)  
**Integrity Mode**: `demo` (read directly from `ORIGINAL_REQUEST.md`, line 8)  
**Profile**: General Project  
**Date**: 2026-10-14  
**Verdict**: **CLEAN**

---

### Phase Results

- **Check 1: Hardcoded Output Detection**: **PASS** — No hardcoded test results, mock checksums, static return values, or bypass flags found in any service or view module.
- **Check 2: Facade Implementation Detection**: **PASS** — Genuine algorithmic implementations verified for `VNPayService.calculate_hmac_sha512` (HMAC-SHA512 + `urllib.parse.quote_plus`), `VNPayService.process_ipn` (5-stage verification gate with DB state mutations), `DichVuDatBan.giu_ban_tam_thoi` (Redis `cache.add` SET NX EX 600), `DichVuDatBan.tao_dat_ban` (pessimistic lock `BanAn.objects.select_for_update()`), and `DichVuKho.khau_tru_nguyen_lieu_bom` (sorted ingredient IDs, deadlock-free row locking, and `LichSuXuatNhapKho` auditing).
- **Check 3: Pre-populated Artifact Detection**: **PASS** — Repository scan (`find . -name '*.log' -o -name '*result*' -o -name '*output*'`) verified zero pre-populated test output logs or fabricated attestations.
- **Check 4: Behavioral Verification**: **PASS** — All system checks and automated test suites ran cleanly with 100% pass rates:
  - `python moc-backend/manage.py check`: 0 issues.
  - `python tests/e2e/runner.py`: 60/60 tests PASSED (100%).
  - `python tests/e2e/test_adversarial_challenger_m1.py`: 18/18 tests PASSED (100%).
  - `python tests/e2e/test_adversarial_stress_m1.py`: 16/16 tests PASSED (100%).
  - `python tests/e2e/test_milestone2_verification.py`: 26/26 tests PASSED (100%).
- **Check 5: Dependency Audit**: **PASS** — No external third-party VNPay or concurrency packages were introduced. Logic relies exclusively on Python standard library (`hmac`, `hashlib`, `urllib.parse`), Django ORM, and Redis cache.
- **Check 6: Independent Adversarial Stress-Testing**: **PASS** — Custom independent auditor suite (`audit_test_m2.py`) executed 11 edge-case stress tests (multi-threaded race conditions, microsecond refund boundary thresholds, penny conservation arithmetic, spoofed signature rejection, and inverted BOM ordering); all 11 passed.

---

## 5-Component Handoff Report

### 1. Observation

1. **Hardcoding & Facade Scan**:
   - `moc-backend/payments/services.py:38-54`:
     ```python
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
     ```
     Observed: Genuinely computes HMAC-SHA512 over ASCII-sorted, URL-encoded parameter strings. Filters empty values and hash fields. Constant-time validation implemented in `verify_signature` (`hmac.compare_digest`).
   - `moc-backend/payments/services.py:121-238`:
     Observed: `process_ipn` strictly validates signature before touching database (fail-fast gate), verifies transaction existence via `select_for_update()`, validates amount matching (`int(so_tien * 100)`), validates idempotency (returns `02` if already confirmed/refunded), updates `trang_thai` to `THANH_CONG`, sets `dat_ban.trang_thai = DA_XAC_NHAN` & `trang_thai_coc = THANH_CONG`, and cleans up Redis hold keys.
   - `moc-backend/reservations/services.py:44-125`:
     Observed: `giu_ban_tam_thoi` verifies table capacity and maintenance status, queries existing DB bookings, sets Redis key with `cache.add(khoa, token, timeout=600)` (atomic SET NX EX), and returns HTTP 409 `BAN_DANG_BAN` on conflict.
   - `moc-backend/reservations/services.py:128-234`:
     Observed: `tao_dat_ban` executes pessimistic lock `BanAn.objects.select_for_update().get(id=ban.id)`, cross-checks Redis token against caller payload, creates `DatBan` and `MonAnTrongDatBan`, and deletes Redis hold keys atomically.
   - `moc-backend/foods/services.py:9-116`:
     Observed: `khau_tru_nguyen_lieu_bom` checks idempotency against `LichSuXuatNhapKho`, aggregates total ingredient demand, sorts ingredient IDs ascending (`sorted_ids = sorted(tong_nhu_cau.keys())`), executes pessimistic locking `NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")`, verifies stock levels, deducts stock, and creates `LichSuXuatNhapKho` records.

2. **System Check & Verification Test Commands Executed**:
   - Command: `./moc-backend/.venv/bin/python moc-backend/manage.py check`
     ```
     System check identified no issues (0 silenced).
     ```
     Exit code: 0.
   - Command: `./moc-backend/.venv/bin/python tests/e2e/runner.py`
     ```
     Ran 60 tests in 0.008s
     OK
     Total Tests Run : 60 | Passed : 60 | Failed : 0 | Errors : 0 | Pass Rate : 100.0%
     ```
     Exit code: 0.
   - Command: `./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m1.py`
     ```
     Ran 18 tests in 0.293s
     OK
     ```
     Exit code: 0.
   - Command: `./moc-backend/.venv/bin/python tests/e2e/test_adversarial_stress_m1.py`
     ```
     Ran 16 tests in 3.973s
     OK
     ```
     Exit code: 0.
   - Command: `./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py`
     ```
     Ran 26 tests in 0.281s
     OK
     ```
     Exit code: 0.

3. **Auditor Independent Adversarial Suite (`audit_test_m2.py`)**:
   - Command: `./moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_auditor_m2_1/audit_test_m2.py`
     ```
     Ran 11 tests in 0.016s
     OK
     ```
     Exit code: 0.
     Tests verified:
     - `test_special_characters_and_vietnamese_accents`: Accented characters and symbols preserve HMAC integrity.
     - `test_hash_strips_both_hash_fields`: `vnp_SecureHash` and `vnp_SecureHashType` excluded properly.
     - `test_none_and_empty_values_filtered`: None/empty string omission validated.
     - `test_ipn_spoofed_signature_fails_fast_without_db`: Returns 97 without triggering DB queries.
     - `test_exact_microsecond_boundary_24h`: 24h + 1µs -> 100%; exactly 24.0h -> 50%; 24h - 1µs -> 50%.
     - `test_exact_microsecond_boundary_6h`: exactly 6.0h -> 50%; 6h - 1µs -> 0%.
     - `test_odd_amount_penny_conservation`: Odd amounts (e.g. 333,333.33) preserve total amount (`refund + penalty == deposit`).
     - `test_maintenance_table_cannot_be_held`: Banned table rejects hold with `ValidationError`.
     - `test_capacity_overflow_cannot_be_held`: Excess guests reject hold with `ValidationError`.
     - `test_concurrent_threads_race_for_same_hold`: 10 concurrent threads racing for same table -> exactly 1 acquires hold, 9 receive 409 `BAN_DANG_BAN`.
     - `test_strict_ordering_preserves_even_when_input_inverted`: Inverted BOM ingredient inputs are locked strictly in ascending ID order (`10, 50, 99`).

---

### 2. Logic Chain

1. **Absence of Hardcoded Results**:
   - Premise: If test results or checksums were hardcoded, searching the codebase for the test hashes or static mock return values would yield matches.
   - Observation: Zero instances of test hashes, mock return constants, or fake bypass logic exist in `payments/`, `reservations/`, `foods/`, or `orders/`.
   - Conclusion: The implementation computes results dynamically through algorithmic execution.

2. **Genuine Concurrency Control (2-Phase Mutex)**:
   - Premise: True concurrency control requires both a short-lived cache-level mutex (Phase 1) and a serialized row-level database lock (Phase 2).
   - Observation: `DichVuDatBan.giu_ban_tam_thoi` uses Redis `cache.add` with 600s TTL, rejecting duplicates with HTTP 409 `BAN_DANG_BAN`. Multi-threaded stress testing confirms exactly 1 winner out of 10 concurrent threads. `DichVuDatBan.tao_dat_ban` locks `BanAn.objects.select_for_update()`, checks the Redis token, and deletes keys inside a database transaction.
   - Conclusion: The 2-phase concurrency mechanism is authentic, robust against race conditions, and correctly enforces mutual exclusion.

3. **BOM Deadlock Prevention via Strict Ascending ID Ordering**:
   - Premise: Concurrent multi-resource locking can trigger circular wait deadlocks unless a global ordering hierarchy is strictly enforced.
   - Observation: `DichVuKho.khau_tru_nguyen_lieu_bom` sorts ingredient IDs with `sorted(tong_nhu_cau.keys())` and queries `NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")`.
   - Conclusion: All transactions lock database rows in identical sequential order, mathematically eliminating the possibility of circular wait deadlocks.

4. **Deposit Refund Mathematical Precision**:
   - Premise: Refund evaluation must strictly adhere to the project specification brackets (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%) and conserve the original deposit amount down to the penny.
   - Observation: Exact microsecond boundary tests and fractional deposit amounts confirmed 100% adherence and penny conservation. `PhieuHoanTien` database records are generated with complete financial and timestamp audit trails.
   - Conclusion: Refund calculation and receipt persistence satisfy all business and accounting requirements.

---

### 3. Caveats

- **No Caveats**: All components for Milestone 2 were empirically verified in code, database models, serializers, service layers, and through multi-tiered automated execution and independent adversarial stress testing.

---

### 4. Conclusion

- **Verdict**: **CLEAN**
- All deliverables for Milestone 2 (VNPay Sandbox Deposit Payment & Table Concurrency Control) are fully and authentically implemented without shortcuts, facades, hardcoding, or external SDK delegation.
- Milestone 2 is certified as complete and ready for Milestone 3 progression.

---

### 5. Verification Method

To independently re-verify this audit:

1. **System Check**:
   ```bash
   ./moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
2. **Master E2E Suite**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
3. **Milestone 2 Verification Suite**:
   ```bash
   ./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py
   ```
4. **Auditor Independent Adversarial Suite**:
   ```bash
   ./moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_auditor_m2_1/audit_test_m2.py
   ```
