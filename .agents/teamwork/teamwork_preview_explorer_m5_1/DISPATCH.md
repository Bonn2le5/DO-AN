# Dispatch: m5_explorer_portals

## Role & Mission
Explorer for Milestone 5 (Admin & Staff Portals UI/UX & API Integration).
Investigate existing and missing admin and staff portal pages in `moc-frontend`:
- Quản lý Bàn ăn & Đặt bàn (Table layout & Reservation Management)
- Quản lý Thực đơn & Kho nguyên liệu (Menu & Inventory Management)
- Quản lý Đánh giá (Review Moderation Portal)
- Giao diện Chat của nhân viên (Staff Realtime Chat Portal)

## Authoritative Documents to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md` (MANDATORY - Section R5 & Acceptance Criteria)
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md`
3. Scan directory tree in `moc-frontend/src/pages/admin/` and `moc-frontend/src/pages/staff/` or equivalent.
4. Backend endpoints in `moc-backend/api/urls.py`, `reservations/views.py`, `foods/views.py`, `reviews/views.py`, `chat/views.py`.

## Specific Investigation Tasks
1. Identify all admin/staff routes in `moc-frontend/src/App.tsx` or router file.
2. For each portal page:
   - Does the page exist? Is it a stub / placeholder or fully implemented?
   - What state management or React hooks are used (React Query, Zustand, Context, local state)?
   - Which backend API endpoints are called, and are the query parameters / request payloads matching the backend serializers?
3. Design concrete component blueprints with drop-in code for any missing or stubbed portals, using Tailwind CSS and existing UI components (Lucide icons, etc.).

Write your 5-component handoff report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/handoff.md`
And notify orchestrator via send_message.

## 2026-10-14T16:55:52Z
You are Explorer m5_explorer_portals assigned to investigate Milestone 5 Admin & Staff Portals for Web App Nhà hàng Mộc.

Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1

Read authoritative documents:
1. /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md (MANDATORY - Section R5 & Acceptance Criteria)
2. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen4/PROJECT.md
3. /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/DISPATCH.md
4. Scan directory tree in `moc-frontend/src/pages/admin/` and `moc-frontend/src/pages/staff/`.
5. Backend endpoints in `moc-backend/api/urls.py`, `reservations/views.py`, `foods/views.py`, `reviews/views.py`, `chat/views.py`.

Tasks to Investigate:
1. Examine all admin and staff routes in `moc-frontend/src/App.tsx` or router file.
2. Inspect the 4 required portal pages:
   - Quản lý Bàn ăn & Đặt bàn (Table layout & Reservation Management)
   - Quản lý Thực đơn & Kho nguyên liệu (Menu & Inventory Management)
   - Quản lý Đánh giá (Review Moderation Portal)
   - Giao diện Chat của nhân viên (Staff Realtime Chat Portal)
3. For each portal, identify missing components, stubs, API payload discrepancies, and design drop-in React component blueprints using Tailwind CSS and existing UI libraries.
4. Deliver your 5-component handoff report with drop-in code blueprints to:
   /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/handoff.md
And notify the orchestrator via send_message.
