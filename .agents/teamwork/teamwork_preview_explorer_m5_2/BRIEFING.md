# BRIEFING — 2026-10-15T00:02:00Z

## Mission
Investigate Milestone 5 Frontend WebSocket Integration for Web App Nhà hàng Mộc (ChatWidget and Order Tracking realtime updates).

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: milestone_5

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Deliver 5-component handoff report with drop-in code blueprints to handoff.md
- Map exact WS schemes, payloads, order tracking, chat widget integration
- Maintain progress.md heartbeat

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `moc-backend/config/routing.py`, `moc-backend/config/asgi.py`, `moc-backend/config/middleware.py`
  - `moc-backend/chat/routing.py`, `moc-backend/chat/consumers.py`, `moc-backend/chat/views.py`, `moc-backend/chat/tests.py`
  - `moc-backend/orders/routing.py`, `moc-backend/orders/consumers.py`, `moc-backend/orders/services.py`, `moc-backend/orders/views.py`
  - `moc-backend/api/urls.py`
  - `moc-frontend/src/components/chat/ChatWidget.tsx`
  - `moc-frontend/src/pages/order/OrderSuccessPage.tsx`
  - `moc-frontend/src/pages/account/AccountOrdersPage.tsx`
  - `moc-frontend/src/pages/admin/AdminOrdersPage.tsx`
  - `moc-frontend/src/store/authStore.ts`, `moc-frontend/src/api/client.ts`, `moc-frontend/src/types/index.ts`
  - `tests/e2e/tier1/test_t1_realtime.py`, `tests/e2e/tier1/test_t1_frontend.py`
- **Key findings**:
  1. Token Query Parameter: Backend ASGI `JWTAuthMiddleware` explicitly extracts `?token=<access_token>` from query string. Browser WebSocket cannot set Authorization headers, so frontend must append `?token=${token}`. If omitted, backend immediately closes with `4401`.
  2. Conversation Access: `ChatConsumer` validates `conversation_id` against `HoiThoai.id` (not `user.id`). Frontend must fetch `/api/chat/conversations/active/` to get real conversation ID and `/api/chat/conversations/<id>/messages/` to load message history.
  3. Action Payload Format: Backend accepts `action: "send_message"`, `content: string`. On connect, backend emits `type: "connection_established"`, which was erroneously parsed as a chat message in the initial ChatWidget code.
  4. Order FSM Push: `OrderTrackingConsumer` at `/ws/orders/<order_id>/` emits `order_snapshot` on connect and `order_status_update` on FSM transition triggered by `DichVuDonHang.doi_trang_thai`.
  5. Staff Order Stream: `StaffOrderConsumer` at `/ws/orders/staff/` provides real-time kitchen/staff monitoring with `order_status_update` and `order_created` events.
- **Unexplored areas**: None. Complete mapping accomplished.

## Key Decisions Made
- Architecture of custom hooks designed: `useWebSocketChat` for customer/staff chat, `useOrderTracking` for individual order FSM tracking, and `useStaffOrderStream` for administrative/kitchen live order monitoring.
- Reusable `OrderTrackingCard` component designed to render 5-step FSM lifecycle (`cho_tiep_nhan` -> `da_xac_nhan` -> `dang_che_bien` -> `san_sang` -> `hoan_tat`).

## Artifact Index
- DISPATCH.md — Initial dispatch instructions
- BRIEFING.md — Situational awareness
- progress.md — Heartbeat and activity log
- handoff.md — Final 5-component handoff report with drop-in blueprints
