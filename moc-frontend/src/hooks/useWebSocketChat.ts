/**
 * Hook chat realtime 2 chiều (khách ↔ nhân viên) qua Django Channels.
 * Không polling: tin mới đến qua WebSocket. REST chỉ dùng để tải lịch sử và bù tin sau khi kết nối lại.
 * Path: moc-frontend/src/hooks/useWebSocketChat.ts
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { apiClient, refreshAccessToken } from "@/api/client";
import { openAuthenticatedWebSocket, scheduleCurrentWebSocketRenewal } from "@/services/websocket";
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
  /** Truyền vào (trang staff) hoặc để trống để lấy hội thoại đang hoạt động của khách. */
  conversationId?: number;
  enabled?: boolean;
  /** Khung chat đang hiển thị trước mắt người dùng? Quyết định unread / đã đọc. */
  open?: boolean;
}

const CHAT_API = "/hoi-thoai";
const PING_MS = 25_000;
const TYPING_IDLE_MS = 2_000;

const byTime = (a: ChatMessageItem, b: ChatMessageItem) =>
  new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();

export function useWebSocketChat(options: UseWebSocketChatOptions = {}) {
  const { conversationId: propConvId, enabled = true, open = true } = options;
  const userId = useAuthStore((s) => s.nguoiDung?.id);
  const isAuthenticated = useAuthStore((s) => s.daDangNhap);

  const [fetchedConvId, setFetchedConvId] = useState<number | null>(null);
  const conversationId = propConvId ?? fetchedConvId;

  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const myIdRef = useRef<number | null>(userId ? Number(userId) : null);
  const openRef = useRef(open);
  const convIdRef = useRef<number | null>(conversationId);
  const idsRef = useRef<Set<string>>(new Set());
  const lastIdRef = useRef(0);
  const historyLoadedRef = useRef(false);
  const syncingRef = useRef<number | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingHideRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingStopRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingActiveRef = useRef(false);

  useEffect(() => {
    myIdRef.current = userId ? Number(userId) : null;
  }, [userId]);

  useEffect(() => {
    convIdRef.current = conversationId;
  }, [conversationId]);

  // Đổi hội thoại -> reset sạch state.
  useEffect(() => {
    idsRef.current = new Set();
    lastIdRef.current = 0;
    historyLoadedRef.current = false;
    setMessages([]);
    setUnreadCount(0);
    setIsTyping(false);
    setTypingUser(null);
  }, [conversationId]);

  const formatMessage = useCallback((raw: any): ChatMessageItem => {
    const senderId = Number(
      raw.sender_id || raw.nguoi_gui_id || raw.senderId || raw.nguoi_gui || 0,
    );
    const rawDate =
      raw.created_at ||
      raw.tao_luc ||
      raw.createdAt ||
      new Date().toISOString();
    const d = new Date(rawDate);
    return {
      id: raw.id ?? Date.now(),
      conversationId:
        raw.conversation_id ||
        raw.hoi_thoai_id ||
        raw.conversationId ||
        raw.hoi_thoai ||
        0,
      senderId,
      senderName:
        raw.sender_name ||
        raw.user_name ||
        (raw.is_staff ? "Nhân viên hỗ trợ" : "Khách hàng"),
      senderRole: raw.sender_role || "",
      isStaff: Boolean(raw.is_staff),
      content: raw.content || raw.noi_dung || raw.message || "",
      messageType: raw.message_type || raw.loai_tin_nhan || "van_ban",
      isRead: Boolean(raw.is_read || raw.da_doc),
      createdAt: rawDate,
      from:
        myIdRef.current !== null && senderId === myIdRef.current
          ? "me"
          : "restaurant",
      time: `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`,
    };
  }, []);

  const mergeMessages = useCallback(
    (incoming: ChatMessageItem[], countUnread = false) => {
      const fresh = incoming.filter((m) => {
        const id = String(m.id);
        if (idsRef.current.has(id)) return false;
        idsRef.current.add(id);
        return true;
      });
      if (!fresh.length) return;
      for (const m of fresh) {
        const n = Number(m.id);
        if (Number.isFinite(n) && n > lastIdRef.current) lastIdRef.current = n;
      }
      if (countUnread) {
        const c = fresh.filter((m) => m.from !== "me").length;
        if (c) setUnreadCount((x) => x + c);
      }
      setMessages((prev) => [...prev, ...fresh].sort(byTime));
    },
    [],
  );

  /** Tải lịch sử lần đầu; các lần sau chỉ lấy tin có id > tin cuối đã có (bù tin sau reconnect). */
  const syncMessages = useCallback(
    async (id: number) => {
      if (syncingRef.current === id) return;
      syncingRef.current = id;
      try {
        const after = lastIdRef.current;
        const res = await apiClient.get(`${CHAT_API}/${id}/tin-nhan/`, {
          params: after ? { after_id: after } : undefined,
        });
        if (convIdRef.current !== id) return; // đã chuyển hội thoại khác
        const list = Array.isArray(res.data)
          ? res.data
          : res.data.results || [];
        mergeMessages(
          list.map(formatMessage),
          historyLoadedRef.current && !openRef.current,
        );
        historyLoadedRef.current = true;
      } catch (err) {
        console.warn("Không thể đồng bộ tin nhắn chat:", err);
      } finally {
        if (syncingRef.current === id) syncingRef.current = null;
      }
    },
    [formatMessage, mergeMessages],
  );

  // Khung chat mở/đóng -> reset unread và báo đã đọc.
  useEffect(() => {
    openRef.current = open;
    if (open) {
      setUnreadCount(0);
      const ws = wsRef.current;
      if (ws?.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify({ action: "mark_read" }));
    }
  }, [open]);

  // 1. Khách: lấy hội thoại đang hoạt động (staff truyền conversationId nên bỏ qua).
  useEffect(() => {
    if (propConvId || fetchedConvId !== null || !enabled || !isAuthenticated)
      return;
    let alive = true;
    apiClient
      .get(`${CHAT_API}/dang-mo/`)
      .then((res) => {
        if (alive && res.data?.id) setFetchedConvId(Number(res.data.id));
      })
      .catch((err) => console.warn("Không lấy được hội thoại hiện tại:", err));
    return () => {
      alive = false;
    };
  }, [propConvId, fetchedConvId, enabled, isAuthenticated]);

  // 2. Tải lịch sử một lần.
  useEffect(() => {
    if (!enabled || !isAuthenticated || !conversationId) return;
    let alive = true;
    setLoadingHistory(true);
    void syncMessages(conversationId).finally(() => {
      if (alive) setLoadingHistory(false);
    });
    return () => {
      alive = false;
    };
  }, [enabled, isAuthenticated, conversationId, syncMessages]);

  // 3. WebSocket /ws/hoi-thoai/<id>/
  useEffect(() => {
    if (!enabled || !isAuthenticated || !conversationId) return;
    let closing = false;
    let retry = 0;
    let pingTimer: ReturnType<typeof setInterval> | undefined;
    let cancelRenewal: (() => void) | undefined;

    const connect = async () => {
      if (closing) return;
      const ws = await openAuthenticatedWebSocket(`/ws/hoi-thoai/${conversationId}/`);
      if (!ws) return;
      if (closing) {
        ws.close();
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        retry = 0;
        cancelRenewal = scheduleCurrentWebSocketRenewal(ws);
        setIsConnected(true);
        if (historyLoadedRef.current) void syncMessages(conversationId); // bù tin bị lỡ
        if (openRef.current) ws.send(JSON.stringify({ action: "mark_read" }));
        clearInterval(pingTimer);
        pingTimer = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN)
            ws.send(JSON.stringify({ action: "ping" }));
        }, PING_MS);
      };

      ws.onmessage = (event) => {
        let data: any;
        try {
          data = JSON.parse(event.data);
        } catch {
          return;
        }

        if (data.type === "chat_message") {
          const msg = formatMessage(data);
          mergeMessages([msg], !openRef.current);
          if (
            openRef.current &&
            msg.from !== "me" &&
            ws.readyState === WebSocket.OPEN
          ) {
            ws.send(
              JSON.stringify({
                action: "mark_read",
                last_read_message_id: msg.id,
              }),
            );
          }
        } else if (data.type === "chat_typing") {
          setIsTyping(Boolean(data.is_typing));
          setTypingUser(data.is_typing ? data.sender_name || null : null);
          if (typingHideRef.current) clearTimeout(typingHideRef.current);
          if (data.is_typing) {
            typingHideRef.current = setTimeout(() => {
              setIsTyping(false);
              setTypingUser(null);
            }, 4000);
          }
        } else if (data.type === "chat_read_receipt") {
          if (Number(data.reader_id) === myIdRef.current) return; // receipt của chính mình
          const lastId = data.last_read_message_id
            ? Number(data.last_read_message_id)
            : Infinity;
          setMessages((prev) =>
            prev.map((m) =>
              m.from === "me" && Number(m.id) <= lastId
                ? { ...m, isRead: true }
                : m,
            ),
          );
        }
      };

      ws.onclose = (event) => {
        clearInterval(pingTimer);
        cancelRenewal?.();
        if (wsRef.current !== ws) return; // socket cũ đã bị thay thế
        setIsConnected(false);
        if (closing || event.code === 4403) return;
        if (event.code === 4401) {
          void refreshAccessToken().then((token) => { if (token && !closing) return connect(); });
          return;
        }
        if (event.code === 4001) {
          void connect();
          return;
        }
        reconnectRef.current = setTimeout(
          connect,
          Math.min(1000 * 2 ** retry++, 15000),
        );
      };
    };

    connect();

    return () => {
      closing = true;
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      if (typingHideRef.current) clearTimeout(typingHideRef.current);
      if (typingStopRef.current) clearTimeout(typingStopRef.current);
      cancelRenewal?.();
      clearInterval(pingTimer);
      typingActiveRef.current = false;
      const ws = wsRef.current;
      wsRef.current = null;
      ws?.close();
      setIsConnected(false);
    };
  }, [
    enabled,
    isAuthenticated,
    conversationId,
    formatMessage,
    mergeMessages,
    syncMessages,
  ]);

  const sendMessage = useCallback(
    async (text: string): Promise<boolean> => {
      const trimmed = text.trim();
      if (!trimmed) return false;
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            action: "send_message",
            content: trimmed,
            message_type: "van_ban",
          }),
        );
        return true;
      }
      if (!conversationId) return false;
      try {
        // Dự phòng khi socket đang reconnect; backend đã broadcast nên phía bên kia vẫn nhận ngay.
        const res = await apiClient.post(
          `${CHAT_API}/${conversationId}/tin-nhan/`,
          {
            noi_dung: trimmed,
            loai_tin_nhan: "van_ban",
          },
        );
        mergeMessages([formatMessage(res.data)]);
        return true;
      } catch {
        return false;
      }
    },
    [conversationId, formatMessage, mergeMessages],
  );

  /** Gọi sendTyping(true) mỗi lần gõ: chỉ gửi 1 frame khi bắt đầu, tự gửi false sau 2s im lặng. */
  const sendTyping = useCallback((typing: boolean) => {
    const emit = (value: boolean) => {
      const ws = wsRef.current;
      if (ws?.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify({ action: "typing", is_typing: value }));
    };
    if (typingStopRef.current) clearTimeout(typingStopRef.current);
    if (typing) {
      if (!typingActiveRef.current) {
        typingActiveRef.current = true;
        emit(true);
      }
      typingStopRef.current = setTimeout(() => {
        typingActiveRef.current = false;
        emit(false);
      }, TYPING_IDLE_MS);
    } else if (typingActiveRef.current) {
      typingActiveRef.current = false;
      emit(false);
    }
  }, []);

  const markRead = useCallback(() => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN)
      ws.send(JSON.stringify({ action: "mark_read" }));
  }, []);

  const clearUnread = useCallback(() => {
    setUnreadCount(0);
    markRead();
  }, [markRead]);

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
    markRead,
    clearUnread,
  };
}
