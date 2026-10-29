# Dispatch: m2_reviewer_2

## Task
You are Reviewer 2 for Milestone 2: 2-Phase Concurrency Control, BOM Deduction & Refund Policy.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2`

## MANDATORY READ
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen2/PROJECT.md`
- Read `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md`

## Review Objectives
1. Inspect `moc-backend/reservations/` (services, views, serializers), `moc-backend/foods/services.py`, and `moc-backend/orders/services.py`.
2. Verify 2-Phase Concurrency Control:
   - Phase 1 Redis hold: key format, 600s TTL, collision detection returning HTTP 409 Conflict with `code: "BAN_DANG_BAN"`. Both detail route (`/api/tables/{id}/giu_ban/`) and frontend list route (`/api/dat-ban/giu-ban/`).
   - Phase 2 pessimistic DB lock: `BanAn.objects.select_for_update().get(id=ban.id)` as table mutex, token validation, Redis key deletion.
3. Verify BOM Material Inventory Deduction:
   - Strict ascending ID ordering before acquiring locks (`sorted_ids = sorted(tong_nhu_cau.keys())`) to prevent deadlocks.
   - Stock availability validation, atomic deduction, and `LichSuXuatNhapKho` audit logging.
4. Verify Deposit Refund Policy & `PhieuHoanTien`:
   - Calculations: >24h 100%, 6–24h 50%, <6h 0%, no-show 0%.
   - Unique code format `RF-{ma_dat_ban}-{YYYYMMDD}` and database persistence.
5. Run verification commands:
   - `./moc-backend/.venv/bin/python moc-backend/manage.py check`
   - `./moc-backend/.venv/bin/python tests/e2e/runner.py`
   - `./moc-backend/.venv/bin/python tests/e2e/test_milestone2_verification.py`
6. Formulate explicit verdict: **APPROVE** or **REQUEST_CHANGES**.

Write your handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2/handoff.md` and notify caller when done.


## 2026-10-14T08:39:23Z
You are m2_reviewer_2, Reviewer 2 for Milestone 2.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m2_1/handoff.md.
Review 2-Phase Concurrency Control (Phase 1 Redis hold HTTP 409, Phase 2 select_for_update table mutex), BOM material deduction with sorted IDs, and refund policies. Run builds and tests.
Deliver your review report and verdict (APPROVE or REQUEST_CHANGES) in /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m2_2/handoff.md and notify the caller.
