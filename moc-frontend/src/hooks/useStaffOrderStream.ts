/**
 * React Hook for Restaurant Staff / Kitchen Realtime Order Monitoring.
 * Connects to /ws/don-hang/nhan-vien/.
 * Path: moc-frontend/src/hooks/useStaffOrderStream.ts
 */

import { useState, useEffect, useRef } from "react";
import { openAuthenticatedWebSocket, scheduleCurrentWebSocketRenewal } from "@/services/websocket";
import { refreshAccessToken } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import type { VaiTroNguoiDung } from "@/types";

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
  const user = useAuthStore((s) => s.nguoiDung);
  const isAuthenticated = useAuthStore((s) => s.daDangNhap);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const isStaff =
    user?.danhSachVaiTro?.some((role: VaiTroNguoiDung) => role === "admin" || role === "staff" || role === "nhan_vien" || role === "quan_tri_vien") ||
    user?.laNhanVien ||
    user?.laNhanVien;

  useEffect(() => {
    if (!isAuthenticated || !isStaff) return;

    let isClosing = false;
    let timer: ReturnType<typeof setTimeout>;
    let cancelRenewal: (() => void) | undefined;

    async function connect() {
      if (isClosing) return;
      try {
        const ws = await openAuthenticatedWebSocket("/ws/don-hang/nhan-vien/");
        if (!ws) return;
        if (isClosing) {
          ws.close();
          return;
        }
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          cancelRenewal = scheduleCurrentWebSocketRenewal(ws);
        };

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

        ws.onclose = (event) => {
          setIsConnected(false);
          cancelRenewal?.();
          if (isClosing) return;
          if (event.code === 4401) {
            void refreshAccessToken().then((token) => { if (token && !isClosing) return connect(); });
          } else if (event.code === 4001) {
            void connect();
          } else if (event.code !== 4403) {
            timer = setTimeout(connect, 3000);
          }
        };
      } catch {
        setIsConnected(false);
      }
    }

    connect();

    return () => {
      isClosing = true;
      clearTimeout(timer);
      cancelRenewal?.();
      if (wsRef.current) wsRef.current.close();
    };
  }, [isAuthenticated, isStaff, options]);

  return { isConnected };
}
