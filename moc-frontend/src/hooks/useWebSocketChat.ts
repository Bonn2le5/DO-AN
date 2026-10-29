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
  const messageIdsRef = useRef<Set<string>>(new Set());
  const historyLoadedRef = useRef(false);
  const syncInFlightRef = useRef(false);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const mergeMessages = useCallback((incoming: ChatMessageItem[], countUnread = false) => {
    const fresh = incoming.filter((message) => {
      const id = String(message.id);
      if (messageIdsRef.current.has(id)) return false;
      messageIdsRef.current.add(id);
      return true;
    });
    if (!fresh.length) return;
    if (countUnread) {
      const incomingCount = fresh.filter((message) => message.from !== "me").length;
      if (incomingCount) setUnreadCount((count) => count + incomingCount);
    }
    setMessages((previous) => [...previous, ...fresh].sort(
      (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
    ));
  }, []);

  useEffect(() => {
    if (!conversationId) return;
    messageIdsRef.current = new Set();
    historyLoadedRef.current = false;
    setMessages([]);
    setUnreadCount(0);
  }, [conversationId]);

  // Helper to format raw message to UI ChatMessageItem
  const formatMessage = useCallback(
    (raw: any): ChatMessageItem => {
      const senderId = Number(raw.sender_id || raw.nguoi_gui_id || raw.senderId || raw.nguoi_gui || 0);
      const myId = user?.id ? Number(user.id) : null;
      const isMe = myId !== null && senderId === myId && !raw.is_staff;
      const text = raw.content || raw.noi_dung || raw.message || "";
      const rawDate = raw.created_at || raw.tao_luc || raw.createdAt || new Date().toISOString();
      const d = new Date(rawDate);
      const time = `${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;

      return {
        id: raw.id || Date.now(),
        conversationId: raw.conversation_id || raw.hoi_thoai_id || raw.conversationId || raw.hoi_thoai || 0,
        senderId,
        senderName: raw.sender_name || raw.user_name || (raw.is_staff ? "Nhân viên hỗ trợ" : "Khách hàng"),
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

  const syncMessages = useCallback(async (id: number) => {
    if (syncInFlightRef.current) return;
    syncInFlightRef.current = true;
    try {
      const response = await apiClient.get(`/chat/conversations/${id}/messages/`);
      const list = Array.isArray(response.data) ? response.data : response.data.results || [];
      mergeMessages(list.map(formatMessage), historyLoadedRef.current);
      historyLoadedRef.current = true;
    } catch (err) {
      console.warn("Không thể đồng bộ tin nhắn chat:", err);
    } finally {
      syncInFlightRef.current = false;
    }
  }, [formatMessage, mergeMessages]);

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
    if (!enabled || !conversationId || !isAuthenticated) return;

    let isMounted = true;
    setLoadingHistory(true);
    apiClient
      .get(`/chat/conversations/${conversationId}/messages/`)
      .then((res) => {
        if (!isMounted) return;
        const list = Array.isArray(res.data) ? res.data : res.data.results || [];
        mergeMessages(list.map(formatMessage));
        historyLoadedRef.current = true;
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
  }, [enabled, conversationId, isAuthenticated, formatMessage, mergeMessages]);

  // Keep messages current while the widget is open, including any received
  // while the WebSocket was reconnecting.
  useEffect(() => {
    if (!enabled || !isAuthenticated || !conversationId) return;
    const timer = window.setInterval(() => void syncMessages(conversationId), 3000);
    return () => window.clearInterval(timer);
  }, [enabled, isAuthenticated, conversationId, syncMessages]);

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
          if (conversationId) void syncMessages(conversationId);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "chat_message") {
              const msg = formatMessage(data);
              mergeMessages([msg], true);
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
  }, [enabled, isAuthenticated, conversationId, formatMessage, mergeMessages, syncMessages]);

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
            mergeMessages([formatMessage(res.data)]);
          });
      }
    },
    [conversationId, formatMessage, mergeMessages]
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
