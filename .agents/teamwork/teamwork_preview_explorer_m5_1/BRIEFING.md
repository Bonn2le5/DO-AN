# BRIEFING — 2026-10-14T17:03:00Z

## Mission
Investigate Milestone 5 Admin & Staff Portals (UI/UX, routing, API payload mapping, missing/stubbed components) for Web App Nhà hàng Mộc and provide drop-in React blueprints.

## 🔒 My Identity
- Archetype: explorer
- Roles: [m5_explorer_portals, investigation, synthesis]
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1
- Original parent: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Milestone: Milestone 5 (Admin & Staff Portals)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement source code directly
- Only write metadata, reports, and blueprints within `.agents/teamwork/teamwork_preview_explorer_m5_1/`
- Deep analysis of 4 required portals: Table/Reservations, Menu/Inventory, Review Moderation, Staff Realtime Chat

## Current Parent
- Conversation ID: e1a47f66-ae44-4e72-ae56-b7ecb23a0048
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `moc-frontend/src/App.tsx`, `AdminLayout.tsx`, `AdminGuard.tsx`, `AdminOrdersPage.tsx`, `AdminDashboardPage.tsx`
  - `moc-backend/api/urls.py`, `reservations/views.py`, `reservations/serializers.py`, `reservations/models.py`
  - `moc-backend/foods/views.py`, `foods/serializers.py`, `foods/models.py`
  - `moc-backend/reviews/views.py`, `reviews/serializers.py`, `reviews/models.py`
  - `moc-backend/chat/views.py`, `chat/serializers.py`, `chat/consumers.py`, `chat/models.py`, `config/asgi.py`, `config/middleware.py`
  - `moc-frontend/src/api/` (`client.ts`, `auth.api.ts`, `foods.api.ts`, `reservations.api.ts`, `reviews.api.ts`, `orders.api.ts`, `mappers.ts`)
  - `moc-frontend/src/types/` (`index.ts`, `auth.ts`)
  - `moc-frontend/src/components/chat/ChatWidget.tsx`
- **Key findings**:
  - `App.tsx` has stub placeholder divs for `/admin/reservations` and `/admin/menu`; missing `/admin/reviews` and `/admin/chat`.
  - `AdminLayout.tsx` lacks sidebar navigation items for Reviews and Staff Chat.
  - Review moderation caveat: `DanhGiaViewSet.get_queryset` hardcodes `hien_thi=True`, preventing staff from viewing hidden reviews without backend adjustment.
  - Chat WebSocket requires `?token=<jwt>` query parameter for `JWTAuthMiddlewareStack` to authenticate user.
  - `ChatConsumer` routes by conversation ID (`HoiThoai.id`), not user ID. Staff has global access to all rooms.
  - All 4 portal pages need drop-in React component blueprints using Tailwind CSS v4, Lucide icons, and existing client/store conventions.
- **Unexplored areas**: None, full scope investigated.

## Key Decisions Made
- Structured blueprints into 4 distinct modular admin pages: `AdminReservationsPage.tsx`, `AdminMenuPage.tsx`, `AdminReviewsPage.tsx`, and `AdminChatPage.tsx`.
- Defined required API helper methods to be added to `reservations.api.ts`, `foods.api.ts`, `reviews.api.ts`, and a new `chat.api.ts`.
- Outlined necessary route additions in `App.tsx` and sidebar links in `AdminLayout.tsx`.

## Artifact Index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/DISPATCH.md — Dispatch log
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/BRIEFING.md — Working memory index
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/progress.md — Liveness heartbeat
- /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_1/handoff.md — Final 5-component handoff report
