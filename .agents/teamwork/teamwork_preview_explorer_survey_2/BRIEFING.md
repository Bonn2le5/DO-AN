# BRIEFING — 2026-10-14T03:15:30Z

## Mission
Comprehensive read-only survey of `moc-frontend`: TypeScript build status, route structure, API endpoint callers vs backend endpoints, ChatWidget & WebSocket status, and missing/incomplete Admin/Staff interfaces.

## 🔒 My Identity
- Archetype: explorer
- Roles: Frontend & Admin UI Explorer
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_2
- Original parent: e7c4f174-4311-49a1-ac7b-15083103a212
- Milestone: Survey & Analysis (M1)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Scope: moc-frontend, package.json, routes, API service callers, TypeScript compilation errors, ChatWidget.tsx, Admin/Staff pages (Table Management, Menu/Inventory, Reviews, Staff Chat)
- Deliverables: Complete report in handoff.md and send_message notification to parent

## Current Parent
- Conversation ID: e7c4f174-4311-49a1-ac7b-15083103a212
- Updated: 2026-10-14T03:06:03Z

## Investigation State
- **Explored paths**:
  - `moc-frontend/package.json`, `vite.config.ts`, `.env`
  - `moc-frontend/src/App.tsx`, `src/types/index.ts`, `src/types/auth.ts`
  - `moc-frontend/src/store/authStore.ts`, `src/store/cartStore.ts`
  - `moc-frontend/src/hooks/useReservationFlow.ts`, `useMenuFilters.ts`
  - `moc-frontend/src/api/*.ts` vs `moc-backend/api/urls.py`, `foods/views.py`, `orders/views.py`, `reservations/views.py`, `accounts/views.py`, `analytics/views.py`, `chat/views.py`
  - `moc-frontend/src/components/chat/ChatWidget.tsx`
  - `moc-frontend/src/pages/admin/*`, `src/components/admin/*`
- **Key findings**:
  1. `node_modules` was missing; `npm ci` completed cleanly with 102 packages.
  2. `npm run build` fails with 175 TypeScript errors across 44 files due to an incomplete half-English/half-Vietnamese renaming in types, stores, hooks, and API exports.
  3. Extensive API mismatches: `/api/mon-an/` vs `/api/foods/`, `/api/dat-ban/` vs `/api/reservations/` & `/api/tables/`, `/api/goi-y/` vs `/api/recommendations/`, and payload field discrepancies.
  4. Admin interfaces (Table Management, Menu & Inventory, Reviews, Staff Chat) are either stubbed (`AdminOrdersPage`, `AdminDashboardPage`) or completely missing.
  5. WebSocket is non-existent in `ChatWidget.tsx` (simulated with `setTimeout`) and Order Tracking.
- **Unexplored areas**: None within the frontend scope.

## Key Decisions Made
- Fully documented all 175 compilation errors, all 9 API caller mismatches, missing admin views, and created concrete step-by-step remediation plan for Milestone 5.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_2/handoff.md — Final investigation report
