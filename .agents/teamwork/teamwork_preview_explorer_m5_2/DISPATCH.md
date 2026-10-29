# Dispatch: m5_explorer_realtime

## Role & Mission
Explorer for Milestone 5 (Frontend Realtime WebSocket Integration).
Investigate `moc-frontend` WebSocket client architecture for:
1. Customer & Staff Realtime Chat (`ChatWidget.tsx` and staff chat view).
2. Live Order Tracking FSM updates without page reload (`OrderDetail.tsx` or `TrackingPage.tsx`).

## Authoritative Documents to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY - Section R3, R5, Acceptance Criteria)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. Backend ASGI & Consumers:
   - `moc-backend/config/routing.py`
   - `moc-backend/chat/consumers.py` (`/ws/chat/<conversation_id>/`)
   - `moc-backend/orders/consumers.py` (`/ws/orders/<order_id>/`, `/ws/orders/staff/`)
   - `moc-backend/config/middleware.py` (SimpleJWT `?token=<token>`)
4. Frontend components:
   - `moc-frontend/src/components/chat/ChatWidget.tsx`
   - `moc-frontend/src/pages/order/` or tracking components.
   - `moc-frontend/src/services/websocket.ts` (if exists).

## Specific Investigation Tasks
1. Map exact WebSocket URL schemes in frontend (ws://localhost:8000/ws/... with JWT token in query parameter `?token=...`).
2. Inspect `ChatWidget.tsx`: does it currently use mock/polling, or is it already attempting WebSocket? What JSON payload format is expected by `ChatConsumer` vs what frontend sends?
3. Inspect Order Tracking: how does the frontend receive `order_snapshot` and `order_status_update`?
4. Propose clean custom React hooks (e.g. `useWebSocketChat`, `useOrderTracking`) or drop-in component updates to integrate cleanly with Django Channels.

Write your 5-component handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2/handoff.md`
And notify orchestrator via send_message.

## 2026-10-14T16:55:52Z
You are Explorer m5_explorer_realtime assigned to investigate Milestone 5 Frontend WebSocket Integration for Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2

Read authoritative documents:
1. /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (MANDATORY - Section R3, R5, Acceptance Criteria)
2. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
3. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2/DISPATCH.md
4. Backend ASGI & Consumers:
   - `moc-backend/config/routing.py`
   - `moc-backend/chat/consumers.py` (`/ws/chat/<conversation_id>/`)
   - `moc-backend/orders/consumers.py` (`/ws/orders/<order_id>/`, `/ws/orders/staff/`)
   - `moc-backend/config/middleware.py` (SimpleJWT `?token=<token>`)
5. Frontend components:
   - `moc-frontend/src/components/chat/ChatWidget.tsx`
   - `moc-frontend/src/pages/order/` or tracking components.

Tasks to Investigate:
1. Map exact WebSocket URL schemes in frontend (ws://localhost:8000/ws/... with JWT token in query parameter `?token=...`).
2. Inspect `ChatWidget.tsx`: compare expected JSON payload format (`action: send_message, noi_dung: ...`) with frontend handler.
3. Inspect Order Tracking: how does frontend connect to `/ws/orders/<order_id>/` and handle `order_snapshot` and `order_status_update`?
4. Propose clean custom React hooks and drop-in component updates to connect frontend to Django Channels seamlessly.
5. Deliver your 5-component handoff report with drop-in code blueprints to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2/handoff.md
And notify the orchestrator via send_message.
