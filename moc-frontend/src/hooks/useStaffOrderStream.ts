/**
 * React Hook for Restaurant Staff / Kitchen Realtime Order Monitoring.
 * Connects to /ws/orders/staff/.
 * Path: moc-frontend/src/hooks/useStaffOrderStream.ts
 */

import { useState, useEffect, useRef } from "react";
import { getWebSocketUrl } from "@/services/websocket";
import { useAuthStore } from "@/store/authStore";
import type { UserRole } from "@/types";

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

  const isStaff =
    user?.roles?.some((role: UserRole) => role === "admin" || role === "staff" || role === "nhan_vien" || role === "quan_tri_vien") ||
    user?.isStaff ||
    user?.laNhanVien;

  useEffect(() => {
    if (!isAuthenticated || !isStaff) return;

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
  }, [isAuthenticated, isStaff, options]);

  return { isConnected };
}
