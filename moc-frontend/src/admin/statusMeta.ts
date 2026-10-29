import type { OrderStatus, ReservationStatus, DepositPaymentStatus, TableStatus } from "./types";

export type Tone = "neutral" | "info" | "warn" | "ok" | "danger" | "dark";
type Meta = { label: string; tone: Tone };

export const ORDER_META: Record<OrderStatus, Meta> = {
  pending: { label: "Chờ xác nhận", tone: "warn" },
  confirmed: { label: "Đã xác nhận", tone: "info" },
  preparing: { label: "Đang chế biến", tone: "info" },
  ready: { label: "Sẵn sàng", tone: "ok" },
  completed: { label: "Hoàn tất", tone: "neutral" },
  cancelled: { label: "Đã huỷ", tone: "danger" },
};

export const ORDER_NEXT: Partial<Record<OrderStatus, { to: OrderStatus; label: string }>> = {
  pending: { to: "confirmed", label: "Xác nhận đơn" },
  confirmed: { to: "preparing", label: "Bắt đầu chế biến" },
  preparing: { to: "ready", label: "Báo sẵn sàng" },
  ready: { to: "completed", label: "Hoàn tất đơn" },
};

export const RES_META: Record<ReservationStatus, Meta> = {
  pending_confirmation: { label: "Chờ nhà hàng xác nhận", tone: "warn" },
  pending_payment: { label: "Chờ đặt cọc", tone: "warn" },
  confirmed: { label: "Đã xác nhận", tone: "info" },
  seated: { label: "Đang dùng bữa", tone: "ok" },
  completed: { label: "Hoàn tất", tone: "neutral" },
  cancelled: { label: "Đã huỷ", tone: "danger" },
  no_show: { label: "Không đến", tone: "danger" },
};

export const DEPOSIT_META: Record<DepositPaymentStatus, Meta> = {
  unpaid: { label: "Chưa cọc", tone: "neutral" },
  pending: { label: "Đang chờ thanh toán", tone: "warn" },
  success: { label: "Đã cọc", tone: "ok" },
  failed: { label: "Thanh toán lỗi", tone: "danger" },
  refunded: { label: "Đã hoàn cọc", tone: "info" },
  partially_refunded: { label: "Hoàn một phần", tone: "info" },
};

export const TABLE_META: Record<TableStatus, Meta> = {
  available: { label: "Còn trống", tone: "ok" },
  held: { label: "Đang giữ", tone: "warn" },
  reserved: { label: "Đã đặt", tone: "info" },
  occupied: { label: "Đang dùng", tone: "dark" },
  maintenance: { label: "Bảo trì", tone: "neutral" },
};
