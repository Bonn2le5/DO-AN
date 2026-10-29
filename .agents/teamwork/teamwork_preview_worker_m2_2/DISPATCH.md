# Dispatch: m2_r2_worker_1

## Task
You are the Implementation Worker for Milestone 2 Iteration 2 (Remediation).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_2`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Input Context (MANDATORY READ)
You MUST read the following authoritative reports before modifying code:
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/handoff.md` and `transaction_scoping_fixes.patch`
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_2/handoff.md`
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_3/handoff.md` and test patches

## Code Ownership & Deliverables
Apply the following 5 remediations:

1. **Transaction Scoping Remediation**:
   - `moc-backend/reservations/services.py:tao_dat_ban`: Decorate with `@transaction.atomic` (or enclose the entire method body in `with transaction.atomic():`), ensuring `BanAn.objects.select_for_update()` and `DatBan` persistence execute strictly inside the active transaction.
   - `moc-backend/foods/services.py:khau_tru_nguyen_lieu_bom`: Enclose the entire method body inside `with transaction.atomic():` (or `@transaction.atomic`), ensuring `NguyenLieu.objects.select_for_update()` and stock updates execute inside the transaction.
   - `moc-backend/foods/services.py:hoan_tra_nguyen_lieu_bom`: Enclose inside `with transaction.atomic():` (or `@transaction.atomic`).
   - `moc-backend/payments/services.py:process_ipn`: Keep Stage 1 (checksum) fail-fast outside transaction. Enclose Stages 2 through 5 inside a single `with transaction.atomic():` block so the row lock on `ThanhToan` remains held through amount validation, idempotency check, and state mutations.
   - `moc-backend/reservations/services.py:doi_trang_thai`: Enclose status mutation and BOM inventory deduction in the atomic transaction without swallowing `ValidationError`.

2. **ViewSet Permissions**:
   - `moc-backend/payments/views.py:ThanhToanViewSet`: Implement `get_permissions(self)` allowing `[AllowAny]` for `vnpay_ipn`, `vnpay_return`, `vnpay_create`, and `tao_phien`.
   - `moc-backend/reservations/views.py:BanAnViewSet`: In `get_permissions(self)`, allow `[AllowAny]` for `giu_ban`, `list`, and `retrieve` actions so guest customers can hold tables.

3. **QueryDict Scalar Extraction in `process_ipn`**:
   - In `moc-backend/payments/services.py:process_ipn`:
     ```python
     if hasattr(query_params, "dict"):
         params = query_params.dict()
     else:
         params = {k: query_params.get(k) for k in query_params.keys()}
     ```
     Preventing list-wrapping (`['20000000']`) that corrupts HMAC checksum calculation.

4. **Table Release on Payment Failure (Code 24 / Non-Zero)**:
   - When IPN receives `vnp_ResponseCode != "00"` (e.g. `24` cancelled payment), set `dat_ban.trang_thai = DatBan.TrangThai.DA_HUY` and `trang_thai_coc = ThanhToanCoc.THAT_BAI`, and release Redis hold keys so the table is not permanently blocked.

5. **Test Suite Upgrades**:
   - Replace/upgrade `tests/e2e/test_milestone2_verification.py` using `m2_r2_explorer_3`'s `proposed_test_milestone2_verification.py` (removing all `MagicMock` on `transaction.atomic` and adding 9 tests for `tao_dat_ban` -> 35 tests total).
   - Replace/upgrade `tests/e2e/test_adversarial_challenger_m2.py` using `m2_r2_explorer_3`'s `proposed_test_adversarial_challenger_m2.py` (16 adversarial tests total).

## Verification Steps (Required in handoff)
1. Run Django system check:
   `./moc-backend/.venv/bin/python moc-backend/manage.py check` (MUST be 0 issues)
2. Run master E2E test runner:
   `./moc-backend/.venv/bin/python tests/e2e/runner.py` (60/60 tests pass)
3. Run Milestone 2 Verification Suite:
   `./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py` (35/35 tests pass)
4. Run Milestone 2 Adversarial Suite:
   `./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py` (16/16 tests pass)

Write your complete handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_2/handoff.md` and notify caller when done.
