# Dispatch: m2_r2_explorer_1

## Task
You are Explorer 1 for Milestone 2 Iteration 2: Transaction Scoping & Concurrency Lock Remediation.

## Context (Previous Gate Failures)
Reviewers and Challengers reported critical transaction scoping defects:
- `reservations/services.py:tao_dat_ban`: `with transaction.atomic():` was closed after line 133, leaving `BanAn.objects.select_for_update()` and `DatBan` creation outside the transaction, raising `TransactionManagementError`.
- `foods/services.py:khau_tru_nguyen_lieu_bom` and `hoan_tra_nguyen_lieu_bom`: `with transaction.atomic():` was closed prematurely, leaving `NguyenLieu.objects.select_for_update()` outside the transaction.
- `payments/services.py:process_ipn`: `with transaction.atomic():` was closed after retrieving `thanh_toan`, releasing the row lock before the idempotency check, amount check, and state updates.
- `reservations/services.py:doi_trang_thai`: Status mutation and BOM inventory deduction must be atomic without swallowing `ValidationError`.

## Input Files
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1/handoff.md`
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2/handoff.md`
- `moc-backend/reservations/services.py`
- `moc-backend/foods/services.py`
- `moc-backend/payments/services.py`

## Deliverables
Formulate exact code-level fix recommendations (decorators, indentation, transaction scoping, error propagation) to ensure 100% adherence to PostgreSQL transaction rules and atomicity. Write `handoff.md` in `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/handoff.md`.

## 2026-10-14T08:56:13Z
You are m2_r2_explorer_1, Explorer 1 for Milestone 2 Iteration 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and the review reports from Iteration 1.
Formulate line-by-line fix recommendations for transaction scoping in tao_dat_ban, khau_tru_nguyen_lieu_bom, hoan_tra_nguyen_lieu_bom, process_ipn, and doi_trang_thai.
Deliver report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/handoff.md and notify the caller.
## 2026-10-14T09:44:01Z
You are m2_r2_explorer_1 (Replacement), Explorer 1 for Milestone 2 Iteration 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and the review reports from Iteration 1 (/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_1/handoff.md and reviewer_m2_2/handoff.md).
Formulate line-by-line fix recommendations for transaction scoping in:
1. reservations/services.py:tao_dat_ban
2. foods/services.py:khau_tru_nguyen_lieu_bom
3. foods/services.py:hoan_tra_nguyen_lieu_bom
4. payments/services.py:process_ipn
5. reservations/services.py:doi_trang_thai
Ensure select_for_update() never executes outside an active transaction and that row locks remain held throughout.
Deliver your report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_r2_1/handoff.md and notify the caller.
