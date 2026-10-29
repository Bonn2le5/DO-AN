# 5-Component Handoff Report: Milestone 5 Admin & Staff Portals

**Agent**: `m5_explorer_portals` (teamwork_preview_explorer_m5_1)  
**Date**: 2026-10-14T17:05:00Z  
**Target Milestone**: Milestone 5 (Admin & Staff Portals UI/UX & API Integration)  
**Authoritative References**: `ORIGINAL_REQUEST.md` (R5), `PROJECT.md` (Features 26, 27, 28, 29, 30)

---

## 1. Observation

### 1.1 Existing Routing and Layout Status in `moc-frontend`
- **`moc-frontend/src/App.tsx` (lines 36–43)**:
  ```tsx
  {/* Admin Routes */}
  <Route path="/admin" element={<AdminGuard />}>
    <Route element={<AdminLayout />}>
      <Route index element={<AdminDashboardPage />} />
      <Route path="orders" element={<AdminOrdersPage />} />
      <Route path="reservations" element={<div className="p-4 font-bold text-gray-500">Đang phát triển: Quản lý đặt bàn</div>} />
      <Route path="menu" element={<div className="p-4 font-bold text-gray-500">Đang phát triển: Quản lý thực đơn</div>} />
    </Route>
  </Route>
  ```
  - Routes `reservations` and `menu` are currently stubbed with placeholder text `<div>` elements.
  - Routes for Review Moderation (`reviews`) and Staff Chat (`chat`) do not exist.
- **`moc-frontend/src/components/layout/AdminLayout.tsx` (lines 8–13)**:
  ```tsx
  const navItems = [
    { name: "Tổng quan", path: "/admin", icon: "📊" },
    { name: "Đơn hàng", path: "/admin/orders", icon: "🛍️" },
    { name: "Đặt bàn", path: "/admin/reservations", icon: "📅" },
    { name: "Thực đơn", path: "/admin/menu", icon: "🍲" },
  ];
  ```
  - Nav items list lacks "Đánh giá" (`/admin/reviews`) and "Hỗ trợ khách" (`/admin/chat`).
- **`moc-frontend/src/components/layout/AdminGuard.tsx` (lines 12–16)**:
  - Properly verifies roles `admin`, `staff`, `nhan_vien`, `quan_tri_vien`, or boolean flags `isStaff`, `laNhanVien`.
- **Existing Page Tree (`moc-frontend/src/pages/admin/`)**:
  - Only `AdminDashboardPage.tsx` and `AdminOrdersPage.tsx` exist. `AdminOrdersPage.tsx` contains note `// Tạm thời gọi API lấy order của user để có giao diện // Sau này sẽ viết hàm api getAdminOrders riêng`.
  - Directory `moc-frontend/src/pages/staff/` does not exist. All staff operations are hosted under `/admin` protected by `AdminGuard`.

---

### 1.2 Backend Endpoint and Model Capabilities

#### Area 1: Table & Reservation Management
- **Endpoints (`moc-backend/api/urls.py` lines 53–57)**:
  - `GET/POST /api/tables/` (`BanAnViewSet`): Staff can create, edit, delete, list tables. Query params supported: `chi_nhanh`, `guest_count`, `reservation_date`, `start_time`.
  - `GET /api/reservations/` (`DatBanViewSet`): Staff returns all bookings across the restaurant; non-staff gets user's own bookings.
  - `PATCH /api/reservations/{id}/trang_thai/` (`DatBanViewSet` lines 157–164): Accepts `{ status: "<new_status>" }`.
  - `POST /api/reservations/{id}/cancel/` or `/api/reservations/{id}/huy_dat_ban/` (lines 127–156): Processes cancellation, triggers `RefundService.process_cancellation_and_refund`, supports `ly_do` and `is_no_show`.
- **Data Models**:
  - `BanAn`: `id`, `chi_nhanh`, `so_ban`, `khu_vuc`, `suc_chua`, `trang_thai` (`trong`, `dang_giu`, `da_dat`, `dang_phuc_vu`, `bao_tri`).
  - `DatBan`: `id`, `ma_dat_ban`, `ngay_dat`, `gio_bat_dau`, `gio_ket_thuc`, `so_luong_khach`, `hinh_thuc`, `trang_thai` (`cho_thanh_toan`, `da_xac_nhan`, `khach_da_den`, `hoan_tat`, `da_huy`, `khach_khong_den`), `yeu_cau_dat_coc`, `so_tien_coc`, `trang_thai_coc`, `ten_khach`, `sdt_khach`, `ghi_chu`, `ban_an`.

#### Area 2: Menu & Inventory Management
- **Endpoints (`moc-backend/api/urls.py` lines 37–48)**:
  - `GET/POST /api/foods/`, `PATCH/DELETE /api/foods/<slug>/` (`MonAnViewSet`): Notice `lookup_field = "duong_dan"`. Filters: `danh_muc`, `tim_kiem`, `la_mon_chay`, `con_hang`, `gia_toi_da`, `co_cay`, `sap_xep`.
  - `GET/POST /api/categories/` (`DanhMucViewSet`): Categories list.
  - `GET/POST/PATCH/DELETE /api/ingredients/` (`NguyenLieuViewSet`): Ingredients with `ton_kho_hien_tai`, `ton_kho_toi_thieu`, `don_vi`.
  - `GET/POST /api/inventory-transactions/` (`LichSuKhoViewSet`): Logs in/out/adjustments (`nhap`, `xuat`, `dieu_chinh`, `so_luong`, `ghi_chu`).
- **Data Models**:
  - `MonAn`: `ten`, `duong_dan`, `don_gia`, `danh_muc`, `mo_ta_ngan`, `mo_ta_chi_tiet`, `con_hang`, `hien_thi`, `noi_bat`, `la_mon_chay`, `do_cay`, `ton_kho_cache`.
  - `NguyenLieu`: `ten`, `don_vi`, `ton_kho_hien_tai`, `ton_kho_toi_thieu`, `con_hoat_dong`.
  - `LichSuXuatNhapKho`: `nguyen_lieu`, `loai_giao_dich`, `so_luong`, `ton_kho_truoc`, `ton_kho_sau`, `ghi_chu`, `tao_boi`.

#### Area 3: Review Moderation Portal
- **Endpoints (`moc-backend/api/urls.py` lines 79–82, `reviews/views.py`)**:
  - `GET /api/reviews/` (`DanhGiaViewSet`): Lists reviews.
  - `PATCH /api/reviews/{id}/` (`DanhGiaViewSet` lines 45–51): Staff can update `hien_thi` (true/false) to hide/show reviews.
  - `DELETE /api/reviews/{id}/`: Authenticated delete.
  - **Identified Caveat**: `reviews/views.py` line 19 hardcodes `q = DanhGia.objects.filter(hien_thi=True)...` which conceals hidden reviews from staff listing unless updated to allow staff access.

#### Area 4: Staff Realtime Chat Portal
- **Endpoints (`moc-backend/api/urls.py` lines 89–93, `chat/views.py`)**:
  - `GET /api/chat/rooms/` (`HoiThoaiViewSet`): Returns all conversation rooms for staff (`user.is_staff or la_nhan_vien_nha_hang`).
  - `GET /api/chat/rooms/{id}/messages/`: Returns message list for a room.
  - `POST /api/chat/rooms/{id}/messages/` or `POST /api/chat/rooms/{id}/gui_tin_nhan/`: REST message sending.
  - `PATCH /api/chat/rooms/{id}/`: Update room status (`mo` or `dong`).
- **WebSocket Gateway (`chat/routing.py`, `chat/consumers.py`)**:
  - Route: `ws://<host>/ws/chat/<conversation_id>/?token=<access_token>`.
  - Middleware: `config/middleware.py` `JWTAuthMiddleware` extracts JWT from `?token=...`.
  - Protocol Actions:
    - Send: `{ "action": "send_message", "message": "...", "content": "..." }`
    - Typing: `{ "action": "typing", "is_typing": true }`
    - Read receipt: `{ "action": "mark_read", "last_read_message_id": 123 }`
  - Broadcast Events Received:
    - `connection_established`: User & room info.
    - `chat_message`: `{ "id": 1, "sender_name": "...", "content": "...", "is_staff": false, "created_at": "..." }`
    - `chat_typing`: `{ "is_typing": true, "sender_name": "..." }`

---

## 2. Logic Chain

1. **Routing Logic**:
   - `App.tsx` has routes `/admin/reservations` and `/admin/menu` rendering inline development stubs.
   - We must replace these stubs with fully realized page components: `AdminReservationsPage` and `AdminMenuPage`.
   - We must introduce `/admin/reviews` for review moderation and `/admin/chat` for live customer support.
   - We must append corresponding navigation items into `AdminLayout.tsx` so staff can toggle between all 6 portals.

2. **Data & State Management Logic**:
   - The frontend codebase standardizes on React local state + hooks (`useState`, `useEffect`) and Axios API client (`apiClient`) configured with interceptors attaching `localStorage.getItem("access_token")`.
   - Zustand stores are reserved for global auth (`useAuthStore`) and cart (`useCartStore`).
   - Therefore, the 4 admin portal pages should leverage responsive local UI state, structured modal controllers, and dedicated typed API service modules.

3. **API Payload Alignment**:
   - *Reservations*: `DatBanViewSet` expects `PATCH /api/reservations/{id}/trang_thai/` with `{ status: string }`. Canceling requires `POST /api/reservations/{id}/cancel/` with `{ ly_do: string, is_no_show: boolean }`.
   - *Tables*: `BanAnViewSet` accepts `so_ban`, `khu_vuc`, `suc_chua`, `trang_thai`, `chi_nhanh`.
   - *Foods*: `MonAnViewSet` uses `lookup_field = "duong_dan"` (slug), so edits/deletes must pass `slug` in the URL path.
   - *Inventory*: `LichSuKhoViewSet` expects `POST /api/inventory-transactions/` with `{ nguyen_lieu: number, loai_giao_dich: "nhap"|"xuat"|"dieu_chinh", so_luong: number, ghi_chu: string }`.
   - *Reviews*: Moderation uses `PATCH /api/reviews/{id}/` with `{ hien_thi: boolean }`.
   - *Chat*: Staff queries `GET /api/chat/rooms/`, connects to `ws://${host}/ws/chat/${conversationId}/?token=${token}`, and receives persistent events stored in PostgreSQL before channel layer broadcast.

---

## 3. Caveats

1. **Review ViewSet Staff Filtering**:
   - In `moc-backend/reviews/views.py:19`:
     ```python
     def get_queryset(self):
         q = DanhGia.objects.filter(hien_thi=True)...
     ```
     Because `hien_thi=True` is unconditional, if a staff hides a review, `GET /api/reviews/` currently excludes it from subsequent GET responses.
     *Recommendation*: Backend implementer should adjust line 19:
     ```python
     def get_queryset(self):
         q = DanhGia.objects.select_related("nguoi_dung", "mon_an", "don_hang", "chi_tiet_don_hang")
         user = self.request.user
         is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
         if not is_staff:
             q = q.filter(hien_thi=True)
     ```
     The frontend blueprint already includes full support for viewing both visible and hidden reviews.

2. **WebSocket Host Resolution in Production vs Development**:
   - In development, Vite runs on port 5173 while Django ASGI runs on port 8000. In production or Docker reverse proxy, both run on the same host/port. The WebSocket connection helper inspects `window.location` and uses `localhost:8000` when on Vite development server.

3. **No Legacy Staff Separate Guard**:
   - System design places all staff tools under `/admin/*` guarded by `AdminGuard.tsx`, which validates both `isStaff` and restaurant staff roles. There is no requirement for a redundant `/staff/*` route tree.

---

## 4. Conclusion & Drop-In Blueprints

We provide the complete drop-in blueprints for:
1. `moc-frontend/src/api/admin.api.ts` (API methods for reservations, menu, inventory, reviews, and chat)
2. `moc-frontend/src/pages/admin/AdminReservationsPage.tsx`
3. `moc-frontend/src/pages/admin/AdminMenuPage.tsx`
4. `moc-frontend/src/pages/admin/AdminReviewsPage.tsx`
5. `moc-frontend/src/pages/admin/AdminChatPage.tsx`
6. Updates to `moc-frontend/src/components/layout/AdminLayout.tsx`
7. Updates to `moc-frontend/src/App.tsx`

---

### BLUEPRINT 1: `moc-frontend/src/api/admin.api.ts`

```typescript
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
```

---

### BLUEPRINT 2: `moc-frontend/src/pages/admin/AdminReservationsPage.tsx`
Drop-in replacement for the current `reservations` placeholder route. Combines Table Layout (Sơ đồ bàn ăn) and Reservation Management (Phiếu đặt bàn).

```tsx
import { useEffect, useState, useMemo } from "react";
import {
  Calendar,
  Users,
  Search,
  CheckCircle,
  XCircle,
  Clock,
  Plus,
  RefreshCw,
  Eye,
  AlertTriangle,
} from "lucide-react";
import {
  getAdminTables,
  getAdminReservations,
  updateReservationStatus,
  cancelReservationAdmin,
  createAdminTable,
  updateAdminTable,
  deleteAdminTable,
  type AdminTableItem,
  type AdminReservationItem,
} from "@/api/admin.api";

export default function AdminReservationsPage() {
  const [activeTab, setActiveTab] = useState<"reservations" | "tables">("reservations");
  const [tables, setTables] = useState<AdminTableItem[]>([]);
  const [reservations, setReservations] = useState<AdminReservationItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState("");

  // Modals
  const [selectedRes, setSelectedRes] = useState<AdminReservationItem | null>(null);
  const [cancelModalRes, setCancelModalRes] = useState<AdminReservationItem | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [isNoShow, setIsNoShow] = useState(false);
  const [tableModalOpen, setTableModalOpen] = useState(false);
  const [editingTable, setEditingTable] = useState<Partial<AdminTableItem> | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tList, rList] = await Promise.all([getAdminTables(), getAdminReservations()]);
      setTables(tList);
      setReservations(rList);
    } catch (err) {
      console.error("Failed to load tables/reservations:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleStatusChange = async (resId: number, newStatus: string) => {
    try {
      await updateReservationStatus(resId, newStatus);
      fetchData();
    } catch (err) {
      alert("Không thể cập nhật trạng thái đặt bàn.");
    }
  };

  const handleConfirmCancel = async () => {
    if (!cancelModalRes) return;
    try {
      const res = await cancelReservationAdmin(cancelModalRes.id, cancelReason || "Nhân viên hủy", isNoShow);
      alert(
        `Đã hủy đặt bàn thành công! Hoàn cọc: ${res.phan_tram_hoan_tien}% (${res.so_tien_hoan.toLocaleString()}đ)`
      );
      setCancelModalRes(null);
      setCancelReason("");
      setIsNoShow(false);
      fetchData();
    } catch (err) {
      alert("Lỗi khi xử lý hủy đặt bàn.");
    }
  };

  const handleSaveTable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTable) return;
    try {
      if (editingTable.id) {
        await updateAdminTable(editingTable.id, editingTable);
      } else {
        await createAdminTable({
          chi_nhanh: 1,
          so_ban: editingTable.so_ban || "B01",
          khu_vuc: editingTable.khu_vuc || "Tầng 1",
          suc_chua: Number(editingTable.suc_chua || 4),
          trang_thai: editingTable.trang_thai || "trong",
        });
      }
      setTableModalOpen(false);
      setEditingTable(null);
      fetchData();
    } catch (err) {
      alert("Lỗi khi lưu thông tin bàn.");
    }
  };

  const handleDeleteTable = async (id: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa bàn này không?")) return;
    try {
      await deleteAdminTable(id);
      fetchData();
    } catch (err) {
      alert("Không thể xóa bàn đang có dữ liệu liên quan.");
    }
  };

  const filteredReservations = useMemo(() => {
    return reservations.filter((r) => {
      const matchStatus = statusFilter === "all" || r.trang_thai === statusFilter;
      const matchDate = !dateFilter || r.ngay_dat === dateFilter;
      const matchSearch =
        !searchQuery ||
        r.ma_dat_ban.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.ten_khach.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.sdt_khach.includes(searchQuery);
      return matchStatus && matchDate && matchSearch;
    });
  }, [reservations, statusFilter, dateFilter, searchQuery]);

  const tablesByZone = useMemo(() => {
    const map: Record<string, AdminTableItem[]> = {};
    tables.forEach((t) => {
      const zone = t.khu_vuc || "Chung";
      if (!map[zone]) map[zone] = [];
      map[zone].push(t);
    });
    return map;
  }, [tables]);

  const getResBadge = (status: string) => {
    const map: Record<string, { label: string; cls: string }> = {
      cho_thanh_toan: { label: "Chờ thanh toán", cls: "bg-amber-100 text-amber-800" },
      da_xac_nhan: { label: "Đã xác nhận", cls: "bg-blue-100 text-blue-800" },
      khach_da_den: { label: "Khách đã đến", cls: "bg-purple-100 text-purple-800" },
      hoan_tat: { label: "Hoàn tất", cls: "bg-green-100 text-green-800" },
      da_huy: { label: "Đã hủy", cls: "bg-red-100 text-red-800" },
      khach_khong_den: { label: "Khách không đến", cls: "bg-gray-100 text-gray-800" },
    };
    const s = map[status] || { label: status, cls: "bg-gray-100 text-gray-700" };
    return <span className={`px-2.5 py-1 text-xs rounded-full font-medium ${s.cls}`}>{s.label}</span>;
  };

  const getTableColor = (status: string) => {
    switch (status) {
      case "trong":
        return "bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100";
      case "dang_giu":
        return "bg-amber-50 border-amber-300 text-amber-800 hover:bg-amber-100";
      case "da_dat":
        return "bg-blue-50 border-blue-300 text-blue-800 hover:bg-blue-100";
      case "dang_phuc_vu":
        return "bg-indigo-50 border-indigo-300 text-indigo-800 hover:bg-indigo-100";
      case "bao_tri":
        return "bg-gray-100 border-gray-300 text-gray-600 hover:bg-gray-200";
      default:
        return "bg-gray-50 border-gray-200 text-gray-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý Bàn ăn & Đặt bàn</h1>
          <p className="text-sm text-gray-500">Giám sát sơ đồ bàn trực tiếp và xử lý danh sách phiếu đặt bàn.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            className="p-2 border rounded-lg hover:bg-gray-100 text-gray-600 transition-colors"
            title="Làm mới"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="flex bg-gray-200 p-1 rounded-lg text-sm">
            <button
              onClick={() => setActiveTab("reservations")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "reservations" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Danh sách đặt bàn ({reservations.length})
            </button>
            <button
              onClick={() => setActiveTab("tables")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "tables" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Sơ đồ bàn ăn ({tables.length})
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: RESERVATIONS */}
      {activeTab === "reservations" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          {/* Filters Bar */}
          <div className="p-4 border-b flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm mã đặt bàn, tên khách, số điện thoại..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <div className="flex gap-2">
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              >
                <option value="all">Tất cả trạng thái</option>
                <option value="cho_thanh_toan">Chờ thanh toán</option>
                <option value="da_xac_nhan">Đã xác nhận</option>
                <option value="khach_da_den">Khách đã đến</option>
                <option value="hoan_tat">Hoàn tất</option>
                <option value="da_huy">Đã hủy</option>
                <option value="khach_khong_den">Khách không đến</option>
              </select>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="p-12 text-center text-gray-500">Đang tải dữ liệu...</div>
          ) : filteredReservations.length === 0 ? (
            <div className="p-12 text-center text-gray-400">Không tìm thấy phiếu đặt bàn nào phù hợp.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                  <tr>
                    <th className="p-3.5">Mã phiếu</th>
                    <th className="p-3.5">Khách hàng</th>
                    <th className="p-3.5">Bàn & Khách</th>
                    <th className="p-3.5">Thời gian đến</th>
                    <th className="p-3.5">Tiền cọc</th>
                    <th className="p-3.5">Trạng thái</th>
                    <th className="p-3.5 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredReservations.map((r) => (
                    <tr key={r.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5 font-semibold text-gray-900">{r.ma_dat_ban}</td>
                      <td className="p-3.5">
                        <div className="font-medium text-gray-900">{r.ten_khach}</div>
                        <div className="text-xs text-gray-500">{r.sdt_khach}</div>
                      </td>
                      <td className="p-3.5">
                        <span className="font-medium">{r.so_ban ? `Bàn ${r.so_ban}` : "Chưa gán"}</span>
                        <span className="text-xs text-gray-500 block">({r.so_luong_khach} người)</span>
                      </td>
                      <td className="p-3.5">
                        <div className="font-medium">{r.gio_bat_dau.slice(0, 5)}</div>
                        <div className="text-xs text-gray-500">{r.ngay_dat}</div>
                      </td>
                      <td className="p-3.5">
                        <div className="font-medium">{Number(r.so_tien_coc).toLocaleString()}đ</div>
                        <div className="text-[11px] text-gray-400">{r.trang_thai_coc}</div>
                      </td>
                      <td className="p-3.5">{getResBadge(r.trang_thai)}</td>
                      <td className="p-3.5 text-right space-x-1">
                        <button
                          onClick={() => setSelectedRes(r)}
                          className="px-2 py-1 text-xs border rounded text-gray-600 hover:bg-gray-100"
                          title="Xem chi tiết"
                        >
                          <Eye className="w-3.5 h-3.5 inline" />
                        </button>
                        {r.trang_thai === "da_xac_nhan" && (
                          <button
                            onClick={() => handleStatusChange(r.id, "khach_da_den")}
                            className="px-2 py-1 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded hover:bg-purple-100 font-medium"
                          >
                            Đã đến
                          </button>
                        )}
                        {r.trang_thai === "khach_da_den" && (
                          <button
                            onClick={() => handleStatusChange(r.id, "hoan_tat")}
                            className="px-2 py-1 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded hover:bg-emerald-100 font-medium"
                          >
                            Hoàn tất
                          </button>
                        )}
                        {["cho_thanh_toan", "da_xac_nhan"].includes(r.trang_thai) && (
                          <button
                            onClick={() => setCancelModalRes(r)}
                            className="px-2 py-1 text-xs bg-red-50 text-red-600 border border-red-200 rounded hover:bg-red-100 font-medium"
                          >
                            Hủy / Hoàn cọc
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: TABLE FLOOR MAP */}
      {activeTab === "tables" && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-4 border rounded-xl shadow-sm">
            <div className="flex flex-wrap gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-500" /> Trống</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-500" /> Đang giữ 10p</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-blue-500" /> Đã đặt</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-indigo-500" /> Đang phục vụ</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-gray-400" /> Bảo trì</span>
            </div>
            <button
              onClick={() => {
                setEditingTable({ chi_nhanh: 1, so_ban: "", khu_vuc: "Tầng 1", suc_chua: 4, trang_thai: "trong" });
                setTableModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-white text-sm rounded-lg hover:bg-primary/90"
            >
              <Plus className="w-4 h-4" /> Thêm bàn
            </button>
          </div>

          {/* Zones */}
          {Object.entries(tablesByZone).map(([zone, zoneTables]) => (
            <div key={zone} className="bg-white border rounded-xl p-5 shadow-sm space-y-4">
              <h3 className="font-bold text-gray-800 text-lg flex items-center gap-2 border-b pb-2">
                <span>📍 {zone}</span>
                <span className="text-xs font-normal text-gray-500">({zoneTables.length} bàn)</span>
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {zoneTables.map((t) => (
                  <div
                    key={t.id}
                    className={`border-2 rounded-xl p-4 flex flex-col justify-between transition-all shadow-sm ${getTableColor(
                      t.trang_thai
                    )}`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="text-lg font-bold">Bàn {t.so_ban}</span>
                      <span className="text-xs font-medium flex items-center gap-0.5">
                        <Users className="w-3.5 h-3.5" /> {t.suc_chua}
                      </span>
                    </div>

                    <div className="mt-4 pt-2 border-t border-black/10 flex justify-between items-center text-xs">
                      <select
                        value={t.trang_thai}
                        onChange={async (e) => {
                          const newStatus = e.target.value as AdminTableItem["trang_thai"];
                          await updateAdminTable(t.id, { trang_thai: newStatus });
                          fetchData();
                        }}
                        className="bg-transparent font-medium border-0 focus:ring-0 p-0 text-xs cursor-pointer"
                      >
                        <option value="trong">Trống</option>
                        <option value="dang_giu">Đang giữ</option>
                        <option value="da_dat">Đã đặt</option>
                        <option value="dang_phuc_vu">Đang dùng</option>
                        <option value="bao_tri">Bảo trì</option>
                      </select>
                      <button
                        onClick={() => handleDeleteTable(t.id)}
                        className="text-red-500 hover:text-red-700 ml-2"
                        title="Xóa bàn"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* DETAIL MODAL */}
      {selectedRes && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b pb-3">
              <h3 className="font-bold text-lg">Chi tiết phiếu đặt: {selectedRes.ma_dat_ban}</h3>
              <button onClick={() => setSelectedRes(null)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="space-y-2 text-sm text-gray-700">
              <p><strong>Khách hàng:</strong> {selectedRes.ten_khach} - {selectedRes.sdt_khach}</p>
              <p><strong>Bàn & Số khách:</strong> Bàn {selectedRes.so_ban || "Chưa gán"} ({selectedRes.so_luong_khach} khách)</p>
              <p><strong>Thời gian:</strong> {selectedRes.gio_bat_dau} ngày {selectedRes.ngay_dat}</p>
              <p><strong>Hình thức:</strong> {selectedRes.hinh_thuc}</p>
              <p><strong>Tiền đặt cọc:</strong> {Number(selectedRes.so_tien_coc).toLocaleString()}đ ({selectedRes.trang_thai_coc})</p>
              {selectedRes.ghi_chu && <p><strong>Ghi chú:</strong> {selectedRes.ghi_chu}</p>}

              {selectedRes.danh_sach_mon && selectedRes.danh_sach_mon.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <h4 className="font-bold mb-2">Món ăn đặt trước:</h4>
                  <ul className="space-y-1">
                    {selectedRes.danh_sach_mon.map((m) => (
                      <li key={m.id} className="flex justify-between text-xs">
                        <span>{m.mon_an?.ten} x{m.so_luong}</span>
                        <span>{Number(m.don_gia_luc_dat * m.so_luong).toLocaleString()}đ</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <div className="pt-3 border-t flex justify-end">
              <button
                onClick={() => setSelectedRes(null)}
                className="px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-700 hover:bg-gray-200"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CANCEL & REFUND MODAL */}
      {cancelModalRes && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-2 text-red-600 font-bold text-lg border-b pb-3">
              <AlertTriangle className="w-5 h-5" /> Hủy đặt bàn & Tính hoàn cọc
            </div>
            <p className="text-sm text-gray-600">
              Bạn đang thực hiện hủy phiếu <strong>{cancelModalRes.ma_dat_ban}</strong> của khách <strong>{cancelModalRes.ten_khach}</strong>. Hệ thống sẽ tự động đối chiếu thời gian và sinh phiếu hoàn tiền theo quy định.
            </p>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-gray-700 block mb-1">Lý do hủy:</label>
                <input
                  type="text"
                  placeholder="Khách báo bận, sự cố..."
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isNoShow}
                  onChange={(e) => setIsNoShow(e.target.checked)}
                  className="rounded text-primary focus:ring-primary"
                />
                Khách không đến (No-show - Phạt 100% cọc)
              </label>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                onClick={() => setCancelModalRes(null)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy bỏ
              </button>
              <button
                onClick={handleConfirmCancel}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 font-medium"
              >
                Xác nhận Hủy
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TABLE MODAL */}
      {tableModalOpen && editingTable && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSaveTable} className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <h3 className="font-bold text-lg border-b pb-3">
              {editingTable.id ? "Chỉnh sửa bàn" : "Thêm bàn ăn mới"}
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold mb-1">Số bàn / Tên bàn:</label>
                <input
                  type="text"
                  required
                  placeholder="B01, VIP1..."
                  value={editingTable.so_ban || ""}
                  onChange={(e) => setEditingTable({ ...editingTable, so_ban: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Khu vực:</label>
                <input
                  type="text"
                  required
                  placeholder="Tầng 1, Tầng 2, Ngoài trời..."
                  value={editingTable.khu_vuc || ""}
                  onChange={(e) => setEditingTable({ ...editingTable, khu_vuc: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Sức chứa (số ghế):</label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  required
                  value={editingTable.suc_chua || 4}
                  onChange={(e) => setEditingTable({ ...editingTable, suc_chua: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setTableModalOpen(false)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90"
              >
                Lưu
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
```

---

### BLUEPRINT 3: `moc-frontend/src/pages/admin/AdminMenuPage.tsx`
Drop-in replacement for the current `menu` placeholder route. Combines Menu Catalog Management (Món ăn) and Inventory & Material Tracking (Kho nguyên liệu).

```tsx
import { useEffect, useState, useMemo } from "react";
import {
  UtensilsCrossed,
  Package,
  History,
  Plus,
  Search,
  Edit,
  Trash2,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import {
  getAdminFoods,
  getAdminCategories,
  createAdminFood,
  updateAdminFood,
  deleteAdminFood,
  getAdminIngredients,
  createAdminIngredient,
  updateAdminIngredient,
  getAdminInventoryTransactions,
  createInventoryTransaction,
  type AdminFoodItem,
  type AdminCategoryItem,
  type AdminIngredientItem,
  type AdminInventoryTransactionItem,
} from "@/api/admin.api";

export default function AdminMenuPage() {
  const [activeTab, setActiveTab] = useState<"foods" | "ingredients" | "transactions">("foods");
  const [foods, setFoods] = useState<AdminFoodItem[]>([]);
  const [categories, setCategories] = useState<AdminCategoryItem[]>([]);
  const [ingredients, setIngredients] = useState<AdminIngredientItem[]>([]);
  const [transactions, setTransactions] = useState<AdminInventoryTransactionItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [catFilter, setCatFilter] = useState("all");

  // Food Modal
  const [foodModalOpen, setFoodModalOpen] = useState(false);
  const [editingFood, setEditingFood] = useState<Partial<AdminFoodItem> | null>(null);

  // Inventory Transaction Modal
  const [txModalOpen, setTxModalOpen] = useState(false);
  const [txData, setTxData] = useState<{
    nguyen_lieu: number;
    loai_giao_dich: "nhap" | "xuat" | "dieu_chinh";
    so_luong: number;
    ghi_chu: string;
  }>({
    nguyen_lieu: 0,
    loai_giao_dich: "nhap",
    so_luong: 1,
    ghi_chu: "",
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [fList, cList, iList, tList] = await Promise.all([
        getAdminFoods(),
        getAdminCategories(),
        getAdminIngredients(),
        getAdminInventoryTransactions(),
      ]);
      setFoods(fList);
      setCategories(cList);
      setIngredients(iList);
      setTransactions(tList);
      if (iList.length > 0 && !txData.nguyen_lieu) {
        setTxData((prev) => ({ ...prev, nguyen_lieu: iList[0].id }));
      }
    } catch (err) {
      console.error("Failed to load menu data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleFoodStatus = async (food: AdminFoodItem, field: "con_hang" | "hien_thi") => {
    try {
      await updateAdminFood(food.duong_dan, { [field]: !food[field] });
      fetchData();
    } catch (err) {
      alert("Không thể cập nhật trạng thái món ăn.");
    }
  };

  const handleSaveFood = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFood) return;
    try {
      if (editingFood.duong_dan) {
        await updateAdminFood(editingFood.duong_dan, editingFood);
      } else {
        await createAdminFood({
          ...editingFood,
          danh_muc: editingFood.danh_muc || categories[0]?.id || 1,
          don_gia: Number(editingFood.don_gia || 50000),
          con_hang: editingFood.con_hang ?? true,
          hien_thi: editingFood.hien_thi ?? true,
        });
      }
      setFoodModalOpen(false);
      setEditingFood(null);
      fetchData();
    } catch (err) {
      alert("Lỗi khi lưu món ăn.");
    }
  };

  const handleDeleteFood = async (slug: string) => {
    if (!confirm("Bạn có chắc chắn muốn xóa món này?")) return;
    try {
      await deleteAdminFood(slug);
      fetchData();
    } catch (err) {
      alert("Không thể xóa món ăn.");
    }
  };

  const handleSaveTransaction = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createInventoryTransaction(txData);
      setTxModalOpen(false);
      fetchData();
      alert("Đã cập nhật kho thành công!");
    } catch (err) {
      alert("Lỗi khi ghi nhận xuất nhập kho.");
    }
  };

  const filteredFoods = useMemo(() => {
    return foods.filter((f) => {
      const matchCat = catFilter === "all" || String(f.danh_muc) === catFilter;
      const matchSearch =
        !searchQuery ||
        f.ten.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.mo_ta_ngan?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [foods, catFilter, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý Thực đơn & Kho nguyên liệu</h1>
          <p className="text-sm text-gray-500">Quản lý danh sách món ăn, định mức và luồng xuất nhập nguyên liệu.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchData} className="p-2 border rounded-lg hover:bg-gray-100" title="Làm mới">
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="flex bg-gray-200 p-1 rounded-lg text-sm">
            <button
              onClick={() => setActiveTab("foods")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "foods" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Món ăn ({foods.length})
            </button>
            <button
              onClick={() => setActiveTab("ingredients")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "ingredients" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Kho nguyên liệu ({ingredients.length})
            </button>
            <button
              onClick={() => setActiveTab("transactions")}
              className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                activeTab === "transactions" ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Lịch sử kho ({transactions.length})
            </button>
          </div>
        </div>
      </div>

      {/* TAB 1: FOOD CATALOG */}
      {activeTab === "foods" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b flex flex-col md:flex-row gap-3 justify-between">
            <div className="flex flex-1 gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <input
                  type="text"
                  placeholder="Tìm món theo tên hoặc mô tả..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <select
                value={catFilter}
                onChange={(e) => setCatFilter(e.target.value)}
                className="px-3 py-2 border rounded-lg text-sm bg-white"
              >
                <option value="all">Tất cả danh mục</option>
                {categories.map((c) => (
                  <option key={c.id} value={String(c.id)}>{c.ten}</option>
                ))}
              </select>
            </div>
            <button
              onClick={() => {
                setEditingFood({
                  ten: "",
                  don_gia: 60000,
                  danh_muc: categories[0]?.id || 1,
                  con_hang: true,
                  hien_thi: true,
                  la_mon_chay: false,
                  do_cay: 0,
                  mo_ta_ngan: "",
                });
                setFoodModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90"
            >
              <Plus className="w-4 h-4" /> Thêm món mới
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center text-gray-500">Đang tải danh sách món...</div>
          ) : filteredFoods.length === 0 ? (
            <div className="p-12 text-center text-gray-400">Không tìm thấy món ăn nào.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                  <tr>
                    <th className="p-3.5">Tên món</th>
                    <th className="p-3.5">Danh mục</th>
                    <th className="p-3.5">Đơn giá</th>
                    <th className="p-3.5">Đặc trưng</th>
                    <th className="p-3.5">Còn hàng</th>
                    <th className="p-3.5">Hiển thị</th>
                    <th className="p-3.5 text-right">Hành động</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredFoods.map((f) => (
                    <tr key={f.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5">
                        <div className="font-semibold text-gray-900">{f.ten}</div>
                        <div className="text-xs text-gray-400 truncate max-w-xs">{f.mo_ta_ngan}</div>
                      </td>
                      <td className="p-3.5 text-gray-600">
                        {categories.find((c) => c.id === f.danh_muc)?.ten || f.chi_tiet_danh_muc?.ten || "Khác"}
                      </td>
                      <td className="p-3.5 font-medium text-gray-900">{Number(f.don_gia).toLocaleString()}đ</td>
                      <td className="p-3.5">
                        <div className="flex gap-1 text-xs">
                          {f.la_mon_chay && <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded">Chay</span>}
                          {f.do_cay > 0 && <span className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded">🌶️ x{f.do_cay}</span>}
                          {f.noi_bat && <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded">⭐ Nổi bật</span>}
                        </div>
                      </td>
                      <td className="p-3.5">
                        <button
                          onClick={() => handleToggleFoodStatus(f, "con_hang")}
                          className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            f.con_hang ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-800"
                          }`}
                        >
                          {f.con_hang ? "Còn hàng" : "Hết hàng"}
                        </button>
                      </td>
                      <td className="p-3.5">
                        <button
                          onClick={() => handleToggleFoodStatus(f, "hien_thi")}
                          className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                            f.hien_thi ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {f.hien_thi ? "Hiển thị" : "Đã ẩn"}
                        </button>
                      </td>
                      <td className="p-3.5 text-right space-x-1">
                        <button
                          onClick={() => {
                            setEditingFood(f);
                            setFoodModalOpen(true);
                          }}
                          className="p-1.5 text-gray-500 hover:text-primary rounded hover:bg-gray-100"
                          title="Sửa"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteFood(f.duong_dan)}
                          className="p-1.5 text-gray-500 hover:text-red-600 rounded hover:bg-gray-100"
                          title="Xóa"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: INGREDIENTS */}
      {activeTab === "ingredients" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="font-bold text-gray-800">Kho nguyên liệu thực phẩm</h3>
            <button
              onClick={() => setTxModalOpen(true)}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700"
            >
              <Package className="w-4 h-4" /> Nhập / Xuất kho
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Tên nguyên liệu</th>
                  <th className="p-3.5">Đơn vị</th>
                  <th className="p-3.5">Tồn kho hiện tại</th>
                  <th className="p-3.5">Mức tối thiểu</th>
                  <th className="p-3.5">Tình trạng cảnh báo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ingredients.map((ing) => {
                  const isLow = Number(ing.ton_kho_hien_tai) <= Number(ing.ton_kho_toi_thieu);
                  return (
                    <tr key={ing.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5 font-semibold text-gray-900">{ing.ten}</td>
                      <td className="p-3.5 text-gray-600">{ing.don_vi}</td>
                      <td className="p-3.5 font-bold text-gray-900">{Number(ing.ton_kho_hien_tai).toFixed(1)}</td>
                      <td className="p-3.5 text-gray-500">{Number(ing.ton_kho_toi_thieu).toFixed(1)}</td>
                      <td className="p-3.5">
                        {isLow ? (
                          <span className="flex items-center gap-1 text-xs text-red-600 font-semibold bg-red-50 px-2.5 py-1 rounded-full w-fit">
                            <AlertTriangle className="w-3.5 h-3.5" /> Sắp hết hàng
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs text-emerald-700 font-medium bg-emerald-50 px-2.5 py-1 rounded-full w-fit">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Đủ hàng
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: TRANSACTIONS */}
      {activeTab === "transactions" && (
        <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
          <div className="p-4 border-b">
            <h3 className="font-bold text-gray-800">Lịch sử xuất nhập điều chỉnh kho</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Thời gian</th>
                  <th className="p-3.5">Nguyên liệu</th>
                  <th className="p-3.5">Loại giao dịch</th>
                  <th className="p-3.5">Số lượng</th>
                  <th className="p-3.5">Trước → Sau</th>
                  <th className="p-3.5">Ghi chú</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {transactions.map((tx) => {
                  const ing = ingredients.find((i) => i.id === tx.nguyen_lieu);
                  const isNhap = tx.loai_giao_dich === "nhap";
                  return (
                    <tr key={tx.id} className="hover:bg-gray-50/70 transition-colors">
                      <td className="p-3.5 text-xs text-gray-500">{new Date(tx.tao_luc).toLocaleString()}</td>
                      <td className="p-3.5 font-medium text-gray-900">{ing?.ten || `Nguyên liệu #${tx.nguyen_lieu}`}</td>
                      <td className="p-3.5">
                        <span
                          className={`px-2 py-0.5 text-xs rounded font-medium ${
                            isNhap ? "bg-green-100 text-green-800" : "bg-orange-100 text-orange-800"
                          }`}
                        >
                          {isNhap ? "Nhập kho" : tx.loai_giao_dich === "xuat" ? "Xuất kho" : "Điều chỉnh"}
                        </span>
                      </td>
                      <td className="p-3.5 font-bold">
                        {isNhap ? "+" : "-"}{Number(tx.so_luong).toFixed(1)} {ing?.don_vi}
                      </td>
                      <td className="p-3.5 text-xs text-gray-600">
                        {Number(tx.ton_kho_truoc).toFixed(1)} → {Number(tx.ton_kho_sau).toFixed(1)}
                      </td>
                      <td className="p-3.5 text-xs text-gray-500">{tx.ghi_chu || "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* FOOD MODAL */}
      {foodModalOpen && editingFood && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSaveFood} className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="font-bold text-lg border-b pb-3">
              {editingFood.duong_dan ? "Chỉnh sửa món ăn" : "Thêm món ăn mới"}
            </h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold mb-1">Tên món ăn:</label>
                <input
                  type="text"
                  required
                  value={editingFood.ten || ""}
                  onChange={(e) => setEditingFood({ ...editingFood, ten: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Đơn giá (VNĐ):</label>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    required
                    value={editingFood.don_gia || 0}
                    onChange={(e) => setEditingFood({ ...editingFood, don_gia: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Danh mục:</label>
                  <select
                    value={editingFood.danh_muc || categories[0]?.id}
                    onChange={(e) => setEditingFood({ ...editingFood, danh_muc: Number(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg bg-white"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.ten}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Mô tả ngắn:</label>
                <textarea
                  rows={2}
                  value={editingFood.mo_ta_ngan || ""}
                  onChange={(e) => setEditingFood({ ...editingFood, mo_ta_ngan: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingFood.la_mon_chay || false}
                    onChange={(e) => setEditingFood({ ...editingFood, la_mon_chay: e.target.checked })}
                    className="rounded text-primary"
                  />
                  Món chay
                </label>
                <label className="flex items-center gap-1.5 text-xs cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingFood.noi_bat || false}
                    onChange={(e) => setEditingFood({ ...editingFood, noi_bat: e.target.checked })}
                    className="rounded text-primary"
                  />
                  Nổi bật
                </label>
              </div>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setFoodModalOpen(false)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy
              </button>
              <button type="submit" className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90">
                Lưu
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TRANSACTION MODAL */}
      {txModalOpen && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <form onSubmit={handleSaveTransaction} className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 space-y-4">
            <h3 className="font-bold text-lg border-b pb-3">Xuất / Nhập nguyên liệu kho</h3>
            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold mb-1">Chọn nguyên liệu:</label>
                <select
                  value={txData.nguyen_lieu}
                  onChange={(e) => setTxData({ ...txData, nguyen_lieu: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                >
                  {ingredients.map((i) => (
                    <option key={i.id} value={i.id}>{i.ten} (Đơn vị: {i.don_vi})</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Loại giao dịch:</label>
                <select
                  value={txData.loai_giao_dich}
                  onChange={(e) => setTxData({ ...txData, loai_giao_dich: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded-lg bg-white"
                >
                  <option value="nhap">Nhập kho (+)</option>
                  <option value="xuat">Xuất kho (-)</option>
                  <option value="dieu_chinh">Điều chỉnh kiểm kê</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Số lượng:</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  required
                  value={txData.so_luong}
                  onChange={(e) => setTxData({ ...txData, so_luong: Number(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Ghi chú:</label>
                <input
                  type="text"
                  placeholder="Nhập kho buổi sáng, chế biến..."
                  value={txData.ghi_chu}
                  onChange={(e) => setTxData({ ...txData, ghi_chu: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
            <div className="pt-3 border-t flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setTxModalOpen(false)}
                className="px-4 py-2 border rounded-lg text-sm text-gray-600 hover:bg-gray-100"
              >
                Hủy
              </button>
              <button type="submit" className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700">
                Xác nhận
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
```

---

### BLUEPRINT 4: `moc-frontend/src/pages/admin/AdminReviewsPage.tsx`
Dedicated review moderation portal for staff/admin to inspect, filter, toggle visibility, and delete customer reviews.

```tsx
import { useEffect, useState, useMemo } from "react";
import { Star, Eye, EyeOff, Trash2, Search, RefreshCw, MessageSquare } from "lucide-react";
import { getAdminReviews, toggleReviewVisibility, deleteAdminReview, type AdminReviewItem } from "@/api/admin.api";

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState<AdminReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [ratingFilter, setRatingFilter] = useState("all");
  const [visibilityFilter, setVisibilityFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const data = await getAdminReviews();
      setReviews(data);
    } catch (err) {
      console.error("Failed to load reviews:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleToggle = async (review: AdminReviewItem) => {
    try {
      await toggleReviewVisibility(review.id, !review.hien_thi);
      fetchReviews();
    } catch (err) {
      alert("Không thể thay đổi trạng thái đánh giá.");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Bạn có chắc chắn muốn xóa vĩnh viễn đánh giá này?")) return;
    try {
      await deleteAdminReview(id);
      fetchReviews();
    } catch (err) {
      alert("Không thể xóa đánh giá.");
    }
  };

  const filteredReviews = useMemo(() => {
    return reviews.filter((r) => {
      const matchRating = ratingFilter === "all" || String(r.diem_danh_gia) === ratingFilter;
      const matchVis =
        visibilityFilter === "all" ||
        (visibilityFilter === "visible" && r.hien_thi) ||
        (visibilityFilter === "hidden" && !r.hien_thi);
      const matchSearch =
        !searchQuery ||
        r.ten_nguoi_dung?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.nhan_xet?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchRating && matchVis && matchSearch;
    });
  }, [reviews, ratingFilter, visibilityFilter, searchQuery]);

  const avgRating = useMemo(() => {
    if (reviews.length === 0) return 0;
    const sum = reviews.reduce((acc, r) => acc + Number(r.diem_danh_gia), 0);
    return (sum / reviews.length).toFixed(1);
  }, [reviews]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Quản lý & Duyệt đánh giá</h1>
          <p className="text-sm text-gray-500">Kiểm duyệt ý kiến phản hồi của khách hàng đối với các món ăn.</p>
        </div>
        <button onClick={fetchReviews} className="p-2 border rounded-lg hover:bg-gray-100" title="Làm mới">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="text-sm text-gray-500 font-medium">Tổng số phản hồi</div>
          <div className="text-3xl font-bold text-gray-900 mt-1">{reviews.length}</div>
        </div>
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="text-sm text-gray-500 font-medium">Điểm đánh giá trung bình</div>
          <div className="text-3xl font-bold text-amber-500 mt-1 flex items-center gap-2">
            ⭐ {avgRating} / 5.0
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border shadow-sm">
          <div className="text-sm text-gray-500 font-medium">Đang hiển thị công khai</div>
          <div className="text-3xl font-bold text-emerald-600 mt-1">
            {reviews.filter((r) => r.hien_thi).length}
          </div>
        </div>
      </div>

      {/* Reviews Table */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        {/* Filters Bar */}
        <div className="p-4 border-b flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              type="text"
              placeholder="Tìm theo tên khách hàng hoặc nội dung nhận xét..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={ratingFilter}
              onChange={(e) => setRatingFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm bg-white"
            >
              <option value="all">Tất cả số sao</option>
              <option value="5">5 Sao ⭐⭐⭐⭐⭐</option>
              <option value="4">4 Sao ⭐⭐⭐⭐</option>
              <option value="3">3 Sao ⭐⭐⭐</option>
              <option value="2">2 Sao ⭐⭐</option>
              <option value="1">1 Sao ⭐</option>
            </select>
            <select
              value={visibilityFilter}
              onChange={(e) => setVisibilityFilter(e.target.value)}
              className="px-3 py-2 border rounded-lg text-sm bg-white"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="visible">Đang hiển thị</option>
              <option value="hidden">Đã ẩn</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-gray-500">Đang tải danh sách đánh giá...</div>
        ) : filteredReviews.length === 0 ? (
          <div className="p-12 text-center text-gray-400">Không có đánh giá nào thỏa mãn bộ lọc.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 border-b text-gray-600 font-medium">
                <tr>
                  <th className="p-3.5">Khách hàng</th>
                  <th className="p-3.5">Món ăn / Đơn</th>
                  <th className="p-3.5">Đánh giá</th>
                  <th className="p-3.5">Nhận xét</th>
                  <th className="p-3.5">Thời gian</th>
                  <th className="p-3.5">Trạng thái</th>
                  <th className="p-3.5 text-right">Hành động</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredReviews.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50/70 transition-colors">
                    <td className="p-3.5 font-semibold text-gray-900">{r.ten_nguoi_dung || "Khách hàng"}</td>
                    <td className="p-3.5 text-gray-600">
                      <div>Món #{r.mon_an}</div>
                      <div className="text-xs text-gray-400">Đơn #{r.don_hang}</div>
                    </td>
                    <td className="p-3.5">
                      <div className="flex text-amber-400">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star
                            key={i}
                            className={`w-4 h-4 ${i < r.diem_danh_gia ? "fill-amber-400" : "text-gray-300"}`}
                          />
                        ))}
                      </div>
                    </td>
                    <td className="p-3.5 text-gray-800 max-w-xs">{r.nhan_xet || <span className="italic text-gray-400">Không có lời bình</span>}</td>
                    <td className="p-3.5 text-xs text-gray-500">{new Date(r.tao_luc).toLocaleDateString("vi-VN")}</td>
                    <td className="p-3.5">
                      <span
                        className={`px-2.5 py-1 text-xs rounded-full font-medium ${
                          r.hien_thi ? "bg-emerald-100 text-emerald-800" : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {r.hien_thi ? "Công khai" : "Đã ẩn"}
                      </span>
                    </td>
                    <td className="p-3.5 text-right space-x-1">
                      <button
                        onClick={() => handleToggle(r)}
                        className={`p-1.5 rounded text-xs border ${
                          r.hien_thi ? "hover:bg-amber-50 text-amber-700" : "hover:bg-emerald-50 text-emerald-700"
                        }`}
                        title={r.hien_thi ? "Ẩn đánh giá" : "Hiển thị công khai"}
                      >
                        {r.hien_thi ? <EyeOff className="w-4 h-4 inline" /> : <Eye className="w-4 h-4 inline" />}
                      </button>
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="p-1.5 text-gray-400 hover:text-red-600 rounded hover:bg-gray-100"
                        title="Xóa đánh giá"
                      >
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### BLUEPRINT 5: `moc-frontend/src/pages/admin/AdminChatPage.tsx`
Full 2-column live messaging workspace for restaurant staff connecting to `ws://${host}/ws/chat/${conversationId}/?token=${token}`.

```tsx
import { useEffect, useState, useRef } from "react";
import { MessageCircle, Send, CheckCheck, User, RefreshCw, X, Sparkles } from "lucide-react";
import {
  getAdminChatRooms,
  getAdminChatMessages,
  sendAdminChatMessage,
  updateChatRoomStatus,
  type AdminChatRoomItem,
  type AdminChatMessageItem,
} from "@/api/admin.api";
import { useAuthStore } from "@/store/authStore";

const CANNED_RESPONSES = [
  "Dạ Mộc Quán xin chào quý khách! Em có thể giúp gì cho mình ạ? 👋",
  "Bàn của quý khách đã được chuẩn bị sẵn sàng, mời quý khách đến nhận bàn ạ.",
  "Đơn hàng của quý khách đang được bếp chế biến, dự kiến khoảng 15-20 phút nữa sẽ giao tới ạ.",
  "Dạ vâng, em đã ghi nhận thông tin và cập nhật giúp mình rồi ạ.",
];

export default function AdminChatPage() {
  const { user } = useAuthStore();
  const [rooms, setRooms] = useState<AdminChatRoomItem[]>([]);
  const [activeRoom, setActiveRoom] = useState<AdminChatRoomItem | null>(null);
  const [messages, setMessages] = useState<AdminChatMessageItem[]>([]);
  const [draft, setDraft] = useState("");
  const [customerTyping, setCustomerTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchRooms = async () => {
    try {
      const data = await getAdminChatRooms();
      setRooms(data);
      if (!activeRoom && data.length > 0) {
        selectRoom(data[0]);
      }
    } catch (err) {
      console.error("Failed to load chat rooms:", err);
    } finally {
      setLoading(false);
    }
  };

  const selectRoom = async (room: AdminChatRoomItem) => {
    setActiveRoom(room);
    try {
      const msgs = await getAdminChatMessages(room.id);
      setMessages(msgs);
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  // WebSocket Connection per Active Room
  useEffect(() => {
    if (!activeRoom) return;

    const token = localStorage.getItem("access_token");
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.hostname === "localhost" ? "localhost:8000" : window.location.host;
    const wsUrl = `${protocol}//${host}/ws/chat/${activeRoom.id}/?token=${token || ""}`;

    let ws: WebSocket;
    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === "chat_message") {
            const newMsg: AdminChatMessageItem = {
              id: payload.id || Date.now(),
              hoi_thoai: activeRoom.id,
              nguoi_gui: payload.sender_id,
              sender_name: payload.sender_name,
              noi_dung: payload.content || payload.noi_dung || payload.message,
              loai_tin_nhan: payload.message_type || "van_ban",
              da_doc: payload.is_read ?? false,
              tao_luc: payload.created_at || new Date().toISOString(),
              is_staff: payload.is_staff,
            };

            setMessages((prev) => {
              if (prev.some((m) => m.id === newMsg.id)) return prev;
              return [...prev, newMsg];
            });
            setTimeout(scrollToBottom, 50);
          } else if (payload.type === "chat_typing") {
            if (!payload.is_staff) {
              setCustomerTyping(Boolean(payload.is_typing));
              if (payload.is_typing) {
                setTimeout(() => setCustomerTyping(false), 3000);
              }
            }
          }
        } catch (e) {
          console.error("WS Parse Error", e);
        }
      };

      ws.onclose = () => setIsConnected(false);
      ws.onerror = () => setIsConnected(false);
    } catch (err) {
      setIsConnected(false);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [activeRoom?.id]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || draft).trim();
    if (!text || !activeRoom) return;

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: "send_message",
          message: text,
          content: text,
        })
      );
    } else {
      // REST fallback
      try {
        const sent = await sendAdminChatMessage(activeRoom.id, text);
        setMessages((prev) => [...prev, sent]);
      } catch (err) {
        alert("Không thể gửi tin nhắn.");
      }
    }

    setDraft("");
    setTimeout(scrollToBottom, 50);
  };

  const handleToggleRoomStatus = async () => {
    if (!activeRoom) return;
    const newStatus = activeRoom.trang_thai === "mo" ? "dong" : "mo";
    try {
      await updateChatRoomStatus(activeRoom.id, newStatus);
      setActiveRoom({ ...activeRoom, trang_thai: newStatus });
      fetchRooms();
    } catch (err) {
      alert("Không thể cập nhật trạng thái hội thoại.");
    }
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col bg-white border rounded-xl shadow-sm overflow-hidden">
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Rooms List */}
        <div className="w-80 border-r flex flex-col bg-gray-50/50">
          <div className="p-4 border-b flex justify-between items-center bg-white">
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-primary" /> Hội thoại khách hàng
            </h2>
            <button onClick={fetchRooms} className="text-gray-400 hover:text-gray-600" title="Tải lại">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
            {loading ? (
              <div className="p-6 text-center text-sm text-gray-500">Đang tải...</div>
            ) : rooms.length === 0 ? (
              <div className="p-6 text-center text-sm text-gray-400">Chưa có hội thoại nào</div>
            ) : (
              rooms.map((room) => {
                const isSelected = activeRoom?.id === room.id;
                const lastMsg = room.danh_sach_tin_nhan?.[room.danh_sach_tin_nhan.length - 1];
                return (
                  <button
                    key={room.id}
                    onClick={() => selectRoom(room)}
                    className={`w-full text-left p-4 transition-colors flex items-start gap-3 ${
                      isSelected ? "bg-white border-l-4 border-primary shadow-xs" : "hover:bg-gray-100/60"
                    }`}
                  >
                    <div className="w-10 h-10 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center shrink-0">
                      <User className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-baseline">
                        <span className="font-semibold text-sm text-gray-900 truncate">
                          Khách #{room.khach_hang}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${room.trang_thai === "mo" ? "bg-green-100 text-green-700" : "bg-gray-200 text-gray-600"}`}>
                          {room.trang_thai === "mo" ? "Đang mở" : "Đã đóng"}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 truncate mt-1">
                        {lastMsg?.noi_dung || "Chưa có tin nhắn"}
                      </p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Live Chat Pane */}
        {activeRoom ? (
          <div className="flex-1 flex flex-col bg-white">
            {/* Header */}
            <div className="p-4 border-b flex justify-between items-center bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold">
                  K{activeRoom.khach_hang}
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-sm">Khách hàng #{activeRoom.khach_hang}</h3>
                  <div className="flex items-center gap-1.5 text-xs">
                    <span className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-amber-400"}`} />
                    <span className="text-gray-500">{isConnected ? "Đã kết nối thời gian thực" : "Mất kết nối WS"}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleToggleRoomStatus}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                  activeRoom.trang_thai === "mo"
                    ? "bg-red-50 text-red-600 border-red-200 hover:bg-red-100"
                    : "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                }`}
              >
                {activeRoom.trang_thai === "mo" ? "Đóng hội thoại" : "Mở lại hội thoại"}
              </button>
            </div>

            {/* Messages Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50/30">
              {messages.map((m) => {
                const isStaff = m.is_staff || m.nguoi_gui === Number(user?.id);
                return (
                  <div key={m.id} className={`flex flex-col ${isStaff ? "items-end" : "items-start"}`}>
                    <div className="text-[11px] text-gray-400 mb-1 px-1">
                      {isStaff ? "Nhân viên hỗ trợ" : `Khách #${m.nguoi_gui}`}
                    </div>
                    <div
                      className={`max-w-md px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                        isStaff
                          ? "bg-primary text-white rounded-br-xs"
                          : "bg-white border text-gray-800 rounded-bl-xs shadow-xs"
                      }`}
                    >
                      {m.noi_dung}
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1 px-1">
                      {new Date(m.tao_luc).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>
                );
              })}
              {customerTyping && (
                <div className="text-xs text-gray-400 italic flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
                  Khách hàng đang nhập tin nhắn...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Quick Canned Responses */}
            <div className="px-4 py-2 border-t bg-gray-50 flex gap-2 overflow-x-auto">
              <span className="text-xs font-semibold text-gray-400 flex items-center gap-1 shrink-0">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" /> Tin mẫu:
              </span>
              {CANNED_RESPONSES.map((res, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(res)}
                  className="px-2.5 py-1 bg-white border rounded-full text-xs text-gray-600 hover:border-primary hover:text-primary shrink-0 transition-colors"
                >
                  {res.slice(0, 32)}...
                </button>
              ))}
            </div>

            {/* Input Bar */}
            <div className="p-3 border-t bg-white flex gap-2">
              <input
                type="text"
                placeholder="Nhập nội dung phản hồi khách hàng..."
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                className="flex-1 px-4 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button
                onClick={() => handleSendMessage()}
                className="px-5 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90 flex items-center gap-1.5"
              >
                <Send className="w-4 h-4" /> Gửi
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
            Chọn một cuộc hội thoại từ danh sách bên trái để bắt đầu chat
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### BLUEPRINT 6: Navigation & Router Integration

#### 1. In `moc-frontend/src/components/layout/AdminLayout.tsx`
Replace `navItems` array with:
```tsx
  const navItems = [
    { name: "Tổng quan", path: "/admin", icon: "📊" },
    { name: "Đơn hàng", path: "/admin/orders", icon: "🛍️" },
    { name: "Đặt bàn", path: "/admin/reservations", icon: "📅" },
    { name: "Thực đơn & Kho", path: "/admin/menu", icon: "🍲" },
    { name: "Đánh giá", path: "/admin/reviews", icon: "⭐" },
    { name: "Hỗ trợ khách", path: "/admin/chat", icon: "💬" },
  ];
```

#### 2. In `moc-frontend/src/App.tsx`
Import and register the 4 new admin components:
```tsx
// Admin Pages
import AdminDashboardPage from "@/pages/admin/AdminDashboardPage";
import AdminOrdersPage from "@/pages/admin/AdminOrdersPage";
import AdminReservationsPage from "@/pages/admin/AdminReservationsPage";
import AdminMenuPage from "@/pages/admin/AdminMenuPage";
import AdminReviewsPage from "@/pages/admin/AdminReviewsPage";
import AdminChatPage from "@/pages/admin/AdminChatPage";
```

Update the `/admin` route block:
```tsx
        {/* Admin Routes */}
        <Route path="/admin" element={<AdminGuard />}>
          <Route element={<AdminLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="orders" element={<AdminOrdersPage />} />
            <Route path="reservations" element={<AdminReservationsPage />} />
            <Route path="menu" element={<AdminMenuPage />} />
            <Route path="reviews" element={<AdminReviewsPage />} />
            <Route path="chat" element={<AdminChatPage />} />
          </Route>
        </Route>
```

---

## 5. Verification Method

### 5.1 Verification Checklist
1. **TypeScript Build Verification**:
   - Command: `npm run build` in `/Users/VuVan/Documents/DO-AN/moc-frontend`.
   - Condition: Clean compilation (exit code 0, 0 TypeScript errors).
2. **Page Existence & Routing**:
   - Navigate to `/admin/reservations`: Displays the 2 tabs ("Danh sách đặt bàn" and "Sơ đồ bàn ăn").
   - Navigate to `/admin/menu`: Displays the 3 tabs ("Món ăn", "Kho nguyên liệu", "Lịch sử kho").
   - Navigate to `/admin/reviews`: Displays KPI metrics, star ratings, visibility toggles.
   - Navigate to `/admin/chat`: Displays conversation list, live chat pane, and canned replies.
3. **API Integration Verification**:
   - Test table addition: `POST /api/tables/` adds a table and updates the floor plan.
   - Test reservation transition: `PATCH /api/reservations/<id>/trang_thai/` updates booking status.
   - Test reservation cancel: `POST /api/reservations/<id>/cancel/` calculates refund and issues refund receipt.
   - Test review moderation: `PATCH /api/reviews/<id>/` changes visibility state.
   - Test staff realtime chat: Open 1 customer browser with `ChatWidget.tsx` and 1 staff browser with `/admin/chat`. Messages exchange in real-time over WebSocket.

### 5.2 Invalidation Conditions
- Any route in `/admin/*` rendering placeholder or stub text.
- WebSocket fails to authenticate due to missing `?token=<jwt>`.
- Food deletion failing due to slug vs numeric ID mismatch.
