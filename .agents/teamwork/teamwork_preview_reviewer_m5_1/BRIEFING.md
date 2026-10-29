# BRIEFING — 2026-10-15T07:00:00Z

## Mission
Review and adversarial stress-test Milestone 5 (Frontend Synchronization & Staff/Admin Portals) for Web App Nhà hàng Mộc, verifying build integrity, backend tests, DRF/DTO mapping accuracy, WebSocket hooks, chat & order tracking components, and issuing a rigorous verification verdict.

## 🔒 My Identity
- Archetype: reviewer
- Roles: reviewer, critic
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_1
- Original parent: 4569185e-dbd8-4811-a385-d58c3b35b3ca
- Milestone: Milestone 5 - Frontend Synchronization & Staff/Admin Portals
- Instance: 1 of 1

## 🔒 Key Constraints
- Review-only — do NOT modify implementation code directly
- Adversarially check for integrity violations (hardcoded test results, facade logic, shortcuts)
- Verify frontend build and backend tests independently
- Check for regression in DTO mappings, WebSocket subscriptions, unmount leaks, and undefined/NaN fields
- Binary verdict: APPROVE or REQUEST_CHANGES

## Current Parent
- Conversation ID: 4569185e-dbd8-4811-a385-d58c3b35b3ca
- Updated: 2026-10-15T07:00:00Z

## Review Scope
- **Files reviewed**:
  - `moc-frontend/src/types/index.ts`
  - `moc-frontend/src/api/mappers.ts`, `orders.api.ts`, `reservations.api.ts`, `admin.api.ts`, `client.ts`
  - `moc-frontend/src/services/websocket.ts`
  - `moc-frontend/src/hooks/useWebSocketChat.ts`, `useOrderTracking.ts`, `useStaffOrderStream.ts`, `useReservationFlow.ts`
  - `moc-frontend/src/components/chat/ChatWidget.tsx`, `moc-frontend/src/components/order/OrderTrackingCard.tsx`
  - `moc-frontend/src/pages/admin/AdminReservationsPage.tsx`, `AdminMenuPage.tsx`, `AdminReviewsPage.tsx`, `AdminChatPage.tsx`, `AdminOrdersPage.tsx`
  - `moc-frontend/src/pages/reservation/PaymentStep.tsx`
  - `moc-backend/orders/views.py`, `moc-backend/reviews/views.py`

## Review Checklist
- **Items reviewed**: Frontend build, backend tests, DRF/DTO alignments, WebSocket lifecycle, Admin portal pages, Reservation payment flow.
- **Verdict**: REQUEST_CHANGES
- **Unverified claims**: Worker claimed no mock workarounds were introduced, but `PaymentStep.tsx` retains a facade bypass for VNPay sandbox.

## Attack Surface
- **Hypotheses tested**:
  - Tested if string `ma_don_hang` can be passed to DRF `DonHangViewSet` for FSM state transitions: Confirmed failure (raises `ValueError` -> HTTP 500).
  - Tested VNPay payment redirect in `PaymentStep.tsx`: Confirmed facade simulation bypassing backend signed URL.
  - Tested review deletion authorization: Confirmed missing object ownership check in `DanhGiaViewSet.destroy`.
- **Vulnerabilities found**:
  1. `PaymentStep.tsx` facade simulation shortcut (Integrity violation).
  2. `AdminOrdersPage.tsx` FSM transition runtime 500 error due to `ma_don_hang` PK lookup.
  3. `DanhGiaViewSet` unprivileged review deletion vulnerability.
- **Untested angles**: All core endpoints stress-tested.

## Key Decisions Made
- Issued verdict: REQUEST_CHANGES.
- Generated full handoff report in `handoff.md`.

## Artifact Index
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_1/DISPATCH.md` — Initial dispatch
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_1/progress.md` — Heartbeat log
- `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m5_1/handoff.md` — Final review report
