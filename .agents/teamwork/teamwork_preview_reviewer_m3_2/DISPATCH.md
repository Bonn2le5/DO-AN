# Dispatch Instructions for Reviewer m3_reviewer_2

## Mission
Independently review Milestone 3 implementation (Django Channels 4.x ASGI, WebSocket query authentication, 2-way chat consumer, Order 6-state FSM, and real-time broadcasts).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m3_2`

## Authoritative Inputs
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Worker Handoff: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md`

## Review Tasks
1. Verify `moc-backend/manage.py check` passes with 0 issues.
2. Verify Django unit & integration tests (`python moc-backend/manage.py test chat orders`).
3. Verify test suites (`tests/e2e/tier2/test_t2_fsm.py`, `tests/e2e/tier1/test_t1_realtime.py`, `tests/e2e/runner.py`).
4. Review code quality, security, and edge cases in:
   - `moc-backend/config/settings.py` (Channels installed, ALLOWED_HOSTS, Channel layers)
   - `moc-backend/config/middleware.py` (JWT auth via query param and header fallback)
   - `moc-backend/config/asgi.py` & `routing.py`
   - `moc-backend/chat/consumers.py` (auth check 4401, room access check 4403, DB persistence BEFORE broadcast, typing indicator, mark read)
   - `moc-backend/orders/services.py` (strict 6-state FSM transition validation, select_for_update locking, BOM hooks, audit log, post-commit broadcast)
   - `moc-backend/orders/consumers.py` & `routing.py` (`ws/orders/staff/` before `<order_id>`)
5. Write your verdict (APPROVE or REQUEST_CHANGES) and report to:
   `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m3_2/handoff.md`


## 2026-10-14T15:36:18Z
From e1a47f66-ae44-4e72-ae56-b7ecb23a0048:
You are Reviewer m3_reviewer_2 for Milestone 3 (Real-Time Communication Channels & Order FSM) of Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m3_2

Read authoritative documents:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m3_2/DISPATCH.md

Review Tasks:
1. Verify system checks pass: python moc-backend/manage.py check
2. Verify unit and integration tests: python moc-backend/manage.py test chat orders
3. Verify test suites: python -m unittest tests/e2e/tier2/test_t2_fsm.py -v, python -m unittest tests/e2e/tier1/test_t1_realtime.py -v, python tests/e2e/runner.py
4. Conduct thorough code review on:
   - moc-backend/config/settings.py
   - moc-backend/config/middleware.py & api/ws_auth.py
   - moc-backend/config/asgi.py & routing.py
   - moc-backend/chat/consumers.py, routing.py, views.py
   - moc-backend/orders/services.py, consumers.py, routing.py, views.py
5. Write your complete handoff report with verdict (APPROVE or REQUEST_CHANGES) to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m3_2/handoff.md
And notify the orchestrator via send_message.
