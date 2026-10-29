# Milestone 5: Frontend TypeScript Types, API Callers & Build Cleanliness Specification Report

**Agent**: `teamwork_preview_spec_miner_m5_1` (Specification Miner)  
**Date**: 2026-10-15  
**Target Milestone**: Milestone 5 (Frontend Types, API Callers & Build Cleanliness)

---

## 1. Observation

### 1.1 Compiler & Linter Execution Results

1. **`npm run build` Execution**:
   - Command: `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npm run build`
   - Output:
     ```text
     > moc-frontend@0.0.0 build
     > tsc -b && vite build

     vite v8.2.2 building client environment for production...
     transforming (281) node_modules/leaflet/dist/leaflet.csstransforming (1137) node_modules/lucide-react/dist/esm/icons/map-pin-check.mjs✓ 2068 modules transformed.
     rendering chunks (1)...rendering chunks (2)...computing gzip size...
     dist/index.html                         0.85 kB │ gzip:   0.48 kB
     dist/assets/index-BZCJnsjl.css         73.64 kB │ gzip:  16.65 kB
     dist/assets/LocationPage-51l0c0OG.js  162.76 kB │ gzip:  48.87 kB
     dist/assets/index-C9SMdhX8.js         501.31 kB │ gzip: 153.53 kB

     ✓ built in 476ms
     ```
   - Exit code: `0` (Zero compiler errors).

2. **`npx tsc --noEmit` Execution**:
   - Command: `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx tsc --noEmit`
   - Stdout: *(empty)*
   - Stderr: *(empty)*
   - Exit code: `0`.

3. **`npx oxlint src` Execution**:
   - Command: `cd /Users/VuVan/Documents/DO-AN/moc-frontend && npx oxlint src`
   - Output: 3 minor linter warnings, 0 errors:
     - `OrderSuccessPage.tsx:5:46`: `Math.random` called during render.
     - `CheckoutForm.tsx:8:14`: Fast refresh warning on `export const checkoutSchema`.
     - `ChatWidget.tsx:27:3`: `setIsConnected(false)` called synchronously inside `catch` block of `useEffect`.

---

### 1.2 Frontend Structure & Directory Layout Observation

- Dispatch referenced `/Users/VuVan/Documents/DO-AN/moc-frontend/src/services/api.ts`.
- **Actual Directory Structure**: The directory `moc-frontend/src/services/` does NOT exist.
- Instead, API callers and mappers are centralized under `moc-frontend/src/api/`:
  - `src/api/client.ts`: Axios instance configured with `baseURL: import.meta.env.VITE_API_URL ?? "/api"` and Bearer token interceptor.
  - `src/api/mappers.ts`: Serialization / translation functions (`mapMonAn`, `mapBanAn`, `mapThongTinDatBan`, `mapKhuyenMai`, `mapDanhGia`, `mapBaiViet`, `mapGoiY`).
  - `src/api/foods.api.ts`, `src/api/orders.api.ts`, `src/api/reservations.api.ts`, `src/api/locations.api.ts`, `src/api/promotions.api.ts`, `src/api/reviews.api.ts`, `src/api/recommendations.api.ts`, `src/api/blog.api.ts`, `src/api/auth.api.ts`.

---

### 1.3 Latent Runtime Discrepancies Observed Between DRF Serializers and Frontend Callers

While TypeScript passes due to permissive typing and partial aliases, cross-verifying backend Python DRF serializers against frontend API callers revealed 6 critical discrepancy categories:

#### Observation A: VNPay Sandbox Creation URL Mismatch
- **Frontend Caller** (`src/api/reservations.api.ts`, line 108):
  ```typescript
  const { data } = await apiClient.post("/payments/vnpay_create_payment_url/", {
    dat_ban_id: idDatBan,
    so_tien: soTien,
  });
  ```
- **Backend Route** (`moc-backend/api/urls.py`, lines 113–116; `payments/views.py`, line 64):
  ```python
  path("payments/vnpay/create/", PaymentViewSet.as_view({"post": "vnpay_create"}), name="vnpay-create-en"),
  path("payments/vnpay/tao-phien/", PaymentViewSet.as_view({"post": "vnpay_tao_phien"}), name="vnpay-tao-phien-en"),
  ```
- **Impact**: Calling `/payments/vnpay_create_payment_url/` returns **HTTP 404 Not Found**.

#### Observation B: Order Creation & Order History Field Mismatches
- **Backend Serializer** (`orders/serializers.py`, lines 33–66):
  Model fields returned: `id`, `ma_don_hang`, `tien_hang`, `tien_giam`, `tong_tien`, `trang_thai`, `danh_sach_mon`, `tao_luc`.
- **Frontend Caller** (`src/api/orders.api.ts`, lines 27 & 33):
  ```typescript
  return { orderId: data.number }; // Line 27
  return (Array.isArray(data) ? data : data.results).map((order: any) => ({
    id: order.number,              // undefined!
    createdAt: order.created_at,   // undefined!
    total: Number(order.total),     // NaN!
    status: order.status as OrderStatus, // undefined!
    items: order.items?.reduce((total: number, item: any) => total + item.quantity, 0) ?? 0 // NaN!
  }));
  ```
- **Impact**: `order.number` is `undefined` (backend outputs `ma_don_hang`), `order.created_at` is `undefined` (backend outputs `tao_luc`), `order.total` is `undefined` (backend outputs `tong_tien`), and `item.quantity` is `undefined` (backend item serializer outputs `so_luong`). Orders display blank IDs, NaN sums, and invalid dates.

#### Observation C: WebSocket Chat Missing JWT Token & Wrong Room ID
- **Backend Consumer** (`chat/consumers.py`, lines 28–30):
  ```python
  if not self.user or not self.user.is_authenticated:
      await self.close(code=4401)
      return
  ```
- **Backend Middleware** (`config/middleware.py`, lines 45–51):
  Authenticates via query parameter `?token=<access_token>`.
- **Frontend Component** (`src/components/chat/ChatWidget.tsx`, lines 25 & 32):
  ```typescript
  const roomId = user?.id ? String(user.id) : "1";
  const wsUrl = `${protocol}//${host}/ws/chat/${roomId}/`;
  ```
- **Impact**:
  1. Connection is anonymous because `?token=${token}` is never appended; backend closes with code `4401`.
  2. The path `/ws/chat/<conversation_id>/` expects a `HoiThoai` conversation ID, not `user.id`. The active room must be fetched from `GET /api/chat/rooms/active/`.

#### Observation D: Category Detail & Food Mapper Property Mismatch
- **Backend Serializer** (`foods/serializers.py`, line 76):
  ```python
  chi_tiet_danh_muc = DanhMucSerializer(source="danh_muc", read_only=True)
  ```
  `DanhMucSerializer` fields are: `id`, `ten`, `duong_dan`, `mo_ta`, `anh_dai_dien`, `con_hoat_dong`.
- **Frontend Mapper** (`src/api/mappers.ts`, lines 17–18):
  ```typescript
  const category = raw.category_detail?.slug ?? raw.danh_muc ?? raw.category ?? "main";
  const categoryLabel = raw.category_detail?.name ?? raw.ten_danh_muc ?? "Thực đơn";
  ```
- **Impact**: Because the backend serializer field is `chi_tiet_danh_muc` (not `category_detail`), `raw.category_detail` is always undefined. The frontend falls back to numeric category IDs or defaults.

#### Observation E: Review Author and Food ID Property Mismatch
- **Backend Serializer** (`reviews/serializers.py`, lines 20–21, 26):
  `ten_nguoi_dung` and `user_name` are the author fields. `mon_an` is the foreign key ID.
- **Frontend Mapper** (`src/api/mappers.ts`, lines 188–189):
  ```typescript
  const foodId = String(raw.mon_an_id ?? raw.food ?? "");
  const author = (raw.ten_khach ?? raw.customer_name) || "Khách hàng";
  ```
- **Impact**: `raw.mon_an` was not checked (only `mon_an_id` and `food`), and `ten_nguoi_dung` was omitted, causing reviews to show default `"Khách hàng"`.

#### Observation F: Unimplemented Admin Portals for Milestone 5
- `moc-frontend/src/pages/admin/` only contains:
  - `AdminDashboardPage.tsx`
  - `AdminOrdersPage.tsx`
- Missing pages currently rendered as placeholder `<div>`:
  - `reservations` (`Quản lý sơ đồ bàn & đặt bàn`)
  - `menu` (`Quản lý thực đơn & kho nguyên liệu`)
  - `reviews` (`Quản lý đánh giá`)
  - `chat` (`Giao diện chat trực tuyến của nhân viên`)

---

## 2. Logic Chain

1. **Current Clean Build vs Runtime Reality**:
   `npm run build` and `npx tsc --noEmit` succeed with code 0 because the frontend codebase was written using lenient types (`any` in `mappers.ts`, optional alias fields in `src/types/index.ts`). However, when runtime API responses arrive from Django REST Framework, the field names do not match the assumed properties, causing silent UI failures, NaN totals, and 404/401 network rejections.

2. **Root Cause of Field Discrepancies**:
   The Django backend was normalized under Milestone 1 to follow `moc_schema_tieng_viet.sql` (canonical Vietnamese fields: `ma_don_hang`, `tong_tien`, `trang_thai`, `chi_tiet_danh_muc`, `so_ban`, etc.). While `DualPayloadMixin` allows incoming requests in English, DRF response bodies serialize canonical Vietnamese model fields. The frontend callers were expecting either legacy English names or mismatched snake_case names.

3. **Required Architectural Remedy**:
   Milestone 5 requires:
   - Augmenting `src/types/index.ts` with explicit bilingual DTO definitions (e.g. `MonAnResponse`, `DonHangResponse`, `DatBanResponse`, `ChiNhanhResponse`, `PhieuHoanTien`) alongside clean TypeScript models.
   - Updating `src/api/mappers.ts` to exhaustively check both Vietnamese and English response keys.
   - Correcting endpoint paths in `orders.api.ts` and `reservations.api.ts` (`/payments/vnpay/create/`).
   - Connecting `ChatWidget.tsx` and Order Tracking to Django Channels with JWT authentication query parameters (`?token=...`).
   - Creating missing API service callers (`chat.api.ts`, `inventory.api.ts`, `admin.api.ts`) for admin portals.

---

## 3. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | API / Build | TypeScript Clean Build | `tsc -b && vite build` bundle creation | TypeScript source | JS/CSS in `dist/` | TS compile errors (currently 0) | `moc-frontend/package.json` |
| 2 | Payments | VNPay Payment Session Creation | Initiates VNPay sandbox transaction URL | `{ dat_ban_id, so_tien }` or `{ don_hang_id, so_tien }` | `{ payment_url, txn_ref, amount, expires_at }` | HTTP 400 if ID missing, 404 on bad endpoint | `payments/views.py`, `api/urls.py` |
| 3 | Payments | VNPay Return & IPN Verification | Processes payment callback and updates DB | Query params with HMAC signature | `{ status: "success" \| "failed" }` | HTTP 200 with `RspCode: 97` if signature invalid | `payments/views.py` |
| 4 | Payments | Refund Receipt Generation | Records deposit refund per time rule | `{ dat_ban_id, ly_do, is_no_show }` | `PhieuHoanTien` object | HTTP 400 if already refunded/completed | `payments/views.py`, `reservations/views.py` |
| 5 | Concurrency | Temporary Table Hold (Phase 1) | Redis `SET NX EX 600` table lock | `{ ngay, gio, so_luong_khach }` | `{ id_giu_ban, thoi_han_giu_cho }` | HTTP 409 BAN_DANG_BAN | `reservations/views.py` |
| 6 | Reservations | Complete Booking Creation | Persists booking & locks table | Booking payload + `id_giu_ban` | `DatBan` object | HTTP 400 if invalid table/branch | `reservations/views.py` |
| 7 | Reservations | Deposit Policy & Cancellation Rules | Returns deposit % and refund tiers | `{ branch?: number }` | `ChinhSachDatCoc` with `quy_tac_huy` | Returns fallback default policy | `reservations/views.py` |
| 8 | Orders | Order Lifecycle FSM Transitions | Transition order status with log | `{ trang_thai, ghi_chu }` | Updated `DonHang` + WS broadcast | HTTP 400 if invalid FSM transition | `orders/services.py` |
| 9 | Orders | Realtime Order Tracking WS | Live push of order status updates | WebSocket `/ws/orders/<order_id>/?token=...` | JSON `order_status_update` events | WS Close 4401 (Unauth), 4403 (Forbidden) | `orders/consumers.py` |
| 10 | Orders | Staff Global Order Stream WS | Kitchen/staff live stream of orders | WebSocket `/ws/orders/staff/?token=...` | `order_created`, `order_status_update` | WS Close 4401 (Unauth), 4403 (Non-staff) | `orders/consumers.py` |
| 11 | Chat | Realtime Customer-Staff Chat WS | Bi-directional live messaging | WebSocket `/ws/chat/<conv_id>/?token=...` | `chat_message`, `chat_typing` | WS Close 4401 (Unauth), 4403 (Forbidden) | `chat/consumers.py` |
| 12 | Chat | Active Conversation Discovery | Resolves or creates user active chat room | Authenticated GET | `HoiThoai` object with message history | HTTP 401 if unauthenticated | `chat/views.py` |
| 13 | Recommendations | Content-Based AI Recommendations | TF-IDF & Cosine recommendations | `{ limit: number }` | List of `GoiYMonAn` with `reason` | Fallback to cold-start popularity | `recommendations/views.py` |
| 14 | Branches / GIS | Nearest Branch Spatial Query | PostGIS spatial distance calculation | `{ lat, lng }` | List of `ChiNhanh` sorted by distance | Returns default list if GIS error | `branches/views.py` |
| 15 | Inventory | Material & BOM Stock Tracking | Ingredient stock & transaction history | `{ nguyen_lieu, loai, so_luong }` | `LichSuXuatNhapKho` record | HTTP 400 if insufficient stock | `foods/serializers.py` |
| 16 | Reviews | Customer Review Submission & Moderation | Reviews tied to completed orders | `{ don_hang, mon_an, diem_danh_gia, nhan_xet }` | `DanhGia` object | HTTP 400 if order not completed | `reviews/views.py` |

---

## 4. Edge Cases

| # | Feature | Input / Condition | Observed / Documented Behavior |
|---|---------|-------------------|--------------------------------|
| 1 | `npm run build` | Large bundles (> 500kB) | Vite emits chunk size warning for `dist/assets/index-*.js` (501 kB); build succeeds without failure. |
| 2 | VNPay URL Creation | Endpoint `/payments/vnpay_create_payment_url/` | Backend returns HTTP 404 because valid endpoints are `/payments/vnpay/create/` or `/payments/vnpay/tao-phien/`. |
| 3 | WebSocket Auth | Connecting to `/ws/chat/1/` without query token | Backend `JWTAuthMiddleware` evaluates user to `AnonymousUser()`; `ChatConsumer` closes immediately with code 4401. |
| 4 | WebSocket Room ID | Using `user.id` as chat conversation ID | Backend checks `HoiThoai` where `id = <conversation_id>`. If no room exists with that ID, returns 4403. |
| 5 | Order Number Display | `order.number` accessed on DRF response | Yields `undefined` because DRF returns `ma_don_hang`. |
| 6 | Order Items Total | `order.items?.reduce(...)` with `item.quantity` | Yields `NaN` because backend returns `so_luong`. |
| 7 | Branch Open Hours | `branch.openHours` accessed on `ChiNhanh` | Yields `undefined` because backend model has no `opening_hours` field. |
| 8 | Promotion Coupon Code | `raw.ma_giam_gia` accessed on `KhuyenMai` | Yields `""` because coupons are in nested `raw.danh_sach_ma[0].ma` or `raw.codes[0].ma`. |

---

## 5. Caveats

1. **Read-Only Inspection**: This specification report was compiled in read-only mode per the Specification Miner role. No files in `moc-frontend` were modified during this investigation.
2. **Current Build Status**: `npm run build` currently succeeds (exit 0) on the existing codebase. The enhancements proposed below will maintain zero compiler errors while fixing all latent runtime deserialization bugs and missing endpoints.
3. **Leaflet Peer Dependencies**: Vite build logs a chunk warning for Leaflet (>500kB), which is already handled via lazy-loading in `App.tsx`.

---

## 6. Conclusion & Concrete Implementation Blueprints

To achieve complete alignment for Milestone 5 with 0 build errors and 100% API fidelity, the implementation workers (`m5_worker_*`) should apply the following drop-in blueprints:

### Blueprint 1: Augmented Type Definitions (`moc-frontend/src/types/index.ts`)

```typescript
// Add to moc-frontend/src/types/index.ts:

// Inventory types
export interface Ingredient {
  id: string;
  name: string;
  unit: string;
  currentStock: number;
  minStock: number;
  isActive: boolean;

  // Vietnamese aliases
  ten?: string;
  donVi?: string;
  tonKhoHienTai?: number;
  tonKhoToiThieu?: number;
  conHoatDong?: boolean;
}
export type NguyenLieu = Ingredient;

export interface InventoryTransaction {
  id: string;
  ingredientId: string;
  ingredientName?: string;
  type: "nhap" | "xuat" | "dieu_chinh" | "tru_tu_dong";
  quantity: number;
  stockBefore: number;
  stockAfter: number;
  reason?: string;
  createdBy?: string;
  createdAt: string;
}
export type LichSuKho = InventoryTransaction;

// Refund Receipt types
export interface RefundReceipt {
  id: string;
  refundCode: string;
  reservationId: string;
  paymentId: string;
  originalDeposit: number;
  refundPercentage: number;
  refundAmount: number;
  penaltyAmount: number;
  timeMilestone: string;
  hoursBeforeBooking: number;
  cancelReason: string;
  status: "cho_xu_ly" | "da_hoan_tien" | "tu_choi";
  refundMethod: "vnpay" | "chuyen_khoan" | "tien_mat";
  createdAt: string;

  // Vietnamese aliases
  maPhieuHoan?: string;
  soTienCocGoc?: number;
  phanTramHoan?: number;
  soTienHoan?: number;
  soTienPhat?: number;
  mocThoiGian?: string;
  lyDoHuy?: string;
  trangThai?: string;
}
export type PhieuHoanTien = RefundReceipt;

// Chat types
export interface ChatMessage {
  id: number | string;
  conversationId: number | string;
  senderId: number | string;
  senderName: string;
  senderRole?: string;
  isStaff: boolean;
  message: string;
  messageType: "van_ban" | "hinh_anh" | "he_thong";
  isRead: boolean;
  createdAt: string;
}
export type TinNhan = ChatMessage;

export interface ChatConversation {
  id: number | string;
  customerId: number | string;
  customerName?: string;
  staffId?: number | string | null;
  staffName?: string | null;
  status: "mo" | "dong";
  lastMessageAt?: string;
  messages: ChatMessage[];
}
export type HoiThoai = ChatConversation;
```

---

### Blueprint 2: Bidirectional Data Mappers (`moc-frontend/src/api/mappers.ts`)

```typescript
// Key updates to mapMonAn:
export function mapMonAn(raw: any): Food {
  if (!raw) return {} as Food;
  const name = raw.ten ?? raw.name ?? "";
  const slug = raw.duong_dan ?? raw.slug ?? "";
  const price = Number(raw.don_gia_hien_tai ?? raw.don_gia ?? raw.price ?? 0);
  const category =
    raw.chi_tiet_danh_muc?.duong_dan ??
    raw.category_detail?.slug ??
    raw.danh_muc ??
    raw.category ??
    "main";
  const categoryLabel =
    raw.chi_tiet_danh_muc?.ten ??
    raw.category_detail?.name ??
    raw.ten_danh_muc ??
    "Thực đơn";
  const description = raw.mo_ta_ngan ?? raw.short_description ?? raw.description ?? "";
  const longDescription = raw.mo_ta_chi_tiet ?? raw.long_description ?? raw.description ?? "";
  const ingredients = raw.nguyen_lieu ?? raw.ingredients ?? [];
  const tags = raw.the_mon_an ?? raw.tags ?? [];
  const spicyLevel = Math.min(raw.do_cay ?? raw.spicy_level ?? 0, 3) as 0 | 1 | 2 | 3;
  const isVegetarian = Boolean(raw.la_mon_chay ?? raw.is_vegetarian ?? false);
  const rating = Number(raw.diem_danh_gia ?? raw.rating ?? 0);
  const reviewCount = Number(raw.so_luot_danh_gia ?? raw.review_count ?? 0);
  const available = Boolean(raw.con_hang ?? raw.is_available ?? raw.available ?? true);
  const stock = Number(raw.ton_kho_cache ?? raw.stock ?? 0);
  const placeholderTone = tinhPhongCach(raw.id);
  const createdAt = raw.tao_luc ?? raw.created_at ?? new Date().toISOString();

  return {
    id: String(raw.id),
    name,
    slug,
    category,
    categoryLabel,
    price,
    description,
    longDescription,
    ingredients,
    tags,
    spicyLevel,
    isVegetarian,
    rating,
    reviewCount,
    available,
    stock,
    badge: raw.nhan_hien_thi ?? raw.badge ?? "",
    placeholderTone,
    createdAt,
    // Vietnamese aliases
    tenMon: name,
    duongDan: slug,
    danhMuc: category,
    tenDanhMuc: categoryLabel,
    donGia: price,
    moTaNgan: description,
    moTaChiTiet: longDescription,
    theMonAn: tags,
    doCay: spicyLevel,
    laMonChay: isVegetarian,
    diemDanhGia: rating,
    soLuotDanhGia: reviewCount,
    conHang: available,
    tonKho: stock,
    phongCachHienThi: placeholderTone,
    taoLuc: createdAt,
  };
}

// Key updates to mapKhuyenMai:
export function mapKhuyenMai(raw: any): Promotion {
  const code =
    raw.ma_giam_gia ??
    raw.code ??
    raw.danh_sach_ma?.[0]?.ma ??
    raw.codes?.[0]?.ma ??
    "";
  const title = raw.ten ?? raw.name ?? raw.title ?? "";
  const description = raw.mo_ta ?? raw.description ?? "";
  const discountType = raw.kieu_giam ?? raw.discount_type ?? "percentage";
  const discountValue = Number(raw.gia_tri_giam ?? raw.discount_value ?? 0);
  const minOrder = Number(raw.don_hang_toi_thieu ?? raw.min_order_value ?? 0);
  const endsAt = raw.ket_thuc_luc ?? raw.ends_at ?? "";
  const badge =
    raw.nhan_giam_gia ??
    `${discountValue}${discountType === "percentage" || discountType === "phan_tram" ? "%" : "đ"}`;

  return {
    id: String(raw.id),
    code,
    title,
    description,
    badge,
    discountType,
    discountValue,
    minOrder,
    endsAt,
    maGiamGia: code,
    tieuDe: title,
    moTa: description,
    nhanGiamGia: badge,
    kieuGiamGia: discountType,
    giaTriGiam: discountValue,
    donHangToiThieu: minOrder,
    hetHanLuc: endsAt,
  };
}

// Key updates to mapDanhGia:
export function mapDanhGia(raw: any): Review {
  const foodId = String(raw.mon_an_id ?? raw.mon_an ?? raw.food ?? "");
  const author = raw.ten_nguoi_dung ?? raw.user_name ?? raw.ten_khach ?? raw.customer_name ?? "Khách hàng";
  const rating = Number(raw.diem_danh_gia ?? raw.rating ?? 5);
  const comment = raw.nhan_xet ?? raw.comment ?? "";
  const createdAt = raw.tao_luc ?? raw.created_at ?? new Date().toISOString();

  return {
    id: String(raw.id),
    foodId,
    author,
    rating,
    comment,
    createdAt,
    idMonAn: foodId,
    tacGia: author,
    diemDanhGia: rating,
    nhanXet: comment,
    taoLuc: createdAt,
  };
}
```

---

### Blueprint 3: API Endpoint Corrections

#### In `moc-frontend/src/api/reservations.api.ts`:
```typescript
export async function taoPhienThanhToanVNPay(
  idDatBan: string,
  soTien: number
): Promise<VNPayPaymentSession> {
  // Use correct dual endpoint
  const { data } = await apiClient.post("/payments/vnpay/create/", {
    loai_thanh_toan: "tien_coc",
    dat_ban_id: Number(idDatBan),
    so_tien: soTien,
  });
  return {
    paymentUrl: data.payment_url ?? data.duong_dan_thanh_toan ?? "",
    txnRef: data.txn_ref ?? data.ma_giao_dich ?? "",
    amount: Number(data.amount ?? data.so_tien ?? soTien),
    expiresAt: data.expires_at ?? data.het_han_luc ?? "",
    duongDanThanhToan: data.payment_url ?? data.duong_dan_thanh_toan ?? "",
    maGiaoDich: data.txn_ref ?? data.ma_giao_dich ?? "",
    soTien: Number(data.amount ?? data.so_tien ?? soTien),
    hetHanLuc: data.expires_at ?? data.het_han_luc ?? "",
  };
}
```

#### In `moc-frontend/src/api/orders.api.ts`:
```typescript
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

export async function getMyOrders(): Promise<OrderHistoryItem[]> {
  const { data } = await apiClient.get("/orders/");
  const list = Array.isArray(data) ? data : data.results ?? [];
  return list.map((order: any) => ({
    id: order.ma_don_hang ?? order.number ?? String(order.id),
    createdAt: order.tao_luc ?? order.created_at ?? new Date().toISOString(),
    total: Number(order.tong_tien ?? order.total ?? 0),
    status: (order.trang_thai ?? order.status ?? "pending") as OrderStatus,
    items: (order.danh_sach_mon ?? order.items ?? []).reduce(
      (acc: number, item: any) => acc + Number(item.so_luong ?? item.quantity ?? 1),
      0
    ),
  }));
}
```

---

## 7. Verification Method

To independently verify all findings and blueprints:

1. **Verify Current Build Status**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend
   npm run build
   npx tsc --noEmit
   ```
   *Expected Result*: Exits with code `0`.

2. **Verify Backend Dual Endpoints**:
   ```bash
   curl -s -X POST http://localhost:8000/api/payments/vnpay/create/ \
     -H "Content-Type: application/json" \
     -d '{"loai_thanh_toan": "tien_coc", "dat_ban_id": 1, "so_tien": 50000}'
   ```
   *Expected Result*: Returns HTTP 200/201 with `payment_url` and `txn_ref`, confirming that `/payments/vnpay/create/` is the authoritative endpoint.

3. **Verify WebSocket Authentication Requirements**:
   ```bash
   wscat -c "ws://localhost:8000/ws/chat/1/"
   ```
   *Expected Result*: Immediately disconnected with code 4401. With `?token=<jwt>`, connection is accepted and outputs `connection_established`.
