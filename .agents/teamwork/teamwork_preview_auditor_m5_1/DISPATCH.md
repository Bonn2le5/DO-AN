## 2026-10-14T23:49:32Z
You are Forensic Integrity Auditor m5_auditor_1 assigned to audit Milestone 5 (Frontend Synchronization & Staff/Admin Portals) for Web App Nhà hàng Mộc.

Your Working Directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m5_1
All your working metadata, progress.md, and handoff.md MUST be saved in your working directory.

MANDATORY FIRST STEP: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md completely.
Also read:
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen5/PROJECT.md
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m5_1/handoff.md

Your Forensic Audit Focus (ZERO TOLERANCE FOR CHEATING / MOCKS / FACADES):
1. Execute thorough static and dynamic forensics on all Milestone 5 code:
   - Check `moc-frontend/src/components/chat/ChatWidget.tsx` and `useWebSocketChat.ts`: verify NO mock timers (`setTimeout`), NO fake responses, NO simulated chat. Verify genuine connection to Django Channels `/ws/chat/...` with real JWT authentication and real PostgreSQL persistence.
   - Check `moc-frontend/src/components/order/OrderTrackingCard.tsx` and `useOrderTracking.ts`: verify genuine subscription to `/ws/orders/...`, real handling of `order_snapshot` and `order_status_update`.
   - Check `moc-frontend/src/pages/admin/AdminReservationsPage.tsx`, `AdminMenuPage.tsx`, `AdminReviewsPage.tsx`, `AdminChatPage.tsx`, `AdminOrdersPage.tsx`: verify genuine API integration, NO hardcoded dummy lists, NO stubs returning fake success.
   - Check `moc-frontend/src/api/admin.api.ts`, `orders.api.ts`, `reservations.api.ts`, `mappers.ts`: verify genuine REST API calls to Django backend endpoints.
   - Check `moc-backend/reviews/views.py`: verify authentic permission checks and genuine DB queries.
2. Verification commands:
   - Run `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit && npm run build`
   - Run `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python moc-backend/manage.py check`
   - Run `cd /Users/VuVan/Documents/DO-AN && moc-backend/.venv/bin/python tests/e2e/runner.py`
3. Forensic Verdict:
   - If ANY cheating, mock facades, fake timer data, or circumvented requirements are detected: report **INTEGRITY VIOLATION** with full evidence.
   - If implementation is genuine, sound, and compliant: report **CLEAN**.
4. Output your full audit report to `handoff.md` in your working directory and notify the orchestrator via send_message.
