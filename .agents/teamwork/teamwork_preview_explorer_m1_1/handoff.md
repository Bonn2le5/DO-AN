# BÁO CÁO CHIẾN LƯỢC CHUẨN HOÁ MODEL & BÍ DANH TƯƠNG THÍCH NGƯỢC (MILESTONE 1)
**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Tác giả**: Milestone 1 Explorer 1 (Models & Aliases Strategy)  
**Thời gian**: 2026-10-14T03:30:00Z  
**Đường dẫn**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_1/handoff.md`  

---

## 1. Observation (Các quan sát trực tiếp & Bằng chứng thực tế)

### 1.1. Lỗi trực tiếp khi thực thi kiểm tra Django (`manage.py check`)
Thực thi lệnh kiểm tra hệ thống trong virtualenv:
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py check
```
Kết quả trả về mã lỗi `1`:
```text
Traceback (most recent call last):
  File "/Users/VuVan/Documents/DO-AN/moc-backend/manage.py", line 22, in <module>
    main()
  File "/Users/VuVan/Documents/DO-AN/moc-backend/manage.py", line 18, in main
    execute_from_command_line(sys.argv)
  File "/Users/VuVan/Documents/DO-AN/moc-backend/.venv/lib/python3.9/site-packages/django/core/management/__init__.py", line 442, in execute_from_command_line
    utility.execute()
  File "/Users/VuVan/Documents/DO-AN/moc-backend/.venv/lib/python3.9/site-packages/django/core/management/__init__.py", line 416, in execute
    django.setup()
  File "/Users/VuVan/Documents/DO-AN/moc-backend/.venv/lib/python3.9/site-packages/django/__init__.py", line 24, in setup
    apps.populate(settings.INSTALLED_APPS)
  File "/Users/VuVan/Documents/DO-AN/moc-backend/.venv/lib/python3.9/site-packages/django/apps/registry.py", line 116, in populate
    app_config.import_models()
  File "/Users/VuVan/Documents/DO-AN/moc-backend/.venv/lib/python3.9/site-packages/django/apps/config.py", line 269, in import_models
    self.models_module = import_module(models_module_name)
  File "/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/importlib/__init__.py", line 127, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  File "<frozen importlib._bootstrap>", line 1030, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1007, in _find_and_load
  File "<frozen importlib._bootstrap>", line 986, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 680, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 850, in exec_module
  File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed
  File "/Users/VuVan/Documents/DO-AN/moc-backend/carts/models.py", line 4, in <module>
    from foods.models import TimeStampedModel, Food
ImportError: cannot import name 'Food' from 'foods.models' (/Users/VuVan/Documents/DO-AN/moc-backend/foods/models.py)
```

### 1.2. Kiểm tra `config/settings.py`
- Tại dòng 163: `AUTH_USER_MODEL = "accounts.User"`
- Trong khi đó, `accounts/models.py` định nghĩa model người dùng là `class NguoiDung(AbstractUser):` với `db_table = "nguoi_dung"`. Model `User` không tồn tại trong `accounts/models.py`.

### 1.3. Kiểm tra `accounts/admin.py`
- Dòng 4: `from .models import Role, User` (Cả hai model đều không tồn tại trong `accounts.models`).
- Dòng 7: `@admin.register(User)`
- Dòng 11: `@admin.register(Role)`
- Dòng 13: `list_display = ("name", "description", "created_at", "updated_at")`
- Dòng 14: `search_fields = ("name",)`
- Trên model `VaiTro` (`accounts/models.py:5-17`), các trường tương ứng là `ten`, `mo_ta`, `tao_luc`, `cap_nhat_luc`. Không có trường `name`, `description`, `created_at`, `updated_at`. Nếu chỉ gán `Role = VaiTro`, Django Admin System Check sẽ báo lỗi `admin.E108` vì các trường trong `list_display` không tồn tại.

### 1.4. Kiểm tra các app có model tiếng Việt nhưng views/serializers viết bằng tiếng Anh
1. **`branches`**:
   - `models.py:6`: `class ChiNhanh(MoHinhThoiGian):` (fields: `ten`, `dia_chi`, `so_dien_thoai`, `toa_do_gis`, `con_hoat_dong`). Không có `Branch`.
   - `serializers.py:2-7`: `from .models import Branch`, sử dụng các trường `name`, `address`, `phone`, `location`, `longitude`, `latitude`, `is_active`.
   - `views.py:2-10`: `from api.permissions import IsStaffOrReadOnly`, `from .models import Branch`, truy cập `request.user.is_restaurant_staff` và `Branch.objects.filter(is_active=True)`.
2. **`payments`**:
   - `models.py:6`: `class ThanhToan(MoHinhThoiGian):` (fields: `nguoi_dung`, `don_hang`, `dat_ban`, `loai_thanh_toan`, `phuong_thuc`, `so_tien`, `ma_giao_dich`, `trang_thai`, `thanh_toan_luc`, `hoan_tien_luc`). Không có `Payment`.
   - `serializers.py:2`: `from .models import Payment`, `attrs.get("payment_type"), attrs.get("order"), attrs.get("reservation")`, `Payment.PaymentType.ORDER`.
   - `views.py:6-7`: `from api.permissions import IsRestaurantStaff`, `from .models import Payment`, gọi `select_related("order", "reservation", "user")`.
3. **`promotions`**:
   - `models.py:7,46,58`: `KhuyenMai`, `MaKhuyenMai`, `LichSuDungKhuyenMai`. Không có `Promotion`, `PromotionCode`, `PromotionUsage`.
   - `serializers.py:2`: `from .models import Promotion, PromotionCode, PromotionUsage`, dùng trường `codes`, `used_count`.
   - `views.py:3-4`: `from api.permissions import IsStaffOrReadOnly, IsRestaurantStaff`, `from .models import Promotion...`, lọc `start_at`, `end_at`, `is_active`.
4. **`chat`**:
   - `models.py:6,26`: `HoiThoai`, `TinNhan`. Không có `ChatRoom`, `ChatMessage`.
   - `serializers.py:2`: `from .models import ChatRoom, ChatMessage`, dùng trường `messages`, `sender`, `customer`, `staff`.
   - `views.py:6`: `from .models import ChatRoom, ChatMessage`, `prefetch_related("messages")`, `room.last_message_at`.
5. **`recommendations`**:
   - `models.py:6,27`: `TuongTacMonAn`, `GoiYMonAn`. Không có `FoodInteraction`, `Recommendation`.
   - `serializers.py:2-3`: `from .models import FoodInteraction, Recommendation`, `from foods.serializers import FoodSerializer`.
   - `views.py:4-7`: `from .models import FoodInteraction, Recommendation`, `from foods.models import Food`, `from .services import RecommendationService`. Trong khi `services.py` định nghĩa `class DichVuGoiY:`.

### 1.5. Kiểm tra các app chưa được Việt hóa (vẫn dùng model tiếng Anh)
1. **`carts`**:
   - `models.py:6,13`: `class Cart(TimeStampedModel):`, `class CartItem(TimeStampedModel):`. Dòng 4: `from foods.models import TimeStampedModel, Food`. Thiếu `db_table = "gio_hang"` và `"chi_tiet_gio_hang"`.
2. **`reviews`**:
   - `models.py:6`: `class Review(TimeStampedModel):`. Dòng 3: `from foods.models import TimeStampedModel, Food`. Dòng 9-10: khóa ngoại tới `"orders.Order"`, `"orders.OrderItem"`. Thiếu `db_table = "danh_gia"`.
3. **`posts`**:
   - `models.py:5,10`: `class PostCategory(TimeStampedModel):`, `class Post(TimeStampedModel):`. Thiếu `db_table = "danh_muc_bai_viet"` và `"bai_viet"`.
4. **`analytics`**:
   - `models.py:6`: `class Notification(TimeStampedModel):`. Thiếu `db_table = "thong_bao"`.
   - `views.py:10-11`: `from orders.models import Order`, `from reservations.models import Reservation`. Dòng 23-24: `Order.objects.exclude(status=Order.Status.CANCELLED)`, tính `Sum("total_amount")`, `values("customer")`, `values("status")`. Tất cả đều là tên trường tiếng Anh cũ không khớp với `DonHang` (`trang_thai`, `tong_tien`, `khach_hang`).

### 1.6. Kiểm tra các lỗi lệch tên trường / relation trong các app đã Việt hóa
1. **`reservations`**:
   - `serializers.py:40`: `danh_sach_mon = MonAnDatBanSerializer(many=True, required=False, source="food_items")`. Trong khi `MonAnTrongDatBan` có `related_name="danh_sach_mon"`. Không có trường `food_items`.
   - `views.py:65`: `prefetch_related("food_items__mon_an")`. Sẽ gây lỗi `Cannot resolve keyword 'food_items' into field`.
2. **`orders`**:
   - `serializers.py:26`: `danh_sach_mon = ChiTietDonHangSerializer(many=True, source="items")`. Trong khi `ChiTietDonHang` có `related_name="danh_sach_mon"`. Không có trường `items`.
   - `views.py:18`: `prefetch_related("items__mon_an", "lich_su_trang_thai")`. Sẽ gây lỗi `Cannot resolve keyword 'items' into field`.
3. **`api/permissions.py`**:
   - Định nghĩa `class LaNhanVienNhaHang` và `class LaNhanVienHoacChiDoc`.
   - Không có `IsRestaurantStaff` và `IsStaffOrReadOnly`, khiến `branches/views.py`, `payments/views.py`, `promotions/views.py`, `posts/views.py`, `analytics/views.py` bị lỗi import.

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới chiến lược)

1. **Từ lỗi `manage.py check` (Mục 1.1) và Bảng hiện trạng (Mục 1.2 - 1.5)**:
   - Dự án bị chia tách thành hai nửa ngôn ngữ: một nửa đã đổi tên sang tiếng Việt nhưng nửa còn lại vẫn là tiếng Anh. Do đó, ngay khi Django khởi động và quét `INSTALLED_APPS`, việc import cross-app bị gãy lập tức tại `carts/models.py` (import `Food`).
   - Nếu chỉ sửa dòng `from foods.models import Food` thành `from foods.models import MonAn` trong `carts/models.py`, Django check sẽ tiếp tục gãy lần lượt ở `reviews/models.py`, `accounts/admin.py`, `branches/views.py`, `payments/views.py`, `chat/views.py`, `promotions/views.py`, `recommendations/views.py`, v.v.
   - *Suy luận*: Cần áp dụng một chiến lược 2 lớp (Two-Layer Adapter Pattern):
     * **Lớp 1: Lược đồ chuẩn tiếng Việt (Canonical Vietnamese Schema)**: Mọi model chính phải mang tên tiếng Việt, chỉ định `db_table` khớp 100% với 36 bảng của `moc_schema_tieng_viet.sql`, sử dụng các trường tiếng Việt.
     * **Lớp 2: Lớp tiếp hợp tương thích ngược (Backward-Compatible Adapter Layer)**:
       - Export Model Aliases ở cuối mỗi `models.py` (ví dụ `Food = MonAn`, `Order = DonHang`, `Branch = ChiNhanh`).
       - Bổ sung các `@property` getters/setters trên model cho các thuộc tính tiếng Anh cũ (`user`, `status`, `name`, `current_price`, `is_restaurant_staff`, v.v.) để bất kỳ code legacy nào gọi `.name` hay `.status` đều hoạt động mượt mà.
       - Cung cấp Serializer & ViewSet Aliases trong `serializers.py` và `views.py`.
       - Cung cấp Permission Aliases trong `api/permissions.py`.

2. **Từ sự sai lệch giữa `models.py` và `admin.py` (Mục 1.3)**:
   - `accounts/admin.py` đăng ký trực tiếp `User` và `Role` với các trường tiếng Anh (`name`, `description`). Nếu chỉ đặt alias `Role = VaiTro`, Django Admin Validation sẽ phát hiện `name` không có trong `VaiTro._meta.fields` và dừng với lỗi `admin.E108`.
   - *Suy luận*: Cần cập nhật `accounts/admin.py` import `NguoiDung, VaiTro` và cấu hình `list_display = ("ten", "mo_ta", "tao_luc", "cap_nhat_luc")`, `search_fields = ("ten",)`. Đồng thời đăng ký đầy đủ các model quản trị cho các app khác.

3. **Từ lỗi Relation `source="food_items"` và `source="items"` (Mục 1.6)**:
   - Trong `reservations/models.py`, `MonAnTrongDatBan` trỏ tới `DatBan` với `related_name="danh_sach_mon"`. Nhưng `DatBanSerializer` lại định nghĩa `source="food_items"` và view gọi `prefetch_related("food_items__mon_an")`.
   - Tương tự trong `orders/models.py`, `ChiTietDonHang` trỏ tới `DonHang` với `related_name="danh_sach_mon"`. Nhưng `DonHangSerializer` lại định nghĩa `source="items"` và view gọi `prefetch_related("items__mon_an")`.
   - *Suy luận*: Cần chuẩn hóa `source` về `danh_sach_mon` và `prefetch_related("danh_sach_mon__mon_an")`, đồng thời trên serializer bổ sung thêm field alias `food_items` và `items` trỏ tới `source="danh_sach_mon"` để client frontend gọi kiểu nào cũng nhận được dữ liệu.

4. **Từ cấu hình `AUTH_USER_MODEL` trong `config/settings.py` (Mục 1.2)**:
   - Django Auth bắt buộc `AUTH_USER_MODEL` phải trỏ tới một model thực tế được đăng ký trong ứng dụng, định dạng `app_label.ModelName`.
   - Khi `accounts.models` định nghĩa `NguoiDung`, giá trị bắt buộc phải là `AUTH_USER_MODEL = "accounts.NguoiDung"`. Nếu để `"accounts.User"`, Django sẽ báo `AUTH_USER_MODEL refers to model 'accounts.User' that has not been installed`.

5. **Từ yêu cầu Dual API Route Support (PROJECT.md Feature 5)**:
   - Frontend hiện có các caller gọi `/api/foods/` nhưng cũng có caller gọi `/api/mon-an/`, `/api/reservations/` và `/api/dat-ban/`.
   - *Suy luận*: `api/urls.py` cần đăng ký song song cả hai tiền tố (bilingual routing) trỏ về cùng một ViewSet để đảm bảo tính thông suốt tuyệt đối.

---

## 3. Caveats (Các điểm giới hạn & Giả định)

1. **Giả định về quyền thực thi**: Agent Explorer tuân thủ nghiêm ngặt nguyên tắc `read-only`, không tự ý ghi đè vào source code của dự án mà cung cấp tài liệu kỹ thuật chi tiết cùng code snippet chuẩn xác để Agent Implementer áp dụng.
2. **PostgreSQL & PostGIS Database Daemon**: Việc chạy `manage.py check` không đòi hỏi kết nối PostgreSQL đang sống. Tuy nhiên, khi Implementer chạy `makemigrations` và `migrate`, database daemon PostgreSQL với PostGIS extension phải được khởi chạy sẵn.
3. **Xóa Migrations cũ là an toàn**: Giả định rằng môi trường phát triển local chưa có dữ liệu sản xuất cần lưu giữ, việc xóa các file migration cũ `0001_initial.py` (từ 07/09/2026 mang tên tiếng Anh) để sinh lại một bộ migration mới tinh đồng bộ với `moc_schema_tieng_viet.sql` là giải pháp an toàn và sạch sẽ nhất.

---

## 4. Conclusion & Complete Strategy (Chiến lược & Hướng dẫn sửa mã chi tiết cho 13 Apps)

### 4.1. Bảng ma trận chuẩn hóa 13 Django Apps (Master Schema & Aliases Matrix)

| # | Django App | Canonical Model (Tiếng Việt) | `db_table` | Model Aliases (Tiếng Anh) | Property Adapters | Serializer & ViewSet Aliases |
|---|---|---|---|---|---|---|
| 1 | `accounts` | `VaiTro`<br>`QuyenHan`<br>`VaiTroQuyenHan`<br>`NguoiDung`<br>`NguoiDungVaiTro` | `vai_tro`<br>`quyen_han`<br>`vai_tro_quyen_han`<br>`nguoi_dung`<br>`nguoi_dung_vai_tro` | `Role = VaiTro`<br>`Permission = QuyenHan`<br>`RolePermission = VaiTroQuyenHan`<br>`User = NguoiDung`<br>`UserRole = NguoiDungVaiTro` | `is_restaurant_staff`<br>`is_restaurant_admin`<br>`roles` | `UserSerializer = NguoiDungSerializer`<br>`UserViewSet = NguoiDungViewSet` |
| 2 | `foods` | `DanhMuc`<br>`TheMonAn`<br>`NguyenLieu`<br>`MonAn`<br>`MonAnThe`<br>`DinhMucNguyenLieu`<br>`HinhAnhMonAn`<br>`LichSuXuatNhapKho` | `danh_muc`<br>`the_mon_an`<br>`nguyen_lieu`<br>`mon_an`<br>`mon_an_the`<br>`dinh_muc_nguyen_lieu`<br>`hinh_anh_mon_an`<br>`lich_su_xuat_nhap_kho` | `Category = DanhMuc`<br>`Tag = TheMonAn`<br>`Ingredient = NguyenLieu`<br>`Food = MonAn`<br>`FoodTag = MonAnThe`<br>`FoodIngredient = DinhMucNguyenLieu`<br>`FoodImage = HinhAnhMonAn`<br>`InventoryTransaction = LichSuXuatNhapKho` | `current_price`<br>`price`<br>`name`<br>`slug`<br>`is_active`<br>`rating_avg`<br>`review_count` | `FoodSerializer = MonAnSerializer`<br>`CategorySerializer = DanhMucSerializer`<br>`FoodViewSet = MonAnViewSet` |
| 3 | `branches` | `ChiNhanh` | `chi_nhanh` | `Branch = ChiNhanh` | `name`, `address`, `phone`<br>`location`, `is_active` | `BranchSerializer = ChiNhanhSerializer`<br>`BranchViewSet = ChiNhanhViewSet` |
| 4 | `reservations` | `BanAn`<br>`ChinhSachDatCoc`<br>`QuyTacHuyDatCoc`<br>`DatBan`<br>`MonAnTrongDatBan` | `ban_an`<br>`chinh_sach_dat_coc`<br>`quy_tac_huy_dat_coc`<br>`dat_ban`<br>`mon_an_trong_dat_ban` | `Table = BanAn`<br>`DepositPolicy = ChinhSachDatCoc`<br>`DepositRefundRule = QuyTacHuyDatCoc`<br>`Reservation = DatBan`<br>`ReservationItem = MonAnTrongDatBan`<br>`DatBan.Status = DatBan.TrangThai`<br>`DatBan.DepositStatus = DatBan.TrangThaiCoc` | `status`, `deposit_status`<br>`deposit_paid_at`, `version` | `TableSerializer = BanAnSerializer`<br>`ReservationSerializer = DatBanSerializer`<br>`TableViewSet = BanAnViewSet`<br>`ReservationViewSet = DatBanViewSet` |
| 5 | `orders` | `DonHang`<br>`ChiTietDonHang`<br>`LichSuTrangThaiDon` | `don_hang`<br>`chi_tiet_don_hang`<br>`lich_su_trang_thai_don` | `Order = DonHang`<br>`OrderItem = ChiTietDonHang`<br>`OrderStatusHistory = LichSuTrangThaiDon`<br>`DonHang.Status = DonHang.TrangThai`<br>`DonHang.Type = DonHang.HinhThuc` | `status`, `customer`<br>`customer_id`, `total_amount`<br>`items` | `OrderSerializer = DonHangSerializer`<br>`OrderItemSerializer = ChiTietDonHangSerializer`<br>`OrderViewSet = DonHangViewSet` |
| 6 | `payments` | `ThanhToan` | `thanh_toan` | `Payment = ThanhToan`<br>`PaymentType = ThanhToan.LoaiThanhToan`<br>`PaymentStatus = ThanhToan.TrangThai`<br>`ThanhToan.PaymentType = ThanhToan.LoaiThanhToan`<br>`ThanhToan.Status = ThanhToan.TrangThai` | `user`, `order`, `reservation`<br>`payment_type`, `status`<br>`paid_at`, `refunded_at` | `PaymentSerializer = ThanhToanSerializer`<br>`PaymentViewSet = ThanhToanViewSet` |
| 7 | `promotions` | `KhuyenMai`<br>`MaKhuyenMai`<br>`LichSuDungKhuyenMai` | `khuyen_mai`<br>`ma_khuyen_mai`<br>`lich_su_dung_khuyen_mai` | `Promotion = KhuyenMai`<br>`PromotionCode = MaKhuyenMai`<br>`PromotionUsage = LichSuDungKhuyenMai`<br>`DiscountType = KhuyenMai.KieuGiam`<br>`KhuyenMai.DiscountType = KhuyenMai.KieuGiam` | `code`, `is_active`<br>`start_at`, `end_at`<br>`used_count`, `codes` | `PromotionSerializer = KhuyenMaiSerializer`<br>`PromotionCodeSerializer = MaKhuyenMaiSerializer`<br>`PromotionViewSet = KhuyenMaiViewSet` |
| 8 | `chat` | `HoiThoai`<br>`TinNhan` | `hoi_thoai`<br>`tin_nhan` | `ChatRoom = HoiThoai`<br>`ChatMessage = TinNhan`<br>`HoiThoai.Status = HoiThoai.TrangThai`<br>`TinNhan.Type = TinNhan.LoaiTinNhan` | `customer`, `staff`, `status`<br>`last_message_at`, `messages`<br>`room`, `sender`, `content` | `ChatRoomSerializer = HoiThoaiSerializer`<br>`ChatMessageSerializer = TinNhanSerializer`<br>`ChatRoomViewSet = HoiThoaiViewSet` |
| 9 | `recommendations` | `TuongTacMonAn`<br>`GoiYMonAn` | `tuong_tac_mon_an`<br>`goi_y_mon_an` | `FoodInteraction = TuongTacMonAn`<br>`Recommendation = GoiYMonAn`<br>`RecommendationService = DichVuGoiY`<br>`FoodInteraction.Type = TuongTacMonAn.LoaiTuongTac` | `user`, `food`, `score`<br>`interaction_type`, `weight` | `InteractionSerializer = TuongTacMonAnSerializer`<br>`RecommendationSerializer = GoiYMonAnSerializer`<br>`InteractionViewSet = TuongTacMonAnViewSet`<br>`RecommendationViewSet = GoiYMonAnViewSet` |
| 10 | `carts` | `GioHang`<br>`ChiTietGioHang` | `gio_hang`<br>`chi_tiet_gio_hang` | `Cart = GioHang`<br>`CartItem = ChiTietGioHang`<br>`GioHang.Status = GioHang.TrangThai`<br>`Cart.Status = GioHang.TrangThai` | `user`, `status`, `items`<br>`cart`, `food`, `quantity`<br>`unit_price`, `note` | `CartSerializer = GioHangSerializer`<br>`CartItemSerializer = ChiTietGioHangSerializer`<br>`CartViewSet = GioHangViewSet` |
| 11 | `reviews` | `DanhGia` | `danh_gia` | `Review = DanhGia` | `user`, `food`, `order`<br>`order_item`, `rating`<br>`comment`, `is_visible` | `ReviewSerializer = DanhGiaSerializer`<br>`ReviewViewSet = DanhGiaViewSet` |
| 12 | `posts` | `DanhMucBaiViet`<br>`BaiViet` | `danh_muc_bai_viet`<br>`bai_viet` | `PostCategory = DanhMucBaiViet`<br>`Post = BaiViet`<br>`BaiViet.Status = BaiViet.TrangThai`<br>`Post.Status = BaiViet.TrangThai` | `name`, `slug`<br>`category`, `author`<br>`title`, `content`, `status`<br>`thumbnail_url`, `published_at` | `PostCategorySerializer = DanhMucBaiVietSerializer`<br>`PostSerializer = BaiVietSerializer`<br>`PostCategoryViewSet = DanhMucBaiVietViewSet`<br>`PostViewSet = BaiVietViewSet` |
| 13 | `analytics` | `ThongBao` | `thong_bao` | `Notification = ThongBao` | `user`, `type`, `title`<br>`message`, `is_read`, `read_at` | `NotificationSerializer = ThongBaoSerializer`<br>`NotificationViewSet = ThongBaoViewSet`<br>`DashboardViewSet` (Updated) |

---

### 4.2. Hướng dẫn sửa mã chi tiết cho từng file (Detailed Code Specifications)

#### 1. `config/settings.py`
**Vị trí**: Dòng 163  
**Thay đổi**:
```python
# Trước:
AUTH_USER_MODEL = "accounts.User"

# Sau:
AUTH_USER_MODEL = "accounts.NguoiDung"
```

#### 2. `api/permissions.py`
**Vị trí**: Cuối file  
**Thay đổi**: Bổ sung alias tiếng Anh:
```python
# Backward-compatible permission aliases
IsRestaurantStaff = LaNhanVienNhaHang
IsStaffOrReadOnly = LaNhanVienHoacChiDoc
```

#### 3. `accounts/models.py` & `accounts/admin.py`
**Tại `accounts/models.py`**: Bổ sung vào cuối file:
```python
    @property
    def is_restaurant_staff(self):
        return self.la_nhan_vien_nha_hang

    @property
    def is_restaurant_admin(self):
        return self.la_quan_tri_vien


# Backward-compatible model aliases
User = NguoiDung
Role = VaiTro
Permission = QuyenHan
RolePermission = VaiTroQuyenHan
UserRole = NguoiDungVaiTro
```
**Tại `accounts/admin.py`**: Thay toàn bộ nội dung thành:
```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import VaiTro, NguoiDung, User, Role


@admin.register(NguoiDung)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "thu_dien_tu", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "thu_dien_tu", "first_name", "last_name", "so_dien_thoai")


@admin.register(VaiTro)
class VaiTroAdmin(admin.ModelAdmin):
    list_display = ("ten", "mo_ta", "tao_luc", "cap_nhat_luc")
    search_fields = ("ten",)
```

#### 4. `foods/models.py` & `foods/serializers.py` & `foods/views.py`
**Tại `foods/models.py`**:
Bổ sung các properties tương thích ngược trên class `MonAn`:
```python
    @property
    def current_price(self):
        return self.don_gia

    @property
    def price(self):
        return self.don_gia

    @property
    def name(self):
        return self.ten

    @property
    def slug(self):
        return self.duong_dan

    @property
    def is_active(self):
        return self.con_hang and self.hien_thi

    @property
    def rating_avg(self):
        return self.diem_danh_gia

    @rating_avg.setter
    def rating_avg(self, val):
        self.diem_danh_gia = val

    @property
    def review_count(self):
        return self.so_luot_danh_gia

    @review_count.setter
    def review_count(self, val):
        self.so_luot_danh_gia = val
```
Và bổ sung vào cuối file:
```python
# Backward-compatible model aliases
Category = DanhMuc
Tag = TheMonAn
Ingredient = NguyenLieu
Food = MonAn
FoodTag = MonAnThe
FoodIngredient = DinhMucNguyenLieu
FoodImage = HinhAnhMonAn
InventoryTransaction = LichSuXuatNhapKho
InventoryHistory = LichSuXuatNhapKho
```
**Tại `foods/serializers.py`**: Bổ sung vào cuối file:
```python
# Backward-compatible serializer aliases
CategorySerializer = DanhMucSerializer
TagSerializer = TheMonAnSerializer
IngredientSerializer = NguyenLieuSerializer
FoodSerializer = MonAnSerializer
FoodImageSerializer = HinhAnhMonAnSerializer
InventoryHistorySerializer = LichSuKhoSerializer
```
**Tại `foods/views.py`**: Bổ sung vào cuối file:
```python
# Backward-compatible viewset aliases
CategoryViewSet = DanhMucViewSet
TagViewSet = TheMonAnViewSet
IngredientViewSet = NguyenLieuViewSet
FoodViewSet = MonAnViewSet
InventoryHistoryViewSet = LichSuKhoViewSet
```

#### 5. `branches/models.py`, `branches/serializers.py`, `branches/views.py`
**Tại `branches/models.py`**:
```python
from django.contrib.gis.db import models as gis_models
from django.db import models
from foods.models import MoHinhThoiGian


class ChiNhanh(MoHinhThoiGian):
    ten = models.CharField(max_length=150)
    dia_chi = models.TextField()
    so_dien_thoai = models.CharField(max_length=20, blank=True)
    toa_do_gis = gis_models.PointField(geography=True, srid=4326)
    con_hoat_dong = models.BooleanField(default=True)

    class Meta:
        db_table = "chi_nhanh"
        verbose_name = "Chi nhánh"

    def __str__(self):
        return self.ten

    @property
    def name(self):
        return self.ten

    @property
    def address(self):
        return self.dia_chi

    @property
    def phone(self):
        return self.so_dien_thoai

    @property
    def location(self):
        return self.toa_do_gis

    @property
    def is_active(self):
        return self.con_hoat_dong


# Backward-compatible model aliases
Branch = ChiNhanh
```
**Tại `branches/serializers.py`**:
```python
from rest_framework import serializers
from .models import ChiNhanh, Branch


class ChiNhanhSerializer(serializers.ModelSerializer):
    kinh_do = serializers.SerializerMethodField()
    vi_do = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()
    name = serializers.CharField(source="ten", read_only=True)
    address = serializers.CharField(source="dia_chi", read_only=True)
    phone = serializers.CharField(source="so_dien_thoai", read_only=True)
    is_active = serializers.BooleanField(source="con_hoat_dong", read_only=True)

    def get_kinh_do(self, obj):
        return obj.toa_do_gis.x if obj.toa_do_gis else None

    def get_vi_do(self, obj):
        return obj.toa_do_gis.y if obj.toa_do_gis else None

    get_longitude = get_kinh_do
    get_latitude = get_vi_do

    class Meta:
        model = ChiNhanh
        fields = (
            "id", "ten", "dia_chi", "so_dien_thoai", "toa_do_gis",
            "kinh_do", "vi_do", "longitude", "latitude",
            "name", "address", "phone", "is_active",
            "con_hoat_dong", "tao_luc", "cap_nhat_luc"
        )


BranchSerializer = ChiNhanhSerializer
```
**Tại `branches/views.py`**:
```python
from rest_framework import viewsets
from api.permissions import LaNhanVienHoacChiDoc, IsStaffOrReadOnly
from .models import ChiNhanh, Branch
from .serializers import ChiNhanhSerializer, BranchSerializer


class ChiNhanhViewSet(viewsets.ModelViewSet):
    queryset = ChiNhanh.objects.all()
    serializer_class = ChiNhanhSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
        q = ChiNhanh.objects.all()
        user = self.request.user
        is_staff = user.is_authenticated and getattr(user, "la_nhan_vien_nha_hang", False)
        return q if is_staff else q.filter(con_hoat_dong=True)


BranchViewSet = ChiNhanhViewSet
```

#### 6. `reservations/models.py`, `serializers.py`, `views.py`, `services.py`
**Tại `reservations/models.py`**:
Bổ sung properties trên `DatBan`:
```python
    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def deposit_status(self):
        return self.trang_thai_coc

    @deposit_status.setter
    def deposit_status(self, val):
        self.trang_thai_coc = val

    @property
    def deposit_paid_at(self):
        return self.thanh_toan_coc_luc

    @deposit_paid_at.setter
    def deposit_paid_at(self, val):
        self.thanh_toan_coc_luc = val

    @property
    def version(self):
        return self.phien_ban

    @version.setter
    def version(self, val):
        self.phien_ban = val
```
Và bổ sung vào cuối file:
```python
# Backward-compatible model aliases
Table = BanAn
DepositPolicy = ChinhSachDatCoc
DepositRefundRule = QuyTacHuyDatCoc
Reservation = DatBan
ReservationItem = MonAnTrongDatBan
ReservationFoodItem = MonAnTrongDatBan
DatBan.Status = DatBan.TrangThai
DatBan.DepositStatus = DatBan.TrangThaiCoc
```
**Tại `reservations/serializers.py`**:
Sửa dòng 40 và thêm alias:
```python
class DatBanSerializer(serializers.ModelSerializer):
    danh_sach_mon = MonAnDatBanSerializer(many=True, required=False)
    food_items = MonAnDatBanSerializer(many=True, source="danh_sach_mon", read_only=True)
    so_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    id_giu_ban = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = DatBan
        fields = "__all__"
        read_only_fields = (
            "nguoi_dung", "ma_dat_ban", "trang_thai",
            "yeu_cau_dat_coc", "so_tien_coc", "trang_thai_coc",
            "thanh_toan_coc_luc", "huy_luc", "phien_ban"
        )
...
# Aliases
TableSerializer = BanAnSerializer
ReservationSerializer = DatBanSerializer
ReservationItemSerializer = MonAnDatBanSerializer
DepositPolicySerializer = ChinhSachCocSerializer
DepositRefundRuleSerializer = QuyTacHuyCocSerializer
```
**Tại `reservations/views.py`**:
- Sửa dòng 65: đổi `prefetch_related("food_items__mon_an")` thành `prefetch_related("danh_sach_mon__mon_an")`.
- Bổ sung alias:
```python
TableViewSet = BanAnViewSet
ReservationViewSet = DatBanViewSet
```
**Tại `reservations/services.py`**:
- Sửa dòng 16:
```python
danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])
```

#### 7. `orders/models.py`, `serializers.py`, `views.py`, `services.py`
**Tại `orders/models.py`**:
Bổ sung properties trên `DonHang`:
```python
    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def customer(self):
        return self.khach_hang

    @property
    def customer_id(self):
        return self.khach_hang_id

    @property
    def total_amount(self):
        return self.tong_tien

    @property
    def items(self):
        return self.danh_sach_mon
```
Và bổ sung vào cuối file:
```python
# Backward-compatible model aliases
Order = DonHang
OrderItem = ChiTietDonHang
OrderStatusHistory = LichSuTrangThaiDon
DonHang.Status = DonHang.TrangThai
DonHang.Type = DonHang.HinhThuc
```
**Tại `orders/serializers.py`**:
- Sửa dòng 26 và thêm alias `items`:
```python
class DonHangSerializer(serializers.ModelSerializer):
    danh_sach_mon = ChiTietDonHangSerializer(many=True, required=False)
    items = ChiTietDonHangSerializer(many=True, source="danh_sach_mon", read_only=True)
    lich_su_trang_thai = LichSuTrangThaiDonSerializer(many=True, read_only=True)
    ma_khuyen_mai = serializers.CharField(write_only=True, required=False)
...
OrderSerializer = DonHangSerializer
OrderItemSerializer = ChiTietDonHangSerializer
OrderStatusHistorySerializer = LichSuTrangThaiDonSerializer
```
**Tại `orders/views.py`**:
- Sửa dòng 18: đổi `prefetch_related("items__mon_an", "lich_su_trang_thai")` thành `prefetch_related("danh_sach_mon__mon_an", "lich_su_trang_thai")`.
- Bổ sung alias:
```python
OrderViewSet = DonHangViewSet
```
**Tại `orders/services.py`**:
- Dòng 12: `danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("items", [])`
- Dòng 22: `so_luong = item.get("so_luong") or item.get("quantity")`

#### 8. `payments/models.py`, `serializers.py`, `views.py`
**Tại `payments/models.py`**:
Bổ sung properties trên `ThanhToan`:
```python
    @property
    def user(self):
        return self.nguoi_dung

    @user.setter
    def user(self, val):
        self.nguoi_dung = val

    @property
    def order(self):
        return self.don_hang

    @order.setter
    def order(self, val):
        self.don_hang = val

    @property
    def reservation(self):
        return self.dat_ban

    @reservation.setter
    def reservation(self, val):
        self.dat_ban = val

    @property
    def payment_type(self):
        return self.loai_thanh_toan

    @payment_type.setter
    def payment_type(self, val):
        self.loai_thanh_toan = val

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def paid_at(self):
        return self.thanh_toan_luc

    @paid_at.setter
    def paid_at(self, val):
        self.thanh_toan_luc = val

    @property
    def refunded_at(self):
        return self.hoan_tien_luc

    @refunded_at.setter
    def refunded_at(self, val):
        self.hoan_tien_luc = val

    @property
    def created_at(self):
        return self.tao_luc

    @property
    def updated_at(self):
        return self.cap_nhat_luc


# Backward-compatible model aliases
Payment = ThanhToan
PaymentType = ThanhToan.LoaiThanhToan
PaymentStatus = ThanhToan.TrangThai
ThanhToan.PaymentType = ThanhToan.LoaiThanhToan
ThanhToan.Status = ThanhToan.TrangThai
```
**Tại `payments/serializers.py`**:
```python
from rest_framework import serializers
from .models import ThanhToan, Payment


class ThanhToanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThanhToan
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "trang_thai", "thanh_toan_luc", "hoan_tien_luc")

    def validate(self, attrs):
        loai = attrs.get("loai_thanh_toan") or attrs.get("payment_type")
        don_hang = attrs.get("don_hang") or attrs.get("order")
        dat_ban = attrs.get("dat_ban") or attrs.get("reservation")

        if loai == ThanhToan.LoaiThanhToan.DON_HANG and (not don_hang or dat_ban):
            raise serializers.ValidationError("Thanh toán đơn hàng chỉ được gắn với đơn hàng.")
        if loai == ThanhToan.LoaiThanhToan.TIEN_COC and (not dat_ban or don_hang):
            raise serializers.ValidationError("Đặt cọc chỉ được gắn với đặt bàn.")
        return attrs


PaymentSerializer = ThanhToanSerializer
```
**Tại `payments/views.py`**:
```python
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.permissions import LaNhanVienNhaHang, IsRestaurantStaff
from .models import ThanhToan, Payment
from .serializers import ThanhToanSerializer, PaymentSerializer


class ThanhToanViewSet(viewsets.ModelViewSet):
    serializer_class = ThanhToanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = ThanhToan.objects.select_related("don_hang", "dat_ban", "nguoi_dung").order_by("-tao_luc")
        user = self.request.user
        return q if getattr(user, "la_nhan_vien_nha_hang", False) else q.filter(nguoi_dung=user)

    def perform_create(self, serializer):
        serializer.save(nguoi_dung=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[LaNhanVienNhaHang])
    def xac_nhan_thanh_cong(self, request, pk=None):
        tt = self.get_object()
        tt.trang_thai = ThanhToan.TrangThai.THANH_CONG
        tt.thanh_toan_luc = timezone.now()
        tt.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])

        if tt.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and tt.dat_ban:
            db = tt.dat_ban
            db.trang_thai_coc = "thanh_cong"
            db.thanh_toan_coc_luc = tt.thanh_toan_luc
            db.trang_thai = "da_xac_nhan"
            db.phien_ban += 1
            db.save(update_fields=["trang_thai_coc", "thanh_toan_coc_luc", "trang_thai", "phien_ban", "cap_nhat_luc"])
        return Response(self.get_serializer(tt).data)

    # Alias for legacy test callers:
    mark_success = xac_nhan_thanh_cong


PaymentViewSet = ThanhToanViewSet
```

#### 9. `promotions/models.py`, `serializers.py`, `views.py`
**Tại `promotions/models.py`**:
Bổ sung properties trên `KhuyenMai`:
```python
    @property
    def code(self):
        return self.ma_giam_gia

    @property
    def is_active(self):
        return self.con_hoat_dong

    @property
    def start_at(self):
        return self.bat_dau_luc

    @property
    def end_at(self):
        return self.ket_thuc_luc

    @property
    def used_count(self):
        return self.so_lan_da_dung

    @property
    def codes(self):
        return self.danh_sach_ma


# Backward-compatible model aliases
Promotion = KhuyenMai
PromotionCode = MaKhuyenMai
PromotionUsage = LichSuDungKhuyenMai
DiscountType = KhuyenMai.KieuGiam
KhuyenMai.DiscountType = KhuyenMai.KieuGiam
```
**Tại `promotions/serializers.py`**:
```python
from rest_framework import serializers
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai, Promotion, PromotionCode, PromotionUsage


class MaKhuyenMaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaKhuyenMai
        fields = "__all__"
        read_only_fields = ("da_dung",)


class KhuyenMaiSerializer(serializers.ModelSerializer):
    danh_sach_ma = MaKhuyenMaiSerializer(many=True, read_only=True)
    codes = MaKhuyenMaiSerializer(source="danh_sach_ma", many=True, read_only=True)

    class Meta:
        model = KhuyenMai
        fields = "__all__"
        read_only_fields = ("so_lan_da_dung",)


class LichSuDungKhuyenMaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = LichSuDungKhuyenMai
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "don_hang", "so_tien_giam")


PromotionSerializer = KhuyenMaiSerializer
PromotionCodeSerializer = MaKhuyenMaiSerializer
PromotionUsageSerializer = LichSuDungKhuyenMaiSerializer
```
**Tại `promotions/views.py`**:
```python
from django.utils import timezone
from rest_framework import viewsets
from api.permissions import LaNhanVienHoacChiDoc, LaNhanVienNhaHang, IsStaffOrReadOnly, IsRestaurantStaff
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai, Promotion, PromotionCode, PromotionUsage
from .serializers import (
    KhuyenMaiSerializer, MaKhuyenMaiSerializer, LichSuDungKhuyenMaiSerializer,
    PromotionSerializer, PromotionCodeSerializer, PromotionUsageSerializer
)


class KhuyenMaiViewSet(viewsets.ModelViewSet):
    serializer_class = KhuyenMaiSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
        q = KhuyenMai.objects.prefetch_related("danh_sach_ma")
        if self.request.query_params.get("active") or self.request.query_params.get("con_han"):
            now = timezone.now()
            q = q.filter(con_hoat_dong=True, bat_dau_luc__lte=now, ket_thuc_luc__gte=now)
        return q


class MaKhuyenMaiViewSet(viewsets.ModelViewSet):
    queryset = MaKhuyenMai.objects.select_related("khuyen_mai")
    serializer_class = MaKhuyenMaiSerializer
    permission_classes = [LaNhanVienHoacChiDoc]


class LichSuDungKhuyenMaiViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LichSuDungKhuyenMaiSerializer
    permission_classes = [LaNhanVienNhaHang]
    queryset = LichSuDungKhuyenMai.objects.select_related("khuyen_mai", "nguoi_dung", "don_hang")


PromotionViewSet = KhuyenMaiViewSet
PromotionCodeViewSet = MaKhuyenMaiViewSet
PromotionUsageViewSet = LichSuDungKhuyenMaiViewSet
```

#### 10. `chat/models.py`, `serializers.py`, `views.py`
**Tại `chat/models.py`**:
Bổ sung properties trên `HoiThoai`:
```python
    @property
    def customer(self):
        return self.khach_hang

    @property
    def staff(self):
        return self.nhan_vien

    @property
    def status(self):
        return self.trang_thai

    @property
    def last_message_at(self):
        return self.tin_nhan_cuoi_luc

    @last_message_at.setter
    def last_message_at(self, val):
        self.tin_nhan_cuoi_luc = val

    @property
    def messages(self):
        return self.danh_sach_tin_nhan
```
Bổ sung properties trên `TinNhan`:
```python
    @property
    def room(self):
        return self.hoi_thoai

    @room.setter
    def room(self, val):
        self.hoi_thoai = val

    @property
    def sender(self):
        return self.nguoi_gui

    @sender.setter
    def sender(self, val):
        self.nguoi_gui = val

    @property
    def content(self):
        return self.noi_dung

    @property
    def message_type(self):
        return self.loai_tin_nhan

    @property
    def is_read(self):
        return self.da_doc
```
Và bổ sung vào cuối file:
```python
# Backward-compatible model aliases
ChatRoom = HoiThoai
ChatMessage = TinNhan
HoiThoai.Status = HoiThoai.TrangThai
TinNhan.Type = TinNhan.LoaiTinNhan
```
**Tại `chat/serializers.py`**:
```python
from rest_framework import serializers
from .models import HoiThoai, TinNhan, ChatRoom, ChatMessage


class TinNhanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TinNhan
        fields = "__all__"
        read_only_fields = ("nguoi_gui",)


class HoiThoaiSerializer(serializers.ModelSerializer):
    danh_sach_tin_nhan = TinNhanSerializer(many=True, read_only=True)
    messages = TinNhanSerializer(source="danh_sach_tin_nhan", many=True, read_only=True)

    class Meta:
        model = HoiThoai
        fields = "__all__"
        read_only_fields = ("khach_hang", "nhan_vien")


ChatMessageSerializer = TinNhanSerializer
ChatRoomSerializer = HoiThoaiSerializer
```
**Tại `chat/views.py`**:
```python
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import HoiThoai, TinNhan, ChatRoom, ChatMessage
from .serializers import HoiThoaiSerializer, TinNhanSerializer, ChatRoomSerializer, ChatMessageSerializer


class HoiThoaiViewSet(viewsets.ModelViewSet):
    serializer_class = HoiThoaiSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = HoiThoai.objects.prefetch_related("danh_sach_tin_nhan")
        user = self.request.user
        return q if getattr(user, "la_nhan_vien_nha_hang", False) else q.filter(khach_hang=user)

    def perform_create(self, serializer):
        serializer.save(khach_hang=self.request.user)

    @action(detail=True, methods=["post"])
    def gui_tin_nhan(self, request, pk=None):
        room = self.get_object()
        serializer = TinNhanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(hoi_thoai=room, nguoi_gui=request.user)
        room.tin_nhan_cuoi_luc = timezone.now()
        room.save(update_fields=["tin_nhan_cuoi_luc", "cap_nhat_luc"])
        return Response(TinNhanSerializer(message).data, status=201)

    # Legacy action alias
    messages = gui_tin_nhan


ChatRoomViewSet = HoiThoaiViewSet
```

#### 11. `recommendations/models.py`, `serializers.py`, `views.py`, `services.py`
**Tại `recommendations/models.py`**:
Bổ sung properties trên `TuongTacMonAn`:
```python
    @property
    def user(self):
        return self.nguoi_dung

    @user.setter
    def user(self, val):
        self.nguoi_dung = val

    @property
    def food(self):
        return self.mon_an

    @food.setter
    def food(self, val):
        self.mon_an = val

    @property
    def interaction_type(self):
        return self.loai_tuong_tac

    @interaction_type.setter
    def interaction_type(self, val):
        self.loai_tuong_tac = val

    @property
    def weight(self):
        return self.trong_so

    @weight.setter
    def weight(self, val):
        self.trong_so = val
```
Bổ sung properties trên `GoiYMonAn`:
```python
    @property
    def user(self):
        return self.nguoi_dung

    @property
    def food(self):
        return self.mon_an

    @property
    def score(self):
        return self.diem_tuong_dong
```
Và bổ sung vào cuối file:
```python
# Backward-compatible model aliases
FoodInteraction = TuongTacMonAn
Recommendation = GoiYMonAn
TuongTacMonAn.Type = TuongTacMonAn.LoaiTuongTac
FoodInteraction.Type = TuongTacMonAn.LoaiTuongTac
```
**Tại `recommendations/services.py`**: Bổ sung adapter và alias:
```python
# Adapter method for legacy callers
def _refresh_for(cls, user, limit=6):
    return cls.cap_nhat_goi_y(user, gioi_han=limit)

DichVuGoiY.refresh_for = classmethod(_refresh_for)
RecommendationService = DichVuGoiY
```
**Tại `recommendations/serializers.py`**:
```python
from rest_framework import serializers
from foods.models import MonAn, Food
from foods.serializers import MonAnSerializer, FoodSerializer
from .models import TuongTacMonAn, GoiYMonAn, FoodInteraction, Recommendation


class TuongTacMonAnSerializer(serializers.ModelSerializer):
    class Meta:
        model = TuongTacMonAn
        fields = ("id", "mon_an", "loai_tuong_tac", "trong_so", "tao_luc")
        read_only_fields = ("tao_luc",)


class GoiYMonAnSerializer(serializers.ModelSerializer):
    chi_tiet_mon = MonAnSerializer(source="mon_an", read_only=True)
    food_detail = MonAnSerializer(source="mon_an", read_only=True)

    class Meta:
        model = GoiYMonAn
        fields = "__all__"


InteractionSerializer = TuongTacMonAnSerializer
RecommendationSerializer = GoiYMonAnSerializer
```
**Tại `recommendations/views.py`**:
```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import TuongTacMonAn, GoiYMonAn, FoodInteraction, Recommendation
from .serializers import (
    TuongTacMonAnSerializer, GoiYMonAnSerializer,
    InteractionSerializer, RecommendationSerializer
)
from .services import DichVuGoiY, RecommendationService


class TuongTacMonAnViewSet(viewsets.ModelViewSet):
    serializer_class = TuongTacMonAnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TuongTacMonAn.objects.filter(nguoi_dung=self.request.user)

    def perform_create(self, serializer):
        serializer.save(nguoi_dung=self.request.user)


class GoiYMonAnViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GoiYMonAnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = GoiYMonAn.objects.filter(nguoi_dung=self.request.user).select_related("mon_an").order_by("-diem_tuong_dong")
        if q.exists():
            return q
        return DichVuGoiY.cap_nhat_goi_y(self.request.user)


InteractionViewSet = TuongTacMonAnViewSet
RecommendationViewSet = GoiYMonAnViewSet
```

#### 12. `carts/models.py`, `serializers.py`, `views.py`
**Tại `carts/models.py`** (Chuẩn hóa toàn diện sang tiếng Việt kèm aliases):
```python
from django.conf import settings
from django.db import models
from django.db.models import Q
from foods.models import MoHinhThoiGian, MonAn, Food


class GioHang(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        DANG_SU_DUNG = "dang_su_dung", "Đang sử dụng"
        DA_THANH_TOAN = "da_thanh_toan", "Đã thanh toán"
        BO_DO = "bo_do", "Bỏ dở"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_gio_hang", on_delete=models.CASCADE
    )
    trang_thai = models.CharField(
        max_length=20, choices=TrangThai.choices, default=TrangThai.DANG_SU_DUNG
    )

    class Meta:
        db_table = "gio_hang"
        verbose_name = "Giỏ hàng"
        constraints = [
            models.UniqueConstraint(
                fields=["nguoi_dung"],
                condition=Q(trang_thai="dang_su_dung"),
                name="uq_gio_hang_active"
            )
        ]

    @property
    def user(self):
        return self.nguoi_dung

    @property
    def status(self):
        return self.trang_thai

    @property
    def items(self):
        return self.danh_sach_mon


class ChiTietGioHang(MoHinhThoiGian):
    gio_hang = models.ForeignKey(GioHang, related_name="danh_sach_mon", on_delete=models.CASCADE)
    mon_an = models.ForeignKey("foods.MonAn", related_name="chi_tiet_gio_hang", on_delete=models.PROTECT)
    so_luong = models.PositiveIntegerField()
    don_gia_luc_dat = models.DecimalField(max_digits=12, decimal_places=2)
    ghi_chu = models.TextField(blank=True)

    class Meta:
        db_table = "chi_tiet_gio_hang"
        unique_together = ("gio_hang", "mon_an")
        verbose_name = "Chi tiết giỏ hàng"

    @property
    def cart(self):
        return self.gio_hang

    @property
    def food(self):
        return self.mon_an

    @property
    def quantity(self):
        return self.so_luong

    @quantity.setter
    def quantity(self, val):
        self.so_luong = val

    @property
    def unit_price(self):
        return self.don_gia_luc_dat

    @property
    def note(self):
        return self.ghi_chu


# Backward-compatible model aliases
Cart = GioHang
CartItem = ChiTietGioHang
GioHang.Status = GioHang.TrangThai
Cart.Status = GioHang.TrangThai
```
**Tại `carts/serializers.py`**:
```python
from rest_framework import serializers
from foods.models import MonAn, Food
from foods.serializers import MonAnSerializer, FoodSerializer
from .models import GioHang, ChiTietGioHang, Cart, CartItem


class ChiTietGioHangSerializer(serializers.ModelSerializer):
    mon_an_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True, hien_thi=True),
        source="mon_an", write_only=True, required=False
    )
    food_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True, hien_thi=True),
        source="mon_an", write_only=True, required=False
    )
    mon_an = MonAnSerializer(read_only=True)
    food = MonAnSerializer(source="mon_an", read_only=True)
    quantity = serializers.IntegerField(source="so_luong", required=False)
    unit_price = serializers.DecimalField(source="don_gia_luc_dat", max_digits=12, decimal_places=2, read_only=True)
    note = serializers.CharField(source="ghi_chu", required=False, allow_blank=True)

    class Meta:
        model = ChiTietGioHang
        fields = (
            "id", "gio_hang", "mon_an", "mon_an_id", "food_id", "food",
            "so_luong", "quantity", "don_gia_luc_dat", "unit_price",
            "ghi_chu", "note", "tao_luc", "cap_nhat_luc"
        )
        read_only_fields = ("gio_hang", "don_gia_luc_dat", "unit_price")


class GioHangSerializer(serializers.ModelSerializer):
    danh_sach_mon = ChiTietGioHangSerializer(many=True, read_only=True)
    items = ChiTietGioHangSerializer(source="danh_sach_mon", many=True, read_only=True)

    class Meta:
        model = GioHang
        fields = "__all__"
        read_only_fields = ("nguoi_dung",)


CartItemSerializer = ChiTietGioHangSerializer
CartSerializer = GioHangSerializer
```
**Tại `carts/views.py`**:
```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import GioHang, ChiTietGioHang, Cart, CartItem
from .serializers import GioHangSerializer, ChiTietGioHangSerializer, CartSerializer, CartItemSerializer


class GioHangViewSet(viewsets.GenericViewSet):
    serializer_class = GioHangSerializer
    permission_classes = [IsAuthenticated]

    def _cart(self):
        gio_hang, _ = GioHang.objects.prefetch_related("danh_sach_mon__mon_an").get_or_create(
            nguoi_dung=self.request.user,
            trang_thai=GioHang.TrangThai.DANG_SU_DUNG
        )
        return gio_hang

    def list(self, request):
        return Response(self.get_serializer(self._cart()).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        serializer = ChiTietGioHangSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = self._cart()
        mon_an = serializer.validated_data["mon_an"]
        so_luong = serializer.validated_data.get("so_luong", 1)
        ghi_chu = serializer.validated_data.get("ghi_chu", "")

        item, created = ChiTietGioHang.objects.get_or_create(
            gio_hang=cart,
            mon_an=mon_an,
            defaults={
                "so_luong": so_luong,
                "don_gia_luc_dat": mon_an.don_gia,
                "ghi_chu": ghi_chu,
            }
        )
        if not created:
            item.so_luong += so_luong
            item.save(update_fields=["so_luong", "cap_nhat_luc"])

        return Response(ChiTietGioHangSerializer(item).data, status=201 if created else 200)

    @action(detail=False, methods=["patch", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item(self, request, item_id=None):
        cart = self._cart()
        item = cart.danh_sach_mon.get(pk=item_id)
        if request.method == "DELETE":
            item.delete()
            return Response(status=204)
        serializer = ChiTietGioHangSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


CartViewSet = GioHangViewSet
```

#### 13. `reviews/models.py`, `serializers.py`, `views.py`
**Tại `reviews/models.py`**:
```python
from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn, Food


class DanhGia(MoHinhThoiGian):
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_danh_gia", on_delete=models.CASCADE
    )
    mon_an = models.ForeignKey(
        "foods.MonAn", related_name="danh_sach_danh_gia", on_delete=models.CASCADE
    )
    don_hang = models.ForeignKey(
        "orders.DonHang", related_name="danh_sach_danh_gia", on_delete=models.CASCADE
    )
    chi_tiet_don_hang = models.OneToOneField(
        "orders.ChiTietDonHang", related_name="danh_gia", on_delete=models.CASCADE
    )
    diem_danh_gia = models.PositiveSmallIntegerField()
    nhan_xet = models.TextField(blank=True)
    hien_thi = models.BooleanField(default=True)

    class Meta:
        db_table = "danh_gia"
        verbose_name = "Đánh giá"
        indexes = [models.Index(fields=["mon_an"])]

    @property
    def user(self):
        return self.nguoi_dung

    @property
    def food(self):
        return self.mon_an

    @property
    def order(self):
        return self.don_hang

    @property
    def order_item(self):
        return self.chi_tiet_don_hang

    @property
    def rating(self):
        return self.diem_danh_gia

    @property
    def comment(self):
        return self.nhan_xet

    @property
    def is_visible(self):
        return self.hien_thi


# Backward-compatible model aliases
Review = DanhGia
```
**Tại `reviews/serializers.py`**:
```python
from rest_framework import serializers
from orders.models import DonHang, ChiTietDonHang, Order, OrderItem
from .models import DanhGia, Review


class DanhGiaSerializer(serializers.ModelSerializer):
    ten_nguoi_dung = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    rating = serializers.IntegerField(source="diem_danh_gia", required=False)
    comment = serializers.CharField(source="nhan_xet", required=False, allow_blank=True)

    class Meta:
        model = DanhGia
        fields = "__all__"
        read_only_fields = ("nguoi_dung",)

    def get_ten_nguoi_dung(self, obj):
        return obj.nguoi_dung.get_full_name() or obj.nguoi_dung.username

    get_user_name = get_ten_nguoi_dung

    def validate_diem_danh_gia(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Điểm đánh giá phải từ 1 đến 5.")
        return value

    def validate(self, attrs):
        if self.instance:
            return attrs
        request = self.context["request"]
        don_hang = attrs.get("don_hang")
        item = attrs.get("chi_tiet_don_hang")
        mon_an = attrs.get("mon_an")

        if don_hang and don_hang.khach_hang_id != request.user.id:
            raise serializers.ValidationError({"don_hang": "Chỉ được đánh giá đơn hàng của bạn."})
        if don_hang and don_hang.trang_thai != DonHang.TrangThai.HOAN_TAT:
            raise serializers.ValidationError({"don_hang": "Chỉ được đánh giá đơn hàng đã hoàn tất."})
        if item and don_hang and item.don_hang_id != don_hang.id:
            raise serializers.ValidationError({"chi_tiet_don_hang": "Món ăn không thuộc đơn hàng đã chọn."})
        if item and mon_an and item.mon_an_id != mon_an.id:
            raise serializers.ValidationError({"chi_tiet_don_hang": "Chi tiết đơn không khớp với món ăn."})
        return attrs


ReviewSerializer = DanhGiaSerializer
```
**Tại `reviews/views.py`**:
```python
from django.db.models import Avg, Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from .models import DanhGia, Review
from .serializers import DanhGiaSerializer, ReviewSerializer
from recommendations.models import TuongTacMonAn, FoodInteraction


class DanhGiaViewSet(viewsets.ModelViewSet):
    serializer_class = DanhGiaSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        q = DanhGia.objects.filter(hien_thi=True).select_related(
            "nguoi_dung", "mon_an", "don_hang", "chi_tiet_don_hang"
        )
        food_id = self.request.query_params.get("food") or self.request.query_params.get("mon_an")
        if food_id:
            q = q.filter(mon_an_id=food_id)
        return q

    def _cap_nhat_diem_mon(self, mon_an):
        ket_qua = mon_an.danh_sach_danh_gia.filter(hien_thi=True).aggregate(
            rating=Avg("diem_danh_gia"), count=Count("id")
        )
        mon_an.diem_danh_gia = ket_qua["rating"] or 0
        mon_an.so_luot_danh_gia = ket_qua["count"] or 0
        mon_an.save(update_fields=["diem_danh_gia", "so_luot_danh_gia", "cap_nhat_luc"])

    def perform_create(self, serializer):
        danh_gia = serializer.save(nguoi_dung=self.request.user)
        self._cap_nhat_diem_mon(danh_gia.mon_an)
        TuongTacMonAn.objects.create(
            nguoi_dung=self.request.user,
            mon_an=danh_gia.mon_an,
            loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DANH_GIA,
            trong_so=5
        )

    def perform_update(self, serializer):
        user = self.request.user
        if serializer.instance.nguoi_dung_id != user.id and not getattr(user, "la_nhan_vien_nha_hang", False):
            raise PermissionDenied("Bạn chỉ có thể sửa đánh giá của mình.")
        danh_gia = serializer.save()
        self._cap_nhat_diem_mon(danh_gia.mon_an)


ReviewViewSet = DanhGiaViewSet
```

#### 14. `posts/models.py`, `serializers.py`, `views.py`
**Tại `posts/models.py`**:
```python
from django.conf import settings
from django.db import models
from django.utils.text import slugify
from foods.models import MoHinhThoiGian


class DanhMucBaiViet(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    duong_dan = models.SlugField(max_length=120, unique=True, blank=True)
    mo_ta = models.TextField(blank=True)

    class Meta:
        db_table = "danh_muc_bai_viet"
        verbose_name = "Danh mục bài viết"

    def save(self, *a, **kw):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*a, **kw)

    @property
    def name(self):
        return self.ten

    @property
    def slug(self):
        return self.duong_dan


class BaiViet(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        NHAP = "nhap", "Bản nháp"
        DA_DANG = "da_dang", "Đã đăng"
        LUU_TRU = "luu_tru", "Lưu trữ"

    danh_muc = models.ForeignKey(
        DanhMucBaiViet, null=True, blank=True,
        related_name="danh_sach_bai_viet", on_delete=models.SET_NULL
    )
    tac_gia = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_bai_viet", on_delete=models.PROTECT
    )
    tieu_de = models.CharField(max_length=200)
    duong_dan = models.SlugField(max_length=220, unique=True, blank=True)
    anh_dai_dien = models.TextField(blank=True)
    noi_dung = models.TextField()
    trang_thai = models.CharField(max_length=10, choices=TrangThai.choices, default=TrangThai.NHAP)
    dang_luc = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bai_viet"
        verbose_name = "Bài viết"
        indexes = [models.Index(fields=["trang_thai", "-dang_luc"])]

    def save(self, *a, **kw):
        if not self.duong_dan:
            self.duong_dan = slugify(self.tieu_de)
        super().save(*a, **kw)

    @property
    def category(self):
        return self.danh_muc

    @property
    def author(self):
        return self.tac_gia

    @property
    def title(self):
        return self.tieu_de

    @property
    def slug(self):
        return self.duong_dan

    @property
    def content(self):
        return self.noi_dung

    @property
    def status(self):
        return self.trang_thai

    @property
    def thumbnail_url(self):
        return self.anh_dai_dien

    @property
    def published_at(self):
        return self.dang_luc


# Backward-compatible model aliases
PostCategory = DanhMucBaiViet
Post = BaiViet
BaiViet.Status = BaiViet.TrangThai
Post.Status = BaiViet.TrangThai
```
**Tại `posts/serializers.py`**:
```python
from rest_framework import serializers
from .models import DanhMucBaiViet, BaiViet, PostCategory, Post


class DanhMucBaiVietSerializer(serializers.ModelSerializer):
    class Meta:
        model = DanhMucBaiViet
        fields = "__all__"


class BaiVietSerializer(serializers.ModelSerializer):
    ten_danh_muc = serializers.CharField(source="danh_muc.ten", read_only=True)
    ten_tac_gia = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="danh_muc.ten", read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BaiViet
        fields = "__all__"
        read_only_fields = ("tac_gia",)

    def get_ten_tac_gia(self, obj):
        return obj.tac_gia.get_full_name() or obj.tac_gia.username if obj.tac_gia else "Nhà hàng"

    get_author_name = get_ten_tac_gia


PostCategorySerializer = DanhMucBaiVietSerializer
PostSerializer = BaiVietSerializer
```
**Tại `posts/views.py`**:
```python
from rest_framework import viewsets
from api.permissions import LaNhanVienHoacChiDoc, IsStaffOrReadOnly
from .models import DanhMucBaiViet, BaiViet, PostCategory, Post
from .serializers import DanhMucBaiVietSerializer, BaiVietSerializer, PostCategorySerializer, PostSerializer


class DanhMucBaiVietViewSet(viewsets.ModelViewSet):
    queryset = DanhMucBaiViet.objects.all()
    serializer_class = DanhMucBaiVietSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"


class BaiVietViewSet(viewsets.ModelViewSet):
    serializer_class = BaiVietSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"

    def get_queryset(self):
        q = BaiViet.objects.select_related("danh_muc", "tac_gia").order_by("-dang_luc", "-tao_luc")
        user = self.request.user
        if not user.is_authenticated or not getattr(user, "la_nhan_vien_nha_hang", False):
            q = q.filter(trang_thai=BaiViet.TrangThai.DA_DANG)
        tim_kiem = self.request.query_params.get("tim_kiem") or self.request.query_params.get("search")
        if tim_kiem:
            q = q.filter(tieu_de__icontains=tim_kiem)
        return q

    def perform_create(self, serializer):
        serializer.save(tac_gia=self.request.user)


PostCategoryViewSet = DanhMucBaiVietViewSet
PostViewSet = BaiVietViewSet
```

#### 15. `analytics/models.py`, `serializers.py`, `views.py`
**Tại `analytics/models.py`**:
```python
from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian


class ThongBao(MoHinhThoiGian):
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_thong_bao", on_delete=models.CASCADE
    )
    loai = models.CharField(max_length=50)
    tieu_de = models.CharField(max_length=200)
    noi_dung = models.TextField()
    loai_tham_chieu = models.CharField(max_length=30, blank=True)
    id_tham_chieu = models.BigIntegerField(null=True, blank=True)
    da_doc = models.BooleanField(default=False)
    doc_luc = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "thong_bao"
        verbose_name = "Thông báo"
        indexes = [models.Index(fields=["nguoi_dung", "da_doc", "-tao_luc"])]

    @property
    def user(self):
        return self.nguoi_dung

    @property
    def type(self):
        return self.loai

    @property
    def title(self):
        return self.tieu_de

    @property
    def message(self):
        return self.noi_dung

    @property
    def is_read(self):
        return self.da_doc

    @is_read.setter
    def is_read(self, val):
        self.da_doc = val

    @property
    def read_at(self):
        return self.doc_luc

    @read_at.setter
    def read_at(self, val):
        self.doc_luc = val


# Backward-compatible model aliases
Notification = ThongBao
```
**Tại `analytics/serializers.py`**:
```python
from rest_framework import serializers
from .models import ThongBao, Notification


class ThongBaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThongBao
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "doc_luc")


NotificationSerializer = ThongBaoSerializer
```
**Tại `analytics/views.py`**:
```python
from django.db.models import Sum, Count
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.permissions import LaNhanVienNhaHang, IsRestaurantStaff
from .models import ThongBao, Notification
from .serializers import ThongBaoSerializer, NotificationSerializer
from orders.models import DonHang, Order
from reservations.models import DatBan, Reservation


class ThongBaoViewSet(viewsets.ModelViewSet):
    serializer_class = ThongBaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ThongBao.objects.filter(nguoi_dung=self.request.user)

    def perform_create(self, serializer):
        serializer.save(nguoi_dung=self.request.user)

    @action(detail=True, methods=["post"])
    def da_doc(self, request, pk=None):
        tb = self.get_object()
        tb.da_doc = True
        tb.doc_luc = timezone.now()
        tb.save(update_fields=["da_doc", "doc_luc", "cap_nhat_luc"])
        return Response(self.get_serializer(tb).data)

    read = da_doc


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [LaNhanVienNhaHang]

    def list(self, request):
        don_hang = DonHang.objects.exclude(trang_thai=DonHang.TrangThai.DA_HUY)
        doanh_thu = don_hang.aggregate(val=Sum("tong_tien"))["val"] or 0
        so_don = don_hang.count()
        so_dat_ban = DatBan.objects.count()
        so_khach = don_hang.values("khach_hang").distinct().count()
        phan_bo_trang_thai = list(don_hang.values("trang_thai").annotate(count=Count("id")))

        return Response({
            # Vietnamese standard keys
            "doanh_thu": doanh_thu,
            "so_don_hang": so_don,
            "so_dat_ban": so_dat_ban,
            "so_khach_hang": so_khach,
            "don_hang_theo_trang_thai": phan_bo_trang_thai,
            # English legacy compatibility keys
            "revenue": doanh_thu,
            "orders": so_don,
            "reservations": so_dat_ban,
            "customers": so_khach,
            "orders_by_status": phan_bo_trang_thai,
        })


NotificationViewSet = ThongBaoViewSet
```

#### 16. `api/urls.py` (Hỗ trợ định tuyến song ngữ - Dual Routing)
Đăng ký router hỗ trợ cả hai phong cách URL:
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import health_check
from accounts.views import XacThucViewSet, NguoiDungViewSet, VaiTroViewSet, QuyenHanViewSet
from foods.views import DanhMucViewSet, NguyenLieuViewSet, MonAnViewSet, TheMonAnViewSet, LichSuKhoViewSet
from orders.views import DonHangViewSet
from reservations.views import BanAnViewSet, DatBanViewSet
from promotions.views import PromotionViewSet, PromotionCodeViewSet, PromotionUsageViewSet
from posts.views import PostViewSet, PostCategoryViewSet
from reviews.views import ReviewViewSet
from recommendations.views import InteractionViewSet, RecommendationViewSet
from chat.views import ChatRoomViewSet
from analytics.views import NotificationViewSet, DashboardViewSet
from branches.views import BranchViewSet
from payments.views import PaymentViewSet
from carts.views import CartViewSet

router = DefaultRouter()

# 1. Accounts
router.register("auth", XacThucViewSet, basename="auth")
router.register("users", NguoiDungViewSet, basename="user")
router.register("nguoi-dung", NguoiDungViewSet, basename="nguoi-dung")
router.register("roles", VaiTroViewSet, basename="role")
router.register("vai-tro", VaiTroViewSet, basename="vai-tro")
router.register("permissions", QuyenHanViewSet, basename="permission")

# 2. Foods
router.register("foods", MonAnViewSet, basename="food")
router.register("mon-an", MonAnViewSet, basename="mon-an")
router.register("categories", DanhMucViewSet, basename="category")
router.register("danh-muc", DanhMucViewSet, basename="danh-muc")
router.register("tags", TheMonAnViewSet, basename="tag")
router.register("the-mon-an", TheMonAnViewSet, basename="the-mon-an")
router.register("ingredients", NguyenLieuViewSet, basename="ingredient")
router.register("nguyen-lieu", NguyenLieuViewSet, basename="nguyen-lieu")
router.register("inventory-transactions", LichSuKhoViewSet, basename="inventory-transaction")
router.register("kho", LichSuKhoViewSet, basename="kho")

# 3. Branches
router.register("branches", BranchViewSet, basename="branch")
router.register("chi-nhanh", BranchViewSet, basename="chi-nhanh")

# 4. Tables & Reservations
router.register("tables", BanAnViewSet, basename="table")
router.register("ban-an", BanAnViewSet, basename="ban-an")
router.register("reservations", DatBanViewSet, basename="reservation")
router.register("dat-ban", DatBanViewSet, basename="dat-ban")

# 5. Orders
router.register("orders", DonHangViewSet, basename="order")
router.register("don-hang", DonHangViewSet, basename="don-hang")

# 6. Payments
router.register("payments", PaymentViewSet, basename="payment")
router.register("thanh-toan", PaymentViewSet, basename="thanh-toan")

# 7. Promotions
router.register("promotions", PromotionViewSet, basename="promotion")
router.register("khuyen-mai", PromotionViewSet, basename="khuyen-mai")
router.register("promotion-codes", PromotionCodeViewSet, basename="promotion-code")
router.register("promotion-usages", PromotionUsageViewSet, basename="promotion-usage")

# 8. Carts
router.register("cart", CartViewSet, basename="cart")
router.register("gio-hang", CartViewSet, basename="gio-hang")

# 9. Reviews
router.register("reviews", ReviewViewSet, basename="review")
router.register("danh-gia", ReviewViewSet, basename="danh-gia")

# 10. Posts
router.register("posts", PostViewSet, basename="post")
router.register("bai-viet", PostViewSet, basename="bai-viet")
router.register("post-categories", PostCategoryViewSet, basename="post-category")
router.register("danh-muc-bai-viet", PostCategoryViewSet, basename="danh-muc-bai-viet")

# 11. Chat
router.register("chat/rooms", ChatRoomViewSet, basename="chat-room")
router.register("hoi-thoai", ChatRoomViewSet, basename="hoi-thoai")

# 12. Recommendations
router.register("recommendations", RecommendationViewSet, basename="recommendation")
router.register("goi-y", RecommendationViewSet, basename="goi-y")
router.register("interactions", InteractionViewSet, basename="interaction")
router.register("tuong-tac", InteractionViewSet, basename="tuong-tac")

# 13. Analytics & Notifications
router.register("notifications", NotificationViewSet, basename="notification")
router.register("thong-bao", NotificationViewSet, basename="thong-bao")
router.register("analytics/dashboard", DashboardViewSet, basename="dashboard")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("", include(router.urls)),
]
```

---

## 5. Verification Method (Kế hoạch kiểm chứng cho Implementer)

Sau khi Implementer hoàn tất việc áp dụng mã theo hướng dẫn trên, tiến hành kiểm chứng độc lập theo các bước sau:

### Bước 1: Kiểm tra cú pháp và tính toàn vẹn của Model & Django Settings
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py check
```
**Điều kiện đạt**:
Lệnh trả về mã thoát `0` và thông báo:
```text
System check identified no issues (0 silenced).
```

### Bước 2: Kiểm tra khả năng import song song tiếng Anh và tiếng Việt
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
from foods.models import Food, MonAn, Category, DanhMuc
assert Food is MonAn
assert Category is DanhMuc

from orders.models import Order, DonHang, OrderItem, ChiTietDonHang
assert Order is DonHang
assert OrderItem is ChiTietDonHang

from reservations.models import Table, BanAn, Reservation, DatBan
assert Table is BanAn
assert Reservation is DatBan

from accounts.models import User, NguoiDung, Role, VaiTro
assert User is NguoiDung
assert Role is VaiTro

from payments.models import Payment, ThanhToan
assert Payment is ThanhToan

from carts.models import Cart, GioHang, CartItem, ChiTietGioHang
assert Cart is GioHang
assert CartItem is ChiTietGioHang

from reviews.models import Review, DanhGia
assert Review is DanhGia

from posts.models import Post, BaiViet, PostCategory, DanhMucBaiViet
assert Post is BaiViet
assert PostCategory is DanhMucBaiViet

from analytics.models import Notification, ThongBao
assert Notification is ThongBao

from chat.models import ChatRoom, HoiThoai, ChatMessage, TinNhan
assert ChatRoom is HoiThoai
assert ChatMessage is TinNhan

from recommendations.models import FoodInteraction, TuongTacMonAn, Recommendation, GoiYMonAn
assert FoodInteraction is TuongTacMonAn
assert Recommendation is GoiYMonAn

print('ALL 13 APPS MODEL ALIASES VERIFIED SUCCESSFULLY!')
"
```
**Điều kiện đạt**: Output in ra `ALL 13 APPS MODEL ALIASES VERIFIED SUCCESSFULLY!`.

### Bước 3: Dọn dẹp và tái sinh Migrations sạch (Clean Migrations)
1. Xóa các migration cũ (giữ lại `__init__.py`):
```bash
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
```
2. Sinh migration mới đồng nhất 13 app:
```bash
./.venv/bin/python manage.py makemigrations accounts foods branches reservations orders payments promotions chat recommendations carts reviews posts analytics
```
3. Kiểm tra kế hoạch migration:
```bash
./.venv/bin/python manage.py showmigrations
```
**Điều kiện đạt**: Mỗi app có migration `0001_initial`, không có xung đột phụ thuộc vòng tròn (circular dependencies).

### Bước 4: Kiểm tra CSDL & Bảng dữ liệu theo `moc_schema_tieng_viet.sql`
Sau khi PostgreSQL khởi chạy:
```bash
./.venv/bin/python manage.py migrate
```
**Điều kiện đạt**: Tất cả 36 bảng CSDL tiếng Việt (`mon_an`, `don_hang`, `dat_ban`, `gio_hang`, `chi_tiet_gio_hang`, `danh_gia`, `bai_viet`, `thong_bao`, v.v.) được tạo thành công trong PostgreSQL.

---
**Tài liệu này đã hoàn tất và sẵn sàng chuyển giao cho Implementer thực thi.**
