# Handoff Report: Milestone 5 Frontend WebSocket Integration

**Agent**: `m5_explorer_realtime`  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m5_2`  
**Milestone**: Milestone 5 — Frontend Synchronization & Realtime Communication  
**Date**: 2026-10-15  
**Target Delivery**: Drop-in architectural analysis and TypeScript code blueprints for Django Channels WebSocket integration.

---

## 1. Observation

### 1.1 Backend ASGI & WebSocket Authentication Architecture
- **ASGI Router Declaration** (`moc-backend/config/asgi.py`, lines 22–31):
  ```python
  application = ProtocolTypeRouter(
      {
          "http": django_http_app,
          "websocket": AllowedHostsOriginValidator(
              JWTAuthMiddlewareStack(
                  URLRouter(config.routing.websocket_urlpatterns)
              )
          ),
      }
  )
  ```
- **JWT Middleware Extraction** (`moc-backend/config/middleware.py`, lines 45–68):
  - Extracts JWT token strictly from `scope["query_string"]` via parameter `?token=<access_token>`:
    ```python
    query_string = scope.get("query_string", b"").decode("utf-8")
    if query_string:
        query_params = urllib.parse.parse_qs(query_string)
        tokens = query_params.get("token", [])
        if tokens:
            token_str = tokens[0]
    ```
  - Standard browser `new WebSocket(url)` cannot send custom HTTP Authorization headers. The query string `?token=...` is the sole functional authentication vector for browser clients.
  - If `token` is missing or invalid, `scope["user"] = AnonymousUser()`.

### 1.2 Chat WebSocket Endpoints & Protocol
- **Chat Routing** (`moc-backend/chat/routing.py`, lines 4–7):
  ```python
  websocket_urlpatterns = [
      re_path(r"^ws/chat/(?P<conversation_id>[a-zA-Z0-9_-]+)/?$", consumers.ChatConsumer.as_asgi()),
      re_path(r"^ws/hoi-thoai/(?P<conversation_id>[a-zA-Z0-9_-]+)/?$", consumers.ChatConsumer.as_asgi()),
  ]
  ```
- **Access Control & Lifecycle** (`moc-backend/chat/consumers.py`, lines 20–60):
  - **4401 Unauthorized**: If user is unauthenticated or anonymous (`self.close(code=4401)`).
  - **4403 Forbidden**: If customer does not own the room (`room.khach_hang_id != user.id` and not staff).
  - **Initial Frame**: On connect, the server immediately sends a system welcome frame:
    ```json
    {
      "type": "connection_established",
      "conversation_id": 1,
      "room_id": "1",
      "user_id": 5,
      "username": "Nguyen Van A",
      "is_staff": false,
      "message": "Kết nối phòng chat thành công."
    }
    ```
- **Inbound Message Actions** (`receive_json`):
  1. `action: "send_message"` (aliases: `"message"`, `"gui_tin_nhan"`):
     Payload: `{"action": "send_message", "content": "...", "message_type": "van_ban"}`.
     - Emits `error` code `EMPTY_CONTENT` if empty, `MESSAGE_TOO_LONG` if > 5000 chars.
     - Persists message to PostgreSQL table `TinNhan` atomically in `_save_message` before broadcast.
  2. `action: "typing"`:
     Payload: `{"action": "typing", "is_typing": true}`.
     - Broadcasts `chat_typing` to group excluding sender.
  3. `action: "mark_read"`:
     Payload: `{"action": "mark_read", "last_read_message_id": 123}`.
     - Updates `da_doc=True` in DB and broadcasts `chat_read_receipt`.
- **Outbound Message Events** (`chat_message`):
  ```json
  {
    "type": "chat_message",
    "id": 101,
    "conversation_id": 1,
    "sender_id": 5,
    "sender_name": "Nguyen Van A",
    "sender_role": "khach_hang",
    "is_staff": false,
    "content": "Xin chào nhà hàng!",
    "noi_dung": "Xin chào nhà hàng!",
    "message": "Xin chào nhà hàng!",
    "message_type": "van_ban",
    "is_read": false,
    "created_at": "2026-10-15T00:00:00Z"
  }
  ```
- **REST Endpoints for Chat** (`moc-backend/chat/views.py`, lines 28–60; `moc-backend/api/urls.py`, lines 90–92):
  - `GET /api/chat/conversations/active/` (or `/api/chat/rooms/active/`, `/api/hoi-thoai/active/`): Retrieves the active open conversation for the requesting customer (creates one automatically if none exists).
  - `GET /api/chat/conversations/<id>/messages/`: Retrieves chronological message history.

### 1.3 Order Lifecycle & Staff WebSocket Endpoints
- **Order Routing** (`moc-backend/orders/routing.py`, lines 4–12):
  ```python
  websocket_urlpatterns = [
      re_path(r"^ws/orders/staff/?$", consumers.StaffOrderConsumer.as_asgi()),
      re_path(r"^ws/don-hang/nhan-vien/?$", consumers.StaffOrderConsumer.as_asgi()),
      re_path(r"^ws/orders/(?P<order_id>[a-zA-Z0-9_-]+)/?$", consumers.OrderTrackingConsumer.as_asgi()),
      re_path(r"^ws/don-hang/(?P<order_id>[a-zA-Z0-9_-]+)/?$", consumers.OrderTrackingConsumer.as_asgi()),
  ]
  ```
- **Order Tracking Consumer** (`moc-backend/orders/consumers.py`, lines 14–120):
  - Connects using either numeric database ID (e.g. `12`) or order number (e.g. `DH-20261014-001`).
  - Rejection: `4401` if anonymous, `4404` if order not found, `4403` if order belongs to another customer.
  - Initial snapshot frame:
    ```json
    {
      "type": "order_snapshot",
      "order_id": 12,
      "order_number": "DH-20261014-001",
      "status": "cho_tiep_nhan",
      "status_display": "Chờ tiếp nhận",
      "order_type": "giao_hang",
      "total": 350000.0,
      "total_amount": "350000.00",
      "customer_name": "Nguyen Van A",
      "created_at": "2026-10-15T00:00:00Z"
    }
    ```
  - Inbound refresh: client can send `{"action": "refresh"}` to trigger a snapshot re-send.
- **FSM Real-Time Broadcast** (`moc-backend/orders/services.py`, lines 269–295):
  - Emitted when `DichVuDonHang.doi_trang_thai` changes status:
    ```json
    {
      "type": "order_status_update",
      "order_id": 12,
      "order_number": "DH-20261014-001",
      "from_status": "cho_tiep_nhan",
      "to_status": "da_xac_nhan",
      "status": "da_xac_nhan",
      "status_display": "Đã xác nhận",
      "note": "Thu ngân đã xác nhận đơn",
      "changed_by": "Thu Ngân A",
      "timestamp": "2026-10-15T00:05:00Z"
    }
    ```
  - Broadcasts to groups: `order_{id}`, `order_{order_number}`, and `staff_orders`.
- **Staff Order Stream Consumer** (`moc-backend/orders/consumers.py`, lines 121–172):
  - Connected at `/ws/orders/staff/`.
  - Enforces `is_staff` or `la_nhan_vien_nha_hang` (rejection `4403`).
  - Receives `order_status_update` and `order_created`.

### 1.4 Frontend Existing Codebase Audit
- **`moc-frontend/src/components/chat/ChatWidget.tsx`**:
  - Line 25: `const roomId = user?.id ? String(user.id) : "1";`
    **Defect**: Assumes `roomId` is `user.id`. `HoiThoai` is an independent database record. If customer ID is 2, room #2 may belong to another user or not exist, triggering `4403 Forbidden`.
  - Line 32: `const wsUrl = `${protocol}//${host}/ws/chat/${roomId}/`;`
    **Defect**: Does NOT append `?token=<access_token>`. Triggers `4401 Unauthorized` immediately.
  - Line 46: `if (data.type === "chat_message" || data.message || data.content)`
    **Defect**: Server sends `{"type": "connection_established", "message": "Kết nối phòng chat thành công."}` on connect. This condition matches `data.message`, rendering the system greeting as an inbound user message!
  - Lines 12–14: Hardcoded static `INITIAL_MESSAGES`. Does not fetch historical messages from PostgreSQL.
  - Line 109–123: When socket is closed/error, it fakes an offline response with `setTimeout`.
- **`moc-frontend/src/pages/order/OrderSuccessPage.tsx`**:
  - Line 5: `const orderId = "MC" + Math.floor(100000 + Math.random() * 900000);`
    **Defect**: Mocks a random order ID instead of receiving the real order code created during checkout. Does not connect to `/ws/orders/<order_id>/`.
- **`moc-frontend/src/pages/account/AccountOrdersPage.tsx`**:
  - Fetches orders once via REST `getMyOrders()`. No real-time updates.
- **`moc-frontend/src/pages/admin/AdminOrdersPage.tsx`**:
  - Fetches orders once via REST. No connection to `/ws/orders/staff/`, and no FSM state transition action triggers.

---

## 2. Logic Chain

1. **Authentication Gate**:
   - Backend `JWTAuthMiddleware` explicitly checks `scope["query_string"]` for `token`.
   - Browser `WebSocket` does not support arbitrary HTTP headers.
   - Therefore, the client MUST append `?token=${encodeURIComponent(token)}` to every WebSocket URL.
   - If token is missing (guest/logged out), attempting to open the socket will result in error `4401`. The frontend must detect this state and display an authentication banner rather than an unhandled error.

2. **Conversation Access Resolution**:
   - `ChatConsumer` validates `room = HoiThoai.objects.filter(id=int(conversation_id)).first()`.
   - Before opening the WebSocket, the frontend must ensure an active conversation exists by calling `GET /api/chat/conversations/active/`.
   - Using the returned `activeConversation.id`, the client connects to `/ws/chat/${activeConversation.id}/?token=${token}`.
   - Concurrently, calling `GET /api/chat/conversations/${activeConversation.id}/messages/` pre-populates previous messages into the UI.

3. **Message Filtering & Protocol Alignment**:
   - The frontend must distinguish between protocol events (`connection_established`, `chat_typing`, `chat_read_receipt`, `error`) and actual chat messages (`chat_message`).
   - Outbound messages must explicitly supply `{"action": "send_message", "content": text, "noi_dung": text}`.

4. **Order Lifecycle Integration**:
   - The customer after checkout receives `orderId` (or `order_number`).
   - Connecting to `/ws/orders/${orderId}/?token=${token}` provides:
     1. Immediate state via `order_snapshot`.
     2. Instant transition updates via `order_status_update`.
   - The 5 canonical FSM steps (`cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat`, or `da_huy`) must be rendered visually in a progress stepper component.

5. **Staff Portal Synchronization**:
   - Staff connects to `/ws/orders/staff/?token=${token}`.
   - When any order changes status, `order_status_update` is pushed; the staff table updates the matching row in-place.
   - When a new order arrives, `order_created` is pushed; the staff table unshifts the new order to the top with a sound/visual alert.

---

## 3. Caveats

1. **Native WebSocket API Header Restriction**:
   In standard browser environments, `new WebSocket(url)` does not accept custom headers (like `Authorization: Bearer <token>`). The token query parameter `?token=...` is the only cross-browser compliant mechanism.
2. **Access Token Expiry**:
   If an access token expires while a WebSocket is connected, Channels does not retroactively close existing connections unless a new handshake occurs. However, on automatic reconnection (e.g. network flap), the client must re-fetch the fresh token from `localStorage` (or trigger token refresh via `/api/auth/refresh/`).
3. **Guest / Unauthenticated Experience**:
   Unregistered visitors cannot open authenticated chat or order tracking (the server closes with 4401). The UI must handle this gracefully with clear prompts (e.g. "Vui lòng đăng nhập để trò chuyện với nhân viên" or "Đăng nhập để theo dõi đơn").
4. **Dev Environment Port Mismatch**:
   In local development, Vite SPA runs on port `5173` while Django Channels runs on `8000`. The URL resolution utility must correctly route WebSocket connections to port `8000` when on localhost, while supporting production domain hosting or environment overrides via `VITE_WS_URL`.

---

## 4. Conclusion & Drop-In Code Blueprints

Below are complete, production-grade drop-in TypeScript blueprints for the frontend implementer.

### Blueprint 1: Central WebSocket Service (`moc-frontend/src/services/websocket.ts`)

```typescript
/**
 * Central WebSocket URL resolver and reconnecting client helper.
 * Path: moc-frontend/src/services/websocket.ts
 */

export function getWebSocketUrl(path: string): string {
  // If absolute ws:// or wss:// is provided, return directly
  if (path.startsWith("ws://") || path.startsWith("wss://")) {
    return path;
  }

  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const envWsUrl = import.meta.env.VITE_WS_URL as string | undefined;

  let base = "";
  if (envWsUrl) {
    base = `${envWsUrl.replace(/\/+$/, "")}${cleanPath}`;
  } else {
    const isHttps = typeof window !== "undefined" && window.location.protocol === "https:";
    const protocol = isHttps ? "wss:" : "ws:";
    const isDev =
      typeof window !== "undefined" &&
      (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

    // In dev, Django Channels runs on port 8000
    const host = isDev ? `${window.location.hostname}:8000` : window.location.host;
    base = `${protocol}//${host}${cleanPath}`;
  }

  // Inject JWT token from localStorage
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    const separator = base.includes("?") ? "&" : "?";
    return `${base}${separator}token=${encodeURIComponent(token)}`;
  }

  return base;
}
```

---

### Blueprint 2: Realtime Chat Hook (`moc-frontend/src/hooks/useWebSocketChat.ts`)

```typescript
/**
 * React Hook for 2-Way Staff-Customer Realtime Chat via Django Channels.
 * Path: moc-frontend/src/hooks/useWebSocketChat.ts
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { apiClient } from "@/api/client";
import { getWebSocketUrl } from "@/services/websocket";
import { useAuthStore } from "@/store/authStore";

export interface ChatMessageItem {
  id: number | string;
  conversationId: number;
  senderId: number;
  senderName: string;
  senderRole?: string;
  isStaff: boolean;
  content: string;
  messageType: string;
  isRead: boolean;
  createdAt: string;
  from: "me" | "restaurant";
  time: string;
}

interface UseWebSocketChatOptions {
  conversationId?: number; // Optional: specify explicit conversation or let hook load active
  enabled?: boolean;
}

export function useWebSocketChat(options: UseWebSocketChatOptions = {}) {
  const { conversationId: propConvId, enabled = true } = options;
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const [conversationId, setConversationId] = useState<number | null>(propConvId ?? null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Helper to format raw message to UI ChatMessageItem
  const formatMessage = useCallback(
    (raw: any): ChatMessageItem => {
      const senderId = Number(raw.sender_id || raw.nguoi_gui_id || raw.senderId || 0);
      const myId = user?.id ? Number(user.id) : null;
      const isMe = myId !== null && senderId === myId && !raw.is_staff;
      const text = raw.content || raw.noi_dung || raw.message || "";
      const rawDate = raw.created_at || raw.tao_luc || raw.createdAt || new Date().toISOString();
      const d = new Date(rawDate);
      const time = `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;

      return {
        id: raw.id || Date.now(),
        conversationId: raw.conversation_id || raw.hoi_thoai_id || raw.conversationId || 0,
        senderId,
        senderName: raw.sender_name || raw.user_name || "Nhân viên hỗ trợ",
        senderRole: raw.sender_role || "",
        isStaff: Boolean(raw.is_staff),
        content: text,
        messageType: raw.message_type || raw.loai_tin_nhan || "van_ban",
        isRead: Boolean(raw.is_read || raw.da_doc),
        createdAt: rawDate,
        from: isMe ? "me" : "restaurant",
        time,
      };
    },
    [user?.id]
  );

  // 1. Fetch active conversation if not provided
  useEffect(() => {
    if (!enabled || !isAuthenticated) return;

    if (propConvId) {
      setConversationId(propConvId);
      return;
    }

    let isMounted = true;
    apiClient
      .get("/chat/conversations/active/")
      .then((res) => {
        if (isMounted && res.data?.id) {
          setConversationId(res.data.id);
        }
      })
      .catch((err) => {
        console.warn("Could not retrieve active conversation:", err);
      });

    return () => {
      isMounted = false;
    };
  }, [enabled, isAuthenticated, propConvId]);

  // 2. Load historical messages via REST once conversationId is known
  useEffect(() => {
    if (!conversationId || !isAuthenticated) return;

    let isMounted = true;
    setLoadingHistory(true);
    apiClient
      .get(`/chat/conversations/${conversationId}/messages/`)
      .then((res) => {
        if (!isMounted) return;
        const list = Array.isArray(res.data) ? res.data : res.data.results || [];
        const formatted = list.map(formatMessage);
        setMessages(formatted);
      })
      .catch((err) => {
        console.warn("Failed to load chat history:", err);
      })
      .finally(() => {
        if (isMounted) setLoadingHistory(false);
      });

    return () => {
      isMounted = false;
    };
  }, [conversationId, isAuthenticated, formatMessage]);

  // 3. Connect WebSocket to /ws/chat/<conversation_id>/
  useEffect(() => {
    if (!enabled || !isAuthenticated || !conversationId) return;

    const wsUrl = getWebSocketUrl(`/ws/chat/${conversationId}/`);
    let isClosing = false;

    function connect() {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "chat_message") {
              const msg = formatMessage(data);
              setMessages((prev) => {
                if (prev.some((m) => m.id === msg.id)) return prev;
                return [...prev, msg];
              });
              if (msg.from !== "me") {
                setUnreadCount((c) => c + 1);
              }
            } else if (data.type === "chat_typing") {
              setIsTyping(Boolean(data.is_typing));
              setTypingUser(data.sender_name || "Nhân viên");
              if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
              typingTimeoutRef.current = setTimeout(() => {
                setIsTyping(false);
                setTypingUser(null);
              }, 4000);
            } else if (data.type === "chat_read_receipt") {
              setMessages((prev) =>
                prev.map((m) => ({ ...m, isRead: true }))
              );
            }
          } catch (e) {
            console.error("Error processing websocket message:", e);
          }
        };

        ws.onclose = (event) => {
          setIsConnected(false);
          if (!isClosing && event.code !== 4401 && event.code !== 4403) {
            // Auto-reconnect after 3s
            reconnectTimeoutRef.current = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch (err) {
        console.error("WebSocket connection failure:", err);
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      isClosing = true;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [enabled, isAuthenticated, conversationId, formatMessage]);

  // Actions
  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            action: "send_message",
            content: trimmed,
            noi_dung: trimmed,
            message_type: "van_ban",
          })
        );
      } else if (conversationId) {
        // Fallback to REST if socket temporarily reconnecting
        apiClient
          .post(`/chat/conversations/${conversationId}/messages/`, {
            noi_dung: trimmed,
            loai_tin_nhan: "van_ban",
          })
          .then((res) => {
            setMessages((prev) => [...prev, formatMessage(res.data)]);
          });
      }
    },
    [conversationId, formatMessage]
  );

  const sendTyping = useCallback((typing: boolean) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: "typing",
          is_typing: typing,
        })
      );
    }
  }, []);

  const clearUnread = useCallback(() => {
    setUnreadCount(0);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "mark_read" }));
    }
  }, []);

  return {
    conversationId,
    messages,
    isConnected,
    isTyping,
    typingUser,
    unreadCount,
    loadingHistory,
    sendMessage,
    sendTyping,
    clearUnread,
  };
}
```

---

### Blueprint 3: Realtime Order Tracking Hook (`moc-frontend/src/hooks/useOrderTracking.ts`)

```typescript
/**
 * React Hook for Customer Real-time Order Tracking via /ws/orders/<order_id>/.
 * Path: moc-frontend/src/hooks/useOrderTracking.ts
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { getWebSocketUrl } from "@/services/websocket";
import { useAuthStore } from "@/store/authStore";
import type { OrderStatus } from "@/types";

export interface OrderLiveSnapshot {
  orderId: number;
  orderNumber: string;
  status: OrderStatus;
  statusDisplay: string;
  orderType: string;
  total: number;
  customerName: string;
  createdAt: string;
  lastUpdated?: string;
  note?: string;
  changedBy?: string;
}

export function useOrderTracking(orderIdOrCode: string | number | null | undefined) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [snapshot, setSnapshot] = useState<OrderLiveSnapshot | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const refresh = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "refresh" }));
    }
  }, []);

  useEffect(() => {
    if (!orderIdOrCode || !isAuthenticated) return;

    const wsUrl = getWebSocketUrl(`/ws/orders/${orderIdOrCode}/`);
    let isClosing = false;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "order_snapshot") {
              setSnapshot({
                orderId: data.order_id,
                orderNumber: data.order_number || data.order_code,
                status: data.status,
                statusDisplay: data.status_display || data.status,
                orderType: data.order_type || "giao_hang",
                total: Number(data.total || data.total_amount || 0),
                customerName: data.customer_name || "",
                createdAt: data.created_at || "",
              });
            } else if (data.type === "order_status_update") {
              setSnapshot((prev) => {
                if (!prev) return null;
                return {
                  ...prev,
                  status: data.to_status || data.status,
                  statusDisplay: data.status_display || data.status,
                  lastUpdated: data.timestamp || data.thoi_gian,
                  note: data.note || data.ghi_chu,
                  changedBy: data.changed_by,
                };
              });
            }
          } catch (err) {
            console.error("Failed to parse order websocket frame:", err);
          }
        };

        ws.onclose = (ev) => {
          setIsConnected(false);
          if (!isClosing) {
            if (ev.code === 4401) {
              setError("Vui lòng đăng nhập để xem trạng thái đơn hàng.");
            } else if (ev.code === 4404) {
              setError("Không tìm thấy đơn hàng.");
            } else if (ev.code === 4403) {
              setError("Bạn không có quyền xem đơn hàng này.");
            } else {
              reconnectTimer = setTimeout(connect, 3000);
            }
          }
        };

        ws.onerror = () => {
          setIsConnected(false);
        };
      } catch (err) {
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      isClosing = true;
      clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [orderIdOrCode, isAuthenticated]);

  return { snapshot, isConnected, error, refresh };
}
```

---

### Blueprint 4: Staff Order Stream Hook (`moc-frontend/src/hooks/useStaffOrderStream.ts`)

```typescript
/**
 * React Hook for Restaurant Staff / Kitchen Realtime Order Monitoring.
 * Connects to /ws/orders/staff/.
 * Path: moc-frontend/src/hooks/useStaffOrderStream.ts
 */

import { useState, useEffect, useRef } from "react";
import { getWebSocketUrl } from "@/services/websocket";
import { useAuthStore } from "@/store/authStore";

export interface StaffOrderUpdateEvent {
  orderId: number;
  orderNumber: string;
  fromStatus: string;
  toStatus: string;
  statusDisplay: string;
  note?: string;
  changedBy?: string;
  timestamp: string;
}

export function useStaffOrderStream(options?: {
  onStatusUpdate?: (event: StaffOrderUpdateEvent) => void;
  onOrderCreated?: (newOrder: any) => void;
}) {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isAuthenticated || !user?.isStaff) return;

    const wsUrl = getWebSocketUrl("/ws/orders/staff/");
    let isClosing = false;
    let timer: ReturnType<typeof setTimeout>;

    function connect() {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => setIsConnected(true);

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "order_status_update") {
              options?.onStatusUpdate?.({
                orderId: data.order_id,
                orderNumber: data.order_number,
                fromStatus: data.from_status || data.trang_thai_cu,
                toStatus: data.to_status || data.trang_thai_moi || data.status,
                statusDisplay: data.status_display,
                note: data.note || data.ghi_chu,
                changedBy: data.changed_by,
                timestamp: data.timestamp || data.thoi_gian,
              });
            } else if (data.type === "order_created") {
              options?.onOrderCreated?.(data.order || data.data);
            }
          } catch (e) {
            console.error("Staff stream frame error:", e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          if (!isClosing) timer = setTimeout(connect, 3000);
        };
      } catch {
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      isClosing = true;
      clearTimeout(timer);
      if (wsRef.current) wsRef.current.close();
    };
  }, [isAuthenticated, user?.isStaff, options]);

  return { isConnected };
}
```

---

### Blueprint 5: Visual FSM Order Tracker Component (`moc-frontend/src/components/order/OrderTrackingCard.tsx`)

```tsx
/**
 * Visual FSM Order Lifecycle Stepper Component.
 * Supports: cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat (or da_huy)
 * Path: moc-frontend/src/components/order/OrderTrackingCard.tsx
 */

import { CheckCircle2, Clock, ChefHat, Package, AlertCircle } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { useOrderTracking } from "@/hooks/useOrderTracking";
import type { OrderStatus } from "@/types";

interface OrderTrackingCardProps {
  orderIdOrCode: string | number;
  className?: string;
}

const STEPS: { key: OrderStatus; label: string; icon: any }[] = [
  { key: "cho_tiep_nhan", label: "Tiếp nhận", icon: Clock },
  { key: "da_xac_nhan", label: "Đã xác nhận", icon: CheckCircle2 },
  { key: "dang_che_bien", label: "Đang nấu", icon: ChefHat },
  { key: "san_sang", label: "Sẵn sàng", icon: Package },
  { key: "hoan_tat", label: "Hoàn tất", icon: CheckCircle2 },
];

function getCanonicalIndex(status: string): number {
  switch (status) {
    case "cho_tiep_nhan":
    case "pending":
      return 0;
    case "da_xac_nhan":
    case "confirmed":
      return 1;
    case "dang_che_bien":
    case "preparing":
      return 2;
    case "san_sang":
    case "ready":
      return 3;
    case "hoan_tat":
    case "completed":
      return 4;
    default:
      return -1;
  }
}

export default function OrderTrackingCard({ orderIdOrCode, className }: OrderTrackingCardProps) {
  const { snapshot, isConnected, error } = useOrderTracking(orderIdOrCode);

  if (error) {
    return (
      <div className={cn("p-4 rounded-xl bg-red-50 text-red-700 text-sm flex items-center gap-2", className)}>
        <AlertCircle width={18} height={18} />
        {error}
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className={cn("card p-6 bg-white animate-pulse space-y-4", className)}>
        <div className="h-5 bg-black/10 rounded w-1/3"></div>
        <div className="h-10 bg-black/5 rounded"></div>
      </div>
    );
  }

  const isCancelled = snapshot.status === "da_huy" || snapshot.status === "cancelled";
  const currentIndex = getCanonicalIndex(snapshot.status);

  return (
    <div className={cn("card p-6 bg-white border border-black/10 rounded-2xl shadow-sm", className)}>
      <div className="flex items-center justify-between border-b pb-4 mb-6">
        <div>
          <div className="text-xs uppercase tracking-wider text-muted font-bold">Mã đơn hàng</div>
          <div className="font-display text-xl font-bold text-dark">#{snapshot.orderNumber}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted">Tổng thanh toán</div>
          <div className="font-bold text-primary text-lg">{formatCurrency(snapshot.total)}</div>
        </div>
      </div>

      {isCancelled ? (
        <div className="p-4 rounded-xl bg-red-50 text-red-700 flex items-center gap-3">
          <AlertCircle width={22} height={22} />
          <div>
            <div className="font-bold">Đơn hàng đã bị hủy</div>
            {snapshot.note && <div className="text-xs mt-0.5">{snapshot.note}</div>}
          </div>
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-5 gap-2 relative">
            {/* Progress line */}
            <div className="absolute top-4 left-6 right-6 h-1 bg-black/10 -z-0" />
            <div
              className="absolute top-4 left-6 h-1 bg-primary transition-all duration-500 -z-0"
              style={{ width: `${Math.min(100, Math.max(0, (currentIndex / 4) * 100))}%` }}
            />

            {STEPS.map((step, idx) => {
              const isPast = idx < currentIndex;
              const isCurrent = idx === currentIndex;
              const Icon = step.icon;

              return (
                <div key={step.key} className="flex flex-col items-center text-center relative z-10">
                  <div
                    className={cn(
                      "w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300",
                      isCurrent && "bg-primary text-white ring-4 ring-primary/20 scale-110",
                      isPast && "bg-primary text-white",
                      !isPast && !isCurrent && "bg-white border-2 border-black/20 text-muted"
                    )}
                  >
                    <Icon width={16} height={16} />
                  </div>
                  <span
                    className={cn(
                      "text-[11px] sm:text-xs mt-2 font-medium leading-tight",
                      isCurrent ? "text-primary font-bold" : "text-muted"
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-6 pt-4 border-t border-black/5 flex items-center justify-between text-xs text-muted">
            <div className="flex items-center gap-1.5">
              <span className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-400")} />
              <span>{isConnected ? "Cập nhật trực tiếp theo thời gian thực" : "Đang kết nối lại..."}</span>
            </div>
            {snapshot.lastUpdated && (
              <div>Cập nhật lúc: {new Date(snapshot.lastUpdated).toLocaleTimeString()}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Blueprint 6: Drop-In Replacement for `ChatWidget.tsx` (`moc-frontend/src/components/chat/ChatWidget.tsx`)

```tsx
/**
 * Production-ready Real-time Customer Support Chat Widget.
 * Path: moc-frontend/src/components/chat/ChatWidget.tsx
 */

import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, LogIn } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useWebSocketChat } from "@/hooks/useWebSocketChat";

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const {
    messages,
    isConnected,
    isTyping,
    typingUser,
    unreadCount,
    loadingHistory,
    sendMessage,
    sendTyping,
    clearUnread,
  } = useWebSocketChat({ enabled: open && isAuthenticated });

  // Scroll to bottom when messages update
  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open, isTyping]);

  const handleOpen = () => {
    setOpen(true);
    clearUnread();
  };

  const handleSend = () => {
    if (!draft.trim()) return;
    sendMessage(draft);
    setDraft("");
    sendTyping(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDraft(e.target.value);
    sendTyping(e.target.value.length > 0);
  };

  return (
    <div className="fixed bottom-6 right-6 z-[95] flex flex-col items-end gap-3">
      {open && (
        <div className="w-[320px] sm:w-[380px] h-[480px] bg-white rounded-2xl shadow-lift border border-black/[0.08] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="bg-dark text-white px-5 py-4 flex items-center justify-between">
            <div>
              <div className="font-display text-[15px] font-semibold">Nhà hàng MỘC</div>
              <div className="text-[11.5px] text-white/70 flex items-center gap-1.5 mt-0.5">
                <span
                  className={`w-2 h-2 rounded-full inline-block ${
                    isConnected ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
                  }`}
                />
                {isConnected ? "Trực tuyến (Real-time)" : "Đang kết nối..."}
              </div>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-white/70 hover:text-white transition-colors p-1"
            >
              <X width={18} height={18} />
            </button>
          </div>

          {/* Chat Body */}
          {!isAuthenticated ? (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center bg-bg">
              <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-3">
                <LogIn width={22} height={22} />
              </div>
              <h4 className="font-display text-base mb-1">Đăng nhập để trò chuyện</h4>
              <p className="text-xs text-muted mb-4 max-w-[240px]">
                Vui lòng đăng nhập vào tài khoản để kết nối trực tiếp với nhân viên hỗ trợ nhà hàng.
              </p>
              <Link
                to="/dang-nhap"
                onClick={() => setOpen(false)}
                className="btn btn-primary text-xs py-2 px-4"
              >
                Đăng nhập ngay
              </Link>
            </div>
          ) : (
            <>
              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 bg-bg">
                {loadingHistory && (
                  <div className="text-center text-xs text-muted py-2">
                    Đang tải lịch sử trò chuyện...
                  </div>
                )}

                {messages.length === 0 && !loadingHistory && (
                  <div className="text-center text-xs text-muted py-6">
                    Chưa có tin nhắn nào. Hãy gửi lời chào đến Mộc nhé! 👋
                  </div>
                )}

                {messages.map((m) => {
                  const isMe = m.from === "me";
                  return (
                    <div key={m.id} className={isMe ? "flex justify-end" : "flex justify-start"}>
                      <div
                        className={
                          isMe
                            ? "bg-primary text-white text-[13.5px] px-3.5 py-2.5 rounded-2xl rounded-br-sm max-w-[78%] shadow-sm"
                            : "bg-white border border-black/[0.07] text-text text-[13.5px] px-3.5 py-2.5 rounded-2xl rounded-bl-sm max-w-[78%] shadow-sm"
                        }
                      >
                        {!isMe && (
                          <div className="text-[10px] font-semibold text-primary mb-1">
                            {m.senderName} {m.isStaff && "• Nhân viên"}
                          </div>
                        )}
                        <div>{m.content}</div>
                        <div
                          className={
                            isMe
                              ? "text-[9.5px] text-white/70 mt-1 text-right"
                              : "text-[9.5px] text-muted mt-1"
                          }
                        >
                          {m.time} {isMe && (m.isRead ? "✓✓" : "✓")}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {isTyping && (
                  <div className="flex items-center gap-1.5 text-xs text-muted italic px-2 py-1">
                    <span className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce" />
                    <span>{typingUser || "Nhân viên"} đang nhập...</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="flex items-center gap-2 border-t border-black/[0.07] p-3 bg-white">
                <input
                  value={draft}
                  onChange={handleInputChange}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  placeholder="Nhập tin nhắn..."
                  className="flex-1 min-w-0 px-3.5 py-2.5 rounded-full bg-bg text-sm outline-none focus:ring-1 focus:ring-primary/40"
                />
                <button
                  onClick={handleSend}
                  disabled={!draft.trim()}
                  className="w-9 h-9 rounded-full bg-primary disabled:opacity-40 text-white flex items-center justify-center flex-shrink-0 transition-opacity"
                >
                  <Send width={15} height={15} />
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        onClick={open ? () => setOpen(false) : handleOpen}
        className="w-14 h-14 rounded-full bg-primary text-white shadow-lift flex items-center justify-center hover:scale-105 transition-transform relative"
        aria-label="Trò chuyện với nhà hàng"
      >
        {open ? <X width={22} height={22} /> : <MessageCircle width={22} height={22} />}
        {!open && unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-dark text-white text-[10px] font-bold flex items-center justify-center animate-bounce">
            {unreadCount}
          </span>
        )}
      </button>
    </div>
  );
}
```

---

## 5. Verification Method

### 5.1 Verification Commands
1. **Tier 1 Realtime & WebSocket Test Suite**:
   ```bash
   python3 tests/e2e/runner.py --tier 1
   ```
   *Expected outcome*: 30/30 tests pass (including `test_t1_realtime` and `test_t1_frontend`).
2. **Tier 4 End-to-End Real-World Scenario Suite**:
   ```bash
   python3 tests/e2e/runner.py --tier 4
   ```
   *Expected outcome*: 5/5 real-world scenarios pass (including S2 Realtime Chat Consultation & S1 Order FSM Tracking).
3. **Frontend Production Build**:
   ```bash
   cd moc-frontend && npm run build
   ```
   *Expected outcome*: Clean TypeScript compilation (`tsc -b`) and Vite asset bundling with zero compilation errors.

### 5.2 Invalidation Conditions
This analysis and blueprint would be invalidated if:
1. Django Channels `JWTAuthMiddleware` is altered to reject query string `?token=` and mandate non-standard browser subprotocols without backward compatibility.
2. `ChatConsumer` is refactored to allow unauthenticated anonymous WebSocket sessions without requiring a database `HoiThoai` record.
3. `DichVuDonHang.doi_trang_thai` alters its broadcast event payload type from `order_status_update` to an unmapped structure.
