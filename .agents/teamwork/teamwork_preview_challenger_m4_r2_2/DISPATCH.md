# Dispatch: m4_r2_challenger_2

## Role & Mission
Challenger 2 for Milestone 4 Round 2 (GIS Edge Cases Verification). Verify that the GIS edge cases have been resolved:
1. Antipodal points no longer raise `ValueError: math domain error` in `haversine_distance_km`.
2. Malformed query parameters `radius=abc` or `limit=abc` return HTTP 400 Bad Request instead of HTTP 500.
3. Coordinates out of range (`lat=999, lng=999`) or special float strings (`nan`, `inf`) in `GET /api/branches/` (list) return HTTP 400 Bad Request instead of HTTP 200.

## Authoritative Documents to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md`
4. `/Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m4.py`
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/verify_blueprints.py`

## Adversarial Tasks
1. Execute `tests/e2e/test_adversarial_challenger_m4.py` (Must PASS 18/18).
2. Execute `.agents/teamwork/teamwork_preview_explorer_m4_r2_3/verify_blueprints.py` (Must PASS 100k antipodal pairs & 32 edge cases).
3. Test edge cases on live endpoints and render verdict (APPROVE or REQUEST_CHANGES).

Write your handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_2/handoff.md`
And notify orchestrator via send_message.

## 2026-10-14T16:45:47Z
Sender: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are Challenger m4_r2_challenger_2 for Milestone 4 Round 2 of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_2

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (MANDATORY)
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_2/DISPATCH.md
- /Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m4.py

Adversarial Tasks:
1. Run PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py (Verify 18/18 PASS).
2. Run TESTING=1 PYTHONPATH=.:moc-backend moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_explorer_m4_r2_3/verify_blueprints.py (Verify antipodal clamp & 32 edge cases PASS).
3. Adversarially stress test invalid query parameters (radius=abc, limit=abc, lat=999, lng=999).
4. Render verdict (APPROVE or REQUEST_CHANGES) and write to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_2/handoff.md
And notify the orchestrator via send_message.
