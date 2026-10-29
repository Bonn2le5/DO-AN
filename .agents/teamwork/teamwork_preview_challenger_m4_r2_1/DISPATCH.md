# Dispatch: m4_r2_challenger_1

## Role & Mission
Challenger 1 for Milestone 4 Round 2 (Recommendations Stress Testing). Re-verify the 3 bugs originally discovered:
1. `GET /api/recommendations/<pk>/` no longer raises HTTP 500 AssertionError (now returns 200 for user's recommendation or 404 cleanly).
2. Creating orders through `orders/services.py:83` assigns `trong_so=4.00` (Feature 20).
3. Creating orders or reviews automatically invalidates `GoiYMonAn` cache for that user via signals.

## Authoritative Documents to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md`
4. `/Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py`

## Adversarial Tasks
1. Execute `tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py` (Must PASS 3/3).
2. Execute `tests/e2e/test_adversarial_challenger_m4_recommendations.py` (Must PASS 13/13).
3. Execute your own stress tests on recommendation endpoints and signals.
4. Render verdict (APPROVE or REQUEST_CHANGES).

Write your handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_1/handoff.md`
And notify orchestrator via send_message.
## 2026-10-14T16:45:47Z
You are Challenger m4_r2_challenger_1 for Milestone 4 Round 2 of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_1

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (MANDATORY)
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_1/DISPATCH.md
- /Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py

Adversarial Tasks:
1. Run PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py (Verify 3/3 PASS).
2. Run PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py (Verify 13/13 PASS).
3. Adversarially test GET /api/recommendations/<pk>/, interaction weight=4 on orders, and cache invalidation signal.
4. Render verdict (APPROVE or REQUEST_CHANGES) and write to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_r2_1/handoff.md
And notify the orchestrator via send_message.
