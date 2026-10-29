import { apiClient } from "./client";

// ==========================================
// 1. Table & Reservation Management
// ==========================================
export interface AdminTableItem {
  id: number;
  chi_nhanh: number;
  so_ban: string;
  khu_vuc: string;
  suc_chua: number;
  trang_thai: "trong" | "dang_giu" | "da_dat" | "dang_phuc_vu" | "bao_tri";
}

export interface AdminReservationItem {
  id: number;
  ma_dat_ban: string;
  ngay_dat: string;
  gio_bat_dau: string;
  gio_ket_thuc?: string;
  so_luong_khach: number;
  hinh_thuc: string;
  trang_thai: "cho_thanh_toan" | "da_xac_nhan" | "khach_da_den" | "hoan_tat" | "da_huy" | "khach_khong_den";
  yeu_cau_dat_coc: boolean;
  so_tien_coc: number;
  trang_thai_coc: string;
  ten_khach: string;
  sdt_khach: string;
  ghi_chu?: string;
  so_ban?: string;
  ban_an_id?: number;
  danh_sach_mon?: Array<{
    id: number;
    mon_an: { id: number; ten: string; don_gia: number };
    so_luong: number;
    don_gia_luc_dat: number;
  }>;
  tao_luc: string;
}

export async function getAdminTables(): Promise<AdminTableItem[]> {
  const { data } = await apiClient.get("/tables/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createAdminTable(payload: Partial<AdminTableItem>): Promise<AdminTableItem> {
  const { data } = await apiClient.post("/tables/", payload);
  return data;
}

export async function updateAdminTable(id: number, payload: Partial<AdminTableItem>): Promise<AdminTableItem> {
  const { data } = await apiClient.patch(`/tables/${id}/`, payload);
  return data;
}

export async function deleteAdminTable(id: number): Promise<void> {
  await apiClient.delete(`/tables/${id}/`);
}

export async function getAdminReservations(): Promise<AdminReservationItem[]> {
  const { data } = await apiClient.get("/reservations/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function updateReservationStatus(id: number, status: string): Promise<AdminReservationItem> {
  const { data } = await apiClient.patch(`/reservations/${id}/trang_thai/`, { status });
  return data;
}

export async function cancelReservationAdmin(
  id: number,
  reason: string,
  isNoShow = false
): Promise<{ status: string; phan_tram_hoan_tien: number; so_tien_hoan: number; ma_hoan_tien?: string }> {
  const { data } = await apiClient.post(`/reservations/${id}/cancel/`, {
    ly_do: reason,
    is_no_show: isNoShow,
  });
  return data;
}

// ==========================================
// 2. Menu & Inventory Management
// ==========================================
export interface AdminCategoryItem {
  id: number;
  ten: string;
  duong_dan: string;
  mo_ta?: string;
  con_hoat_dong: boolean;
}

export interface AdminFoodItem {
  id: number;
  ten: string;
  duong_dan: string;
  danh_muc: number;
  chi_tiet_danh_muc?: { id: number; ten: string };
  don_gia: number;
  mo_ta_ngan: string;
  mo_ta_chi_tiet: string;
  con_hang: boolean;
  hien_thi: boolean;
  noi_bat: boolean;
  la_mon_chay: boolean;
  do_cay: number;
  diem_danh_gia: number;
  so_luot_danh_gia: number;
  the_mon_an?: string[];
}

export interface AdminIngredientItem {
  id: number;
  ten: string;
  don_vi: string;
  ton_kho_hien_tai: number;
  ton_kho_toi_thieu: number;
  con_hoat_dong: boolean;
}

export interface AdminInventoryTransactionItem {
  id: number;
  nguyen_lieu: number;
  loai_giao_dich: "nhap" | "xuat" | "dieu_chinh";
  so_luong: number;
  ton_kho_truoc: number;
  ton_kho_sau: number;
  ghi_chu: string;
  tao_luc: string;
}

export async function getAdminCategories(): Promise<AdminCategoryItem[]> {
  const { data } = await apiClient.get("/categories/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getAdminFoods(): Promise<AdminFoodItem[]> {
  const { data } = await apiClient.get("/foods/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createAdminFood(payload: any): Promise<AdminFoodItem> {
  const { data } = await apiClient.post("/foods/", payload);
  return data;
}

export async function updateAdminFood(slug: string, payload: any): Promise<AdminFoodItem> {
  const { data } = await apiClient.patch(`/foods/${slug}/`, payload);
  return data;
}

export async function deleteAdminFood(slug: string): Promise<void> {
  await apiClient.delete(`/foods/${slug}/`);
}

export async function getAdminIngredients(): Promise<AdminIngredientItem[]> {
  const { data } = await apiClient.get("/ingredients/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createAdminIngredient(payload: Partial<AdminIngredientItem>): Promise<AdminIngredientItem> {
  const { data } = await apiClient.post("/ingredients/", payload);
  return data;
}

export async function updateAdminIngredient(id: number, payload: Partial<AdminIngredientItem>): Promise<AdminIngredientItem> {
  const { data } = await apiClient.patch(`/ingredients/${id}/`, payload);
  return data;
}

export async function getAdminInventoryTransactions(): Promise<AdminInventoryTransactionItem[]> {
  const { data } = await apiClient.get("/inventory-transactions/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function createInventoryTransaction(payload: {
  nguyen_lieu: number;
  loai_giao_dich: "nhap" | "xuat" | "dieu_chinh";
  so_luong: number;
  ghi_chu?: string;
}): Promise<AdminInventoryTransactionItem> {
  const { data } = await apiClient.post("/inventory-transactions/", payload);
  return data;
}

// ==========================================
// 3. Review Moderation
// ==========================================
export interface AdminReviewItem {
  id: number;
  mon_an: number;
  food_name?: string;
  don_hang: number;
  diem_danh_gia: number;
  nhan_xet: string;
  hien_thi: boolean;
  ten_nguoi_dung: string;
  tao_luc: string;
}

export async function getAdminReviews(): Promise<AdminReviewItem[]> {
  const { data } = await apiClient.get("/reviews/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function toggleReviewVisibility(id: number, isVisible: boolean): Promise<AdminReviewItem> {
  const { data } = await apiClient.patch(`/reviews/${id}/`, { hien_thi: isVisible });
  return data;
}

export async function deleteAdminReview(id: number): Promise<void> {
  await apiClient.delete(`/reviews/${id}/`);
}

// ==========================================
// 4. Staff Realtime Chat
// ==========================================
export interface AdminChatRoomItem {
  id: number;
  khach_hang: number;
  khach_hang_ten?: string;
  nhan_vien?: number;
  trang_thai: "mo" | "dong";
  tin_nhan_cuoi_luc?: string;
  tao_luc: string;
  danh_sach_tin_nhan?: AdminChatMessageItem[];
}

export interface AdminChatMessageItem {
  id: number;
  hoi_thoai: number;
  nguoi_gui: number;
  sender_name?: string;
  noi_dung: string;
  loai_tin_nhan: "van_ban" | "hinh_anh" | "he_thong";
  da_doc: boolean;
  tao_luc: string;
  is_staff?: boolean;
}

export async function getAdminChatRooms(): Promise<AdminChatRoomItem[]> {
  const { data } = await apiClient.get("/chat/rooms/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function getAdminChatMessages(roomId: number): Promise<AdminChatMessageItem[]> {
  const { data } = await apiClient.get(`/chat/rooms/${roomId}/messages/`);
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function sendAdminChatMessage(roomId: number, content: string): Promise<AdminChatMessageItem> {
  const { data } = await apiClient.post(`/chat/rooms/${roomId}/messages/`, {
    noi_dung: content,
    loai_tin_nhan: "van_ban",
  });
  return data;
}

export async function updateChatRoomStatus(roomId: number, status: "mo" | "dong"): Promise<AdminChatRoomItem> {
  const { data } = await apiClient.patch(`/chat/rooms/${roomId}/`, { trang_thai: status });
  return data;
}

export async function updateAdminOrderStatus(
  orderId: number | string,
  status: string,
  note = ""
): Promise<any> {
  const { data } = await apiClient.patch(`/orders/${orderId}/trang_thai/`, { status, note });
  return data;
}

