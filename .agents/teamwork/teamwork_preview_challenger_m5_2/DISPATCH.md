## 2026-10-14T23:49:32Z
You are Challenger m5_challenger_2 assigned to empirically stress-test Milestone 5 (Frontend Synchronization & Staff/Admin Portals) for Web App Nhà hàng Mộc.

Your Working Directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m5_2
All your working metadata, progress.md, and handoff.md MUST be saved in your working directory.

MANDATORY FIRST STEP: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md completely.
Also read:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1/handoff.md

Your Empirical Testing Focus (Admin/Staff Portals Integration & Permissions Stress):
1. Design and run an empirical Python stress/adversarial test harness (e.g. under `tests/e2e/test_adversarial_m5_portals.py` or within your test environment) that validates:
   - Review moderation API (`reviews/views.py`): verify that unapproved/hidden reviews (`hien_thi=False`) are strictly HIDDEN from regular users / anonymous callers, but accessible and modifiable by staff / `is_staff=True` / `la_nhan_vien_nha_hang=True`. Test unauthorized attempts to toggle `hien_thi`.
   - Inventory & BOM management: test rapid concurrent inventory transactions (stock in, stock out, adjustment) via `foods/views.py` / `admin.api.ts` endpoints.
   - Order FSM Admin transitions: test validity of state transitions initiated by staff (`cho_tiep_nhan` -> `da_xac_nhan` -> `dang_che_bien` -> `san_sang` -> `hoan_tat`), invalid transitions (e.g. attempting to jump to completed without prior valid state), and audit logging.
   - Table reservation floor plan data consistency: test active table statuses and booking filters under high concurrency.
2. Run full backend checks:
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py check`
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py test reviews orders foods reservations`
3. Provide your empirical test results, pass rates, and binary verdict: **APPROVE** or **REQUEST_CHANGES** in `handoff.md` in your working directory.
4. Send your handoff verdict and empirical findings back to the orchestrator via send_message.
