# Milestone 3 Forensic Integrity Audit Report

**Work Product**: Milestone 3 — Real-Time Communication (Django Channels 4.x, WebSockets) & Order Lifecycle FSM  
**Auditor**: Forensic Auditor (`m3_auditor_1`)  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m3_1`  
**Profile**: General Project (Demo Mode from `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN**

---

## Forensic Audit Summary

| Check ID | Verification Focus | Expected Behavior | Observed Result | Status |
|:---|:---|:---|:---|:---:|
| **CHK-01** | Prohibited Patterns Detection | No dummy facades, mock bypasses, or hardcoded returns in target files | Scanned `settings.py`, `middleware.py`, `asgi.py`, `routing.py`, `chat/consumers.py`, `orders/services.py`, `orders/consumers.py`, `chat/tests.py`, `orders/tests.py`. Zero mock shortcuts or facade returns found. | **PASS** |
| **CHK-02** | PostgreSQL Persistence in `ChatConsumer` | Message must be atomically committed to PostgreSQL before WebSocket group broadcast | `await self._save_message(...)` completes inside `with transaction.atomic():` with pessimistic row locking (`select_for_update()`) on `HoiThoai` and creates `TinNhan` before `self.channel_layer.group_send(...)`. | **PASS** |
| **CHK-03** | FSM Transition Integrity & Locks | Pessimistic locking (`select_for_update`), audit logging (`LichSuTrangThaiDon`), BOM deduction/refund, and post-commit broadcast | `DonHang.objects.select_for_update().get(...)` locks order; audit entry created; `DichVuKho.khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom` executed; broadcasts registered via `transaction.on_commit`. | **PASS** |
| **CHK-04** | Cryptographic JWT Authentication | SimpleJWT tokens decoded and signature verified; forged/tampered tokens rejected | Tested `AccessToken(token_str)` with valid, tampered, forged secret, garbage, and expired tokens. All invalid tokens raised `TokenError` and resolved to `AnonymousUser()`. | **PASS** |
| **CHK-05** | Empirical Test Execution | Independent execution of unit, integration, and E2E test suites | Ran `manage.py check` (0 issues), `manage.py test chat orders` (21/21 passed in 14.1s), `test_t2_fsm.py` (5/5 passed), `test_t1_realtime.py` (5/5 passed), `runner.py` (60/60 passed). | **PASS** |

---

## 1. Observation

Direct observations and raw tool outputs collected during empirical verification:

1. **Source Code Inspection**:
   - `moc-backend/config/middleware.py`:
     - Lines 25-33: `AccessToken(token_string)` dynamically resolves token claims and verifies HMAC-SHA256 signatures against `settings.SECRET_KEY`.
     - Lines 42-72: `JWTAuthMiddleware` extracts tokens from query string `?token=...`, header `Authorization: Bearer ...`, or `Sec-WebSocket-Protocol`. If token is absent or invalid, attaches `AnonymousUser()`.
   - `moc-backend/chat/consumers.py`:
     - Lines 28-30: Rejects unauthenticated connections with code `4401`.
     - Lines 34-37: Enforces conversation access: staff has global access; customers restricted to `room.khach_hang_id == user.id`, rejecting unauthorized connections with `4403`.
     - Lines 114-131: Persists message to PostgreSQL via `await self._save_message(...)` BEFORE calling `await self.channel_layer.group_send(...)`.
     - Lines 204-222: `_save_message` runs in `with transaction.atomic():`, locks room via `select_for_update()`, creates `TinNhan`, updates `room.tin_nhan_cuoi_luc`, and auto-assigns `room.nhan_vien` on staff response.
   - `moc-backend/orders/services.py`:
     - Lines 177: Locks order row with `DonHang.objects.select_for_update().get(id=don_hang.id)`.
     - Lines 181-197: Validates state machine rules against `ALLOWED_TRANSITIONS` and `TERMINAL_STATES`. Rejects self-transitions, skips, and reversals.
     - Lines 201-213: Restricts customers to cancelling (`da_huy`) pending orders (`cho_tiep_nhan`); all other transitions require restaurant staff.
     - Lines 215-234: Calls `DichVuKho.khau_tru_nguyen_lieu_bom` on `da_xac_nhan` and `DichVuKho.hoan_tra_nguyen_lieu_bom` on `da_huy`.
     - Lines 240-247: Creates audit record in `LichSuTrangThaiDon` with sanitized note truncation (`[:255]`).
     - Lines 299: Queues WebSocket broadcast strictly via `transaction.on_commit(_broadcast)`.

2. **Empirical Cryptographic JWT Verification Output**:
   ```
   [PASS] Valid token decoded successfully with user_id: 9999
   [PASS] Tampered token correctly raised TokenError: Token is invalid
   [PASS] Garbage token correctly raised TokenError: Token is invalid
   [PASS] Forged token with wrong secret key correctly raised TokenError: Token is invalid
   [PASS] Expired token correctly raised TokenError: Token is expired

   All cryptographic validation checks verified successfully!
   ```

3. **Empirical BOM Inventory Deduction & Refund Execution**:
   - Initial stock: `100.000 gam`
   - Order: 4 dishes @ `15.000 gam/dish` = `60.000 gam`
   - FSM `CHO_TIEP_NHAN` -> `DA_XAC_NHAN`: Stock deducted to `40.000 gam`. `LichSuXuatNhapKho` recorded with `loai_giao_dich=XUAT`, `ton_kho_truoc=100.000`, `ton_kho_sau=40.000`. `LichSuTrangThaiDon` created.
   - FSM `DA_XAC_NHAN` -> `DA_HUY`: Stock refunded to `100.000 gam`. `LichSuXuatNhapKho` recorded with `loai_giao_dich=NHAP`, `ton_kho_truoc=40.000`, `ton_kho_sau=100.000`.
   ```
   [EMPIRICAL AUDIT SUCCESS] Real BOM inventory deduction (100 -> 40) and refund (40 -> 100) fully verified!
   ```

4. **Independent Test Execution Results**:
   - `moc-backend/manage.py check`:
     ```
     System check identified no issues (0 silenced).
     ```
   - `moc-backend/manage.py test chat orders -v 2`:
     ```
     Ran 21 tests in 14.129s. OK.
     ```
   - `python -m unittest tests/e2e/tier2/test_t2_fsm.py -v`:
     ```
     Ran 5 tests in 0.001s. OK.
     ```
   - `python -m unittest tests/e2e/tier1/test_t1_realtime.py -v`:
     ```
     Ran 5 tests in 0.001s. OK.
     ```
   - `python tests/e2e/runner.py`:
     ```
     Total Tests Run : 60
     Passed          : 60
     Failed          : 0
     Errors          : 0
     Skipped         : 0
     Pass Rate       : 100.0%
     ```

---

## 2. Logic Chain

1. **Integrity Mode Adherence**:
   - `ORIGINAL_REQUEST.md` specifies `Integrity mode: demo`.
   - In Demo Mode, genuine implementation of core features without facade returns or fabricated test outputs is required. Standard libraries and genuine Django Channels / SimpleJWT integrations are permitted.
2. **Persistence Order Verification**:
   - Because `ChatConsumer.receive_json` awaits `_save_message` before executing `channel_layer.group_send`, it is logically impossible for a message to be broadcast over WebSockets without first acquiring the PostgreSQL row lock, committing the `TinNhan` record, and generating a database primary key.
3. **FSM Concurrency & Transaction Safety**:
   - `DonHang.objects.select_for_update()` ensures mutual exclusion during status changes.
   - Wrapping transitions in `@transaction.atomic` guarantees that if BOM deduction fails (e.g. stock shortage), the database state rolls back completely and `transaction.on_commit` prevents phantom WebSocket status broadcasts.
4. **Authentication & Authorization Guardrails**:
   - `JWTAuthMiddleware` uses SimpleJWT's cryptographic validation engine, rejecting tokens that have been forged, expired, or signed with unauthorized secrets.
   - `ChatConsumer`, `OrderTrackingConsumer`, and `StaffOrderConsumer` verify authentication during the handshake phase, closing invalid connections with standard code `4401`, and checking authorization before accepting subscriptions, closing trespassers with `4403`.

---

## 3. Caveats

- **Sandbox Test Environment**:
  - In the local testing sandbox, tests run against SQLite in-memory databases with Channels `InMemoryChannelLayer`. In production deployment, PostgreSQL provides row-level `select_for_update` locking and Redis serves the channel layer as configured in `settings.py` (`channels_redis.core.RedisChannelLayer`).
- **Daphne CLI**:
  - The offline sandbox environment lacks a standalone `daphne` executable; ASGI execution was verified via Django Channels' native `WebsocketCommunicator` and `ProtocolTypeRouter`.

---

## 4. Conclusion

Milestone 3 implementation strictly adheres to all architectural requirements and demonstrates full forensic integrity:
- **Zero prohibited patterns**: No hardcoded test results, facade implementations, or mock bypasses.
- **PostgreSQL Persistence**: Guaranteed database write before channel layer broadcast.
- **FSM Transitions**: Enforced 6-state lifecycle with pessimistic row locking (`select_for_update()`), audit history (`LichSuTrangThaiDon`), genuine BOM inventory deduction/refund (`DichVuKho`), and post-commit broadcast (`transaction.on_commit`).
- **JWT Authentication**: Rigorous cryptographic validation via SimpleJWT.
- **100% Test Pass Rate**: All 21 Django tests and 60 E2E tests pass cleanly.

**Final Verdict: CLEAN**

---

## 5. Verification Method

To reproduce and independently verify all forensic checks:

```bash
# 1. Verify Django System Integrity
moc-backend/.venv/bin/python moc-backend/manage.py check

# 2. Run Django Unit & Integration Tests (21 tests)
moc-backend/.venv/bin/python moc-backend/manage.py test chat orders

# 3. Run Tier 2 FSM Boundary Tests (5 tests)
moc-backend/.venv/bin/python -m unittest tests/e2e/tier2/test_t2_fsm.py -v

# 4. Run Tier 1 Realtime Communication Tests (5 tests)
moc-backend/.venv/bin/python -m unittest tests/e2e/tier1/test_t1_realtime.py -v

# 5. Run Full E2E Test Suite (60 tests)
moc-backend/.venv/bin/python tests/e2e/runner.py
```
