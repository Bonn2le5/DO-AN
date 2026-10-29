import { ago, lineTotal, ymd } from "../lib";
import type { LineItem, AdminOrder, AdminReservation, AdminTable, AdminPayment, DepositPolicyData } from "../types";
import type { OrderStatus } from "../types";

const L = (name: string, qty: number, price: number): LineItem => ({ name, qty, price });
const FLOW: OrderStatus[] = ["pending", "confirmed", "preparing", "ready", "completed"];

function order(
  n: number, customer: string, phone: string, type: AdminOrder["type"], status: OrderStatus,
  minutesAgo: number, items: LineItem[], discount = 0, payment: AdminOrder["payment"] = "cod", address?: string,
): AdminOrder {
  const subtotal = lineTotal(items);
  const steps: OrderStatus[] = status === "cancelled" ? ["pending", "cancelled"] : FLOW.slice(0, FLOW.indexOf(status) + 1);
  return {
    id: `o${n}`, code: `MC${482900 + n * 7}`, customer, phone, type, address, items, subtotal, discount,
    total: subtotal - discount, payment, status, createdAt: ago(minutesAgo),
    note: n % 3 === 0 ? "Ít cay, không hành" : undefined,
    history: steps.map((s, i) => ({
      to: s, at: ago(minutesAgo - i * 6), by: i === 0 ? "Khách hàng" : "Lê Thu Hà",
      note: s === "cancelled" ? "Khách đổi ý" : undefined,
    })),
  };
}

export const ordersSeed: AdminOrder[] = [
  order(1, "Nguyễn Lan Anh", "0903 112 233", "delivery", "pending", 4, [L("Lẩu Thái hải sản", 1, 259000), L("Trà đào cam sả", 2, 45000)], 0, "cod", "45 Nguyễn Thị Minh Khai, Q.3"),
  order(2, "Trần Minh Tân", "0987 654 321", "pickup", "pending", 11, [L("Bò lúc lắc sốt tiêu", 2, 189000)], 37800, "vnpay"),
  order(3, "Phạm Hoài Thương", "0912 345 678", "delivery", "confirmed", 25, [L("Cơm tấm sườn bì chả", 3, 75000), L("Gỏi cuốn tôm thịt", 2, 69000)], 0, "bank", "12 Hoàng Văn Thụ, Phú Nhuận"),
  order(4, "Võ Quốc Bảo", "0933 221 100", "pickup", "preparing", 38, [L("Bún chả Hà Nội", 2, 79000)]),
  order(5, "Đặng Mỹ Linh", "0909 888 777", "delivery", "preparing", 52, [L("Lẩu Thái hải sản", 2, 259000), L("Chè khúc bạch nhãn", 2, 39000)], 50000, "vnpay", "88 Lê Văn Sỹ, Q.3"),
  order(6, "Hồ Gia Huy", "0977 123 456", "pickup", "ready", 70, [L("Cơm tấm sườn bì chả", 1, 75000), L("Trà đào cam sả", 1, 45000)]),
  order(7, "Ngô Thanh Vân", "0966 000 111", "delivery", "completed", 190, [L("Bò lúc lắc sốt tiêu", 1, 189000), L("Gỏi cuốn tôm thịt", 1, 69000)], 0, "cod", "5 Trần Quang Diệu, Q.3"),
  order(8, "Bùi Khánh Ly", "0944 567 890", "pickup", "cancelled", 300, [L("Chè khúc bạch nhãn", 4, 39000)]),
];

export const tablesSeed: AdminTable[] = [
  { id: "t1", number: "Bàn 1", zone: "Trong nhà", capacity: 2, status: "available" },
  { id: "t2", number: "Bàn 2", zone: "Trong nhà", capacity: 2, status: "reserved" },
  { id: "t3", number: "Bàn 3", zone: "Trong nhà", capacity: 4, status: "available" },
  { id: "t4", number: "Bàn 4", zone: "Trong nhà", capacity: 4, status: "occupied" },
  { id: "t5", number: "Bàn 5", zone: "Ban công", capacity: 6, status: "available" },
  { id: "t6", number: "Bàn 6", zone: "Ban công", capacity: 6, status: "maintenance" },
  { id: "t7", number: "Bàn 7", zone: "Sân vườn", capacity: 8, status: "available" },
  { id: "t8", number: "Bàn 8", zone: "Sân vườn", capacity: 4, status: "available" },
];

function res(
  n: number, customer: string, phone: string, tableId: string, tableLabel: string, date: string, time: string,
  partySize: number, option: AdminReservation["option"], status: AdminReservation["status"],
  items: LineItem[] = [], extra: Partial<AdminReservation> = {},
): AdminReservation {
  const deposit = option === "table_only" ? 0 : Math.round(lineTotal(items) * 0.2);
  const paid = status !== "pending_payment" && deposit > 0;
  return {
    id: `r${n}`, code: `RS${1000 + n * 13}`, customer, phone, tableId, tableLabel, date, time, partySize, option, status,
    depositAmount: deposit, depositStatus: deposit === 0 ? "unpaid" : paid ? "success" : "pending",
    foodItems: items, version: 0, ...extra,
  };
}

export const reservationsSeed: AdminReservation[] = [
  res(1, "Nguyễn Văn Hùng", "0901 234 567", "t5", "Bàn 5", ymd(0), "18:00", 6, "table_and_food", "confirmed", [L("Lẩu Thái hải sản", 2, 259000), L("Gỏi cuốn tôm thịt", 3, 69000)], { note: "Sinh nhật, cần bánh kem" }),
  res(2, "Lê Thị Mai", "0912 000 345", "t3", "Bàn 3", ymd(0), "12:00", 4, "table_only", "seated"),
  res(3, "Phan Quốc Đạt", "0987 111 222", "t7", "Bàn 7", ymd(0), "19:30", 8, "table_and_food_editable", "pending_payment", [L("Bò lúc lắc sốt tiêu", 4, 189000)]),
  res(4, "Trịnh Bảo Châu", "0933 456 789", "t1", "Bàn 1", ymd(0), "20:00", 2, "table_only", "confirmed"),
  res(5, "Đỗ Minh Khôi", "0944 321 987", "t8", "Bàn 8", ymd(1), "18:30", 4, "table_and_food", "confirmed", [L("Cơm tấm sườn bì chả", 4, 75000), L("Trà đào cam sả", 4, 45000)]),
  res(6, "Vũ Ngọc Hân", "0966 777 888", "t5", "Bàn 5", ymd(-1), "19:00", 5, "table_and_food", "cancelled", [L("Lẩu Thái hải sản", 2, 259000)], { cancelledAt: ago(60 * 30), cancelReason: "Khách báo bận việc đột xuất" }),
  res(7, "Hoàng Gia Bảo", "0908 555 666", "t7", "Bàn 7", ymd(-2), "18:00", 8, "table_and_food", "no_show", [L("Bò lúc lắc sốt tiêu", 3, 189000), L("Lẩu Thái hải sản", 2, 259000)], { cancelledAt: ago(60 * 40) }),
  res(8, "Tạ Thanh Hằng", "0977 888 999", "t3", "Bàn 3", ymd(-4), "12:30", 4, "table_and_food", "cancelled", [L("Bún chả Hà Nội", 4, 79000)], {
    cancelledAt: ago(60 * 24 * 5), cancelReason: "Đổi lịch", depositStatus: "refunded",
    refund: { percent: 100, amount: 63200, reference: "VCB-0910-2231", note: "CSKH xác minh qua điện thoại", at: ago(60 * 24 * 3), by: "Lê Thu Hà" },
  }),
];

export const paymentsSeed: AdminPayment[] = [
  { id: "p1", code: "VNP4410023", kind: "deposit", ref: "RS1013", method: "vnpay", amount: 233000, status: "success", createdAt: ago(60 * 5) },
  { id: "p2", code: "VNP4410031", kind: "order", ref: "MC482914", method: "vnpay", amount: 340200, status: "success", createdAt: ago(40) },
  { id: "p3", code: "BANK-7781", kind: "order", ref: "MC482921", method: "bank", amount: 357000, status: "pending", createdAt: ago(28) },
  { id: "p4", code: "VNP4409877", kind: "deposit", ref: "RS1039", method: "vnpay", amount: 756000, status: "pending", createdAt: ago(9) },
  { id: "p5", code: "VNP4409102", kind: "deposit", ref: "RS1104", method: "vnpay", amount: 63200, status: "refunded", createdAt: ago(60 * 24 * 5) },
  { id: "p6", code: "VNP4408890", kind: "order", ref: "MC482872", method: "vnpay", amount: 120000, status: "failed", createdAt: ago(60 * 26) },
];

export const depositPolicySeed: DepositPolicyData[] = [
  {
    id: "dp1", depositPercentage: 20, holdMinutes: 10, paymentDeadlineMinutes: 15, hotline: "028 3822 1234",
    guideText:
      "MỘC không tự động hoàn cọc. Khi cần huỷ, bạn vui lòng liên hệ lễ tân hoặc CSKH để được hướng dẫn thủ tục. Sau khi nhà hàng xác minh và chuyển khoản, tiền sẽ về tài khoản của bạn trong thời gian ngân hàng xử lý.",
    rules: [
      { bucket: ">24h", refundPercentage: 100 },
      { bucket: "6-24h", refundPercentage: 50 },
      { bucket: "<6h", refundPercentage: 0 },
      { bucket: "no_show", refundPercentage: 0 },
    ],
  },
];
