export type OrderStatus = "pending" | "confirmed" | "preparing" | "ready" | "completed" | "cancelled";
export type ReservationStatus = "pending_confirmation" | "pending_payment" | "confirmed" | "seated" | "completed" | "cancelled" | "no_show";
export type DepositPaymentStatus = "unpaid" | "pending" | "success" | "failed" | "refunded" | "partially_refunded";
export type ReservationOption = "table_only" | "table_and_food" | "table_and_food_editable";
export type TableStatus = "available" | "held" | "reserved" | "occupied" | "cleaning" | "maintenance";
export type DiningSessionStatus = "active" | "cleaning" | "closed";
export type CancellationBucket = ">24h" | "6-24h" | "<6h" | "no_show";

export type Module =
  | "dashboard" | "orders" | "reservations" | "tables" | "chat"
  | "foods" | "categories" | "ingredients" | "stock" | "promotions" | "posts" | "reviews"
  | "payments" | "deposit" | "branches" | "users" | "roles" | "ai" | "settings";
export type Action = "view" | "create" | "update" | "delete";
export type RoleName = "admin" | "branch_manager" | "staff";

export interface LineItem { id?: string; foodId?: string; name: string; qty: number; price: number; note?: string; image?: string }

export interface AdminOrder {
  id: string;
  code: string;
  customer: string;
  phone: string;
  branchId?: string;
  sessionId?: string;
  reservationId?: string;
  note?: string;
  items: LineItem[];
  subtotal: number;
  discount: number;
  total: number;
  payment: "cod" | "bank" | "payos";
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
  branchId?: string;
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
  checkedInAt?: string;
  sessionId?: string;
  orderId?: string;
  orderCode?: string;
}

export interface AdminDiningSession {
  id: string;
  code: string;
  branchId: string;
  tableId: string;
  tableLabel: string;
  reservationId?: string;
  orderId?: string;
  orderCode?: string;
  orderTotal?: number;
  /** Tiền cọc khách đã trả khi đặt bàn, được trừ khi thanh toán. */
  depositPaid?: number;
  guestCount: number;
  customer: string;
  phone: string;
  note?: string;
  status: DiningSessionStatus;
  startedAt: string;
  checkedOutAt?: string;
}

export interface AdminTable {
  id: string;
  branchId?: string;
  number: string;
  zone: string;
  roomId?: string;
  roomName?: string;
  capacity: number;
  status: TableStatus;
  archived?: boolean;
  activeSession?: AdminDiningSession;
}

export interface AdminPrivateRoom {
  id: string;
  branchId: string;
  name: string;
  floor: string;
  capacity: number;
  active: boolean;
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
  method: "cod" | "bank" | "payos";
  amount: number;
  status: "pending" | "success" | "failed" | "refunded";
  createdAt: string;
}
