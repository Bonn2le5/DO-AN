import type { OrderStatus } from "@/types";

export interface OrderHistoryItem {
  id: string;
  createdAt: string;
  total: number;
  status: OrderStatus;
  items: number;
}

const mockOrders: OrderHistoryItem[] = [
  { id: "MC482910", createdAt: "2026-08-20", total: 328000, status: "preparing", items: 3 },
  { id: "MC471203", createdAt: "2026-08-12", total: 154000, status: "completed", items: 2 },
  { id: "MC459981", createdAt: "2026-07-30", total: 620000, status: "completed", items: 5 },
];

export default mockOrders;
