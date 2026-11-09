import { apiClient } from "@/api/client";
import type { Store } from "./store";
import type { AdminOrder, AdminReservation, AdminTable, AdminPrivateRoom, AdminPayment, AdminDiningSession, DepositPolicyData, RefundRecord } from "../types";
import type { AdminFood, AdminCategory, AdminTag, AdminIngredient, AdminPromotion, AdminPost, AdminReview, AdminUser, AdminBranch } from "../data/mockCatalog";
import type { CancellationBucket, DiningSessionStatus, OrderStatus, ReservationStatus, TableStatus } from "../types";

type Raw = Record<string, any>;
const val = (o: Raw, ...keys: string[]) => keys.map((k) => o?.[k]).find((v) => v !== undefined && v !== null);
const num = (v: unknown) => Number(v ?? 0);
const text = (v: unknown) => String(v ?? "");
const bool = (v: unknown) => Boolean(v);
const list = async (path: string): Promise<Raw[]> => {
  const { data } = await apiClient.get(path);
  return Array.isArray(data) ? data : (data?.results ?? data?.data ?? []);
};
const remove = async (path: string, id: string) => { await apiClient.delete(`${path}${id}/`); };
const mappedStore = <T extends { id: string }>(path: string, from: (r: Raw) => T, to: (v: Partial<T>) => Raw, keyOf = (r: Raw) => text(r.id)): Store<T> => {
  const keys = new Map<string, string>();
  return {
    async list() { const rows = await list(path); keys.clear(); return rows.map((r) => { const item = from(r); keys.set(item.id, keyOf(r)); return item; }); },
    async create(draft) { const payload = to(draft as Partial<T>); if (path === "/tables/" && !payload.branch) payload.branch = (await list("/branches/"))[0]?.id; const { data: raw } = path === "/users/" ? await apiClient.post("/users/admin_create/", payload) : await apiClient.post(path, payload); const item = from(raw); keys.set(item.id, keyOf(raw)); return item; },
    async update(id, patch) { const payload = to(patch); const { data: raw } = path === "/users/" ? await apiClient.patch(`/users/${keys.get(id) ?? id}/admin_update/`, payload) : path === "/payments/" ? await apiClient.post(`/payments/${id}/mark_success/`) : path === "/chat/rooms/" && "unread" in patch ? await apiClient.post(`/chat/rooms/${id}/mark_read/`) : await apiClient.patch(`${path}${keys.get(id) ?? id}/`, payload); const item = from(raw); keys.set(item.id, keyOf(raw)); return item; },
    async remove(id) { await remove(path, keys.get(id) ?? id); keys.delete(id); },
  };
};
const stateMap = (v: unknown, mapping: Record<string, string>) => mapping[text(v)] ?? text(v);
const orderState: Record<string, string> = { cho_tiep_nhan: "pending", da_xac_nhan: "confirmed", dang_che_bien: "preparing", san_sang: "ready", hoan_tat: "completed", da_huy: "cancelled" };
const reservationState: Record<string, string> = { cho_xac_nhan: "pending_confirmation", cho_thanh_toan: "pending_payment", da_xac_nhan: "confirmed", khach_da_den: "seated", hoan_tat: "completed", da_huy: "cancelled", khach_khong_den: "no_show" };
const depositState: Record<string, string> = { chua_thanh_toan: "unpaid", dang_xu_ly: "pending", thanh_cong: "success", that_bai: "failed", da_hoan_tien: "refunded", hoan_tien_mot_phan: "partially_refunded" };
const tableState: Record<string, string> = { trong: "available", dang_giu: "held", da_dat: "reserved", dang_phuc_vu: "occupied", cho_don: "cleaning", bao_tri: "maintenance" };
const sessionState: Record<string, string> = { dang_phuc_vu: "active", cho_don: "cleaning", da_dong: "closed" };
const statusToBackend: Record<string, string> = { pending: "cho_tiep_nhan", confirmed: "da_xac_nhan", preparing: "dang_che_bien", ready: "san_sang", completed: "hoan_tat", cancelled: "da_huy", pending_confirmation: "cho_xac_nhan", pending_payment: "cho_thanh_toan", seated: "khach_da_den", no_show: "khach_khong_den", available: "trong", held: "dang_giu", reserved: "da_dat", occupied: "dang_phuc_vu", cleaning: "cho_don", maintenance: "bao_tri" };
const lineItems = (rows: Raw[] = []) => rows.map((i) => ({ id: text(i.id) || undefined, foodId: text(val(i, "food_id", "mon_an_id") ?? i.mon_an?.id) || undefined, name: text(val(i, "name", "ten_mon") ?? val(i.mon_an, "ten", "name")), qty: num(val(i, "qty", "quantity", "so_luong")), price: num(val(i, "price", "don_gia_luc_dat", "don_gia")), note: text(val(i, "note", "ghi_chu")) || undefined, image: text(val(i, "image", "anh_dai_dien") ?? val(i.mon_an, "anh_dai_dien")) || undefined }));
const mapDiningSession = (r: Raw): AdminDiningSession => ({
  id: text(r.id), code: text(val(r, "code", "ma_phien")), branchId: text(val(r, "branch_id", "chi_nhanh_id", "chi_nhanh")),
  tableId: text(val(r, "table_id", "ban_an_id", "ban_an")), tableLabel: text(val(r, "table_label", "so_ban", "ten_ban")),
  reservationId: text(val(r, "reservation_id", "dat_ban_id", "dat_ban")) || undefined,
  orderId: text(val(r, "order_id", "don_hang_id")) || undefined,
  orderCode: text(val(r, "order_code", "ma_don_hang")) || undefined,
  orderTotal: val(r, "order_total") != null ? num(val(r, "order_total")) : undefined,
  depositPaid: val(r, "tien_coc_da_tra") != null ? num(val(r, "tien_coc_da_tra")) : undefined,
  guestCount: num(val(r, "guest_count", "so_luong_khach")), customer: text(val(r, "customer_name", "ten_khach")),
  phone: text(val(r, "customer_phone", "sdt_khach")), note: text(val(r, "note", "ghi_chu")) || undefined,
  status: stateMap(val(r, "status", "trang_thai"), sessionState) as DiningSessionStatus,
  startedAt: text(val(r, "started_at", "bat_dau_luc", "tao_luc")), checkedOutAt: text(val(r, "checked_out_at", "check_out_luc")) || undefined,
});

export const ordersStore = mappedStore<AdminOrder>("/orders/", (r) => ({
  id: text(r.id), code: text(val(r, "code", "ma_don_hang")), customer: text(val(r, "customer_name", "ten_khach", "name")), phone: text(val(r, "customer_phone", "sdt_khach", "phone")),
  branchId: text(val(r, "branch_id", "chi_nhanh_id", "chi_nhanh")) || undefined,
  sessionId: text(val(r, "session_id", "phien_phuc_vu_id", "phien_phuc_vu")) || undefined,
  reservationId: text(val(r, "reservation_id", "dat_ban_id", "dat_ban")) || undefined,
  note: text(val(r, "note", "ghi_chu")),
  items: lineItems(val(r, "items", "danh_sach_mon") ?? []), subtotal: num(val(r, "subtotal", "tien_hang")), discount: num(val(r, "discount", "tien_giam")), total: num(val(r, "total", "tong_tien")),
  payment: stateMap(val(r, "payment_method", "phuong_thuc_thanh_toan"), { tien_mat: "cod", chuyen_khoan: "bank" }) as AdminOrder["payment"], status: stateMap(val(r, "status", "trang_thai"), orderState) as OrderStatus,
  createdAt: text(val(r, "created_at", "tao_luc")), history: (val(r, "lich_su_trang_thai", "status_history") ?? []).map((h: Raw) => ({ to: stateMap(val(h, "to_status", "sang_trang_thai"), orderState) as OrderStatus, at: text(val(h, "created_at", "tao_luc")), by: text(val(h, "by", "doi_boi_name")), note: text(val(h, "note", "ghi_chu")) })),
}), (v) => ({ customer_name: v.customer, customer_phone: v.phone, note: v.note, items: v.items?.map((i) => ({ name: i.name, qty: i.qty, price: i.price })), status: statusToBackend[text(v.status)] ?? v.status }));

export const reservationsStore = mappedStore<AdminReservation>("/reservations/", (r) => {
  const table = val(r, "ban_an", "table") ?? {};
  const items = val(r, "food_items", "danh_sach_mon") ?? [];
  const branch = val(r, "branch", "chi_nhanh");
  return { id: text(r.id), code: text(val(r, "code", "ma_dat_ban")), customer: text(val(r, "customer_name", "ten_khach")), phone: text(val(r, "customer_phone", "sdt_khach")), tableId: text(val(r, "table_id", "ban_an_id") ?? table.id), tableLabel: text(val(r, "so_ban", "ten_ban") ?? val(table, "so_ban", "number")), branchId: text(val(r, "branch_id", "chi_nhanh_id") ?? (typeof branch === "object" ? branch.id : branch)), date: text(val(r, "date", "ngay_dat")), time: text(val(r, "time", "gio_bat_dau")).slice(0, 5), partySize: num(val(r, "guest_count", "so_luong_khach")), option: stateMap(val(r, "type", "hinh_thuc"), { chi_giu_cho: "table_only", dat_ban_va_goi_mon: "table_and_food", dat_ban_goi_mon_chinh_sua: "table_and_food_editable" }) as AdminReservation["option"], status: stateMap(val(r, "status", "trang_thai"), reservationState) as ReservationStatus, depositAmount: num(val(r, "deposit_amount", "so_tien_coc")), depositStatus: stateMap(val(r, "deposit_status", "trang_thai_coc"), depositState) as AdminReservation["depositStatus"], foodItems: lineItems(items.map((i: Raw) => ({ ...i, name: val(i.mon_an, "ten", "name") }))), note: text(val(r, "note", "ghi_chu")), version: num(val(r, "version", "phien_ban")), cancelledAt: text(val(r, "cancelled_at", "huy_luc")), cancelReason: text(val(r, "cancel_reason", "ly_do_huy")), refund: val(r, "refund", "refund_record"), checkedInAt: text(val(r, "checked_in_at", "check_in_luc")) || undefined, sessionId: text(val(r, "session_id", "phien_phuc_vu_id")) || undefined, orderId: text(val(r, "order_id", "don_hang_id")) || undefined, orderCode: text(val(r, "order_code", "ma_don_hang")) || undefined };
}, (v) => ({ table: v.tableId, date: v.date, time: v.time, guest_count: v.partySize, type: v.option === "table_only" ? "chi_giu_cho" : v.option === "table_and_food" ? "dat_ban_va_goi_mon" : "dat_ban_goi_mon_chinh_sua", customer_name: v.customer, customer_phone: v.phone, note: v.note, status: statusToBackend[text(v.status)] ?? v.status }));

export const tablesStore = mappedStore<AdminTable>("/tables/", (r) => ({ id: text(r.id), branchId: text(val(r, "branch_id", "chi_nhanh_id", "branch")), number: text(val(r, "number", "so_ban")), zone: (text(val(r, "zone", "khu_vuc")) || "Trong nhà") as AdminTable["zone"], capacity: num(val(r, "capacity", "suc_chua")), status: stateMap(val(r, "status", "trang_thai"), tableState) as TableStatus, activeSession: r.phien_phuc_vu_hien_tai ? mapDiningSession(r.phien_phuc_vu_hien_tai) : undefined }), (v) => ({ number: v.number, area: v.zone, capacity: v.capacity, status: statusToBackend[text(v.status)] ?? v.status } as Raw));

const unwrapList = (data: any): Raw[] => Array.isArray(data) ? data : data?.results ?? data?.data ?? [];
export async function getTableManagementBranches(): Promise<AdminBranch[]> {
  const { data } = await apiClient.get("/branches/");
  return unwrapList(data).map((r) => ({ id: text(r.id), name: text(val(r, "name", "ten")), address: text(val(r, "address", "dia_chi")), phone: text(val(r, "phone", "so_dien_thoai")), lat: num(val(r, "lat", "vi_do")), lng: num(val(r, "lng", "kinh_do")), active: bool(val(r, "active", "con_hoat_dong")) }));
}
export async function getTableManagementTables(branchId?: string, includeArchived = false): Promise<AdminTable[]> {
  const { data } = await apiClient.get("/tables/", { params: { ...(branchId ? { chi_nhanh: branchId } : {}), ...(includeArchived ? { include_archived: "true" } : {}) } });
  return unwrapList(data).map((r) => ({ id: text(r.id), branchId: text(val(r, "chi_nhanh", "branch")), number: text(val(r, "so_ban", "number")), zone: text(val(r, "khu_vuc", "area")) || "Chưa phân khu", roomId: val(r, "phong_rieng") ? text(val(r, "phong_rieng")) : undefined, capacity: num(val(r, "suc_chua", "capacity")), status: stateMap(val(r, "trang_thai", "status"), tableState) as TableStatus, archived: bool(r.da_luu_tru), activeSession: r.phien_phuc_vu_hien_tai ? { ...mapDiningSession(r.phien_phuc_vu_hien_tai), tableId: text(r.id), tableLabel: text(val(r, "so_ban", "number")), branchId: text(val(r, "chi_nhanh", "branch")) } : undefined }));
}
export async function getTableManagementRooms(branchId?: string, includeInactive = false): Promise<AdminPrivateRoom[]> {
  const { data } = await apiClient.get("/rooms/", { params: { ...(branchId ? { chi_nhanh: branchId } : {}), ...(includeInactive ? { include_inactive: "true" } : {}) } });
  return unwrapList(data).map((r) => ({ id: text(r.id), branchId: text(r.chi_nhanh), name: text(r.ten_phong), floor: text(r.tang), capacity: num(r.suc_chua), active: bool(r.con_hoat_dong) }));
}
export async function createTableManagementRoom(room: Omit<AdminPrivateRoom, "id" | "active">): Promise<void> {
  await apiClient.post("/rooms/", { chi_nhanh: Number(room.branchId), ten_phong: room.name, tang: room.floor, suc_chua: room.capacity, con_hoat_dong: true });
}
export async function updateTableManagementRoom(room: AdminPrivateRoom): Promise<void> {
  await apiClient.patch(`/rooms/${room.id}/`, { ten_phong: room.name, tang: room.floor, suc_chua: room.capacity, con_hoat_dong: room.active });
}
export async function archiveTableManagementRoom(id: string): Promise<void> { await apiClient.delete(`/rooms/${id}/`); }
export async function createTableManagementTable(table: Omit<AdminTable, "id">): Promise<void> {
  await apiClient.post("/tables/", { chi_nhanh: Number(table.branchId), so_ban: table.number, khu_vuc: table.zone, suc_chua: table.capacity, trang_thai: statusToBackend[table.status], phong_rieng: table.roomId ? Number(table.roomId) : null });
}
export async function updateTableManagementTable(table: AdminTable): Promise<void> {
  await apiClient.patch(`/tables/${table.id}/`, { chi_nhanh: Number(table.branchId), so_ban: table.number, khu_vuc: table.zone, suc_chua: table.capacity, trang_thai: statusToBackend[table.status], phong_rieng: table.roomId ? Number(table.roomId) : null });
}
export async function archiveTableManagementTable(id: string): Promise<void> { await apiClient.delete(`/tables/${id}/`); }
export async function restoreTableManagementTable(id: string): Promise<void> { await apiClient.patch(`/tables/${id}/`, { da_luu_tru: false }); }
export async function listDiningSessions(branchId?: string): Promise<AdminDiningSession[]> {
  const { data } = await apiClient.get("/dining-sessions/", { params: branchId ? { chi_nhanh: branchId } : undefined });
  return unwrapList(data).map(mapDiningSession);
}
export async function getDiningSession(id: string): Promise<AdminDiningSession> {
  const { data } = await apiClient.get(`/dining-sessions/${id}/`);
  return mapDiningSession(data);
}
export async function startWalkIn(input: { tableId: string; guestCount: number; customer?: string; phone?: string; note?: string }): Promise<AdminDiningSession> {
  const { data } = await apiClient.post("/dining-sessions/walk-in/", { ban_an: Number(input.tableId), so_luong_khach: input.guestCount, ten_khach: input.customer ?? "", sdt_khach: input.phone ?? "", ghi_chu: input.note ?? "" });
  return mapDiningSession(data);
}
export async function checkInReservation(id: string, version: number): Promise<AdminReservation> {
  await apiClient.post(`/reservations/${id}/check-in/`, { version });
  const reservation = (await reservationsStore.list()).find((item) => item.id === id);
  if (!reservation) throw new Error("Không tìm thấy đặt bàn vừa check-in.");
  return reservation;
}
export async function startReservationSession(reservationId: string, tableId: string): Promise<AdminDiningSession> {
  const { data } = await apiClient.post(`/reservations/${reservationId}/seat/`, { ban_an: Number(tableId) });
  return mapDiningSession(data);
}
export async function addDiningSessionItems(sessionId: string, items: { foodId: string; quantity: number; note?: string }[]): Promise<AdminDiningSession> {
  const { data } = await apiClient.post(`/dining-sessions/${sessionId}/items/`, { danh_sach_mon: items.map((item) => ({ mon_an_id: Number(item.foodId), so_luong: item.quantity, ghi_chu: item.note ?? "" })) });
  return mapDiningSession(data);
}
export interface LowStockWarning { id: string; name: string; unit: string; stock: number; minStock: number; foods: string[] }
type RawLowStock = { nguyen_lieu_id: number; ten: string; don_vi: string; ton_kho_hien_tai: number; ton_kho_toi_thieu: number; mon_an: string[] };
const mapLowStock = (rows?: RawLowStock[]): LowStockWarning[] => (rows ?? []).map((r) => ({ id: String(r.nguyen_lieu_id), name: r.ten, unit: r.don_vi, stock: Number(r.ton_kho_hien_tai), minStock: Number(r.ton_kho_toi_thieu), foods: r.mon_an ?? [] }));
export function lowStockMessage(rows: LowStockWarning[]) {
  if (!rows.length) return "";
  const parts = rows.map((r) => `${r.name} còn ${r.stock}${r.unit ? " " + r.unit : ""} (${r.foods.join(", ")})`);
  return `Sắp hết nguyên liệu: ${parts.join("; ")}`;
}
export async function replaceDiningSessionItems(sessionId: string, items: { foodId: string; quantity: number; note?: string }[]): Promise<AdminDiningSession & { lowStock: LowStockWarning[] }> {
  const { data } = await apiClient.put(`/dining-sessions/${sessionId}/items/`, { danh_sach_mon: items.map((item) => ({ mon_an_id: Number(item.foodId), so_luong: item.quantity, ghi_chu: item.note ?? "" })) });
  return { ...mapDiningSession(data), lowStock: mapLowStock(data.canh_bao_kho) };
}
export async function moveDiningSession(sessionId: string, tableId: string): Promise<AdminDiningSession> {
  const { data } = await apiClient.post(`/dining-sessions/${sessionId}/move-table/`, { ban_an: Number(tableId) });
  return mapDiningSession(data);
}
export async function checkoutDiningSession(sessionId: string, paymentMethod: "cod" | "bank" | "vnpay", reference?: string): Promise<AdminDiningSession> {
  const { data } = await apiClient.post(`/dining-sessions/${sessionId}/checkout/`, { phuong_thuc: paymentMethod === "cod" ? "tien_mat" : paymentMethod === "bank" ? "chuyen_khoan" : "vnpay", ma_tham_chieu: reference ?? "" });
  return mapDiningSession(data);
}
/** Huỷ bàn: nhân viên khi chưa gửi bếp, quản lý khi đã gửi bếp (hoá đơn chuyển "Đã huỷ"). */
export async function cancelDiningSession(sessionId: string, reason = ""): Promise<AdminDiningSession> {
  const { data } = await apiClient.post(`/dining-sessions/${sessionId}/cancel/`, { ly_do: reason });
  return mapDiningSession(data);
}
/** Nguyên liệu đang thiếu và các món bị ảnh hưởng, để đánh dấu trên thực đơn. */
export async function getStockAlerts(): Promise<LowStockWarning[]> {
  const { data } = await apiClient.get("/dining-sessions/canh-bao-kho/");
  return mapLowStock(data);
}
export async function confirmDiningSessionCleaned(sessionId: string): Promise<AdminDiningSession> {
  const { data } = await apiClient.post(`/dining-sessions/${sessionId}/confirm-cleaned/`);
  return mapDiningSession(data);
}

export const foodsStore = mappedStore<AdminFood>("/foods/", (r) => ({ id: text(r.id), name: text(val(r, "name", "ten")), category: text(val(r, "category_name", "ten_danh_muc") ?? val(r.chi_tiet_danh_muc, "ten", "name") ?? r.danh_muc), price: num(val(r, "price", "don_gia_hien_tai", "don_gia")), stock: num(val(r, "stock", "ton_kho_cache")), available: bool(val(r, "available", "con_hang")), spicy: num(val(r, "spicy_level", "do_cay")), vegetarian: bool(val(r, "is_vegetarian", "la_mon_chay")), trackInventory: bool(val(r, "track_inventory", "quan_ly_kho")), description: text(val(r, "description", "mo_ta_ngan", "mo_ta_chi_tiet")), image: text(val(r, "image", "anh_dai_dien") ?? val((r.hinh_anh ?? [])[0], "image", "anh")), tone: 1, rating: num(val(r, "rating", "diem_danh_gia")) }), (v) => ({ name: v.name, category: v.category, price: v.price, short_description: v.description, description: v.description, image: v.image, spicy_level: v.spicy, is_vegetarian: v.vegetarian, is_available: v.available, ton_kho_cache: v.stock, quan_ly_kho: v.trackInventory }), (r) => text(val(r, "slug", "duong_dan", "id")));
export async function importFoodsFile(file: File): Promise<{ created: number; message: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post("/foods/import-file/", form, { headers: { "Content-Type": "multipart/form-data" } });
  return data;
}
export const categoriesStore = mappedStore<AdminCategory>("/categories/", (r) => ({ id: text(r.id), name: text(val(r, "name", "ten")), description: text(val(r, "description", "mo_ta")), active: bool(val(r, "active", "con_hoat_dong")) }), (v) => ({ name: v.name, description: v.description, is_active: v.active }), (r) => text(val(r, "slug", "duong_dan", "id")));
export const tagsStore = mappedStore<AdminTag>("/tags/", (r) => ({ id: text(r.id), name: text(val(r, "name", "ten")) }), (v) => ({ name: v.name }));
export const ingredientsStore = mappedStore<AdminIngredient>("/ingredients/", (r) => ({ id: text(r.id), name: text(val(r, "name", "ten")), unit: text(val(r, "unit", "don_vi")), currentStock: num(val(r, "current_stock", "ton_kho_hien_tai")), minimumStock: num(val(r, "min_stock", "ton_kho_toi_thieu")), active: bool(val(r, "is_active", "con_hoat_dong")), recipeCount: num(r.so_mon_dinh_muc), updatedAt: text(r.cap_nhat_luc) }), (v) => ({ ten: v.name, don_vi: v.unit, ton_kho_hien_tai: v.currentStock, ton_kho_toi_thieu: v.minimumStock, con_hoat_dong: v.active }));
export const promotionsStore = mappedStore<AdminPromotion>("/promotions/", (r) => ({ id: text(r.id), code: text(val(r, "code", "ma_giam_gia")), name: text(val(r, "name", "ten")), discountType: stateMap(val(r, "discount_type", "kieu_giam"), { phan_tram: "percent", so_tien_co_dinh: "fixed" }) as AdminPromotion["discountType"], discountValue: num(val(r, "discount_value", "gia_tri_giam")), minOrder: num(val(r, "min_order_value", "don_hang_toi_thieu")), maxDiscount: num(val(r, "max_discount", "giam_toi_da")), startAt: text(val(r, "start_at", "bat_dau_luc")), endAt: text(val(r, "end_at", "ket_thuc_luc")), usageLimit: num(val(r, "usage_limit", "gioi_han_su_dung")), usedCount: num(val(r, "used_count", "so_lan_da_dung")), active: bool(val(r, "is_active", "con_hoat_dong")) }), (v) => ({ code: v.code, name: v.name, discount_type: v.discountType === "percent" ? "phan_tram" : "so_tien_co_dinh", discount_value: v.discountValue, min_order_value: v.minOrder, max_discount: v.maxDiscount || null, start_at: v.startAt, end_at: v.endAt, usage_limit: v.usageLimit || null, is_active: v.active }));
export const postsStore = mappedStore<AdminPost>("/posts/", (r) => ({ id: text(r.id), title: text(val(r, "title", "tieu_de")), category: text(val(r, "category_name", "ten_danh_muc") ?? val(r.danh_muc, "ten", "name") ?? "Ẩm thực"), status: stateMap(val(r, "status", "trang_thai"), { nhap: "draft", da_dang: "published", luu_tru: "archived" }) as AdminPost["status"], content: text(val(r, "content", "noi_dung")), image: text(val(r, "image", "anh_dai_dien")), createdAt: text(val(r, "created_at", "tao_luc")) }), (v) => ({ title: v.title, category: v.category, status: stateMap(v.status, { draft: "nhap", published: "da_dang", archived: "luu_tru" }), content: v.content, thumbnail: v.image } as Raw), (r) => text(val(r, "slug", "duong_dan", "id")));
export const reviewsStore = mappedStore<AdminReview>("/reviews/", (r) => ({ id: text(r.id), food: text(val(r, "food_name", "ten_mon_an") ?? val(r.mon_an, "ten", "name") ?? r.mon_an), customer: text(val(r, "user_name", "ten_nguoi_dung")), rating: num(val(r, "rating", "diem_danh_gia")), comment: text(val(r, "comment", "nhan_xet")), visible: bool(val(r, "is_visible", "visible", "hien_thi")), createdAt: text(val(r, "created_at", "tao_luc")) }), (v) => ({ comment: v.comment, hien_thi: v.visible }));
export const usersStore = mappedStore<AdminUser>("/users/", (r) => {
  const branchId = text(val(r, "chi_nhanh_quan_ly")) || undefined;
  const roleName = text((val(r, "roles", "danh_sach_vai_tro") ?? [])[0]);
  const role: AdminUser["role"] = ({ admin: "admin", quan_tri_vien: "admin", branch_manager: "branch_manager", quan_ly_chi_nhanh: "branch_manager", staff: "staff", employee: "staff", nhan_vien_ban_hang: "staff", nhan_vien: branchId ? "branch_manager" : "staff", customer: "customer", khach_hang: "customer" } as Record<string, AdminUser["role"]>)[roleName] ?? "customer";
  return { id: text(r.id), name: text(val(r, "name", "ho_ten")), email: text(val(r, "email", "thu_dien_tu")), phone: text(val(r, "phone", "so_dien_thoai")), role, active: bool(val(r, "is_active", "con_hoat_dong")), createdAt: text(val(r, "date_joined", "tao_luc")), branchId };
}, (v) => ({ name: v.name, email: v.email, phone: v.phone, role: v.role, active: v.active, password: v.password, branch_id: v.branchId }));
export const branchesStore = mappedStore<AdminBranch>("/branches/", (r) => ({ id: text(r.id), name: text(val(r, "name", "ten")), address: text(val(r, "address", "dia_chi")), phone: text(val(r, "phone", "so_dien_thoai")), lat: num(val(r, "lat", "vi_do")), lng: num(val(r, "lng", "kinh_do")), active: bool(val(r, "is_active", "con_hoat_dong")) }), (v) => ({ name: v.name, address: v.address, phone: v.phone, lat: v.lat, lng: v.lng, is_active: v.active, location: `POINT(${v.lng} ${v.lat})` }));

export const paymentsStore = mappedStore<AdminPayment>("/payments/", (r) => ({ id: text(r.id), code: text(val(r, "transaction_id", "ma_giao_dich")), kind: val(r, "payment_type", "loai_thanh_toan") === "tien_coc" ? "deposit" : "order", ref: text(val(r, "reservation_code", "order_code") ?? val(r, "dat_ban", "don_hang")), method: stateMap(val(r, "method", "phuong_thuc"), { tien_mat: "cod", chuyen_khoan: "bank" }) as AdminPayment["method"], amount: num(val(r, "amount", "so_tien")), status: stateMap(val(r, "status", "trang_thai"), { cho_xu_ly: "pending", thanh_cong: "success", that_bai: "failed", da_hoan_tien: "refunded" }) as AdminPayment["status"], createdAt: text(val(r, "created_at", "tao_luc")) }), (v) => ({ status: v.status }));
export async function createInvoice(input: { targetType: "order" | "deposit"; targetId: string; method: "tien_mat" | "chuyen_khoan"; amount: number }) {
  const { data } = await apiClient.post("/payments/", {
    loai_thanh_toan: input.targetType === "order" ? "don_hang" : "tien_coc",
    don_hang: input.targetType === "order" ? Number(input.targetId) : null,
    dat_ban: input.targetType === "deposit" ? Number(input.targetId) : null,
    phuong_thuc: input.method,
    so_tien: input.amount,
  });
  return data;
}

const policyPath = "/reservations/chinh_sach_coc/";
export async function getDepositPolicy(): Promise<DepositPolicyData> { const { data } = await apiClient.get(policyPath); return normalizePolicy(data); }
const normalizePolicy = (r: Raw): DepositPolicyData => ({ id: text(r.id), depositPercentage: num(val(r, "deposit_percentage", "phan_tram_coc")), holdMinutes: num(val(r, "hold_time_minutes", "thoi_gian_giu_cho_phut")), paymentDeadlineMinutes: num(val(r, "payment_limit_minutes", "han_thanh_toan_phut")), hotline: text(val(r, "hotline", "so_dien_thoai_lien_he")), guideText: text(val(r, "guide_text", "noi_dung_huong_dan")), rules: (val(r, "quy_tac_huy", "rules") ?? []).map((x: Raw) => ({ bucket: stateMap(val(x, "time_milestone", "moc_thoi_gian"), { truoc_24h: ">24h", tu_6_den_24h: "6-24h", trong_6h: "<6h", khach_khong_den: "no_show" }) as CancellationBucket, refundPercentage: num(val(x, "refund_percentage", "phan_tram_hoan_tien")) })) });
export async function saveDepositPolicy(policy: DepositPolicyData) { const { data } = await apiClient.put(policyPath, { deposit_percentage: policy.depositPercentage, hold_time_minutes: policy.holdMinutes, payment_limit_minutes: policy.paymentDeadlineMinutes, hotline: policy.hotline, guide_text: policy.guideText, rules: policy.rules.map((r) => ({ time_milestone: ({ ">24h": "truoc_24h", "6-24h": "tu_6_den_24h", "<6h": "trong_6h", no_show: "khach_khong_den" } as Record<string, string>)[r.bucket], refund_percentage: r.refundPercentage })) }); return normalizePolicy(data); }

export async function setOrderStatus(order: AdminOrder, to: OrderStatus, note?: string) {
  const { data } = await apiClient.patch(`/orders/${order.id}/status/`, { status: statusToBackend[text(to)] ?? to, note });
  const updated = (await ordersStore.list()).find((r) => r.id === order.id)!;
  return Object.assign(updated, { lowStock: mapLowStock(data?.canh_bao_kho) });
}
export async function setReservationStatus(id: string, to: ReservationStatus, version: number, reason?: string) { await apiClient.patch(`/reservations/${id}/trang_thai/`, { status: statusToBackend[text(to)] ?? to, version, reason }); return (await reservationsStore.list()).find((r) => r.id === id)!; }
export async function assignReservationTable(id: string, tableId: string | null) {
  await apiClient.patch(`/reservations/${id}/`, { ban_an: tableId ? Number(tableId) : null });
}
export async function recordRefund(res: AdminReservation, refund: Omit<RefundRecord, "at" | "by">) { await apiClient.post(`/reservations/${res.id}/record-refund/`, { percent: refund.percent, amount: refund.amount, reference: refund.reference, note: refund.note, bucket: refundBucket(res) }); return (await reservationsStore.list()).find((r) => r.id === res.id)!; }
export function refundBucket(res: AdminReservation): CancellationBucket { if (res.status === "no_show") return "no_show"; const slot = new Date(`${res.date}T${res.time}:00`).getTime(); const at = res.cancelledAt ? new Date(res.cancelledAt).getTime() : Date.now(); const hours = (slot - at) / 36e5; return hours > 24 ? ">24h" : hours >= 6 ? "6-24h" : "<6h"; }
export const needsRefund = (r: AdminReservation) => (r.status === "cancelled" || r.status === "no_show") && r.depositStatus === "success" && !r.refund;
export type StockMoveType = "nhap" | "xuat" | "dieu_chinh";
export interface StockMove { id: string; ingredientId: string; ingredientName: string; unit: string; type: StockMoveType; qty: number; before: number; after: number; refType: string; refId?: string; note: string; by: string; at: string }
const mapStockMove = (r: Raw): StockMove => ({ id: text(r.id), ingredientId: text(r.nguyen_lieu), ingredientName: text(r.ten_nguyen_lieu), unit: text(r.don_vi), type: text(r.loai_giao_dich) as StockMoveType, qty: num(r.so_luong), before: num(r.ton_kho_truoc), after: num(r.ton_kho_sau), refType: text(r.loai_tham_chieu), refId: r.id_tham_chieu != null ? text(r.id_tham_chieu) : undefined, note: text(r.ghi_chu), by: text(r.ten_nguoi_tao), at: text(r.tao_luc) });
export async function listStockMoves(ingredientId?: string): Promise<StockMove[]> { return (await list(`/inventory-transactions/${ingredientId ? `?nguyen_lieu=${ingredientId}` : ""}`)).map(mapStockMove); }
export async function createStockMove(ingredientId: string, type: StockMoveType, qty: number, note: string): Promise<StockMove> {
  const { data } = await apiClient.post("/inventory-transactions/", { nguyen_lieu: Number(ingredientId), loai_giao_dich: type, so_luong: qty, ghi_chu: note });
  return mapStockMove(data);
}
export interface IngredientRecipe { id: string; foodId: string; foodName: string; ingredientId: string; ingredientName: string; unit: string; qty: number }
const mapRecipe = (r: Raw): IngredientRecipe => ({ id: text(r.id), foodId: text(r.mon_an), foodName: text(r.ten_mon), ingredientId: text(r.nguyen_lieu), ingredientName: text(r.ten_nguyen_lieu), unit: text(r.don_vi), qty: num(r.so_luong_can) });
export async function listRecipes(ingredientId: string): Promise<IngredientRecipe[]> { return (await list(`/dinh-muc-nguyen-lieu/?nguyen_lieu=${ingredientId}`)).map(mapRecipe); }
export async function createRecipe(ingredientId: string, foodId: string, qty: number) { const { data } = await apiClient.post("/dinh-muc-nguyen-lieu/", { nguyen_lieu: Number(ingredientId), mon_an: Number(foodId), so_luong_can: qty }); return mapRecipe(data); }
export async function updateRecipe(id: string, qty: number) { const { data } = await apiClient.patch(`/dinh-muc-nguyen-lieu/${id}/`, { so_luong_can: qty }); return mapRecipe(data); }
export async function deleteRecipe(id: string) { await apiClient.delete(`/dinh-muc-nguyen-lieu/${id}/`); }

export type Range = 1 | 7 | 30;
export type LiveTableState = "free" | "busy" | "cleaning" | "maintenance" | "held";
export interface DashboardBranch { id: string; name: string; tables: { name: string; seats: number; state: LiveTableState }[]; guests: number; openTotal: number; todayRevenue: number; todayBills: number; rangeRevenue: number; rangeBills: number; rangeGuests: number }
export interface DashboardLeak { count: number; value: number; worstBranch: string | null }
export interface DashboardData {
  revenue: number; orderCount: number; reservationsToday: number; newCustomers: number; series: { label: string; value: number }[]; byStatus: { status: OrderStatus; value: number }[]; topFoods: [string, number][];
  tasks: { pendingOrders: number; pendingDeposits: number; refundQueue: number; lowStock: number; unreadChats: number; pendingConfirm: number };
  now: string; live: DashboardBranch[]; unassigned: { revenue: number; bills: number } | null;
  leaks: Record<"discount" | "cancelled" | "noShow" | "lowReviews", DashboardLeak> | null;
  today: { revenue: number; bills: number; lastWeekSameTime: number; reservations: number; upcomingCount: number };
  upcoming: { id: string; time: string; customer: string; party: number; status: string; branch: string; preorder: boolean }[];
}
export async function getDashboard(range: Range): Promise<DashboardData> { const { data } = await apiClient.get("/analytics/dashboard/", { params: { days: range } }); return { revenue: num(val(data, "revenue", "doanh_thu")), orderCount: num(val(data, "orders", "so_don_hang")), reservationsToday: num(val(data, "reservations_today", "so_dat_ban_hom_nay", "reservations")), newCustomers: num(val(data, "new_customers", "khach_hang_moi")), series: data.revenue_by_day ?? data.series ?? [], byStatus: (data.orders_by_status ?? []).map((x: Raw) => ({ status: stateMap(val(x, "status", "trang_thai"), orderState) as OrderStatus, value: num(val(x, "count", "value")) })), topFoods: data.top_foods ?? [], tasks: { pendingOrders: 0, pendingDeposits: 0, refundQueue: 0, lowStock: 0, unreadChats: 0, pendingConfirm: 0, ...(data.tasks ?? {}) },
    leaks: data.leaks ? Object.fromEntries((["discount", "cancelled", "no_show", "low_reviews"] as const).map((k) => [k.replace(/_(\w)/, (_, c: string) => c.toUpperCase()), { count: num(data.leaks[k]?.count), value: num(data.leaks[k]?.value), worstBranch: data.leaks[k]?.worst_branch ? text(data.leaks[k].worst_branch) : null }])) as DashboardData["leaks"] : null,
    now: text(data.now), unassigned: data.unassigned ? { revenue: num(data.unassigned.revenue), bills: num(data.unassigned.bills) } : null,
    live: (data.live ?? []).map((b: Raw) => ({ id: text(b.id), name: text(b.name), tables: b.tables ?? [], guests: num(b.guests), openTotal: num(b.open_total), todayRevenue: num(b.today_revenue), todayBills: num(b.today_bills), rangeRevenue: num(b.range_revenue), rangeBills: num(b.range_bills), rangeGuests: num(b.range_guests) })),
    today: { revenue: num(data.today?.revenue), bills: num(data.today?.bills), lastWeekSameTime: num(data.today?.last_week_same_time), reservations: num(data.today?.reservations), upcomingCount: num(data.today?.upcoming_count) },
    upcoming: (data.upcoming ?? []).map((r: Raw) => ({ id: text(r.id), time: text(r.time), customer: text(r.customer), party: num(r.party), status: text(r.status), branch: text(r.branch), preorder: bool(r.preorder) })),
  }; }
export interface AiAnalyticsData { overview: { suggested: number; clicks?: number; ctr: number; conversion: number }; positions?: { key: string; label: string; shown: number; clicks: number; ctr: number }[]; top: Record<"recommended" | "viewed" | "ordered" | "favorited", [string, number][]>; recent: { user: string; food: string; score: number; reason: string }[] }
export async function getAiAnalytics(): Promise<AiAnalyticsData> { const { data } = await apiClient.get("/analytics/ai/"); return data; }
export async function changePassword(current: string, next: string) { await apiClient.post("/auth/change_password/", { current_password: current, new_password: next }); }
export async function getRestaurantSettings() { const { data } = await apiClient.get("/analytics/settings/"); return data; }
export async function saveRestaurantSettings(settings: Raw) { const { data } = await apiClient.put("/analytics/settings/", settings); return data; }
const roleId = async (key: string) => { const roles = await list("/roles/"); const wanted = key === "admin" ? ["quan_tri_vien", "admin"] : key === "branch_manager" ? ["quan_ly_chi_nhanh", "nhan_vien"] : ["nhan_vien_ban_hang", "nhan_vien", "staff"]; const role = roles.find((r) => wanted.includes(text(val(r, "name", "ten")))); if (!role) throw new Error("Không tìm thấy vai trò trên máy chủ."); return text(role.id); };
export async function getRolePermissions(key: string) { const id = await roleId(key); const { data } = await apiClient.get(`/roles/${id}/permissions/`); return data.permissions ?? {}; }
export async function saveRolePermissions(key: string, permissions: Raw) { const id = await roleId(key); const { data } = await apiClient.put(`/roles/${id}/permissions/`, { permissions }); return data.permissions ?? {}; }

