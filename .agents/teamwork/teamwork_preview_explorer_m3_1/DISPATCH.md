# Dispatch: Channels & ASGI Architecture Explorer (m3_explorer_1)

## Mission
Investigate and design the ASGI and Django Channels infrastructure for Milestone 3.

## Mandatory Inputs to Read
1. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md`
2. `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md`
3. Current settings in `moc-backend/config/settings.py` and `moc-backend/config/asgi.py`
4. Dependencies installed in the Python virtualenv / requirements (check `channels`, `daphne`, `channels_redis`).

## Specific Investigation Scope
1. **Django Channels Configuration**:
   - Check `INSTALLED_APPS`: ensure `daphne` (if used, placed before `django.contrib.staticfiles`) or `channels` is properly registered.
   - Configure `ASGI_APPLICATION = "config.asgi.application"`.
   - Configure `CHANNEL_LAYERS`:
     * Redis backend using `channels_redis.core.RedisChannelLayer`.
     * Read `REDIS_URL` or `REDIS_HOST`/`REDIS_PORT` from settings/env.
     * Fallback to `channels.layers.InMemoryChannelLayer` for local testing/CI if Redis is unavailable or in unit tests.
2. **ASGI Application Architecture (`moc-backend/config/asgi.py`)**:
   - `ProtocolTypeRouter` separating `http` (`django_asgi_app`) and `websocket`.
   - WebSocket URL routing (`URLRouter`).
   - Authentication middleware: How to authenticate WebSocket connections via JWT token passed in query string (`?token=...`) or `Authorization` header, converting token to `scope['user']` (using `channels.auth.AuthMiddlewareStack` + custom `JWTAuthMiddleware` if necessary).
3. **Routing Layout**:
   - Central websocket routing in `config/routing.py` or `chat/routing.py` and `orders/routing.py`.
   - URL patterns matching:
     * `ws/chat/<str:conversation_id>/`
     * `ws/orders/<str:order_id>/`
     * `ws/orders/staff/`
4. **Channels Test Infrastructure**:
   - How tests can run without live Redis (using `InMemoryChannelLayer` or test runner setting).
   - How `channels.testing.WebsocketCommunicator` can be used for end-to-end consumer tests.

## Output Deliverable
Write your complete architectural and design report to:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_1/handoff.md`
and notify caller when complete.

## 2026-10-14T10:28:49Z
Received dispatch message:
You are m3_explorer_1, the Channels & ASGI Architecture Explorer for Milestone 3.
Your working directory: /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_1
Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_1/DISPATCH.md
MANDATORY: Read /Users/VuVan/Documents/DO-AN/.agents/teamwork/ORIGINAL_REQUEST.md and /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_orchestrator_gen3/PROJECT.md before starting work.
Investigate and provide technical architecture for:
1. Channels settings in moc-backend/config/settings.py (INSTALLED_APPS daphne/channels, ASGI_APPLICATION, CHANNEL_LAYERS redis configuration and in-memory test fallback).
2. ASGI entry point moc-backend/config/asgi.py (ProtocolTypeRouter, URLRouter, AuthMiddlewareStack, and JWT token authentication middleware for WebSocket connections).
3. WebSocket routing structure (config/routing.py or chat/routing.py + orders/routing.py) matching /ws/chat/<conversation_id>/, /ws/orders/<order_id>/, /ws/orders/staff/.
4. Channels test strategy using WebsocketCommunicator.
Write your findings and architecture report to /Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m3_1/handoff.md and notify the caller when done.
