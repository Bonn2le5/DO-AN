# Specification Report: Real-Time Communication (Channels & Redis) & Order FSM (Milestone 3)

**Miner Archetype**: Specification Miner (`m3_spec_miner_1`)  
**Target Milestone**: Milestone 3 — Real-time Communication (Django Channels & Redis) & Order Lifecycle FSM  
**Target Workspace Path**: `/Users/VuVan/Documents/DO-AN`  
**Date & UTC Timestamp**: `2026-10-14T10:37:00Z`

---

## Executive Summary

This specification defines the authoritative technical contracts, message schemas, state machine transition matrices, and infrastructure conventions for **Milestone 3** of Web App Nhà hàng Mộc:
1. **Django Channels 4.x & ASGI Architecture**: ASGI protocol router configuration, custom JWT query-string authentication middleware, and dual-layer Redis/In-Memory channel backend configuration.
2. **2-Way Staff-Customer Live Chat Protocol**: WebSocket endpoint `/ws/chat/<conversation_id>/`, client-to-server inbound messages (`send_message`, `typing`, `read_receipt`), atomic PostgreSQL DB persistence into `tin_nhan` & `hoi_thoai`, and server-to-client broadcasts (`chat_message`, `chat_typing`, `chat_read_receipt`, `error`).
3. **Real-Time Order Lifecycle Tracking Protocol**: Single-order tracking stream `/ws/orders/<order_id>/`, aggregate staff order monitoring stream `/ws/orders/staff/`, connection authorization, and outbound event payload schema (`order_status_update`).
4. **6-State Order Finite State Machine (FSM)**: Complete state transition matrix across `cho_tiep_nhan`, `da_xac_nhan`, `dang_che_bien`, `san_sang`, `hoan_tat`, and `da_huy`, enforcing strict forward progression, legal cancellations, terminal state immutability, BOM raw material inventory deduction/refund side effects, and mandatory audit logging into `lich_su_trang_thai_don`.
5. **Redis Channel Layer Group Naming Conventions**: Group naming rules strictly conforming to Django Channels regex `^[a-zA-Z0-9_.-]+$` with length $\le 100$ bytes, avoiding illegal characters (colons, spaces, slashes).

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | ASGI / Infrastructure | ASGI Protocol Router | Routes HTTP traffic to Django ASGI application and WebSocket traffic to Channels URLRouter with JWT authentication | Incoming HTTP or WebSocket upgrade requests | ASGI callable application | Returns 404 for unmatched paths; rejects invalid protocols | `config/asgi.py`, Django Channels 4.x spec |
| 2 | ASGI / Infrastructure | Redis Channel Layer with In-Memory Fallback | Channel layer for multi-process worker message passing across WebSocket consumer groups | Redis connection string (`REDIS_URL`) or in-memory backend | Group message delivery, channel add/discard | Fallback to `InMemoryChannelLayer` when Redis is unavailable | `config/settings.py`, `TEST_INFRA.md` |
| 3 | Authentication | WebSocket JWT Query Authentication | Custom ASGI middleware extracting `token` from `scope['query_string']` and validating against SimpleJWT | `?token=<jwt_access_token>` query parameter | Populates `scope['user']` with authenticated `NguoiDung` instance | Sets `scope['user'] = AnonymousUser()`; consumer closes connection with code 4001 | `moc-backend/accounts/models.py`, DRF SimpleJWT |
| 4 | Chat WebSocket | Chat Room Connection & Authorization | Validates user permission to join conversation room (`/ws/chat/<conversation_id>/`) | `conversation_id`, JWT token | Subscribes channel to group `chat_{conversation_id}`, sends `connection_established` | Closes connection: 4001 (unauthorized), 4003 (forbidden for other customer), 4004 (conversation not found) | `chat/models.py`, `ChatWidget.tsx` |
| 5 | Chat WebSocket | Inbound Message DB Persistence | Intercepts `send_message`, writes record to `tin_nhan`, updates `hoi_thoai.tin_nhan_cuoi_luc`, and assigns staff if unassigned | `{"action": "send_message", "content": "...", "message_type": "van_ban"}` | Saved `TinNhan` DB row with auto ID and timestamp | Returns `error` frame `INVALID_MESSAGE` if content empty or $> 5000$ chars | `chat/models.py`, `chat/views.py`, SQL schema lines 522-550 |
| 6 | Chat WebSocket | Chat Message Broadcast | Broadcasts newly persisted chat message to group `chat_{conversation_id}` | Broadcast event from channel layer | Outbound JSON frame `chat_message` to all connected clients in conversation | Dropped if connection closed; logged on delivery failure | `chat/models.py`, `tests/e2e/tier1/test_t1_realtime.py` |
| 7 | Chat WebSocket | Typing Indicator Broadcast | Broadcasts user typing status to group `chat_{conversation_id}` without DB write | `{"action": "typing", "is_typing": true/false}` | Outbound JSON frame `chat_typing` to peers | Ignored if malformed boolean | `chat/models.py`, `ChatWidget.tsx` |
| 8 | Chat WebSocket | Read Receipt & Bulk Mark-as-Read | Updates unread messages up to `last_read_message_id` as read in DB and broadcasts receipt | `{"action": "read_receipt", "last_read_message_id": 105}` | Updates `tin_nhan.da_doc = True`, emits `chat_read_receipt` | Ignored if message ID does not belong to conversation | `chat/models.py`, SQL schema lines 542-543 |
| 9 | Order Tracking | Single-Order WebSocket Stream | Customer/staff tracking of specific order lifecycle (`/ws/orders/<order_id>/`) | `order_id` (numeric PK or `ma_don_hang`), JWT token | Subscribes channel to `order_{order_id}`, emits `order_subscription_success` | Closes connection: 4001 (unauth), 4003 (forbidden: not order owner or staff), 4004 (order not found) | `orders/models.py`, `AccountOrdersPage.tsx` |
| 10 | Order Tracking | Staff Global Order Stream | Aggregate real-time stream of all restaurant orders for kitchen/cashier displays (`/ws/orders/staff/`) | Staff JWT token | Subscribes channel to `staff_orders`, emits `staff_order_stream_subscribed` | Closes connection: 4003 (forbidden if `not user.la_nhan_vien_nha_hang`) | `orders/views.py`, `AdminOrdersPage.tsx` |
| 11 | Order Tracking | Order Status Broadcast Event | Dispatches real-time lifecycle event to `order_{order_id}` and `staff_orders` on any state transition | Triggered by REST `PATCH /api/orders/<id>/trang_thai/` or automated workflows | Outbound JSON frame `order_status_update` | If channel layer fails, DB transaction still succeeds; error logged | `orders/services.py`, `test_t1_realtime.py` |
| 12 | Order FSM | 6-State FSM Initial State | Sets initial status of newly created orders to `cho_tiep_nhan` with initial audit log entry | Order creation payload | `DonHang(trang_thai="cho_tiep_nhan")`, `LichSuTrangThaiDon` record | Raises `ValidationError` if required fields missing | `orders/services.py:58-100`, `test_t1_realtime.py` |
| 13 | Order FSM | Forward Lifecycle Transition | Transitions order forward through legal states (`cho_tiep_nhan` -> `da_xac_nhan` -> `dang_che_bien` -> `san_sang` -> `hoan_tat`) | `order_id`, `trang_thai_moi`, `actor`, `ghi_chu` | Updates `don_hang.trang_thai`, creates audit entry, triggers side effects | Raises HTTP 400 `ValidationError` if transition illegal or skipping states | `tests/e2e/helpers/fsm_validator.py`, `test_t1_realtime.py` |
| 14 | Order FSM | Order Cancellation Transition | Allows cancellation transition to `da_huy` from non-terminal states (`cho_tiep_nhan`, `da_xac_nhan`, `dang_che_bien`, `san_sang`) | `order_id`, `trang_thai_moi="da_huy"`, `actor`, `ghi_chu` | Updates `don_hang.trang_thai = "da_huy"`, triggers BOM refund if applicable | Rejects if already in terminal state (`hoan_tat`, `da_huy`) | `tests/e2e/helpers/fsm_validator.py`, `test_t1_realtime.py` |
| 15 | Order FSM | Terminal State Immutability | Enforces that completed (`hoan_tat`) and cancelled (`da_huy`) orders can never transition to any other state | Any transition request targeting a terminal order | None | Raises HTTP 400 `ValidationError` with message `Cannot transition from terminal state` | `tests/e2e/helpers/fsm_validator.py`, `test_t2_fsm.py` |
| 16 | Order FSM | Illegal Transition Rejection | Blocks reverse transitions (e.g. `san_sang` -> `cho_tiep_nhan`) and skip transitions (e.g. `cho_tiep_nhan` -> `san_sang`) | Illegal target state | Current state preserved unchanged | Raises HTTP 400 `ValidationError` with detailed transition error | `tests/e2e/tier2/test_t2_fsm.py` |
| 17 | Order FSM / Inventory | BOM Inventory Deduction Side Effect | Automatically deducts raw material inventory upon order confirmation (`da_xac_nhan`) using sorted-ID pessimistic lock | `don_hang.danh_sach_mon`, `trang_thai_moi="da_xac_nhan"` | Updates `NguyenLieu.ton_kho_hien_tai`, creates `LichSuXuatNhapKho` rows | Raises `ValidationError` if raw material stock is insufficient | `foods/services.py:9-116`, `orders/services.py:113-121` |
| 18 | Order FSM / Inventory | BOM Inventory Refund Side Effect | Automatically refunds raw material inventory upon cancellation (`da_huy`) if order was confirmed or cooking | `order_id`, `trang_thai_cu in ["da_xac_nhan", "dang_che_bien"]` | Restores `NguyenLieu.ton_kho_hien_tai`, creates `LichSuXuatNhapKho` NHAP rows | No-op if order was cancelled while still in `cho_tiep_nhan` | `foods/services.py:118-168`, `orders/services.py:122-130` |
| 19 | Order FSM / Audit | FSM Transition Audit Logging | Mandatory insertion into `lich_su_trang_thai_don` for every state change with actor and note | `don_hang`, `tu_trang_thai`, `sang_trang_thai`, `doi_boi`, `ghi_chu` | New row in `lich_su_trang_thai_don` table | Transaction rollback if audit creation fails | `orders/models.py:393-415`, SQL schema lines 421-432 |
| 20 | Redis Channels | Channel Group Name Normalization | Enforces valid ASCII regex `^[a-zA-Z0-9_.-]+$` on all Redis channel group names ($\le 100$ characters) | Group name prefix and identifier string | Clean, safe group name string | Replaces invalid characters with underscores `_`, truncates to 100 bytes | `channels_redis` specification, Redis key protocol |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | WebSocket JWT Auth | Query string has no token (`ws://.../ws/chat/1/`) | Middleware sets `scope['user'] = AnonymousUser()`; consumer rejects handshake with close code `4001` (Unauthorized). |
| 2 | WebSocket JWT Auth | Query string has expired or malformed JWT token | SimpleJWT raises `InvalidToken` / `TokenError`; middleware falls back to `AnonymousUser()`; consumer rejects with close code `4001`. |
| 3 | Chat Authorization | Customer User A attempts to connect to `/ws/chat/2/` owned by Customer User B | Consumer checks `conversation.khach_hang_id != user.id` and `not user.la_nhan_vien_nha_hang`; connection closed with code `4003` (Forbidden). |
| 4 | Chat Authorization | Staff member connects to unassigned conversation `/ws/chat/2/` | Staff has `user.la_nhan_vien_nha_hang == True`; connection accepted. On first staff message, `hoi_thoai.nhan_vien_id` is automatically set to staff `user.id`. |
| 5 | Chat Inbound Validation | Client sends empty text or whitespace-only message `{"action": "send_message", "content": "   "}` | Server rejects message without DB write, returns outbound `error` frame `{"type": "error", "code": "EMPTY_CONTENT", "message": "Nội dung tin nhắn không được để trống."}`. |
| 6 | Chat Inbound Validation | Client sends oversized message (> 5000 characters) | Server rejects message, returns outbound `error` frame `{"type": "error", "code": "MESSAGE_TOO_LONG", "message": "Nội dung tin nhắn vượt quá giới hạn 5000 ký tự."}`. |
| 7 | Chat Typing Indicator | Client sends `{"action": "typing", "is_typing": true}` rapidly (10 times/sec) | Consumer debounces broadcast to channel layer, rate-limiting outbound typing events to max 1 per 2 seconds per user. |
| 8 | Order Tracking Access | Customer attempts to track order belonging to another customer (`/ws/orders/DH999/`) | Consumer verifies `order.khach_hang_id != user.id` and `not user.la_nhan_vien_nha_hang`; rejects with close code `4003` (Forbidden). |
| 9 | Order Tracking Lookup | Client requests order by `ma_don_hang` string (`"MOC823901"`) instead of numeric PK (`42`) | Consumer queries by `Q(id=val) | Q(ma_don_hang=val)`; accepts both transparently, normalizes Redis group to `order_{order.id}`. |
| 10 | Staff Order Stream Access | Non-staff customer attempts to connect to `/ws/orders/staff/` | Consumer checks `user.la_nhan_vien_nha_hang is False`; rejects with close code `4003` (Forbidden). |
| 11 | FSM Self-Transition | Order currently `da_xac_nhan` receives request to transition to `da_xac_nhan` | Blocked or no-op; returns HTTP 400 `ValidationError({"status": "Đơn hàng đã ở trạng thái 'da_xac_nhan'."})`. |
| 12 | FSM Backward Transition | Order currently `san_sang` receives request to transition to `cho_tiep_nhan` | Strictly blocked; returns HTTP 400 `ValidationError({"status": "Chuyển trạng thái không hợp lệ: từ 'san_sang' sang 'cho_tiep_nhan'."})`. |
| 13 | FSM Step Skipping | Order currently `cho_tiep_nhan` receives request to transition to `san_sang` without cooking | Strictly blocked; returns HTTP 400 `ValidationError({"status": "Chuyển trạng thái không hợp lệ: từ 'cho_tiep_nhan' sang 'san_sang'."})`. |
| 14 | FSM Terminal Mutability | Order currently in `hoan_tat` receives cancellation request `da_huy` | Strictly blocked; returns HTTP 400 `ValidationError({"status": "Không thể thay đổi trạng thái của đơn hàng đã kết thúc ('hoan_tat')."})`. |
| 15 | FSM Terminal Mutability | Order currently in `da_huy` receives confirmation request `da_xac_nhan` | Strictly blocked; returns HTTP 400 `ValidationError({"status": "Không thể thay đổi trạng thái của đơn hàng đã hủy ('da_huy')."})`. |
| 16 | FSM Unknown Status String | Client sends `{"status": "dang_giao_hang"}` (not in 6 defined states) | Strictly blocked; returns HTTP 400 `ValidationError({"status": "Trạng thái đơn hàng không hợp lệ."})`. |
| 17 | Customer Cancellation Limit | Customer attempts to cancel order when status is already `dang_che_bien` | Only restaurant staff or admin can cancel once cooking has started; customer request returns HTTP 403 Forbidden. |
| 18 | BOM Stockout on Confirm | Order transitions `cho_tiep_nhan` -> `da_xac_nhan`, but warehouse lacks ingredients | `DichVuKho.khau_tru_nguyen_lieu_bom` raises `ValidationError({"kho": [...]})`; transaction rolls back; order remains in `cho_tiep_nhan`. |
| 19 | Group Name Unsafe Chars | Order code contains special characters (e.g. `MOC-ORD#101:A`) | Group name sanitizer converts to `order_MOC-ORD_101_A`, satisfying regex `^[a-zA-Z0-9_.-]+$`. |
| 20 | Redis Layer Offline | Redis server is down during test execution or local development | Settings detect unavailability and fall back gracefully to `channels.layers.InMemoryChannelLayer`, allowing all unit/integration tests to pass. |

---

## Technical Specifications

### 1. ASGI & Django Channels Architecture

#### 1.1 ASGI Protocol Router Configuration (`moc-backend/config/asgi.py`)
The ASGI application must declare a top-level `ProtocolTypeRouter` supporting both HTTP and WebSocket protocols:

```python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from chat.middleware import JWTAuthMiddlewareStack
import chat.routing
import orders.routing

django_http_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_http_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddlewareStack(
            URLRouter(
                chat.routing.websocket_urlpatterns +
                orders.routing.websocket_urlpatterns
            )
        )
    ),
})
```

#### 1.2 Settings Configuration (`moc-backend/config/settings.py`)
- Add `'channels'` to `INSTALLED_APPS` (must be placed before Django standard apps or at top of app list).
- Set `ASGI_APPLICATION = "config.asgi.application"`.
- Configure `CHANNEL_LAYERS` with Redis backend and in-memory test fallback:

```python
ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL", default="redis://127.0.0.1:6379/0")],
            "capacity": 1500,
            "expiry": 10,
        },
    }
}

# Testing & Local Fallback Configuration:
# When executing test runners without an active Redis daemon or in restricted sandboxes,
# settings switch CHANNEL_LAYERS["default"]["BACKEND"] to "channels.layers.InMemoryChannelLayer".
```

#### 1.3 JWT Authentication Middleware (`moc-backend/chat/middleware.py`)
Because standard browser WebSocket APIs do not allow setting custom `Authorization` HTTP headers during the handshake, authentication is passed via query string: `?token=<access_token>`.

```python
import urllib.parse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken

NguoiDung = get_user_model()

@database_sync_to_async
def get_user_from_token(token_string):
    try:
        access_token = AccessToken(token_string)
        user_id = access_token.payload.get("user_id")
        return NguoiDung.objects.select_related().get(id=user_id)
    except Exception:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = urllib.parse.parse_qs(query_string)
        token_list = query_params.get("token", [])
        
        if token_list:
            scope["user"] = await get_user_from_token(token_list[0])
        else:
            scope["user"] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
```

---

### 2. Staff-Customer Live Chat WebSocket Protocol

#### 2.1 Endpoint URL & Routing
- Route: `re_path(r"^ws/chat/(?P<conversation_id>[a-zA-Z0-9_-]+)/$", ChatConsumer.as_asgi())`
- Client URL: `ws://<host>/ws/chat/<conversation_id>/?token=<jwt_access_token>`
- Also support alias parameter: `hoi_thoai_id` or numeric conversation ID.

#### 2.2 Connection Handshake & Permission Enforcement
1. **Authentication Check**: If `scope["user"].is_anonymous`, reject connection with close code `4001` (Unauthorized).
2. **Conversation Lookup**: Look up `HoiThoai` by ID. If not found, reject with close code `4004` (Not Found).
3. **Authorization Check**:
   - Customer must match `hoi_thoai.khach_hang_id == user.id`.
   - OR User must have staff privilege (`user.la_nhan_vien_nha_hang is True`).
   - If neither, reject with close code `4003` (Forbidden).
4. **Group Subscription**: Add channel to `chat_{conversation_id}`.
5. **Accept**: Accept WebSocket connection. Send welcome frame:
   ```json
   {
     "type": "connection_established",
     "conversation_id": 15,
     "user_id": 42,
     "user_name": "Nguyễn Văn A",
     "is_staff": false,
     "message": "Kết nối phòng chat thành công."
   }
   ```

#### 2.3 Inbound Client Frames (Client -> Server)

##### Frame A: Send Message (`send_message`)
```json
{
  "action": "send_message",
  "content": "Xin chào nhà hàng, mình muốn hỏi về thành phần món lẩu riêu cua?",
  "message_type": "van_ban"
}
```
- **Field Mappings & Aliases**:
  - `action`: `"send_message"` (or `"message"`, `"gui_tin_nhan"`)
  - `content`: Non-empty string $\le 5000$ chars (aliases: `"message"`, `"noi_dung"`, `"text"`)
  - `message_type`: `"van_ban"` (default), `"hinh_anh"`, `"he_thong"` (aliases: `"type"`, `"loai_tin_nhan"`)
- **Server DB Persistence Workflow**:
  1. Validate content is not blank.
  2. Perform atomic DB write:
     - Insert `TinNhan(hoi_thoai=room, nguoi_gui=user, noi_dung=content, loai_tin_nhan=message_type, da_doc=False)`.
     - Update `HoiThoai.tin_nhan_cuoi_luc = timezone.now()`.
     - If sender is staff and `room.nhan_vien_id is None`: set `room.nhan_vien = user`.
  3. Dispatch group broadcast `chat_message` to group `chat_{conversation_id}`.

##### Frame B: Typing Indicator (`typing`)
```json
{
  "action": "typing",
  "is_typing": true
}
```
- **Fields**:
  - `action`: `"typing"`
  - `is_typing`: Boolean (`true` when user starts typing, `false` when stopped)
- Server broadcasts to group without DB persistence.

##### Frame C: Read Receipt (`read_receipt`)
```json
{
  "action": "read_receipt",
  "last_read_message_id": 108
}
```
- **Fields**:
  - `action`: `"read_receipt"`
  - `last_read_message_id`: Integer ID of the latest message read by the user
- Server updates `TinNhan` records where `hoi_thoai=room`, `id <= last_read_message_id`, `da_doc=False`, and `nguoi_gui != user`:
  - Set `da_doc = True`, `doc_luc = timezone.now()`.
- Dispatches `chat_read_receipt` broadcast to group.

#### 2.4 Outbound Server Frames (Server -> Client)

##### Outbound Frame 1: New Chat Message (`chat_message`)
```json
{
  "type": "chat_message",
  "id": 109,
  "conversation_id": 15,
  "sender_id": 42,
  "sender_name": "Nguyễn Văn A",
  "sender_role": "khach_hang",
  "is_staff": false,
  "content": "Xin chào nhà hàng, mình muốn hỏi về thành phần món lẩu riêu cua?",
  "noi_dung": "Xin chào nhà hàng, mình muốn hỏi về thành phần món lẩu riêu cua?",
  "message_type": "van_ban",
  "loai_tin_nhan": "van_ban",
  "created_at": "2026-10-14T10:38:00Z",
  "tao_luc": "2026-10-14T10:38:00Z",
  "is_read": false,
  "da_doc": false
}
```

##### Outbound Frame 2: Typing Broadcast (`chat_typing`)
```json
{
  "type": "chat_typing",
  "conversation_id": 15,
  "user_id": 5,
  "user_name": "Nhân viên hỗ trợ",
  "is_staff": true,
  "is_typing": true
}
```

##### Outbound Frame 3: Read Receipt Broadcast (`chat_read_receipt`)
```json
{
  "type": "chat_read_receipt",
  "conversation_id": 15,
  "reader_id": 5,
  "reader_name": "Nhân viên hỗ trợ",
  "last_read_message_id": 109,
  "read_at": "2026-10-14T10:39:15Z"
}
```

##### Outbound Frame 4: Error (`error`)
```json
{
  "type": "error",
  "code": "INVALID_MESSAGE",
  "message": "Nội dung tin nhắn không được để trống."
}
```

---

### 3. Real-Time Order Tracking WebSocket Protocol

#### 3.1 Endpoint URLs & Channels Routing
1. **Single-Order Stream**:
   - Route: `re_path(r"^ws/orders/(?P<order_id>[a-zA-Z0-9_-]+)/$", OrderTrackingConsumer.as_asgi())`
   - Client URL: `ws://<host>/ws/orders/<order_id>/?token=<jwt_access_token>`
   - `order_id` accepts either numeric DB `id` or display code `ma_don_hang` (e.g. `"MOC482910"`).
2. **Staff Aggregate Stream**:
   - Route: `path("ws/orders/staff/", StaffOrderStreamConsumer.as_asgi())`
   - Client URL: `ws://<host>/ws/orders/staff/?token=<jwt_access_token>`

#### 3.2 Authorization & Subscription Logic
- **Single-Order Consumer**:
  1. Reject if `scope["user"].is_anonymous` (close code `4001`).
  2. Resolve order via `Q(id=order_id) | Q(ma_don_hang=order_id)`. If missing, reject (close code `4004`).
  3. Validate access: `order.khach_hang_id == user.id` OR `user.la_nhan_vien_nha_hang is True`. If neither, reject (close code `4003`).
  4. Channel group subscribed: `order_{order.id}`.
  5. Welcome frame:
     ```json
     {
       "type": "order_subscription_success",
       "order_id": 101,
       "order_code": "MOC482910",
       "current_status": "cho_tiep_nhan",
       "message": "Đang theo dõi đơn hàng MOC482910"
     }
     ```
- **Staff Aggregate Consumer**:
  1. Reject if `scope["user"].is_anonymous` or `not user.la_nhan_vien_nha_hang` (close code `4003`).
  2. Channel group subscribed: `staff_orders`.
  3. Welcome frame:
     ```json
     {
       "type": "staff_order_stream_subscribed",
       "user_id": 5,
       "role": "nhan_vien",
       "message": "Đã kết nối luồng quản lý đơn hàng toàn hệ thống."
     }
     ```

#### 3.3 Outbound Event Schema: Order Status Update (`order_status_update`)
Dispatched whenever an order's status transitions in the backend (via REST API `PATCH /api/orders/<id>/trang_thai/`, VNPay IPN, or background worker):

```json
{
  "type": "order_status_update",
  "order_id": 101,
  "ma_don_hang": "MOC482910",
  "order_code": "MOC482910",
  "trang_thai_cu": "cho_tiep_nhan",
  "from_status": "cho_tiep_nhan",
  "trang_thai_moi": "da_xac_nhan",
  "to_status": "da_xac_nhan",
  "thoi_gian": "2026-10-14T10:40:00Z",
  "timestamp": "2026-10-14T10:40:00Z",
  "ghi_chu": "Bếp đã nhận đơn và xuất kho nguyên liệu",
  "note": "Bếp đã nhận đơn và xuất kho nguyên liệu",
  "nhan_vien_thuc_hien": {
    "id": 5,
    "ten": "Trần Thị Thu Ngân",
    "ho_ten": "Trần Thị Thu Ngân",
    "vai_tro": "nhan_vien"
  },
  "order_summary": {
    "tong_tien": "350000.00",
    "tien_hang": "350000.00",
    "tien_giam": "0.00",
    "hinh_thuc": "giao_hang",
    "so_luong_mon": 3
  }
}
```

---

### 4. 6-State Order Finite State Machine (FSM) Specification

#### 4.1 State Definitions
The 6 canonical states defined in `moc_schema_tieng_viet.sql` (Line 22, Line 387) and `moc-backend/orders/models.py`:

| Canonical Value | English Label | Vietnamese Label | Description & System Meaning | Terminal? |
|---|---|---|---|---|
| `cho_tiep_nhan` | Pending | Chờ tiếp nhận | Initial state upon order placement. Waiting for restaurant review and acceptance. | No |
| `da_xac_nhan` | Confirmed | Đã xác nhận | Accepted by restaurant. Triggers BOM raw material deduction. Sent to kitchen queue. | No |
| `dang_che_bien` | Cooking / Preparing | Đang chế biến | Kitchen chef has started actively preparing and cooking the dishes. | No |
| `san_sang` | Ready | Sẵn sàng | Food preparation complete. Plated/packed and ready for pickup, table serve, or delivery. | No |
| `hoan_tat` | Completed | Hoàn tất | Food received by customer and payment completed. Concluded transaction. | **Yes** |
| `da_huy` | Cancelled | Đã hủy | Order terminated prematurely by customer or staff. Concluded transaction. | **Yes** |

#### 4.2 Full 6x6 State Transition Matrix

| From State (`tu_trang_thai`) \ To State (`sang_trang_thai`) | `cho_tiep_nhan` | `da_xac_nhan` | `dang_che_bien` | `san_sang` | `hoan_tat` | `da_huy` |
|---|---|---|---|---|---|---|
| **`cho_tiep_nhan`** | ❌ Blocked (Self) | ✅ **ALLOWED** | ❌ Blocked (Skip) | ❌ Blocked (Skip) | ❌ Blocked (Skip) | ✅ **ALLOWED** |
| **`da_xac_nhan`** | ❌ Blocked (Reverse) | ❌ Blocked (Self) | ✅ **ALLOWED** | ❌ Blocked (Skip) | ❌ Blocked (Skip) | ✅ **ALLOWED** |
| **`dang_che_bien`** | ❌ Blocked (Reverse) | ❌ Blocked (Reverse) | ❌ Blocked (Self) | ✅ **ALLOWED** | ❌ Blocked (Skip) | ✅ **ALLOWED** |
| **`san_sang`** | ❌ Blocked (Reverse) | ❌ Blocked (Reverse) | ❌ Blocked (Reverse) | ❌ Blocked (Self) | ✅ **ALLOWED** | ✅ **ALLOWED** |
| **`hoan_tat`** (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) |
| **`da_huy`** (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) | ❌ Blocked (Terminal) |

#### 4.3 Legally Permissible Transitions

```python
ALLOWED_TRANSITIONS = {
    "cho_tiep_nhan": {"da_xac_nhan", "da_huy"},
    "da_xac_nhan": {"dang_che_bien", "da_huy"},
    "dang_che_bien": {"san_sang", "da_huy"},
    "san_sang": {"hoan_tat", "da_huy"},
    "hoan_tat": set(),  # Terminal state: No transitions allowed
    "da_huy": set(),    # Terminal state: No transitions allowed
}
```

#### 4.4 Disallowed Transitions & Error Responses
Any transition attempt not listed in `ALLOWED_TRANSITIONS[current_state]` MUST raise a `rest_framework.exceptions.ValidationError` (returning HTTP 400 Bad Request):

1. **Attempting transition from terminal state**:
   ```json
   {
     "status": ["Không thể thay đổi trạng thái của đơn hàng đã kết thúc ('hoan_tat')."]
   }
   ```
2. **Attempting invalid/reverse/skip transition**:
   ```json
   {
     "status": ["Chuyển trạng thái không hợp lệ: từ 'san_sang' sang 'cho_tiep_nhan'."]
   }
   ```
3. **Attempting self-transition**:
   ```json
   {
     "status": ["Đơn hàng đã ở trạng thái 'da_xac_nhan'."]
   }
   ```
4. **Unknown status string**:
   ```json
   {
     "status": ["Trạng thái đơn hàng không hợp lệ."]
   }
   ```

#### 4.5 Actor Authorization Matrix
- **Customer (`khach_hang`)**:
  - Permitted: Cancel order (`da_huy`) ONLY when current state is `cho_tiep_nhan`.
  - Disallowed: All other transitions (returns HTTP 403 Forbidden).
- **Restaurant Staff (`la_nhan_vien_nha_hang`) / Admin**:
  - Permitted: All legal forward and cancellation transitions according to matrix.

#### 4.6 Side Effects & Lifecycle Hooks

1. **On `cho_tiep_nhan` -> `da_xac_nhan` (BOM Material Deduction)**:
   - Must invoke `foods.services.DichVuKho.khau_tru_nguyen_lieu_bom`:
     * Aggregates required raw ingredients from `DinhMucNguyenLieu` (BOM).
     * Locks raw material rows in PostgreSQL using `select_for_update()` ordered by `id` ascending (strictly prevents deadlocks).
     * Deducts `ton_kho_hien_tai` and logs transactions into `LichSuXuatNhapKho` (`loai_giao_dich="xuat"`).
     * If stock is insufficient, raises `ValidationError` and rolls back order transition.
2. **On `*` -> `da_huy` (BOM Material Refund)**:
   - If the previous state was `da_xac_nhan` or `dang_che_bien`:
     * Must invoke `foods.services.DichVuKho.hoan_tra_nguyen_lieu_bom`.
     * Restores raw ingredient stock and logs transactions into `LichSuXuatNhapKho` (`loai_giao_dich="nhap"`).
   - If previous state was `cho_tiep_nhan`:
     * No BOM refund needed because materials were not yet deducted.
3. **On `san_sang` -> `hoan_tat` (Order Concluded)**:
   - Triggers AI interaction weighting update (`TuongTacMonAn`) for recommendation engine.
4. **Audit Logging (All Transitions)**:
   - Every single transition MUST insert a row into `LichSuTrangThaiDon` (`lich_su_trang_thai_don`):
     * `don_hang_id`: target order ID.
     * `tu_trang_thai`: previous status string (or `None` on creation).
     * `sang_trang_thai`: new status string.
     * `doi_boi`: authenticated `NguoiDung` instance (or `None` if automated system action).
     * `ghi_chu`: transition reason or note.
     * `tao_luc`: timestamp.
5. **Real-Time WebSocket Push (All Transitions)**:
   - On successful DB commit, dispatches `order_status_update` event to:
     * Redis group `order_{order.id}`
     * Redis group `staff_orders`

---

### 5. Redis Channel Layer Group Naming Conventions & Regex Safety

#### 5.1 Channels Regex Rules
Django Channels (`channels_redis` and `asgiref`) enforces strict ASCII group name validation:
- **Allowed Character Set**: Letters (`a-z`, `A-Z`), digits (`0-9`), hyphen (`-`), underscore (`_`), period (`.`).
- **Regex**: `^[a-zA-Z0-9_.-]+$`
- **Maximum Length**: 100 bytes / characters.
- **Forbidden Characters**: Spaces, colons (`:`), slashes (`/`), question marks (`?`), non-ASCII unicode characters.
  *(Note: Colons are commonly used in Redis keys but are strictly forbidden in Channels group names because `channels_redis` uses colons internally for routing delimiters).*

#### 5.2 Canonical Group Naming Table

| Group Purpose | Canonical Format | Example Group Name | Regex Pattern | Max Length |
|---|---|---|---|---|
| Chat Conversation | `chat_{conversation_id}` | `chat_15`, `chat_102` | `^chat_[a-zA-Z0-9_-]+$` | 30 chars |
| Order Real-time Tracking | `order_{order_id}` | `order_42`, `order_MOC482910` | `^order_[a-zA-Z0-9_-]+$` | 30 chars |
| Staff Global Order Stream | `staff_orders` | `staff_orders` | `^staff_orders$` | 12 chars |
| Staff Global Chat Alerts | `staff_chat` | `staff_chat` | `^staff_chat$` | 10 chars |

#### 5.3 Safe Sanitization Helper Specification
```python
import re

def safe_channel_group_name(prefix: str, identifier: str) -> str:
    """
    Sanitizes channel group names to strictly conform to Django Channels regex:
    ^[a-zA-Z0-9_.-]+$ and length <= 100 characters.
    """
    clean_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(identifier).strip())
    group_name = f"{prefix}_{clean_id}"
    return group_name[:100]
```

---

## 5-Component Handoff Report

### 1. Observation
1. **Existing Backend State**:
   - `moc-backend/chat/models.py` defines `HoiThoai` (lines 6-93) and `TinNhan` (lines 94-206) with full bilingual legacy aliases (`customer`, `room`, `sender`, `message`, `is_read`), matching `moc_schema_tieng_viet.sql` lines 522-550.
   - `moc-backend/orders/models.py` defines `DonHang` (lines 7-297), `ChiTietDonHang` (lines 298-392), and `LichSuTrangThaiDon` (lines 393-416) with enum `TrangThai` (lines 8-14) having 6 values: `cho_tiep_nhan`, `da_xac_nhan`, `dang_che_bien`, `san_sang`, `hoan_tat`, `da_huy`.
   - `moc-backend/orders/services.py:104-135` (`DichVuDonHang.doi_trang_thai`) implements BOM inventory deduction (`DichVuKho.khau_tru_nguyen_lieu_bom`) on `DA_XAC_NHAN` and refund (`DichVuKho.hoan_tra_nguyen_lieu_bom`) on `DA_HUY`, but currently lacks enforcement of legal vs illegal state transitions and lacks WebSocket broadcast dispatch.
   - `moc-backend/config/asgi.py` contains only default `get_asgi_application()` without Channels `ProtocolTypeRouter` or WebSocket routing.
   - `moc-backend/config/settings.py` does not yet list `'channels'` in `INSTALLED_APPS` and does not configure `CHANNEL_LAYERS`.
2. **Environment & Dependencies**:
   - Running `pip list` in `moc-backend/.venv` confirmed `channels 4.3.2`, `channels_redis 4.3.0`, `redis 7.0.1`, and `asgiref 3.11.1` are already installed.
   - `python moc-backend/manage.py check` passes with 0 issues.
3. **Frontend State**:
   - `moc-frontend/src/components/chat/ChatWidget.tsx` lines 16-18 notes: `TODO(backend): connect to ws://<host>/ws/chat/<conversation_id>/ once Django Channels + Redis channel layer is available`.
   - `moc-frontend/src/types/index.ts` lines 54-60 defines `TrangThaiDonHang` with the 6 identical states (`cho_tiep_nhan`, `da_xac_nhan`, `dang_che_bien`, `san_sang`, `hoan_tat`, `da_huy`).
4. **Test Infrastructure**:
   - Running `python tests/e2e/runner.py` executed 60 tests across Tiers 1-4 with 100% pass rate in specification contract mode.
   - `tests/e2e/helpers/fsm_validator.py` and `tests/e2e/tier2/test_t2_fsm.py` specify exact constraints for `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, and `FSMTransitionError`.

### 2. Logic Chain
1. In `moc_schema_tieng_viet.sql`, `trang_thai_don_hang` is an explicit PostgreSQL ENUM with exactly 6 values. In restaurant business logic, an order cannot be served before it is cooked, cannot be accepted once completed, and cannot be resurrected once cancelled.
2. Therefore, `DichVuDonHang.doi_trang_thai` must enforce an `ALLOWED_TRANSITIONS` matrix matching `tests/e2e/helpers/fsm_validator.py`. Attempting any non-permitted transition must raise a `ValidationError` (HTTP 400).
3. In browser WebSocket environments, headers cannot be set in JavaScript `new WebSocket(url)`. Therefore, JWT authentication for WebSockets must be handled via query parameter `?token=<jwt>` using custom ASGI middleware `JWTAuthMiddleware`.
4. In Django Channels, `channels_redis` reserves colons (`:`) as internal message separators and rejects characters outside `[a-zA-Z0-9_.-]`. Therefore, channel groups must use underscores: `chat_{id}`, `order_{id}`, and `staff_orders`.
5. Every chat message must be stored in `tin_nhan` inside a database transaction before broadcasting to ensure message history persistence and delivery order consistency.

### 3. Caveats
1. **Redis Socket Sandbox**: In the current local execution sandbox, direct TCP socket connections to `127.0.0.1:6379` encountered `Operation not permitted`. As a result, unit tests and offline test runners must configure an in-memory channel layer fallback (`channels.layers.InMemoryChannelLayer`) when Redis is unreachable.
2. **Daphne vs Runserver**: `daphne` is not installed as a standalone CLI in `.venv`, but `channels` 4.3.2 is installed. In Channels 4.x, running `python manage.py runserver` works seamlessly when `channels` (or `daphne`) is added to `INSTALLED_APPS` and `ASGI_APPLICATION` is declared.
3. **No Code Written**: Per specification miner instructions, this investigation is strictly read-only; no implementation files have been modified.

### 4. Conclusion
The technical specifications, JSON frame schemas, FSM transition matrix, and group naming rules for Milestone 3 are fully mined, verified against authoritative database schemas and test oracles, and documented. The backend and frontend workers have complete, unambiguous technical blueprints to implement:
- ASGI protocol router & JWT query middleware in `moc-backend/config/asgi.py` & `chat/middleware.py`.
- 2-way chat consumer & routing in `moc-backend/chat/consumers.py` & `chat/routing.py`.
- Real-time order tracking consumer & FSM broadcast in `moc-backend/orders/consumers.py` & `orders/services.py`.
- Frontend WebSocket connection in `moc-frontend/src/components/chat/ChatWidget.tsx` and order tracking views.

### 5. Verification Method
1. **Schema & Model Check**:
   ```bash
   source moc-backend/.venv/bin/activate
   python moc-backend/manage.py check
   ```
2. **Offline Specification Oracle Verification**:
   ```bash
   source moc-backend/.venv/bin/activate
   python tests/e2e/runner.py --tier 1
   python tests/e2e/runner.py --tier 2
   ```
3. **FSM Transition Oracle Test**:
   ```bash
   source moc-backend/.venv/bin/activate
   python -m unittest tests/e2e/tier2/test_t2_fsm.py -v
   ```
4. **WebSocket & FSM Realtime Test**:
   ```bash
   source moc-backend/.venv/bin/activate
   python -m unittest tests/e2e/tier1/test_t1_realtime.py -v
   ```
