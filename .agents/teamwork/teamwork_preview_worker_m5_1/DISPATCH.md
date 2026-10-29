# Dispatch: m5_worker_1

## Task
Implement Milestone 5 (Frontend Synchronization & Staff/Admin Portals) for Web App Nhà hàng Mộc based on the exact blueprints and handoff reports produced by `m5_spec_miner_1`, `m5_explorer_portals`, and `m5_explorer_realtime`.

## Working Directory
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Authoritative Documents & Blueprints to Read:
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY - Section R5 & Acceptance Criteria)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_spec_miner_m5_1/handoff.md` (Types, API callers, and mappers blueprints)
4. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/handoff.md` (Admin & Staff portal blueprints)
5. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2/handoff.md` (WebSocket, ChatWidget, and OrderTracking blueprints)

## Implementation Tasks:
1. **Types & API Callers**:
   - Update `moc-frontend/src/types/index.ts`: augment types with Vietnamese/English aliases (`ma_don_hang`, `don_gia`, `trang_thai`, `so_luong`, `tong_tien`, `danh_muc`, etc.).
   - Update `moc-frontend/src/services/api.ts`: fix endpoints (`/api/payments/vnpay/create/`, `/api/chat/conversations/active/`, etc.).
   - Create/update `moc-frontend/src/services/mappers.ts`: bidirectional data normalization.
2. **WebSocket Realtime Communication**:
   - Create `moc-frontend/src/services/websocket.ts`: `getWebSocketUrl` with query string `?token=<jwt>` and dev port 8000 handling.
   - Create `moc-frontend/src/hooks/useWebSocketChat.ts`: Realtime 2-way chat with Django Channels.
   - Create `moc-frontend/src/hooks/useOrderTracking.ts`: Realtime order FSM status updates.
   - Create `moc-frontend/src/hooks/useStaffOrderStream.ts`: Realtime staff order stream.
   - Update `moc-frontend/src/components/chat/ChatWidget.tsx`: Connect to live Django Channels WebSocket, pre-load history, remove fake offline mocks.
   - Create `moc-frontend/src/components/order/OrderTrackingCard.tsx`: Visual stepper for 5-state Order FSM.
3. **Admin & Staff Portals**:
   - Implement `moc-frontend/src/pages/admin/AdminReservationsPage.tsx`: Table layout & reservation management.
   - Implement `moc-frontend/src/pages/admin/AdminMenuPage.tsx`: Menu & inventory management with low-stock alerts.
   - Implement `moc-frontend/src/pages/admin/AdminReviewsPage.tsx`: Review moderation dashboard with visibility toggles.
   - Implement `moc-frontend/src/pages/admin/AdminChatPage.tsx`: Realtime 2-column staff chat workspace.
   - Update `moc-frontend/src/App.tsx` and `moc-frontend/src/components/layout/AdminLayout.tsx`: wire routes and navigation.
4. **Backend Review Moderation Queryset Support**:
   - In `moc-backend/reviews/views.py`: in `DanhGiaViewSet.get_queryset()`, allow staff to view all reviews including unapproved/hidden ones (`hien_thi=False`) so admin can moderate them.

## Verification Commands to Execute:
1. `cd moc-frontend && npm run build` (Must compile cleanly with 0 errors, Exit code: 0)
2. `cd moc-frontend && npx tsc --noEmit` (0 TypeScript errors)
3. `moc-backend/.venv/bin/python moc-backend/manage.py check` (0 issues)
4. `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders reviews`
5. `moc-backend/.venv/bin/python tests/e2e/runner.py` (60/60 PASS)

When finished, write your handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1/handoff.md`
And notify the orchestrator via send_message.
