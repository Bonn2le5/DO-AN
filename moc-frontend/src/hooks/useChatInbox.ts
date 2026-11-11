/**
 * Hộp thư chat cho staff: danh sách hội thoại + tin mới qua WebSocket (/ws/hoi-thoai/hop-thu/).
 * Chỉ gọi REST khi mở lần đầu, sau khi kết nối lại, hoặc khi có hội thoại mới chưa biết.
 * Path: moc-frontend/src/hooks/useChatInbox.ts
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient, refreshAccessToken } from "@/api/client";
import { openAuthenticatedWebSocket, scheduleCurrentWebSocketRenewal } from "@/services/websocket";

export interface InboxItem {
  id: number;
  customerName: string;
  lastMessage: string;
  lastAt: string | null;
  unread: number;
  status: "open" | "closed";
}

export interface InboxMessage {
  id: number;
  conversation_id: number;
  sender_name?: string;
  is_staff?: boolean;
  content?: string;
  created_at?: string;
}

const CHAT_API = "/hoi-thoai/";
const PING_MS = 25_000;

const mapItem = (r: any): InboxItem => ({
  id: Number(r.id),
  customerName: r.customer_name ?? "Khách hàng",
  lastMessage: r.last_message ?? "",
  lastAt: r.tin_nhan_cuoi_luc ?? null,
  unread: Number(r.unread_count ?? 0),
  status: r.trang_thai === "dong" ? "closed" : "open",
});

export function useChatInbox(
  enabled: boolean,
  onIncoming?: (item: InboxItem, message: InboxMessage) => void,
) {
  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const itemsRef = useRef<InboxItem[]>([]);
  const activeRef = useRef<number | null>(null);
  const onIncomingRef = useRef(onIncoming);

  useEffect(() => {
    onIncomingRef.current = onIncoming;
  }, [onIncoming]);

  const commit = useCallback((next: InboxItem[]) => {
    itemsRef.current = next;
    setItems(next);
  }, []);

  const load = useCallback(async () => {
    try {
      const res = await apiClient.get(CHAT_API);
      const list = Array.isArray(res.data) ? res.data : res.data.results || [];
      commit(
        list
          .map(mapItem)
          .map((i: InboxItem) =>
            i.id === activeRef.current ? { ...i, unread: 0 } : i,
          ),
      );
    } catch (err) {
      console.warn("Không tải được danh sách hội thoại:", err);
    } finally {
      setLoading(false);
    }
  }, [commit]);

  useEffect(() => {
    if (!enabled) return;
    let closing = false;
    let retry = 0;
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let pingTimer: ReturnType<typeof setInterval> | undefined;
    let cancelRenewal: (() => void) | undefined;

    const connect = async () => {
      if (closing) return;
      const socket = await openAuthenticatedWebSocket("/ws/hoi-thoai/hop-thu/");
      if (!socket) return;
      if (closing) {
        socket.close();
        return;
      }
      ws = socket;

      socket.onopen = () => {
        retry = 0;
        cancelRenewal = scheduleCurrentWebSocketRenewal(socket);
        void load(); // bù những gì bị lỡ lúc mất kết nối
        clearInterval(pingTimer);
        pingTimer = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN)
            socket.send(JSON.stringify({ action: "ping" }));
        }, PING_MS);
      };

      socket.onmessage = (e) => {
        let d: any;
        try {
          d = JSON.parse(e.data);
        } catch {
          return;
        }
        if (d.type !== "inbox_update" || !d.last_message) return;

        const m: InboxMessage = d.last_message;
        const convId = Number(d.conversation_id);
        const known = itemsRef.current.find((i) => i.id === convId);

        if (!known) {
          void load(); // hội thoại mới: tải lại danh sách một lần
        } else {
          const fromCustomer = !m.is_staff;
          const updated: InboxItem = {
            ...known,
            lastMessage: m.content ?? known.lastMessage,
            lastAt: m.created_at ?? known.lastAt,
            unread:
              fromCustomer && convId !== activeRef.current
                ? known.unread + 1
                : known.unread,
          };
          commit([updated, ...itemsRef.current.filter((i) => i.id !== convId)]);
        }

        if (!m.is_staff) {
          onIncomingRef.current?.(
            known ?? {
              id: convId,
              customerName: m.sender_name ?? "Khách hàng",
              lastMessage: m.content ?? "",
              lastAt: m.created_at ?? null,
              unread: 1,
              status: "open",
            },
            m,
          );
        }
      };

      socket.onclose = (ev) => {
        clearInterval(pingTimer);
        cancelRenewal?.();
        if (closing || ev.code === 4403) return;
        if (ev.code === 4401) {
          void refreshAccessToken().then((token) => { if (token && !closing) return connect(); });
          return;
        }
        if (ev.code === 4001) {
          void connect();
          return;
        }
        retryTimer = setTimeout(connect, Math.min(1000 * 2 ** retry++, 15000));
      };
    };

    void load();
    connect();
    return () => {
      closing = true;
      clearTimeout(retryTimer);
      clearInterval(pingTimer);
      cancelRenewal?.();
      ws?.close();
    };
  }, [enabled, load, commit]);

  /** Trang chat báo hội thoại đang mở để không đếm unread cho nó. */
  const setActive = useCallback(
    (id: number | null) => {
      activeRef.current = id;
      if (id !== null) {
        commit(
          itemsRef.current.map((i) => (i.id === id ? { ...i, unread: 0 } : i)),
        );
      }
    },
    [commit],
  );

  const setStatus = useCallback(
    (id: number, status: InboxItem["status"]) =>
      commit(itemsRef.current.map((i) => (i.id === id ? { ...i, status } : i))),
    [commit],
  );

  const totalUnread = items.reduce((sum, i) => sum + i.unread, 0);

  return { items, loading, totalUnread, setActive, setStatus };
}

export type ChatInbox = ReturnType<typeof useChatInbox>;
