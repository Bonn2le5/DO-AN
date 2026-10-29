# MỘC — Website quản lý đặt món nhà hàng (Frontend)

## Công nghệ sử dụng
- React 19 + TypeScript + Vite
- Tailwind CSS v4
- React Router v7 (routing)
- Zustand (state management: giỏ hàng, yêu thích, auth)
- React Hook Form + Zod (validate form)
- Lucide React (icon)

## Cài đặt & chạy thử
```bash
npm install
npm run dev       # chạy dev server tại http://localhost:5173
npm run build     # build production vào thư mục dist/
```

## Cấu trúc thư mục
```
src/
  components/
    layout/     Header, Footer, Layout, AccountLayout
    food/       FoodCard
    cart/       CartDrawer
    chat/       ChatWidget (UI chat realtime, chưa nối WebSocket)
    ui/         PlaceholderMedia, RatingStars, SectionHeading
  pages/        Các trang: Home, Menu, FoodDetail, Checkout, Reservation,
                Promotions, Blog, Login, Register, Account/*
  store/        cartStore, favoriteStore, authStore (Zustand)
  data/mock.ts  Dữ liệu giả lập — SẼ THAY BẰNG API THẬT khi nối backend
  types/        Định nghĩa TypeScript dùng chung
  lib/utils.ts  Hàm tiện ích (format tiền, format ngày...)
```

## Trạng thái hiện tại — CHƯA nối backend
Toàn bộ dữ liệu (món ăn, đơn hàng, đặt bàn, khuyến mãi, bài viết...) đang lấy
từ `src/data/mock.ts`. Các điểm cần thay bằng API thật khi làm backend Django
đều được đánh dấu bằng comment `// TODO(backend): ...` ngay tại chỗ gọi, ví dụ:
- `src/pages/CheckoutPage.tsx` → `POST /api/orders/`
- `src/pages/ReservationPage.tsx` → `POST /api/reservations/`
- `src/pages/LoginPage.tsx`, `RegisterPage.tsx` → `POST /api/auth/login|register/`
- `src/components/chat/ChatWidget.tsx` → `ws://<host>/ws/chat/<id>/` (Django Channels)

## Ảnh món ăn
Hiện đang dùng `PlaceholderMedia` (gradient màu + icon) thay cho ảnh thật.
Khi có ảnh thật từ nhà hàng, chỉ cần thay component này trong `FoodCard`,
`FoodDetailPage`, `HomePage`... bằng thẻ `<img>` trỏ tới URL ảnh từ backend.

## Kiến trúc 3 lớp (cập nhật)

Để dễ sửa lỗi và mở rộng, mỗi trang được tách thành 3 lớp tách biệt:

```
src/api/         Lớp DỮ LIỆU — mỗi resource 1 file (foods.api.ts, orders.api.ts...)
                 Hiện đang trả về mock data giả lập độ trễ mạng.
                 Khi nối backend Django: CHỈ sửa bên trong các file này,
                 không cần đụng vào page/component nào khác.

src/hooks/       Lớp LOGIC dùng lại được — useAsync (loading/error/data chuẩn hoá),
                 useMenuFilters (toàn bộ state lọc/sắp xếp của trang Menu).

src/pages/       Lớp GIAO DIỆN — mỗi trang lớn có 1 folder riêng:
                   pages/home/HomePage.tsx        -> chỉ ghép các section lại
                   pages/home/sections/*.tsx      -> mỗi section 1 file, tự fetch data riêng
                   pages/menu/MenuPage.tsx        -> ghép MenuFilters + MenuResults
                   pages/food-detail/*.tsx        -> Gallery/Purchase/Reviews/Related tách riêng
                   pages/checkout/*.tsx           -> Form + OrderSummary tách riêng
                   pages/reservation/*.tsx        -> TablePicker + Form tách riêng
```

**Quy tắc**: 1 file không vượt quá ~150 dòng. Nếu 1 page cần hiển thị nhiều
phần độc lập (section, panel, form...), mỗi phần tách ra 1 file riêng trong
folder của page đó. Muốn sửa phần nào → mở đúng file đó, không phải cuộn qua
cả trang.

**Khi nối backend**: chỉ sửa các file trong `src/api/*.ts` (thay `mockDelay(...)`
bằng `apiClient.get(...)` thật), toàn bộ `pages/` và `hooks/` giữ nguyên không đổi.
