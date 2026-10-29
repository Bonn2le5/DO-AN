# Dispatch Instructions for Worker m3_worker_1

## Mission
Implement Milestone 3: Real-Time Communication (Channels 4.x & Redis Channel Layer) and Order Lifecycle FSM (6-state progression, BOM inventory side effects, audit logging, and WebSocket broadcasts).

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1`

## Authoritative Inputs & Blueprints
- User Request: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
- Project Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
- Spec Miner Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m3_1/handoff.md`
- Channels & ASGI Explorer Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_1/handoff.md`
- Consumer & FSM Explorer Blueprint: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_2/handoff.md`

## Files You Own Exclusively
- `moc-backend/config/settings.py` (Add `'channels'`, `ASGI_APPLICATION`, `CHANNEL_LAYERS` with `InMemoryChannelLayer` fallback)
- `moc-backend/config/middleware.py` (JWTAuthMiddleware & JWTAuthMiddlewareStack)
- `moc-backend/config/asgi.py` (ProtocolTypeRouter with HTTP and WebSocket routes)
- `moc-backend/config/routing.py` (Central WebSocket routing)
- `moc-backend/chat/consumers.py` (ChatConsumer with DB persistence before broadcast, typing, mark_read)
- `moc-backend/chat/routing.py` (`ws/chat/<conversation_id>/`)
- `moc-backend/chat/views.py` (`active` and `messages` actions)
- `moc-backend/chat/tests.py` (Comprehensive WebSocket & REST tests)
- `moc-backend/orders/services.py` (6-state FSM validation, `select_for_update()`, BOM deduction/refund, audit log, post-commit broadcast)
- `moc-backend/orders/consumers.py` (`OrderTrackingConsumer` & `StaffOrderConsumer`)
- `moc-backend/orders/routing.py` (`ws/orders/staff/` before `<order_id>`)
- `moc-backend/orders/views.py` (Dual routing / status aliases)
- `moc-backend/orders/tests.py` (Comprehensive FSM & tracking tests)
- `moc-backend/api/urls.py` (Route aliases)
- `moc-backend/api/tests_channels_helper.py` (Daphne mock helper for `WebsocketCommunicator`)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Completion Criteria
1. `python moc-backend/manage.py check` passes with 0 errors.
2. `python moc-backend/manage.py test chat orders` passes all tests.
3. `python -m unittest tests/e2e/tier2/test_t2_fsm.py -v` passes.
4. `python -m unittest tests/e2e/tier1/test_t1_realtime.py -v` passes.
5. `python tests/e2e/runner.py --tier 1` and `python tests/e2e/runner.py --tier 2` pass.
6. Write full handoff report to `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md`.

## 2026-10-14T15:14:26Z
You are Worker m3_worker_1 assigned to implement Milestone 3 (Real-Time Communication Channels & Order FSM) for Web App Nhà hàng Mộc.
Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1
Tasks: settings, middleware, asgi, routing, chat consumers, routing, views, orders services FSM, consumers, routing, tests, verification.

## 2026-10-14T15:24:47Z
From: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
Milestone 3 Implementation Status Check
Orchestrator checking in on your progress for Milestone 3 (Channels 4.x, JWT middleware, ChatConsumer, Order FSM, and test suite). Please update progress.md with your current task.
Action: Report your current progress and status.
