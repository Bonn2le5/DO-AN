# Báo Cáo Điều Tra Toàn Diện: Frontend & Admin UI (moc-frontend)

**Người thực hiện**: Frontend & Admin UI Explorer (Subagent Survey 2)  
**Mục tiêu**: Điều tra toàn diện `moc-frontend` (Vite + React 19 + TypeScript + Tailwind CSS v4), cấu trúc định tuyến, tình trạng lỗi biên dịch TypeScript, đối soát các lời gọi API REST với Django backend, hiện trạng WebSocket trong `ChatWidget.tsx` và trang theo dõi đơn hàng, khảo sát các giao diện Quản trị/Nhân viên (Admin/Staff) theo yêu cầu R5, và lập kế hoạch khắc phục chi tiết cho Milestone 5.

---

## 1. Observation (Các Quan Sát Thực Tế & Bằng Chứng Trực Tiếp)

### 1.1. Cấu hình Dự án & Trạng thái Build (`npm run build`)
- **Loại hình dự án**: `moc-frontend` là Single Page Application (SPA) xây dựng trên nền **Vite v8.2.0** + **React v19.2.8** + **TypeScript ~6.0.2** + **Tailwind CSS v4.3.3** (`@tailwindcss/vite`), định tuyến bằng **React Router v7.18.2** (xem `/Users/VuVan/Documents/DO-AN/moc-frontend/package.json` dòng 12–41). Không phải Next.js.
- **Thư mục `node_modules` ban đầu**: Không tồn tại (`ls: /Users/VuVan/Documents/DO-AN/moc-frontend/node_modules: No such file or directory`). Lệnh `npm run build` ban đầu thoát mã `127: sh: tsc: command not found`.
- **Cài đặt dependencies**: Chạy `npm ci` thành công trong 5s, nạp đủ 102 packages từ `package-lock.json` không gặp lỗi xung đột package.
- **Lỗi biên dịch TypeScript**: Chạy `npx tsc -b --pretty false` trả về mã lỗi 2 với **175 lỗi TypeScript trên 44 files nguồn**. Phân bố lỗi cụ thể:
  - `src/pages/reservation/ReservationPage.tsx`: **49 lỗi** (TS2339 - các thuộc tính `step`, `option`, `date`, `time`, `partySize`, `tables`, `foodItems`, `submitContact`, `reservation`, `paymentSession` không tồn tại trên hook).
  - `src/components/cart/CartDrawer.tsx`: **11 lỗi** (TS2339 - các thuộc tính `items`, `isDrawerOpen`, `closeDrawer`, `subtotal`, `discount`, `total`, `applyPromo`, `updateQuantity`, `removeItem` không tồn tại trên `useCartStore`).
  - `src/data/mock.ts`: **8 lỗi** (TS2305 - không tìm thấy các kiểu `Food`, `ComboItem`, `Review`, `RestaurantTable`, `Promotion`, `BlogPost`, `Recommendation`, `Branch` trong `@/types`).
  - `src/pages/checkout/CheckoutPage.tsx`: **6 lỗi** (`items`, `subtotal`, `discount`, `total`, `appliedPromo`, `clearCart`).
  - `src/api/mappers.ts`: **5 lỗi** (`MonAn`, `BanAn`, `ThongTinDatBan`, `KhuyenMai`, `DanhGiaMonAn`, `BaiVietBlog`, `GoiYMonAn` do ép kiểu không tương thích).
  - `src/pages/home/sections/AIRecommendationSection.tsx`: **5 lỗi** (không tìm thấy hàm `getRecommendations`).
  - `src/pages/home/sections/CategorySection.tsx`: **5 lỗi** (không tìm thấy hàm `getCategories`).
  - `src/pages/reservation/FoodStep.tsx`: **5 lỗi** (không tìm thấy kiểu `ReservationFoodItem`, `Food` và hàm `getFoods`).
  - `src/pages/food-detail/RelatedFoods.tsx`: **5 lỗi**.
  - `src/components/layout/Header.tsx`: **4 lỗi** (`itemCount`, `openDrawer`, `isAuthenticated`, `user.name`).
  - `src/hooks/useMenuFilters.ts`: **4 lỗi** (`Food`, `FoodCategory`, `getFoods`).
  - `src/pages/menu/MenuFilters.tsx`: **4 lỗi**.
  - `src/pages/food-detail/FoodDetailPage.tsx`: **4 lỗi** (`getFoodBySlug`).
  - `src/pages/account/AccountFavoritesPage.tsx`: **4 lỗi**.
  - `src/components/layout/AccountLayout.tsx`: **3 lỗi** (`user.avatarInitial`, `user.name`, `logout`).
  - `src/components/layout/AdminGuard.tsx`: **3 lỗi** (`isAuthenticated`, `user.roles`, `user.isStaff`).
  - `src/pages/home/sections/BestSellerSection.tsx`: **3 lỗi** (`getBestSellers`).
  - `src/pages/home/sections/ComboSection.tsx`: **3 lỗi** (`getCombos`).
  - `src/pages/reservation/ContactStep.tsx`: **3 lỗi** (`RestaurantTable`, `ReservationOption`).
  - `src/pages/food-detail/FoodPurchasePanel.tsx`: **3 lỗi** (`Food`).
  - `src/components/layout/AdminLayout.tsx`: **2 lỗi** (`user.avatarInitial`, `logout`).
  - `src/components/food/FoodCard.tsx`: **2 lỗi** (`Food`, `addItem`).
  - `src/pages/checkout/OrderSummary.tsx`: **2 lỗi** (`CartItem`, `Promotion`).
  - `src/pages/location/BranchList.tsx`, `DirectionsMap.tsx`, `LocationPage.tsx`: **mỗi file 2 lỗi** (`Branch`, `RouteInfo`).
  - `src/api/orders.api.ts`: **2 lỗi** (`CartItem`, `OrderStatus`).
  - `src/api/promotions.api.ts`: **2 lỗi** (`Promotion`).
  - `src/api/reviews.api.ts`: **2 lỗi** (`Review`).
  - `src/api/blog.api.ts`: **2 lỗi** (`BlogPost`).
  - `src/api/locations.api.ts`: **2 lỗi** (`Branch`, `RouteInfo`).
  - `src/pages/reservation/ReservationStepper.tsx`, `ReservationSuccess.tsx`, `PaymentStep.tsx`: **mỗi file 2 lỗi**.
  - `src/pages/reservation/TablePicker.tsx`, `TableStep.tsx`, `OptionStep.tsx`: **mỗi file 1–2 lỗi**.
  - `src/pages/auth/LoginPage.tsx`: **1 lỗi** (`useAuthStore(s => s.login)`).
  - `src/pages/auth/RegisterPage.tsx`: **1 lỗi** (`useAuthStore(s => s.login)`).
  - `src/pages/account/AccountOrdersPage.tsx`: **1 lỗi** (`OrderStatus`).
  - `src/pages/account/AccountProfilePage.tsx`: **1 lỗi** (`user`).
  - `src/pages/menu/MenuResults.tsx`: **1 lỗi** (`Food`).
  - `src/data/mockOrders.ts`: **1 lỗi** (`OrderStatus`).
  - `src/api/auth.api.ts`: **1 lỗi** (`import("@/types").UserRole`).

---

### 1.2. Đối Soát Toàn Diện Các Endpoint API: Frontend vs Backend Django

Căn cứ định nghĩa URL backend tại `/Users/VuVan/Documents/DO-AN/moc-backend/api/urls.py` và các ViewSet tương ứng, kết quả đối chiếu chi tiết như sau:

| STT | File Frontend | Hàm / Hành động | Endpoint Frontend Gọi | Endpoint Backend Thực Tế | Hiện Trạng & Xung Đột |
|:---:|---|---|---|---|---|
| 1 | `api/foods.api.ts:18` | `layDanhSachMonAn` | `GET /api/mon-an/?...` | `GET /api/foods/?...` | **SAI ĐƯỜNG DẪN**: Backend router đăng ký `router.register("foods", MonAnViewSet)`. `/api/mon-an/` trả về 404. Ngoài ra dùng `fetch` trần thay vì `apiClient`. |
| 2 | `api/foods.api.ts:29` | `layChiTietMonAn` | `GET /api/mon-an/${slug}/` | `GET /api/foods/${duong_dan}/` | **SAI ĐƯỜNG DẪN**: Phải là `/api/foods/${slug}/`. |
| 3 | `api/foods.api.ts` | `getFoods`, `getFoodBySlug`, `getBestSellers`, `getCombos`, `getCategories` | Không có hàm | `GET /api/foods/`, `GET /api/categories/` | **THIẾU HÀM EXPORT**: Các trang `MenuPage`, `HomePage`, `FoodDetailPage`, `FoodStep` đều gọi các hàm này nhưng file không export. |
| 4 | `api/orders.api.ts:21` | `createOrder` | `POST /orders/` | `POST /api/orders/` | **SAI PAYLOAD**: Frontend gửi `{ items: [{ food_id, quantity }], order_type, payment_method, customer_name, phone }`. Backend `DonHangSerializer` yêu cầu `{ danh_sach_mon: [{ mon_an_id, so_luong }], ma_khuyen_mai }`. Frontend mong đợi nhận `{ orderId: data.number }` nhưng backend trả về `{ ma_don_hang: ... }`. |
| 5 | `api/orders.api.ts:32` | `getMyOrders` | `GET /orders/` | `GET /api/orders/` | **SAI TRƯỜNG DỮ LIỆU**: Frontend map `order.number`, `order.created_at`, `order.total`, `order.items`. Backend trả về `order.ma_don_hang`, `order.tao_luc`, `order.tong_tien`, `order.danh_sach_mon`. |
| 6 | `api/reservations.api.ts:13` | `layDanhSachBan` | `GET /api/dat-ban/ban-an/` | `GET /api/tables/` | **SAI ĐƯỜNG DẪN**: Backend router là `router.register("tables", BanAnViewSet)`. `/api/dat-ban/ban-an/` không tồn tại. |
| 7 | `api/reservations.api.ts:42` | `giuBan` | `POST /api/dat-ban/giu-ban/` | `POST /api/tables/{id}/giu_ban/` | **SAI KIỂU ROUTE**: Backend thiết kế `giu_ban` là detail action `@action(detail=True)` trên `BanAnViewSet`, URL là `/api/tables/{id}/giu_ban/`. |
| 8 | `api/reservations.api.ts:69` | `taoDatBan` | `POST /api/dat-ban/` | `POST /api/reservations/` | **SAI ĐƯỜNG DẪN**: Backend router là `router.register("reservations", DatBanViewSet)`. |
| 9 | `api/reservations.api.ts:22` | `layChinhSachDatCoc` | Hardcoded local object | `GET /api/reservations/chinh_sach_coc/` | Backend đã có action động trả về `ChinhSachCocSerializer`, frontend lại tự hardcode tĩnh. |
| 10 | `api/reservations.api.ts:113` | `taoPhienThanhToanVNPay` | `POST /api/thanh-toan/vnpay/tao-phien/` | `POST /api/payments/` hoặc endpoint VNPay | **SAI ĐƯỜNG DẪN**: Endpoint `/api/thanh-toan/...` không có trong backend. |
| 11 | `api/recommendations.api.ts:6` | `layGoiYMonAn` | `GET /api/goi-y/?gioi_han=6` | `GET /api/recommendations/` | **SAI ĐƯỜNG DẪN**: Backend đăng ký `router.register("recommendations", RecommendationViewSet)`. Thiếu export `getRecommendations`. |
| 12 | `api/auth.api.ts:18` | `login` | `POST /auth/login/` | `POST /api/auth/login/` | Khớp route qua baseURL `/api`, nhưng trả về `access`, `refresh`. |
| 13 | `api/auth.api.ts:20` | `login` (lấy profile) | `GET /auth/profile/` | `GET /api/auth/ho_so/` | **SAI ĐƯỜNG DẪN**: Backend action lấy thông tin user là `@action ho_so` thuộc `XacThucViewSet`. |
| 14 | `api/auth.api.ts:24` | `register` | `POST /auth/register/` | `POST /api/auth/dang_ky/` | **SAI ĐƯỜNG DẪN & PAYLOAD**: Backend action đăng ký là `@action dang_ky` (`/api/auth/dang_ky/`). Payload backend yêu cầu `{ thu_dien_tu, mat_khau, ho_ten, so_dien_thoai }`, frontend gửi `{ email, password, name, phone }`. |
| 15 | `api/locations.api.ts:5` | `getBranches` | `GET /branches/` | `GET /api/branches/` | Khớp route. Cần đồng bộ trường `latitude`/`kinh_do`, `longitude`/`vi_do`. |
| 16 | `api/promotions.api.ts:6` | `getPromotions` | `GET /promotions/?active=true` | `GET /api/promotions/?active=true` | Khớp route. |
| 17 | `api/reviews.api.ts:6` | `getReviewsByFood` | `GET /reviews/?food={id}` | `GET /api/reviews/?food={id}` | Khớp route. |
| 18 | `api/blog.api.ts:6,11` | `getBlogPosts`, `getBlogPostBySlug` | `GET /posts/`, `GET /posts/{slug}/` | `GET /api/posts/`, `GET /api/posts/{slug}/` | Khớp route qua `PostViewSet`. |

---

### 1.3. Khảo Sát Hiện Trạng Các Giao Diện Admin & Staff (Yêu cầu R5)

Kiểm tra thư mục `src/pages/admin/`, `src/components/admin/`, và định tuyến tại `src/App.tsx`:

1. **Thư mục `src/components/admin/`**:
   - Hoàn toàn **RỖNG** (0 file, 0 bytes).
2. **Định tuyến Admin trong `src/App.tsx` (dòng 36–43)**:
   ```tsx
   <Route path="/admin" element={<AdminGuard />}>
     <Route element={<AdminLayout />}>
       <Route index element={<AdminDashboardPage />} />
       <Route path="orders" element={<AdminOrdersPage />} />
       <Route path="reservations" element={<div className="p-4 font-bold text-gray-500">Đang phát triển: Quản lý đặt bàn</div>} />
       <Route path="menu" element={<div className="p-4 font-bold text-gray-500">Đang phát triển: Quản lý thực đơn</div>} />
     </Route>
   </Route>
   ```
3. **Menu Sidebar tại `src/components/layout/AdminLayout.tsx` (dòng 8–13)**:
   - Chỉ có 4 mục: Tổng quan (`/admin`), Đơn hàng (`/admin/orders`), Đặt bàn (`/admin/reservations`), Thực đơn (`/admin/menu`).
   - **HOÀN TOÀN THIẾU**: Quản lý Đánh giá (`/admin/reviews`) và Giao diện Chat của nhân viên (`/admin/chat`).
4. **Trang `AdminDashboardPage.tsx`**:
   - 100% dữ liệu cứng tĩnh: "0 đơn hàng hôm nay", "0 khách đặt bàn", "0 đ doanh thu", "Biểu đồ đang cập nhật...".
   - Không hề gọi API thống kê `/api/analytics/dashboard/` của backend.
5. **Trang `AdminOrdersPage.tsx`**:
   - Gọi `getMyOrders()` (API của khách hàng cá nhân) thay vì API quản trị đơn hàng toàn hệ thống.
   - Thanh tìm kiếm và bộ lọc trạng thái chưa có `onChange` hay logic xử lý.
   - Nút "+ Đơn mới" và nút "Chi tiết" không có handler.
   - Hoàn toàn thiếu hành động chuyển đổi trạng thái đơn hàng theo FSM (`cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat`/`da_huy`) thông qua API `PATCH /api/orders/{id}/trang_thai/`.
6. **Trang Quản lý Bàn ăn & Đặt bàn (`/admin/reservations`)**:
   - Đang là placeholder `<div>Đang phát triển: Quản lý đặt bàn</div>`.
   - Chưa có sơ đồ/danh sách bàn ăn (`BanAn`), chưa có bảng lịch đặt bàn (`DatBan`), chưa có nút chuyển trạng thái tiếp nhận khách, xác nhận cọc hay hủy bàn.
7. **Trang Quản lý Thực đơn & Kho nguyên liệu (`/admin/menu`)**:
   - Đang là placeholder `<div>Đang phát triển: Quản lý thực đơn</div>`.
   - Chưa có danh sách món ăn, tạo/sửa món, bật/tắt còn hàng (`con_hang`), chưa có danh sách nguyên liệu kho (`/api/ingredients/`) và lịch sử nhập/xuất kho (`/api/inventory-transactions/`).
8. **Trang Quản lý Đánh giá (`/admin/reviews`)**:
   - Chưa tồn tại cả route lẫn component. Chưa có tính năng kiểm duyệt/ẩn hiện đánh giá (`is_visible`) qua `/api/reviews/`.
9. **Giao diện Chat của nhân viên (`/admin/chat`)**:
   - Chưa tồn tại cả route lẫn component. Chưa có danh sách phòng chat (`/api/chat/rooms/`) và khung chat hỗ trợ khách hàng theo thời gian thực.

---

### 1.4. Hiện Trạng Tích Hợp WebSocket trong `ChatWidget.tsx` & Theo Dõi Đơn Hàng

1. **Khách hàng Chat (`src/components/chat/ChatWidget.tsx`)**:
   - Dòng 15–19 ghi rõ:
     ```tsx
     /**
      * TODO(backend): connect to ws://<host>/ws/chat/<conversation_id>/ once
      * Django Channels + Redis channel layer is available. For now this renders
      * the full UI (unread badge, message list, input) against local state only.
      */
     ```
   - Dòng 33–44: Sử dụng `setTimeout(..., 900)` để sinh tin nhắn giả lập từ "Nhà hàng".
   - Hoàn toàn chưa khởi tạo đối tượng `WebSocket`, không có cơ chế truyền JWT Token, không lưu trữ phòng chat hay kết nối tới ASGI Channels.
2. **Theo dõi đơn hàng thời gian thực (Order Tracking)**:
   - Trang sau khi đặt hàng thành công (`OrderSuccessPage.tsx`) sinh mã ngẫu nhiên `MC + Math.random()` và dẫn link về `/tai-khoan/don-hang`.
   - Trang `AccountOrdersPage.tsx` chỉ thực hiện fetch tĩnh danh sách đơn hàng 1 lần bằng `useAsync(getMyOrders)`.
   - Hoàn toàn **chưa có kết nối WebSocket** đến kênh đơn hàng (`ws://<host>/ws/orders/<order_id>/`).
   - Không có giao diện hiển thị tiến trình FSM 5 bước chuyển đổi trạng thái đơn hàng tự động mà không cần reload trang.

---

## 2. Logic Chain (Chuỗi Lập Luận Từ Quan Sát Đến Kết Luận)

1. **Nguyên nhân gốc rễ của 175 lỗi TypeScript**:
   - *Bước 1*: Khi tiến hành chuẩn hóa tên tiếng Việt theo schema `moc_schema_tieng_viet.sql`, người phát triển trước đã đổi tên các kiểu dữ liệu trong `src/types/index.ts` thành `MonAn`, `BanAn`, `DonHang`, `ThongTinDatBan`, `NguoiDung`, v.v.
   - *Bước 2*: Đồng thời, người phát triển trước cũng sửa tên hàm/biến trong 3 file: `src/store/authStore.ts` (đổi `user` → `nguoiDung`, `login` → `dangNhap`), `src/store/cartStore.ts` (đổi `items` → `danhSachMon`, `addItem` → `themMon`), và `src/hooks/useReservationFlow.ts` (đổi `step` → `buocHienTai`, `tables` → `danhSachBan`).
   - *Bước 3*: Tuy nhiên, hơn **40 component giao diện** của khách hàng (`FoodCard`, `CartDrawer`, `Header`, `FoodDetailPage`, `useMenuFilters`, `mock.ts`, v.v.) và toàn bộ file `ReservationPage.tsx` cùng các sub-step (`TableStep`, `FoodStep`, `ContactStep`, `PaymentStep`) **vẫn được viết bằng các định danh tiếng Anh cũ** (`Food`, `RestaurantTable`, `ReservationOption`, `items`, `addItem`, `subtotal`, `user`, `login`, `step`, v.v.).
   - *Bước 4*: Do `src/types/index.ts` không còn export các kiểu tiếng Anh, và các store không còn export các getter/action tiếng Anh, TypeScript compiler báo lỗi `TS2305` (missing export) và `TS2339` (missing property) hàng loạt tại mọi điểm tiêu thụ dữ liệu.
   - *Kết luận*: Cần áp dụng giải pháp Kiến trúc Adapter hai chiều (Dual-Interface / Aliases): `src/types/index.ts` và các Store/Hook phải cung cấp cả hai bộ định danh (hoặc alias tương thích 100%) để vừa thỏa mãn schema chuẩn hóa tiếng Việt, vừa tương thích nguyên vẹn với toàn bộ cây giao diện hiện tại mà không phải đập bỏ viết lại hàng chục nghìn dòng code JSX.

2. **Nguyên nhân của các lỗi gọi API không thành công (HTTP 404 / 400)**:
   - Các file API service (`foods.api.ts`, `reservations.api.ts`, `recommendations.api.ts`) được sửa vội vàng sang các đường dẫn giả định bằng tiếng Việt (`/api/mon-an/`, `/api/dat-ban/`, `/api/goi-y/`).
   - Trong khi đó, file Router trung tâm của Django backend (`moc-backend/api/urls.py`) đăng ký các endpoint chuẩn RESTful chuẩn quốc tế: `/api/foods/`, `/api/tables/`, `/api/reservations/`, `/api/recommendations/`, `/api/orders/`, `/api/payments/`.
   - Kết luận: Tất cả API service callers trong frontend cần được nắn lại chính xác 100% khớp với `moc-backend/api/urls.py`. `mappers.ts` sẽ đóng vai trò cầu nối chuyển đổi giữa format JSON backend và view model frontend.

3. **Nguyên nhân khiếm khuyết trong Giao diện Quản trị (Admin) và WebSocket**:
   - Dự án mới chỉ xây dựng khung sườn sơ khai cho Admin (`AdminLayout` và bảng đơn hàng dạng demo). Các tính năng nghiệp vụ cốt lõi theo đề cương (Quản lý Bàn & Đặt bàn với Concurrency, Quản lý Menu & Kho nguyên liệu, Quản lý Đánh giá, Quản lý Chat) chưa từng được hiện thực hóa trên frontend.
   - Tương tự, WebSocket trong `ChatWidget.tsx` chỉ là bản mockup UI bằng state nội bộ và `setTimeout`, hoàn toàn chưa có kênh truyền dữ liệu thật.

---

## 3. Caveats (Các Điểm Giới Hạn & Giả Định)

1. **Quyền hạn điều tra**: Theo nguyên tắc của vai trò Explorer, quá trình này là **Read-Only** (không sửa trực tiếp mã nguồn trong `moc-frontend` hay `moc-backend`). Toàn bộ đề xuất kỹ thuật được chuẩn hóa để chuyển giao cho Implementer tại Milestone 5.
2. **Môi trường Backend khi chạy thử**: Lệnh `npm run build` chỉ kiểm tra tính hợp lệ tĩnh của TypeScript và build bundle của Vite, không phụ thuộc vào việc backend Django hay Redis có đang chạy hay không. Tuy nhiên, việc kiểm thử end-to-end các luồng API và WebSocket sẽ cần backend hoàn thành các Milestone 1–4.
3. **Thư viện bản đồ Leaflet**: `LocationPage.tsx` sử dụng OSRM demo công cộng (`https://router.project-osrm.org`) để vẽ tuyến đường lái xe. Phương án này phù hợp với đồ án tốt nghiệp / demo, không yêu cầu API key tốn phí.

---

## 4. Conclusion (Kết Luận & Đánh Giá Tổng Thể)

1. **Về Build & Biên dịch**: `moc-frontend` hiện **chưa thể build thành công** (175 lỗi TypeScript). Sau khi khắc phục triệt để bằng việc mở rộng `src/types/index.ts` (export thêm các kiểu/alias tiếng Anh: `Food`, `RestaurantTable`, `ReservationOption`, `Reservation`, `OrderStatus`, `Branch`, `User`, v.v.), khôi phục backward compatibility cho `authStore`, `cartStore`, `useReservationFlow`, và bổ sung các hàm export còn thiếu trong `foods.api.ts`, `recommendations.api.ts`, lệnh `npm run build` sẽ pass 100% không còn một lỗi nào.
2. **Về API Service Callers**: Cần sửa lại toàn bộ URL trong `foods.api.ts`, `reservations.api.ts`, `recommendations.api.ts`, `auth.api.ts`, `orders.api.ts` để trỏ đúng vào backend Django (`/api/foods/`, `/api/tables/`, `/api/reservations/`, `/api/recommendations/`, `/api/auth/dang_ky/`, `/api/auth/ho_so/`), đồng thời đồng bộ payload request/response trong `orders.api.ts`.
3. **Về Giao diện Admin/Staff**: Cần xây dựng mới 4 trang hoàn chỉnh và nâng cấp 2 trang hiện có:
   - Nâng cấp `AdminDashboardPage`: kết nối API `GET /api/analytics/dashboard/`.
   - Nâng cấp `AdminOrdersPage`: thêm bộ lọc, modal xem chi tiết món ăn trong đơn, và nút cập nhật trạng thái đơn hàng theo FSM.
   - Xây dựng mới `AdminReservationsPage`: quản lý sơ đồ bàn (`BanAn`) và danh sách đặt bàn (`DatBan`).
   - Xây dựng mới `AdminMenuPage`: quản lý món ăn (`MonAn`) và tồn kho nguyên liệu (`NguyenLieu`, `LichSuXuatNhapKho`).
   - Xây dựng mới `AdminReviewsPage`: kiểm duyệt và ẩn/hiện đánh giá món ăn (`Review`).
   - Xây dựng mới `AdminChatPage`: giao diện nhân viên tư vấn khách hàng trực tiếp qua WebSocket/API.
   - Bổ sung các route và menu sidebar tương ứng trong `App.tsx` và `AdminLayout.tsx`.
4. **Về WebSocket**:
   - Xây dựng hook `useWebSocket` hoặc `useChatSocket` dùng chuẩn Native WebSocket của trình duyệt, kết nối `ws://localhost:8000/ws/chat/<room_id>/?token=<jwt>` trong `ChatWidget.tsx` và `AdminChatPage`.
   - Xây dựng component/hook theo dõi vòng đời đơn hàng theo thời gian thực (`OrderLiveTracking`) gắn vào `AccountOrdersPage` và trang thành công của đơn hàng.

---

## 5. Kế Hoạch Khắc Phục Chi Tiết Cho Milestone 5 (Remediation Plan)

### Giai đoạn 5.1: Xóa Bỏ Triệt Để 175 Lỗi TypeScript & Chuẩn Hóa Type Layer (P0)
1. **File `src/types/index.ts`**:
   - Giữ nguyên toàn bộ schema tiếng Việt hiện tại (`MonAn`, `BanAn`, `DonHang`, `ThongTinDatBan`, v.v.).
   - Định nghĩa và export đầy đủ các interface và type aliases mà UI đang sử dụng:
     - `Food` (với các trường: `id`, `name`, `slug`, `category`, `categoryLabel`, `price`, `description`, `longDescription`, `ingredients`, `tags`, `spicyLevel`, `isVegetarian`, `rating`, `reviewCount`, `available`, `stock`, `badge`, `placeholderTone`, `createdAt`).
     - `FoodCategory = "main" | "appetizer" | "drink" | "dessert" | "combo"`.
     - `ComboItem`, `Review`, `Promotion`, `BlogPost`, `Recommendation`, `Branch`, `RouteInfo`.
     - `RestaurantTable` (với `status`: `"available" | "held" | "reserved" | "occupied" | "maintenance"`, `capacity`, `number`, `zone`).
     - `ReservationOption = "table_only" | "table_and_food" | "table_and_food_editable"`.
     - `ReservationFoodItem = { food: Food; quantity: number }`.
     - `Reservation = { id, tableId, tableLabel, date, time, partySize, customerName, phone, note, option, foodItems, foodSubtotal, depositAmount, status, paymentStatus, createdAt }`.
     - `VNPayPaymentSession = { paymentUrl, txnRef, amount, expiresAt }`.
     - `OrderStatus = "pending" | "confirmed" | "preparing" | "ready" | "completed" | "cancelled"`.
     - `CartItem = { food: Food; quantity: number; note?: string }`.
     - `UserRole = "customer" | "staff" | "admin"`, `User = { id, name, email, phone, avatarInitial, roles, isStaff }`.
2. **File `src/store/authStore.ts`**:
   - Hỗ trợ cả 2 chuẩn getter/setter: `{ user, isAuthenticated, login, logout, nguoiDung, daDangNhap, dangNhap, dangXuat }`.
3. **File `src/store/cartStore.ts`**:
   - Hỗ trợ song song các phương thức tiếng Anh và tiếng Việt: `items` / `danhSachMon`, `addItem` / `themMon`, `removeItem` / `xoaMon`, `updateQuantity` / `capNhatSoLuong`, `clearCart` / `lamTrongGio`, `subtotal` / `tinhTienHang`, `discount` / `tinhTienGiam`, `total` / `tinhTongTien`, `itemCount` / `demSoMon`, `isDrawerOpen` / `nganKeoMo`, `openDrawer` / `moNganKeo`, `closeDrawer` / `dongNganKeo`, `appliedPromo` / `khuyenMaiApDung`, `applyPromo` / `apDungKhuyenMai`.
4. **File `src/hooks/useReservationFlow.ts`**:
   - Cung cấp đầy đủ các property tiếng Anh mà `ReservationPage.tsx` gọi: `step`, `setStep`, `option`, `chooseOption`, `date`, `setDate`, `time`, `setTime`, `partySize`, `setPartySize`, `tables`, `tablesLoading`, `selectedTableId`, `selectedTable`, `holdLoading`, `holdError`, `holdInfo`, `selectTable`, `proceedAfterTable`, `foodItems`, `addFood`, `updateFoodQty`, `foodSubtotal`, `depositAmount`, `submitting`, `submitContact`, `reservation`, `paymentSession`, `simulatePaymentSuccess`, `reset`.
5. **Kiểm tra**: Chạy `npm run build` xác nhận số lỗi giảm về 0.

### Giai đoạn 5.2: Khắc Phục Toàn Diện API Callers & Payload Mappers (P1)
1. **File `src/api/foods.api.ts`**:
   - Chuyển toàn bộ sang dùng `apiClient`.
   - Đổi URL sang `/foods/` (hoặc `/foods/${slug}/`).
   - Export đầy đủ: `getFoods`, `getFoodBySlug`, `getBestSellers`, `getCombos`, `getCategories` (gọi `/categories/`).
2. **File `src/api/reservations.api.ts`**:
   - `layDanhSachBan` & `getTables`: gọi `GET /tables/`.
   - `giuBan` & `holdTable`: gọi `POST /tables/${id}/giu_ban/`.
   - `taoDatBan` & `createReservation`: gọi `POST /reservations/`.
   - `layChinhSachDatCoc`: gọi `GET /reservations/chinh_sach_coc/`.
3. **File `src/api/recommendations.api.ts`**:
   - Đổi URL gọi `GET /recommendations/`. Export cả `layGoiYMonAn` và `getRecommendations`.
4. **File `src/api/auth.api.ts`**:
   - Đổi `profile` thành `GET /auth/ho_so/`.
   - Đổi `register` thành `POST /auth/dang_ky/` với payload `{ thu_dien_tu, mat_khau, ho_ten, so_dien_thoai }`.
5. **File `src/api/orders.api.ts`**:
   - Điều chỉnh mapper cho `createOrder`: gửi đúng trường `{ danh_sach_mon: [...], ma_khuyen_mai }`.
   - Xử lý response đọc `data.ma_don_hang`.
   - Mapper `getMyOrders`: đọc `ma_don_hang`, `tong_tien`, `trang_thai`, `tao_luc`.

### Giai đoạn 5.3: Hoàn Thiện Các Giao Diện Quản Trị Admin/Staff (P1)
1. **Cập nhật `AdminLayout.tsx` & `App.tsx`**:
   - Thêm đầy đủ 6 menu navigation: Tổng quan, Đơn hàng, Đặt bàn, Thực đơn & Kho, Đánh giá, Live Chat.
   - Khai báo các Route tương ứng trong `App.tsx` dưới `AdminGuard`.
2. **Hoàn thiện `AdminDashboardPage.tsx`**:
   - Gọi API `GET /api/analytics/dashboard/` lấy doanh thu thực tế, số đơn, số lượt đặt bàn, số khách hàng, và phân bố trạng thái đơn hàng.
3. **Hoàn thiện `AdminOrdersPage.tsx`**:
   - Hiển thị danh sách đơn toàn nhà hàng; thanh lọc theo mã đơn, SĐT, trạng thái FSM.
   - Thêm Drawer/Modal hiển thị chi tiết món ăn trong đơn.
   - Thêm nút thao tác đổi trạng thái: Xác nhận (`da_xac_nhan`), Bắt đầu chế biến (`dang_che_bien`), Sẵn sàng giao (`san_sang`), Hoàn tất (`hoan_tat`), Hủy đơn (`da_huy`) gọi `PATCH /api/orders/{id}/trang_thai/`.
4. **Xây dựng mới `AdminReservationsPage.tsx`**:
   - Tab 1: Sơ đồ bàn ăn (Bàn số, Sức chứa, Khu vực, Trạng thái: Trống, Đang giữ chỗ, Đã đặt, Bảo trì). Có nút đổi trạng thái bảo trì/trống.
   - Tab 2: Danh sách phiếu đặt bàn (Khách hàng, Giờ đến, Bàn, Tiền cọc, Trạng thái cọc). Có nút xác nhận khách đã đến hoặc hủy đặt bàn.
5. **Xây dựng mới `AdminMenuPage.tsx`**:
   - Tab 1: Quản lý món ăn (Danh sách món, danh mục, giá bán, nút toggle `con_hang`, form thêm/sửa món).
   - Tab 2: Quản lý kho nguyên liệu (Danh sách nguyên liệu `/api/ingredients/`, số lượng tồn, đơn vị tính, cảnh báo sắp hết, form ghi nhận phiếu nhập/xuất kho `/api/inventory-transactions/`).
6. **Xây dựng mới `AdminReviewsPage.tsx`**:
   - Danh sách đánh giá khách hàng (Món ăn, Người đánh giá, Điểm sao, Nội dung nhận xét, Ngày tạo).
   - Nút bật/tắt hiển thị đánh giá (`is_visible`) gọi `PATCH /api/reviews/{id}/`.
7. **Xây dựng mới `AdminChatPage.tsx`**:
   - Bên trái: Danh sách các phòng chat (`/api/chat/rooms/`), hiển thị khách hàng và tin nhắn gần nhất.
   - Bên phải: Khung hội thoại trực tiếp, hiển thị tin nhắn hai chiều giữa nhân viên và khách qua WebSocket.

### Giai đoạn 5.4: Tích Hợp Realtime WebSocket & Order Tracking (P2)
1. **Hook `useWebSocket`**:
   - Quản lý lifecycle WebSocket: kết nối tự động khi mở chat, tự động reconnect khi mất kết nối, tự gửi token xác thực JWT.
2. **Nâng cấp `ChatWidget.tsx`**:
   - Thay thế `setTimeout` giả lập bằng WebSocket client thật.
   - Gửi tin nhắn lên kênh `ws://localhost:8000/ws/chat/<room_id>/` và nhận broadcast hiển thị ngay lập tức.
3. **Realtime Order Tracking**:
   - Xây dựng component `OrderLiveTracking.tsx` kết nối kênh WebSocket trạng thái đơn hàng `ws://localhost:8000/ws/orders/<order_id>/`.
   - Hiển thị thanh tiến trình 5 bước trực quan theo FSM (`cho_tiep_nhan` → `da_xac_nhan` → `dang_che_bien` → `san_sang` → `hoan_tat`).
   - Tự động nhảy bước và hiển thị thông báo toast khi nhân viên đổi trạng thái trong Admin.

---

## 6. Verification Method (Phương Pháp Xác Minh Độc Lập)

Sau khi Implementer hoàn thành Milestone 5, người kiểm thử có thể xác minh độc lập bằng các bước sau:

1. **Xác minh Biên dịch TypeScript**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-frontend
   export PATH=$PATH:/usr/local/bin:/opt/homebrew/bin
   npm run build
   ```
   *Điều kiện thành công*: Lệnh thoát mã 0, thư mục `dist/` được tạo, không xuất hiện bất kỳ thông báo lỗi TypeScript nào (`Found 0 errors`).

2. **Xác minh Định tuyến & Giao diện Admin**:
   - Truy cập `http://localhost:5173/admin`: chuyển hướng đúng đến trang đăng nhập nếu chưa đăng nhập; hiển thị 403 nếu tài khoản không phải nhân viên/admin; hiển thị dashboard nếu là admin.
   - Kiểm tra sidebar có đủ 6 mục và bấm chuyển trang không gặp lỗi màn hình trắng (404/Crash).
   - Kiểm tra các trang `/admin/orders`, `/admin/reservations`, `/admin/menu`, `/admin/reviews`, `/admin/chat` hiển thị dữ liệu và thao tác mượt mà.

3. **Xác minh API Endpoints qua Network Tab Trình Duyệt**:
   - Mở DevTools Network:
     - Khi vào trang Thực đơn: gọi `GET /api/foods/` (200 OK).
     - Khi chọn bàn: gọi `POST /api/tables/{id}/giu_ban/` (200 OK hoặc 409 nếu bị trùng).
     - Khi tạo đặt bàn: gọi `POST /api/reservations/` (201 Created).
     - Khi đặt món: gọi `POST /api/orders/` (201 Created).

4. **Xác minh Realtime WebSocket**:
   - Mở hai cửa sổ trình duyệt: 1 bên là Khách hàng (`ChatWidget`), 1 bên là Nhân viên (`/admin/chat`).
   - Gửi tin nhắn từ phía Khách: bên Nhân viên lập tức nhận được tin nhắn mà không cần F5 trang.
   - Đổi trạng thái đơn hàng trên `/admin/orders`: màn hình khách hàng tại `/tai-khoan/don-hang` tự động cập nhật thanh FSM tức thì.
