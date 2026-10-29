import { apiClient } from "./client";
import type { CartItem } from "@/types";
import type { OrderStatus } from "@/types";

export interface CreateOrderPayload {
  items: CartItem[];
  orderType: "delivery" | "pickup";
  paymentMethod: "cod" | "bank";
  name: string;
  phone: string;
  address?: string;
  note?: string;
  promoCode?: string;
}

export interface CreateOrderResult {
  orderId: string;
}

export async function createOrder(payload: CreateOrderPayload): Promise<CreateOrderResult> {
  const { data } = await apiClient.post("/orders/", {
    items: payload.items.map(({ food, quantity }) => ({ food_id: food.id, quantity })),
    order_type: payload.orderType === "delivery" ? "giao_hang" : "mang_ve",
    payment_method: payload.paymentMethod,
    customer_name: payload.name,
    phone: payload.phone,
    address: payload.address || "",
    note: payload.note || "",
    promo_code: payload.promoCode || "",
  });
  return { orderId: data.ma_don_hang ?? data.number ?? String(data.id) };
}

export interface OrderHistoryItem {
  id: number | string;
  orderNumber?: string;
  code?: string;
  createdAt: string;
  total: number;
  status: OrderStatus;
  items: number;
}

export async function getMyOrders(): Promise<OrderHistoryItem[]> {
  const { data } = await apiClient.get("/orders/");
  const list = Array.isArray(data) ? data : data.results ?? [];
  return list.map((order: any) => {
    const rawNum = order.id !== undefined && order.id !== null ? Number(order.id) : NaN;
    const orderCode = order.ma_don_hang ?? order.number ?? (order.id ? String(order.id) : "");
    return {
      id: !isNaN(rawNum) && rawNum > 0 ? rawNum : (orderCode || order.id),
      orderNumber: orderCode,
      code: orderCode,
      createdAt: order.tao_luc ?? order.created_at ?? new Date().toISOString(),
      total: Number(order.tong_tien ?? order.total ?? 0),
      status: (order.trang_thai ?? order.status ?? "pending") as OrderStatus,
      items: (order.danh_sach_mon ?? order.items ?? []).reduce(
        (acc: number, item: any) => acc + Number(item.so_luong ?? item.quantity ?? 1),
        0
      ),
    };
  });
}

