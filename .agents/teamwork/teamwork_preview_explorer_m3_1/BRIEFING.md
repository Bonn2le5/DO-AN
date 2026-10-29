# BRIEFING — 2026-10-14T10:41:00Z

## Mission
Investigate and design the ASGI and Django Channels infrastructure for Milestone 3 (real-time chat and order notifications).

## 🔒 My Identity
- Archetype: explorer
- Roles: Channels & ASGI Architecture Explorer
- Working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_1
- Original parent: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Milestone: Milestone 3

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly in source code.
- Provide comprehensive architectural design for Django Channels settings, ASGI entry point, JWT auth middleware for WebSockets, routing structure, and Channels testing strategy.

## Current Parent
- Conversation ID: 3b4ac039-b543-49a4-9b3d-21e996771d3e
- Updated: 2026-10-14T10:30:00Z

## Investigation State
- **Explored paths**:
  * `moc-backend/config/settings.py` (INSTALLED_APPS, ASGI_APPLICATION, CHANNEL_LAYERS, CACHES)
  * `moc-backend/config/asgi.py` (ProtocolTypeRouter, get_asgi_application initialization order)
  * `moc-backend/chat/` (models HoiThoai & TinNhan, serializers, views)
  * `moc-backend/orders/` (models DonHang & LichSuTrangThaiDon, services FSM transitions)
  * `moc-backend/accounts/models.py` (NguoiDung, la_nhan_vien_nha_hang)
  * `.venv/lib/python3.9/site-packages/` (channels 4.3.2, channels_redis 4.3.0, daphne absence)
  * `.agents/teamwork/teamwork_preview_spec_miner_m3_1/handoff.md` (message contracts & FSM matrix)
- **Key findings**:
  * `channels` 4.3.2 and `channels_redis` 4.3.0 are installed; `daphne` is NOT installed in `.venv`.
  * Environment is offline (no PyPI downloads), so `INSTALLED_APPS` must contain `"channels"`, but CANNOT contain `"daphne"`.
  * `from channels.testing import WebsocketCommunicator` fails unless `daphne` and `daphne.testing` are stubbed in `sys.modules`. With stubbing, `WebsocketCommunicator` functions 100% reliably.
  * `InMemoryChannelLayer` works completely without external Redis daemon or open socket connections.
  * Browser WebSockets cannot send `Authorization` HTTP headers; `JWTAuthMiddleware` must extract `?token=<jwt>` from query string, decode with SimpleJWT `AccessToken`, and set `scope['user']`.
  * Route ordering: `ws/orders/staff/` must precede `ws/orders/<str:order_id>/` to prevent route collision.
- **Unexplored areas**: None. All 4 target areas thoroughly verified with executable code proofs.

## Key Decisions Made
- Architecture design completed for Settings, ASGI entry point, JWT Middleware, Routing layout, and Testing Strategy.
- Ready to write final `handoff.md`.

## Artifact Index
- DISPATCH.md — Dispatch instructions
- BRIEFING.md — Working memory and context
- progress.md — Liveness heartbeat and step tracking
- handoff.md — Final architecture and handoff report
