## 2026-10-14T23:49:32Z
You are Challenger m5_challenger_1 assigned to empirically stress-test Milestone 5 (Frontend Synchronization & Staff/Admin Portals) for Web App Nhà hàng Mộc.

Your Working Directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m5_1
All your working metadata, progress.md, and handoff.md MUST be saved in your working directory.

MANDATORY FIRST STEP: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md completely.
Also read:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1/handoff.md

Your Empirical Testing Focus (WebSocket Real-Time Chat & Tracking Stress):
1. Design and run an empirical Python stress/adversarial test harness (e.g. under `tests/e2e/test_adversarial_m5_realtime.py` or within your test environment) that validates:
   - WebSocket authentication in `JWTAuthMiddleware` (`moc-backend/config/middleware.py`): verify that valid JWT in query param `?token=<jwt>` authenticates successfully, whereas missing or invalid JWT results in AnonymousUser or close code 4401.
   - Real-time Chat Consumer (`moc-backend/chat/consumers.py`): verify persistent message storage in PostgreSQL `TinNhan` table before broadcast, multi-party messaging between customer and staff, handling of empty/malformed payloads.
   - Order FSM Real-time Stream: verify order status update broadcasts on channel layer, delivery to individual order room `/ws/orders/<id>/` and staff stream `/ws/orders/staff/`.
   - Concurrency & reconnection: rapid connection cycling, message ordering, no memory leaks or channel leaks.
2. Run backend regression checks:
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py test chat orders`
   - `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python tests/e2e/runner.py`
3. Provide your empirical test results, performance metrics, and binary verdict: **APPROVE** or **REQUEST_CHANGES** in `handoff.md` in your working directory.
4. Send your handoff verdict and empirical findings back to the orchestrator via send_message.
