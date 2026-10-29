export type OrderStatus = "pending" | "confirmed" | "preparing" | "ready" | "completed" | "cancelled";
export type ReservationStatus = "pending_confirmation" | "pending_payment" | "confirmed" | "seated" | "completed" | "cancelled" | "no_show";
export type DepositPaymentStatus = "unpaid" | "pending" | "success" | "failed" | "refunded" | "partially_refunded";
export type ReservationOption = "table_only" | "table_and_food" | "table_and_food_editable";
export type TableStatus = "available" | "held" | "reserved" | "occupied" | "maintenance";
export type CancellationBucket = ">24h" | "6-24h" | "<6h" | "no_show";

export type Module =
  | "dashboard" | "orders" | "reservations" | "tables" | "chat"
  | "foods" | "categories" | "ingredients" | "promotions" | "posts" | "reviews"
  | "payments" | "deposit" | "branches" | "users" | "roles" | "ai" | "settings";
export type Action = "view" | "create" | "update" | "delete";
export type RoleName = "admin" | "staff";

export interface LineItem { name: string; qty: number; price: number }

export interface AdminOrder {
  id: string;
  code: string;
  customer: string;
  phone: string;
  type: "delivery" | "pickup";
  address?: string;
  note?: string;
  items: LineItem[];
  subtotal: number;
  discount: number;
  total: number;
  payment: "cod" | "bank" | "vnpay";
  status: OrderStatus;
  createdAt: string;
  history: { to: OrderStatus; at: string; by: string; note?: string }[];
}

export interface RefundRecord {
  percent: number;
  amount: number;
  reference: string;
  note: string;
  at: string;
  by: string;
}

export interface AdminReservation {
  id: string;
  code: string;
  customer: string;
  phone: string;
  tableId: string;
  tableLabel: string;
  date: string; // YYYY-MM-DD
  time: string; // HH:mm
  partySize: number;
  option: ReservationOption;
  status: ReservationStatus;
  depositAmount: number;
  depositStatus: DepositPaymentStatus;
  foodItems: LineItem[];
  note?: string;
  version: number;
  cancelledAt?: string;
  cancelReason?: string;
  refund?: RefundRecord;
}

export interface AdminTable {
  id: string;
  number: string;
  zone: "Trong nhà" | "Ban công" | "Sân vườn";
  capacity: number;
  status: TableStatus;
}

export interface DepositPolicyData {
  id: string;
  depositPercentage: number;
  holdMinutes: number;
  paymentDeadlineMinutes: number;
  hotline: string;
  guideText: string;
  rules: { bucket: CancellationBucket; refundPercentage: number }[];
}

export interface AdminPayment {
  id: string;
  code: string;
  kind: "order" | "deposit";
  ref: string;
  method: "cod" | "bank" | "vnpay";
  amount: number;
  status: "pending" | "success" | "failed" | "refunded";
  createdAt: string;
}
