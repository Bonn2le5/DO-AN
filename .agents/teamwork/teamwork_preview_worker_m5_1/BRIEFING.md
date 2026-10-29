# BRIEFING — 2026-10-15T00:23:00Z

## Mission
Implement Milestone 5: Frontend Synchronization & Staff/Admin Portals for Web App Nhà hàng Mộc, ensuring 100% API alignment, live Django Channels WebSocket integration, full Admin/Staff portals, and zero TypeScript compilation errors.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 5 (Frontend Synchronization & Staff/Admin Portals)

## 🔒 Key Constraints
- Minimal change principle: no unnecessary refactoring.
- Maintain genuine implementations (no dummy mocks, fake offline timers, or hardcoded strings).
- Zero TypeScript errors (`npm run build` and `npx tsc --noEmit` exit 0).
- Backend sanity: `manage.py check` passes with 0 issues.
- All backend tests (`recommendations branches chat orders reviews`) and e2e runner pass.

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: 2026-10-15T00:23:00Z

## Task Summary
- **What to build**:
  1. Types & API Callers: `moc-frontend/src/types/index.ts`, `moc-frontend/src/api/mappers.ts`, `moc-frontend/src/api/reservations.api.ts`, `moc-frontend/src/api/orders.api.ts`, `moc-frontend/src/api/admin.api.ts`.
  2. WebSocket Realtime Communication: `moc-frontend/src/services/websocket.ts`, `moc-frontend/src/hooks/useWebSocketChat.ts`, `moc-frontend/src/hooks/useOrderTracking.ts`, `moc-frontend/src/hooks/useStaffOrderStream.ts`, `moc-frontend/src/components/chat/ChatWidget.tsx`, `moc-frontend/src/components/order/OrderTrackingCard.tsx`.
  3. Admin & Staff Portals: `AdminReservationsPage.tsx`, `AdminMenuPage.tsx`, `AdminReviewsPage.tsx`, `AdminChatPage.tsx`, `AdminOrdersPage.tsx`, `AdminLayout.tsx`, `App.tsx`, `OrderSuccessPage.tsx`, `CheckoutPage.tsx`.
  4. Backend Support: `moc-backend/reviews/views.py` `DanhGiaViewSet.get_queryset` staff support.
- **Success criteria**:
  - `cd moc-frontend && npm run build` (Exit code: 0) — PASS
  - `cd moc-frontend && npx tsc --noEmit` (0 TS errors) — PASS
  - `moc-backend/.venv/bin/python moc-backend/manage.py check` (0 issues) — PASS
  - `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders reviews` (58/58 PASS)
  - `moc-backend/.venv/bin/python tests/e2e/runner.py` (60/60 PASS)
- **Interface contracts**: PROJECT.md, Spec Miner & Explorer Handoffs.
- **Code layout**: Frontend under `moc-frontend/src/`, backend under `moc-backend/`.

## Key Decisions Made
- Use exact blueprints provided by spec miner and explorer agents.
- Correct API callers in `reservations.api.ts` (`/payments/vnpay/create/`) and `orders.api.ts` (Vietnamese model field mappings).
- Maintain backward-compatible aliases in `types/index.ts` and bidirectional normalization in `mappers.ts`.
- Integrated realtime staff order stream into `AdminOrdersPage.tsx`.

## Artifact Index
- `.agents/teamwork/teamwork_preview_worker_m5_1/DISPATCH.md` — assignment
- `.agents/teamwork/teamwork_preview_worker_m5_1/BRIEFING.md` — persistent working memory
- `.agents/teamwork/teamwork_preview_worker_m5_1/progress.md` — liveness heartbeat
- `.agents/teamwork/teamwork_preview_worker_m5_1/handoff.md` — final completion report

## Change Tracker
- **Files modified**:
  - `moc-backend/reviews/views.py`: allowed staff to moderate reviews by viewing hidden ones in `get_queryset`
  - `moc-frontend/src/types/index.ts`: added Ingredient, LichSuKho, RefundReceipt, ChatMessage, ChatConversation
  - `moc-frontend/src/api/mappers.ts`: bidirectional mapping for categories, discounts, reviews, dishes
  - `moc-frontend/src/api/reservations.api.ts`: fixed VNPay endpoint `/payments/vnpay/create/`
  - `moc-frontend/src/api/orders.api.ts`: mapped DRF model fields `ma_don_hang`, `tong_tien`, `danh_sach_mon`, `tao_luc`
  - `moc-frontend/src/api/admin.api.ts`: created admin API callers for tables, menu, inventory, reviews, chat
  - `moc-frontend/src/services/websocket.ts`: created central WebSocket resolver with JWT query string handling
  - `moc-frontend/src/hooks/useWebSocketChat.ts`: created 2-way chat hook with Django Channels
  - `moc-frontend/src/hooks/useOrderTracking.ts`: created customer live order FSM tracking hook
  - `moc-frontend/src/hooks/useStaffOrderStream.ts`: created staff live order broadcast stream hook
  - `moc-frontend/src/components/chat/ChatWidget.tsx`: live WS connection, history loading, offline fake mocks removed
  - `moc-frontend/src/components/order/OrderTrackingCard.tsx`: 5-step FSM visual stepper
  - `moc-frontend/src/pages/admin/AdminReservationsPage.tsx`: implemented table floor map and bookings table
  - `moc-frontend/src/pages/admin/AdminMenuPage.tsx`: implemented food catalog, ingredients, inventory transactions
  - `moc-frontend/src/pages/admin/AdminReviewsPage.tsx`: implemented review moderation dashboard
  - `moc-frontend/src/pages/admin/AdminChatPage.tsx`: implemented 2-column live staff chat workspace
  - `moc-frontend/src/pages/admin/AdminOrdersPage.tsx`: enhanced with staff order stream and FSM status transitions
  - `moc-frontend/src/pages/order/OrderSuccessPage.tsx`: embedded OrderTrackingCard with real order ID
  - `moc-frontend/src/pages/checkout/CheckoutPage.tsx`: forwarded real orderId to OrderSuccessPage
  - `moc-frontend/src/components/layout/AdminLayout.tsx`: wired review moderation and chat in sidebar navigation
  - `moc-frontend/src/App.tsx`: registered admin pages under `/admin/*` routes
- **Build status**: Pass (0 errors)
- **Pending issues**: none

## Quality Status
- **Build/test result**: All checks and test suites PASS (TypeScript 0 errors, Django check 0 issues, Django tests 58/58 PASS, E2E runner 60/60 PASS)
- **Lint status**: Clean
- **Tests added/modified**: Full E2E suite compatibility validated
