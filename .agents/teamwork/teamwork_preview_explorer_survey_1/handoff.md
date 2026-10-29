# BÁO CÁO KHẢO SÁT & ĐIỀU TRA TOÀN DIỆN BACKEND & DATABASE SCHEMA
**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Tác giả**: Backend & Database Schema Explorer  
**Thời gian**: 2026-10-14T03:16:00Z  
**Đường dẫn**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_survey_1/handoff.md`

---

## 1. Observation (Các quan sát trực tiếp và bằng chứng thực tế)

### 1.1. Lỗi trực tiếp khi chạy kiểm tra hệ thống (`python manage.py check`)
Khi thực thi lệnh kiểm tra Django trong môi trường ảo:
```bash
./.venv/bin/python manage.py check
```
Kết quả trả về mã lỗi `1` với Traceback nguyên văn:
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

### 1.2. Phân tích hiện trạng các Django App (Inventory & Trạng thái phân mảnh)
Tại thư mục `moc-backend/`, có 13 ứng dụng Django và thư mục cấu hình `config/` (lưu ý: dispatch nhắc đến `moc-backend/core/`, nhưng thực tế project cấu hình tại `moc-backend/config/` với `ROOT_URLCONF = 'config.urls'` và `WSGI_APPLICATION = 'config.wsgi.application'`):

| Tên App | models.py | views.py | serializers.py | admin.py | Đánh giá hiện trạng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`accounts`** | Tiếng Việt (`VaiTro`, `QuyenHan`, `NguoiDung`, `NguoiDungVaiTro`) | Tiếng Việt (`XacThucViewSet`, `NguoiDungViewSet`, ...) | Tiếng Việt (`NguoiDungSerializer`, ...) | ❌ **LỖI**: dòng 4 import `Role, User` vốn không tồn tại | `settings.AUTH_USER_MODEL = "accounts.User"` bị sai (phải là `accounts.NguoiDung`) |
| **`foods`** | Tiếng Việt (`DanhMuc`, `MonAn`, `TheMonAn`, `NguyenLieu`, `HinhAnhMonAn`, `LichSuXuatNhapKho`) | Tiếng Việt (`DanhMucViewSet`, `MonAnViewSet`, ...) | Tiếng Việt (`DanhMucSerializer`, `MonAnSerializer`, ...) | Trống | Model chuẩn theo SQL, nhưng thiếu alias `Food`, `Category` khiến app khác import bị gãy |
| **`branches`** | Tiếng Việt (`ChiNhanh`) | ❌ **LỖI**: dòng 3 import `Branch` | ❌ **LỖI**: dòng 2 import `Branch` | Trống | View và serializer viết bằng tiếng Anh trên model tiếng Việt |
| **`reservations`**| Tiếng Việt (`BanAn`, `ChinhSachDatCoc`, `DatBan`, `MonAnTrongDatBan`) | Tiếng Việt (`BanAnViewSet`, `DatBanViewSet`) | Tiếng Việt (`DatBanSerializer`, ...) | Trống | Có bug query: `prefetch_related("food_items__mon_an")` và `source="food_items"` lệch `related_name="danh_sach_mon"` |
| **`orders`** | Tiếng Việt (`DonHang`, `ChiTietDonHang`, `LichSuTrangThaiDon`) | Tiếng Việt (`DonHangViewSet`) | Tiếng Việt (`DonHangSerializer`, ...) | Trống | Có bug query: `prefetch_related("items__mon_an")` và `source="items"` lệch `related_name="danh_sach_mon"` |
| **`payments`** | Tiếng Việt (`ThanhToan`) | ❌ **LỖI**: dòng 7 import `Payment` | ❌ **LỖI**: dòng 2 import `Payment` | Trống | View & serializer dùng model tiếng Anh và field tiếng Anh |
| **`promotions`**| Tiếng Việt (`KhuyenMai`, `MaKhuyenMai`, `LichSuDungKhuyenMai`) | ❌ **LỖI**: dòng 4 import `Promotion, PromotionCode, PromotionUsage` | ❌ **LỖI**: dòng 2 import `Promotion...` | Trống | View & serializer dùng model tiếng Anh |
| **`chat`** | Tiếng Việt (`HoiThoai`, `TinNhan`) | ❌ **LỖI**: dòng 6 import `ChatRoom, ChatMessage` | ❌ **LỖI**: dòng 2 import `ChatRoom, ChatMessage` | Trống | View & serializer dùng model tiếng Anh |
| **`recommendations`** | Tiếng Việt (`TuongTacMonAn`, `GoiYMonAn`), `services.py` hoàn thiện thuật toán TF-IDF | ❌ **LỖI**: dòng 4 import `FoodInteraction, Recommendation`, dòng 6 import `Food` | ❌ **LỖI**: dòng 2 import `FoodInteraction`, dòng 3 import `FoodSerializer` | Trống | `services.py` dùng tiếng Việt đúng chuẩn, nhưng `views.py` và `serializers.py` dùng tiếng Anh |
| **`carts`** | ❌ **LỖI**: Tiếng Anh (`Cart`, `CartItem`), dòng 4 import `Food` | Tiếng Anh (`CartViewSet`) | ❌ **LỖI**: dòng 2-3 import `Food`, `FoodSerializer` | Không có | Chưa được Việt hóa, thiếu `db_table = "gio_hang"` |
| **`reviews`** | ❌ **LỖI**: Tiếng Anh (`Review`), dòng 3 import `Food`, dòng 9-10 FK tới `"orders.Order"`, `"orders.OrderItem"` | ❌ **LỖI**: dòng 18 import `FoodInteraction` | ❌ **LỖI**: dòng 2 import `Order, OrderItem` | Trống | Chưa được Việt hóa, thiếu `db_table = "danh_gia"` |
| **`posts`** | ❌ **LỖI**: Tiếng Anh (`PostCategory`, `Post`) | Tiếng Anh (`PostViewSet`) | Tiếng Anh (`PostSerializer`) | Trống | Chưa được Việt hóa, thiếu `db_table = "danh_muc_bai_viet"`, `"bai_viet"` |
| **`analytics`** | ❌ **LỖI**: Tiếng Anh (`Notification`) | ❌ **LỖI**: dòng 10-11 import `Order`, `Reservation` | Tiếng Anh (`NotificationSerializer`) | Trống | Chưa được Việt hóa, thiếu `db_table = "thong_bao"` |

### 1.3. Khảo sát Lược đồ CSDL chuẩn (`moc_schema_tieng_viet.sql`)
File CSDL chuẩn `moc_schema_tieng_viet.sql` định nghĩa:
- **Extensions**: `postgis` (cho `chi_nhanh.toa_do_gis` kiểu `geography(Point, 4326)`), `pgcrypto`.
- **17 Kiểu ENUM**:
  1. `kieu_gioi_tinh`: `'nam','nu','khac'`
  2. `trang_thai_ban`: `'trong','dang_giu','da_dat','dang_phuc_vu','bao_tri'`
  3. `hinh_thuc_dat_ban`: `'chi_giu_cho','dat_ban_va_goi_mon','dat_ban_goi_mon_chinh_sua'`
  4. `trang_thai_dat_ban`: `'cho_thanh_toan','da_xac_nhan','khach_da_den','hoan_tat','da_huy','khach_khong_den'`
  5. `trang_thai_coc`: `'chua_thanh_toan','dang_xu_ly','thanh_cong','that_bai','da_hoan_tien','hoan_tien_mot_phan'`
  6. `moc_huy_dat_ban`: `'truoc_24h','tu_6_den_24h','trong_6h','khach_khong_den'`
  7. `trang_thai_don_hang`: `'cho_tiep_nhan','da_xac_nhan','dang_che_bien','san_sang','hoan_tat','da_huy'`
  8. `hinh_thuc_don_hang`: `'giao_hang','tu_den_lay'`
  9. `loai_thanh_toan`: `'don_hang','tien_coc'`
  10. `trang_thai_thanh_toan`: `'cho_xu_ly','thanh_cong','that_bai','da_hoan_tien'`
  11. `kieu_giam_gia`: `'phan_tram','so_tien_co_dinh'`
  12. `trang_thai_gio_hang`: `'dang_su_dung','da_thanh_toan','bo_do'`
  13. `trang_thai_bai_viet`: `'nhap','da_dang','luu_tru'`
  14. `trang_thai_hoi_thoai`: `'mo','dong'`
  15. `loai_tin_nhan`: `'van_ban','hinh_anh','he_thong'`
  16. `loai_tuong_tac`: `'xem','them_gio_hang','dat_mon','danh_gia','yeu_thich'`
  17. `loai_giao_dich_kho`: `'nhap','xuat','dieu_chinh'`
- **36 Bảng nghiệp vụ**:
  * Nhóm RBAC: `vai_tro`, `quyen_han`, `vai_tro_quyen_han`, `nguoi_dung`, `nguoi_dung_vai_tro`.
  * Nhóm Cơ sở & Bàn: `chi_nhanh`, `ban_an`.
  * Nhóm Thực đơn & Kho: `danh_muc`, `the_mon_an`, `nguyen_lieu`, `mon_an`, `hinh_anh_mon_an`, `mon_an_the`, `dinh_muc_nguyen_lieu`, `lich_su_xuat_nhap_kho`.
  * Nhóm Giỏ hàng: `gio_hang`, `chi_tiet_gio_hang`.
  * Nhóm Đặt bàn & Đặt cọc: `chinh_sach_dat_coc`, `quy_tac_huy_dat_coc`, `dat_ban`, `mon_an_trong_dat_ban`.
  * Nhóm Khuyến mãi: `khuyen_mai`, `ma_khuyen_mai`, `lich_su_dung_khuyen_mai`.
  * Nhóm Đơn hàng: `don_hang`, `chi_tiet_don_hang`, `lich_su_trang_thai_don`.
  * Nhóm Thanh toán: `thanh_toan`.
  * Nhóm Blog & Đánh giá: `danh_muc_bai_viet`, `bai_viet`, `danh_gia`.
  * Nhóm Chat: `hoi_thoai`, `tin_nhan`.
  * Nhóm Thông báo: `thong_bao`.
  * Nhóm AI: `tuong_tac_mon_an`, `goi_y_mon_an`.

### 1.4. Tình trạng Migrations hiện tại
Tất cả các file migration `0001_initial.py` trong 13 app đều được sinh ra từ ngày **07/09/2026** dựa trên bộ model tiếng Anh cũ (ví dụ: `foods/migrations/0001_initial.py` tạo `Category`, `Food`, `Tag`; `orders/migrations/0001_initial.py` tạo `Order`, `OrderItem`).
Chưa có bất kỳ file migration nào cho các model tiếng Việt (`MonAn`, `DonHang`, `DatBan`, `NguoiDung`, v.v.).
Nếu áp dụng `migrate`, CSDL sẽ bị tạo các bảng tiếng Anh mặc định (`foods_food`, `orders_order`) thay vì các bảng tiếng Việt (`mon_an`, `don_hang`) như thiết kế của `moc_schema_tieng_viet.sql`.

### 1.5. Cấu hình Môi trường & Dịch vụ ngoài (PostgreSQL, GIS, Redis, Channels)
1. **PostGIS, GDAL, GEOS**:
   - `config/settings.py` đã cấu hình đường dẫn thư viện Homebrew trên macOS:
     ```python
     if platform.system() == "Darwin":
         GDAL_LIBRARY_PATH = "/opt/homebrew/opt/gdal/lib/libgdal.dylib"
         GEOS_LIBRARY_PATH = "/opt/homebrew/opt/geos/lib/libgeos_c.dylib"
     ```
   - Kiểm tra trực tiếp trên máy: cả 2 symlink `/opt/homebrew/opt/gdal/lib/libgdal.dylib` và `/opt/homebrew/opt/geos/lib/libgeos_c.dylib` đều tồn tại hợp lệ và liên kết tới `libgdal.39.dylib` và `libgeos_c.1.dylib`.
2. **PostgreSQL**:
   - `moc-backend/.env` định cấu hình `DB_NAME=moc_db`, `DB_USER=postgres`, `DB_PASSWORD=vu2005`, `DB_HOST=localhost`, `DB_PORT=5432`.
   - Kiểm tra `pg_isready -h localhost -p 5432`: Trả về `no response` (service PostgreSQL chưa được kích hoạt ở thời điểm khảo sát).
3. **Redis & Django Channels**:
   - `requirements.txt` và virtualenv đã có sẵn `channels==4.3.2`, `channels_redis==4.3.0`, `redis==8.1.0`.
   - `config/settings.py`: Chưa có `'channels'` trong `INSTALLED_APPS`, chưa cấu hình `ASGI_APPLICATION`, chưa cấu hình `CHANNEL_LAYERS`, chưa cấu hình Redis trong `CACHES`.
   - `config/asgi.py`: Mới chỉ bọc `get_asgi_application()`, chưa có WebSocket routing hay middleware xác thực.
   - App `chat`: Chưa có file `consumers.py` và `routing.py`.

### 1.6. Khảo sát dữ liệu test (`Du-lieu-test.txt`)
Nội dung file gồm:
- 5 câu lệnh `INSERT INTO categories` (Lẩu, Nướng, Gỏi, Nhâm nhi, Đồ uống).
- 100 câu lệnh `INSERT INTO foods` (mỗi danh mục đúng 20 món ăn, có `spicy_level`, `price`, `is_vegetarian`, `track_inventory`).
- 4 câu lệnh `INSERT INTO tags` (Món mới, Bán chạy, Đặc biệt, Ăn chay).
- **Điểm thiếu hụt so với Acceptance Criteria**: File hoàn toàn không có dữ liệu cho chi nhánh (`chi_nhanh`), bàn ăn (`ban_an`), chính sách đặt cọc (`chinh_sach_dat_coc`, `quy_tac_huy_dat_coc`), tài khoản người dùng mẫu (`nguoi_dung`).

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới kết luận)

1. **Từ lỗi `manage.py check` (Mục 1.1) và Bảng Inventory (Mục 1.2)**:
   - Các ứng dụng trong `moc-backend` bị chia cắt thành 2 nửa: một nửa đã refactor sang tiếng Việt (`foods`, `orders`, `reservations`, `branches`, `payments`, `promotions`, `chat`, `recommendations`, `accounts`), nhưng nửa còn lại (`carts`, `reviews`, `posts`, `analytics`) vẫn giữ nguyên model tiếng Anh cũ.
   - Khi `carts/models.py:4` và `reviews/models.py:3` cố import `Food` từ `foods.models`, Python throw `ImportError` ngay lập tức vì `foods/models.py` chỉ định nghĩa `MonAn`.
   - Đồng thời `reviews/models.py:9-10` trỏ khóa ngoại tới `"orders.Order"` và `"orders.OrderItem"`, trong khi `orders` chỉ có `DonHang` và `ChiTietDonHang`.
   - Hơn nữa, `config/settings.py:163` đặt `AUTH_USER_MODEL = "accounts.User"`, trong khi `accounts/models.py` đặt tên model là `NguoiDung`. `accounts/admin.py:4` cũng cố import `Role, User`.
   - *Suy luận*: Hệ thống backend hiện không thể khởi động hay biên dịch ở bất kỳ môi trường nào nếu không chuẩn hóa triệt để tên model hoặc cung cấp cơ chế tương thích alias.

2. **Từ sự sai lệch giữa `models.py` với `views.py` và `serializers.py` (Mục 1.2)**:
   - Trong các app `branches`, `payments`, `promotions`, `chat`, `recommendations`, các kỹ sư trước đây đã đổi tên trong `models.py` sang tiếng Việt (`ChiNhanh`, `ThanhToan`, `KhuyenMai`, `HoiThoai`, `TuongTacMonAn`), nhưng **quên** không cập nhật `views.py` và `serializers.py` của chính các app đó, dẫn đến việc các file này tiếp tục import `Branch`, `Payment`, `Promotion`, `ChatRoom`, `FoodInteraction` từ `.models` cục bộ.
   - Khi fix xong `Food` vs `MonAn`, `manage.py check` sẽ tiếp tục gãy lần lượt tại tất cả các view/serializer này nếu không được xử lý đồng bộ.

3. **Từ tình trạng Migrations (Mục 1.4) và CSDL (Mục 1.3)**:
   - Các file migration cũ từ 07/09/2026 hoàn toàn không phản ánh thực tế cấu trúc bảng trong `moc_schema_tieng_viet.sql`. Nếu chạy `makemigrations` mà vẫn giữ các migration cũ, Django sẽ cố tạo các lệnh `AlterField` / `RenameModel` phức tạp và dễ gây xung đột toàn bộ khóa ngoại.
   - Vì CSDL trên local chưa chạy migration (Postgres chưa chạy và database chưa nạp), phương án tối ưu nhất là xóa bỏ toàn bộ các migration cũ 2026-09-07 và tạo một bộ migration ban đầu mới tinh (`0001_initial.py`) đồng nhất hoàn toàn với `moc_schema_tieng_viet.sql`.

4. **Từ cấu hình Frontend và API Mappers (Khảo sát frontend)**:
   - `moc-frontend/src/api/mappers.ts` đã được thiết kế sẵn để hỗ trợ cả hai phong cách đặt tên field: `raw.ten ?? raw.name`, `raw.duong_dan ?? raw.slug`, `raw.don_gia ?? raw.price`.
   - Tuy nhiên, một số endpoint frontend đang gọi đường dẫn tiếng Việt như `/api/mon-an/`, `/api/dat-ban/`, `/api/goi-y/`, trong khi `api/urls.py` của backend đăng ký router tiếng Anh (`foods`, `reservations`, `recommendations`).
   - *Suy luận*: Để frontend và backend kết nối mượt mà không lỗi 404, backend cần hỗ trợ song song (dual routing) hoặc đồng bộ chuẩn xác endpoint theo tài liệu API.

5. **Từ phân tích dữ liệu test (Mục 1.6)**:
   - Dữ liệu `Du-lieu-test.txt` viết cho các bảng tiếng Anh (`categories`, `foods`, `tags`). Do đó, script nạp dữ liệu không thể chỉ chạy `psql < Du-lieu-test.txt` trực tiếp, mà cần một Management Command của Django (`seed_data` hoặc `nap_du_lieu_mau`) đọc và ánh xạ vào `DanhMuc`, `MonAn`, `TheMonAn`, đồng thời tự động bổ sung dữ liệu chi nhánh, bàn ăn, chính sách cọc và người dùng mẫu theo tiêu chí nghiệm thu của đề bài.

---

## 3. Caveats (Các điểm giới hạn & Giả định)

1. **Giả định về CSDL chưa khởi tạo dữ liệu thật**: Giả định rằng CSDL PostgreSQL trên máy phát triển chưa có dữ liệu quan trọng cần giữ lại, do đó việc reset toàn bộ migration `0001_initial.py` là an toàn 100% và không làm mất dữ liệu sản xuất.
2. **Quyền thao tác của Agent Explorer**: Theo nguyên tắc `read-only`, Explorer không trực tiếp sửa đổi source code của dự án, mà cung cấp chi tiết mọi vị trí và phương án xử lý cụ thể để Implementer thực hiện trong Milestone 1.
3. **Môi trường Redis & PostgreSQL**: Hiện tại PostgreSQL và Redis daemon chưa được start trên máy local. Khi Implementer thực hiện bước chạy migration và test realtime, cần khởi chạy PostgreSQL và Redis daemon.

---

## 4. Conclusion (Kết luận đánh giá tổng thể)

1. **Nguyên nhân cốt lõi**: Dự án `moc-backend` đang dừng lại ở giữa chừng của một đợt tái cấu trúc (refactoring) từ mô hình tiếng Anh sang lược đồ tiếng Việt theo `moc_schema_tieng_viet.sql`. Việc đổi tên chỉ mới thực hiện ở 9/13 app `models.py`, trong khi `carts`, `reviews`, `posts`, `analytics`, các file `admin.py`, và toàn bộ `views.py`/`serializers.py` của các app còn lại chưa được cập nhật.
2. **Giải pháp kiến trúc tốt nhất (Model Alias & Schema Unification)**:
   - Chuẩn hóa 100% tất cả các model chính theo đúng tên tiếng Việt và chỉ định rõ `db_table` khớp từng chữ với `moc_schema_tieng_viet.sql`.
   - Cung cấp **Model Alias** tại cuối mỗi `models.py` (ví dụ: `Food = MonAn`, `Category = DanhMuc`, `Order = DonHang`, `Branch = ChiNhanh`, `Payment = ThanhToan`, `User = NguoiDung`) để:
     * Khắc phục ngay lập tức mọi lỗi `ImportError` ở các file chưa kịp refactor.
     * Đảm bảo tính tương thích ngược tuyệt đối (Backward Compatibility).
   - Tái tạo sạch sẽ toàn bộ migration ban đầu (`0001_initial.py`) cho tất cả các app.
   - Xây dựng một Django Management Command `nap_du_lieu_mau` để nạp danh mục, 100 món ăn từ `Du-lieu-test.txt` cùng các chi nhánh, bàn ăn, chính sách cọc mẫu.

---

## 5. Verification Method (Kế hoạch hành động & Phương pháp kiểm chứng chi tiết cho Milestone 1)

Dưới đây là kế hoạch 8 bước chi tiết có thể thực thi ngay cho Implementer trong Milestone 1:

### Bước 1: Cấu hình `config/settings.py` & `api/permissions.py`
1. Tại `moc-backend/config/settings.py`:
   - Dòng 163: Đổi `AUTH_USER_MODEL = "accounts.User"` thành `AUTH_USER_MODEL = "accounts.NguoiDung"`.
   - Bổ sung alias trong `accounts/models.py`: `User = NguoiDung`, `Role = VaiTro`, `Permission = QuyenHan`.
2. Tại `moc-backend/accounts/admin.py`:
   - Sửa dòng 4 từ `from .models import Role, User` thành `from .models import VaiTro, NguoiDung`.
3. Tại `moc-backend/api/permissions.py`:
   - Thêm alias tương thích ngược:
     ```python
     IsRestaurantStaff = LaNhanVienNhaHang
     IsStaffOrReadOnly = LaNhanVienHoacChiDoc
     ```

### Bước 2: Bổ sung Model Alias tại các app tiếng Việt
1. `foods/models.py`:
   ```python
   Food = MonAn
   Category = DanhMuc
   Tag = TheMonAn
   Ingredient = NguyenLieu
   FoodImage = HinhAnhMonAn
   ```
   Tại `foods/serializers.py`:
   ```python
   FoodSerializer = MonAnSerializer
   CategorySerializer = DanhMucSerializer
   ```
2. `orders/models.py`:
   ```python
   Order = DonHang
   OrderItem = ChiTietDonHang
   OrderStatusHistory = LichSuTrangThaiDon
   ```
   Tại `orders/serializers.py`:
   - Dòng 26: Đổi `source="items"` thành `source="danh_sach_mon"`.
   Tại `orders/views.py`:
   - Dòng 18: Đổi `prefetch_related("items__mon_an")` thành `prefetch_related("danh_sach_mon__mon_an")`.
3. `branches/models.py`:
   ```python
   Branch = ChiNhanh
   ```
   Bổ sung các thuộc tính `@property` hoặc cập nhật `branches/serializers.py` và `branches/views.py` để dùng `ChiNhanh`.
4. `reservations/models.py`:
   ```python
   Reservation = DatBan
   Table = BanAn
   ```
   Tại `reservations/serializers.py`:
   - Dòng 40: Đổi `source="food_items"` thành `source="danh_sach_mon"`.
   Tại `reservations/views.py`:
   - Dòng 65: Đổi `prefetch_related("food_items__mon_an")` thành `prefetch_related("danh_sach_mon__mon_an")`.
5. `payments/models.py`:
   ```python
   Payment = ThanhToan
   ```
   Cập nhật `payments/views.py` và `payments/serializers.py` dùng `ThanhToan` (kèm alias cho các trường `order` -> `don_hang`, `reservation` -> `dat_ban`).
6. `promotions/models.py`:
   ```python
   Promotion = KhuyenMai
   PromotionCode = MaKhuyenMai
   PromotionUsage = LichSuDungKhuyenMai
   ```
   Cập nhật `promotions/views.py` và `promotions/serializers.py`.
7. `chat/models.py`:
   ```python
   ChatRoom = HoiThoai
   ChatMessage = TinNhan
   ```
   Cập nhật `chat/views.py` và `chat/serializers.py`.
8. `recommendations/models.py`:
   ```python
   FoodInteraction = TuongTacMonAn
   Recommendation = GoiYMonAn
   ```
   Cập nhật `recommendations/views.py` và `recommendations/serializers.py` liên kết tới `DichVuGoiY` trong `services.py`.

### Bước 3: Chuẩn hóa 4 app còn lại (`carts`, `reviews`, `posts`, `analytics`)
1. **`carts/models.py`**:
   - Đặt tên model `GioHang` (`db_table = "gio_hang"`), `ChiTietGioHang` (`db_table = "chi_tiet_gio_hang"`).
   - Thêm alias `Cart = GioHang`, `CartItem = ChiTietGioHang`.
2. **`reviews/models.py`**:
   - Đặt tên model `DanhGia` (`db_table = "danh_gia"`), liên kết khóa ngoại với `mon_an`, `don_hang`, `chi_tiet_don_hang`.
   - Thêm alias `Review = DanhGia`.
3. **`posts/models.py`**:
   - Đặt tên model `DanhMucBaiViet` (`db_table = "danh_muc_bai_viet"`), `BaiViet` (`db_table = "bai_viet"`).
   - Thêm alias `PostCategory = DanhMucBaiViet`, `Post = BaiViet`.
4. **`analytics/models.py`**:
   - Đặt tên model `ThongBao` (`db_table = "thong_bao"`).
   - Thêm alias `Notification = ThongBao`.

### Bước 4: Tái thiết lập Migrations (Clean Migrations)
1. Xóa các file `0001_initial.py` và `0002_initial.py` cũ trong thư mục `migrations/` của tất cả 13 app (giữ lại file `__init__.py`).
2. Chạy lệnh sinh migration mới:
   ```bash
   ./.venv/bin/python manage.py makemigrations accounts foods branches reservations orders payments promotions chat recommendations carts reviews posts analytics
   ```
3. Chạy lệnh kiểm tra tính hợp lệ của model và cấu hình:
   ```bash
   ./.venv/bin/python manage.py check
   ```
   *Điều kiện nghiệm thu*: Lệnh thoát với mã `0`, không có lỗi (System check identified no issues).

### Bước 5: Cấu hình URL Routing tương thích đa năng (Dual Routing)
Trong `api/urls.py`, đăng ký router để hỗ trợ cả hai phong cách URL mà frontend đang gọi:
```python
router.register("foods", MonAnViewSet, basename="food")
router.register("mon-an", MonAnViewSet, basename="mon-an")
router.register("categories", DanhMucViewSet, basename="category")
router.register("danh-muc", DanhMucViewSet, basename="danh-muc")
router.register("tables", BanAnViewSet, basename="table")
router.register("ban-an", BanAnViewSet, basename="ban-an")
router.register("reservations", DatBanViewSet, basename="reservation")
router.register("dat-ban", DatBanViewSet, basename="dat-ban")
router.register("recommendations", RecommendationViewSet, basename="recommendation")
router.register("goi-y", RecommendationViewSet, basename="goi-y")
```
Và bổ sung các route alias cho Auth trong `accounts/views.py`: `dang_ky` và `register`, `ho_so` và `profile`.

### Bước 6: Xây dựng Management Command nạp dữ liệu mẫu
Tạo command `foods/management/commands/nap_du_lieu_mau.py` (hoặc `seed_data.py`):
1. Đọc và phân tích `Du-lieu-test.txt`.
2. Tạo 5 Danh mục (`DanhMuc`).
3. Tạo 4 Thẻ món ăn (`TheMonAn`).
4. Nạp 100 món ăn (`MonAn`) tương ứng với các danh mục, gán `ton_kho_cache = 100`, `hien_thi = True`, `con_hang = True`.
5. Tạo 3 Chi nhánh (`ChiNhanh`) kèm tọa độ `Point` PostGIS hợp lệ.
6. Tạo 20 Bàn ăn (`BanAn`) trải đều các chi nhánh, sức chứa 2, 4, 6, 8 chỗ.
7. Tạo Chính sách cọc (`ChinhSachDatCoc` và `QuyTacHuyDatCoc`) khớp đúng quy tắc 100% (>24h), 50% (6-24h), 0% (<6h).
8. Tạo các tài khoản người dùng kiểm thử (`admin`, `staff`, `customer`).

### Phương pháp kiểm chứng độc lập (Independent Verification Method):
1. **Kiểm tra Model & Import**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-backend
   ./.venv/bin/python manage.py check
   ```
   *Kỳ vọng*: `System check identified no issues (0 silenced).`
2. **Kiểm tra Migration Plan**:
   ```bash
   ./.venv/bin/python manage.py showmigrations
   ```
   *Kỳ vọng*: Hiển thị danh sách migration sạch của 13 app không có lỗi phụ thuộc vòng tròn (circular dependency).
3. **Kiểm tra Dữ liệu mẫu**:
   ```bash
   ./.venv/bin/python manage.py nap_du_lieu_mau
   ./.venv/bin/python manage.py shell -c "from foods.models import MonAn; print('Tong so mon an:', MonAn.objects.count())"
   ```
   *Kỳ vọng*: In ra `Tong so mon an: 100` (hoặc 100+).
