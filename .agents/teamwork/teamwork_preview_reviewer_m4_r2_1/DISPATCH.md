# Dispatch: m4_r2_reviewer_1

## Role & Mission
Reviewer 1 for Milestone 4 Round 2 (Remediation Verification). Verify that all 3 challenger bugs and GIS edge cases have been resolved cleanly without regressions.

## Authoritative Documents to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md`

## Review Tasks
1. Run system checks: `moc-backend/.venv/bin/python moc-backend/manage.py check`
2. Run Bug Reproduction Suite: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py` (Must be 3/3 PASS)
3. Run Recommendation Tests: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py` (13/13 PASS)
4. Run GIS Tests: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py` (18/18 PASS)
5. Run Regression Suite: `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders` (58/58 PASS)
6. Run Master E2E Suite: `moc-backend/.venv/bin/python tests/e2e/runner.py` (60/60 PASS)
7. Conduct code review on the changes in:
   - `moc-backend/recommendations/views.py`
   - `moc-backend/recommendations/signals.py`
   - `moc-backend/recommendations/apps.py`
   - `moc-backend/orders/services.py`
   - `moc-backend/branches/services.py`
   - `moc-backend/branches/views.py`
   - `tests/e2e/helpers/ai_gis_oracle.py`

Write your handoff report with verdict (APPROVE or REQUEST_CHANGES) to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_r2_1/handoff.md`
And notify orchestrator via send_message.

## 2026-10-14T16:45:47Z
From: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
Priority: MESSAGE_PRIORITY_HIGH
Content:
You are Reviewer m4_r2_reviewer_1 for Milestone 4 Round 2 (Remediation Verification) of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_r2_1

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (MANDATORY)
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_2/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_r2_1/DISPATCH.md

Review Tasks:
1. Verify system checks pass: moc-backend/.venv/bin/python moc-backend/manage.py check
2. Verify bug reproduction: PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py (Must PASS 3/3)
3. Verify test suites:
   - PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py
   - PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py
   - moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders
   - moc-backend/.venv/bin/python tests/e2e/runner.py
4. Conduct thorough code review on:
   - moc-backend/recommendations/views.py (GoiYMonAnViewSet queryset & get_queryset)
   - moc-backend/recommendations/signals.py & apps.py
   - moc-backend/orders/services.py:83 (trong_so=4)
   - moc-backend/branches/services.py & branches/views.py
   - tests/e2e/helpers/ai_gis_oracle.py
5. Write your complete handoff report with verdict (APPROVE or REQUEST_CHANGES) to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_r2_1/handoff.md
And notify the orchestrator via send_message.
