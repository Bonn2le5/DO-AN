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
