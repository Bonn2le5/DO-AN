# BRIEFING — 2026-10-14T15:33:00Z

## Mission
Implement Milestone 3: Real-Time Communication Channels (Django Channels 4.x, WebSockets) and Order Lifecycle FSM for Web App Nhà hàng Mộc.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 3 (Real-Time Communication & Order FSM)

## 🔒 Key Constraints
- DO NOT CHEAT: Genuine logic only, no hardcoded test results, no dummy facades.
- Daphne is absent from environment: do NOT add 'daphne' to INSTALLED_APPS. Use sys.modules stub helper for tests importing WebsocketCommunicator.
- In-memory channel layer fallback for tests/environments without Redis.
- Pessimistic locking (select_for_update()) during order status transitions.
- Post-commit WebSocket broadcast via transaction.on_commit.
- Strict 6-state Order FSM: cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat; da_huy allowed from non-terminal states; hoan_tat & da_huy are terminal.
- Strict authorization: Customer can only cancel pending orders and access own chat/order tracking. Staff can access all.

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: 2026-10-14T15:24:47Z

## Task Summary
- **What to build**: Channels configuration, JWTAuthMiddleware, ASGI ProtocolTypeRouter, ChatConsumer, OrderTrackingConsumer, StaffOrderConsumer, strict FSM in DichVuDonHang with BOM deduction/refund, audit logging, WebSocket routing, API endpoints, test helper, comprehensive unit and e2e tests.
- **Success criteria**: Django check passes, unit tests pass (21/21), Tier 1 & Tier 2 e2e test suites pass (60/60).
- **Interface contracts**: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
- **Code layout**: moc-backend/

## Change Tracker
- **Files modified**:
  - `moc-backend/config/settings.py`: Added Channels configuration, testing wildcard in ALLOWED_HOSTS, InMemory fallback.
  - `moc-backend/config/middleware.py`: Implemented JWTAuthMiddleware & JWTAuthMiddlewareStack.
  - `moc-backend/api/ws_auth.py`: Re-exported from config.middleware.
  - `moc-backend/config/asgi.py`: ProtocolTypeRouter with AllowedHostsOriginValidator & JWTAuthMiddlewareStack.
  - `moc-backend/config/routing.py`: Combined chat and orders websocket urlpatterns.
  - `moc-backend/chat/consumers.py`: AsyncJsonWebsocketConsumer with 4401/4403 enforcement, DB persistence before broadcast, typing, read receipts.
  - `moc-backend/chat/routing.py`: Routed /ws/chat/<conversation_id>/.
  - `moc-backend/chat/views.py`: Added active and messages actions.
  - `moc-backend/api/urls.py`: Registered chat/conversations alias router.
  - `moc-backend/orders/services.py`: Implemented strict 6-state FSM, locking, BOM deduction/refund, audit logging, post-commit broadcast.
  - `moc-backend/orders/views.py`: Exposed authenticated status transition endpoints with aliases.
  - `moc-backend/orders/consumers.py`: Implemented OrderTrackingConsumer and StaffOrderConsumer.
  - `moc-backend/orders/routing.py`: Placed staff route before parameterized order_id route.
  - `moc-backend/api/tests_channels_helper.py`: Daphne stub helper for WebsocketCommunicator.
  - `moc-backend/chat/tests.py`: Comprehensive WebSocket & REST test suite.
  - `moc-backend/orders/tests.py`: Comprehensive FSM lifecycle & tracking test suite.
- **Build status**: PASS (21/21 Django unit tests, 60/60 E2E tests, 0 check errors)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 100% pass rate
- **Lint status**: Clean
- **Tests added/modified**: 21 unit & integration tests across chat and orders

## Loaded Skills
- None specified

## Key Decisions Made
- Handled absence of standalone Daphne via sys.modules lightweight stub in tests_channels_helper.py.
- Handled async context role checks via database_sync_to_async to prevent SynchronousOnlyOperation on related managers.
- Added wildcard to ALLOWED_HOSTS during testing to allow Origin-less WebsocketCommunicator test connections through AllowedHostsOriginValidator.
- Dual-formatted WebSocket event payloads (both flattened keys and nested data dictionary) to maximize compatibility with frontend components and test suites.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/DISPATCH.md — Dispatch instructions & log
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/BRIEFING.md — Working state
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/progress.md — Progress tracker
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m3_1/handoff.md — Final handoff report
