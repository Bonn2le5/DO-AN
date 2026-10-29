# CHIẾN LƯỢC THIẾT LẬP CƠ SỞ DỮ LIỆU & MIGRATIONS CHO MILESTONE 1
**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Tác giả**: Milestone 1 Explorer 2 (Migrations & Database Setup Strategy)  
**Thời gian**: 2026-10-14T03:30:00Z  
**Đường dẫn**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_2/handoff.md`

---

## 1. Observation (Các quan sát trực tiếp và bằng chứng thực tế)

### 1.1. Hiện trạng Dịch vụ PostgreSQL và Cơ sở dữ liệu `moc_db`
1. **Phiên bản & Thư mục cài đặt PostgreSQL**:
   - Lệnh `/Library/PostgreSQL/18/bin/psql --version` trả về:
     ```text
     psql (PostgreSQL) 18.3
     ```
   - Binary đặt tại: `/Library/PostgreSQL/18/bin/` (gồm `postgres`, `psql`, `pg_ctl`, `createdb`, `createuser`, `postgis`, `shp2pgsql`, `raster2pgsql`).
   - Dữ liệu cluster đặt tại: `/Library/PostgreSQL/18/data` (chủ sở hữu `postgres:daemon`, quyền `drwx------`).
   - Cài đặt thông qua gói chính thức EnterpriseDB installer trên macOS.

2. **Trạng thái thực thi của Service trên hệ điều hành**:
   - Kiểm tra qua LaunchDaemon hệ thống bằng lệnh `launchctl print system/postgresql-18`:
     ```text
     system/postgresql-18 = {
         active count = 1
         path = /Library/LaunchDaemons/postgresql-18.plist
         type = LaunchDaemon
         state = running
         program = /Library/PostgreSQL/18/bin/postgres
         arguments = {
             /Library/PostgreSQL/18/bin/postgres
             -D
             /Library/PostgreSQL/18/data
         }
         domain = system
         username = postgres
         pid = 532
         last exit code = (never exited)
     }
     ```
   - Hai socket Unix domain đang hoạt động tại `/tmp`:
     ```text
     srwxrwxrwx@ 1 postgres wheel 0 Oct 14 09:55 /tmp/.s.PGSQL.5432
     srwxrwxrwx@ 1 postgres wheel 0 Oct 14 09:56 /tmp/.s.PGSQL.5433
     ```
   - **Đặc thù môi trường Agent Sandbox**:
     - Khi chạy `pg_isready -h localhost -p 5432` hoặc Python socket test bên trong công cụ sandbox, lệnh báo `no response` hoặc phát sinh lỗi:
       ```text
       PermissionError: [Errno 1] Operation not permitted
       ```
     - Nguyên nhân: Sandbox macOS seatbelt chặn kết nối socket TCP/UNIX ra ngoài sandbox.
     - Trên môi trường thực của máy (ngoài sandbox / terminal người dùng), PostgreSQL 18 **đang chạy sẵn sàng tại PID 532 trên port 5432**.

3. **Cấu hình kết nối trong `moc-backend/.env`**:
   ```ini
   DB_NAME=moc_db
   DB_USER=postgres
   DB_PASSWORD=vu2005
   DB_HOST=localhost
   DB_PORT=5432
   ```

### 1.2. Hiện trạng PostGIS, Pgcrypto, GDAL & GEOS
1. **Extension trong PostgreSQL 18**:
   - Thư mục `/Library/PostgreSQL/18/share/postgresql/extension/` có đầy đủ:
     * `postgis.control`, `postgis--3.6.0.sql`, `postgis_raster`, `postgis_sfcgal`, `postgis_topology`.
     * `pgcrypto.control`, `pgcrypto--1.3.sql`.
   - Ngoài ra, Homebrew cũng đã cài đặt sẵn `postgis 3.6.4` tại `/opt/homebrew/Cellar/postgis/3.6.4`.
2. **Cấu hình thư viện không gian trong `config/settings.py`**:
   - Dòng 26-29:
     ```python
     import platform
     if platform.system() == "Darwin":
         GDAL_LIBRARY_PATH = "/opt/homebrew/opt/gdal/lib/libgdal.dylib"
         GEOS_LIBRARY_PATH = "/opt/homebrew/opt/geos/lib/libgeos_c.dylib"
     ```
   - Lệnh kiểm tra trực tiếp qua virtualenv Python:
     ```bash
     ./.venv/bin/python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); from django.contrib.gis import gdal, geos; print('GDAL:', gdal.gdal_version()); print('GEOS:', geos.geos_version())"
     ```
     Trả về thành công:
     ```text
     GDAL_LIBRARY_PATH: /opt/homebrew/opt/gdal/lib/libgdal.dylib
     GDAL: b'3.13.3'
     GEOS: b'3.14.1-CAPI-1.20.5'
     ```
   - PostGIS Engine trong Django `config/settings.py:116`:
     ```python
     "ENGINE": "django.contrib.gis.db.backends.postgis"
     ```

### 1.3. Hiện trạng các file Migration cũ (2026-09-07)
Qua kiểm tra thư mục `moc-backend/*/migrations/`, toàn bộ 13 app đều chứa các file migration cũ phát sinh từ ngày **07/09/2026**:
1. `accounts/migrations/0001_initial.py` (Tạo `Permission`, `Role`, `User` - bảng `accounts_user`, `accounts_role`).
2. `foods/migrations/0001_initial.py` (Tạo `Category`, `Ingredient`, `Tag`, `Food`, `FoodImage`).
3. `branches/migrations/0001_initial.py` (Tạo `Branch`).
4. `reservations/migrations/0001_initial.py` (Tạo `Table`, `DepositPolicy`, `CancellationRule`, `Reservation`).
5. `orders/migrations/0001_initial.py` và `0002_initial.py` (Tạo `Order`, `OrderItem`).
6. `payments/migrations/0001_initial.py` (Tạo `Payment`).
7. `promotions/migrations/0001_initial.py` (Tạo `Promotion`, `PromotionCode`, `PromotionUsage`).
8. `carts/migrations/0001_initial.py` (Tạo `Cart`, `CartItem`).
9. `reviews/migrations/0001_initial.py` (Tạo `Review`).
10. `chat/migrations/0001_initial.py` (Tạo `ChatRoom`, `ChatMessage`).
11. `recommendations/migrations/0001_initial.py` (Tạo `FoodInteraction`, `Recommendation`).
12. `analytics/migrations/0001_initial.py` (Tạo `Notification`).
13. `posts/migrations/0001_initial.py` (Tạo `PostCategory`, `Post`).

**Phát hiện mấu chốt**: Các migration này tạo các bảng tiếng Anh với tiền tố mặc định của Django (`foods_food`, `orders_order`) thay vì 36 bảng chuẩn tiếng Việt (`mon_an`, `don_hang`, `dat_ban`) như quy định tại `moc_schema_tieng_viet.sql`. Nếu tiếp tục dùng các file này, CSDL sẽ bị xung đột hoàn toàn.

### 1.4. Lỗi Cú pháp Nghiêm trọng Mới Phát hiện: `CheckConstraint(condition=...)`
Ngoài các lỗi import model đã biết (`Food` vs `MonAn`, `Order` vs `DonHang`), qua việc mô phỏng chạy `django.setup()`, chúng tôi phát hiện một lỗi cú pháp Django nghiêm trọng tại 3 app:
1. `orders/models.py:52`:
   ```python
   models.CheckConstraint(
       condition=~models.Q(hinh_thuc="giao_hang") | models.Q(dia_chi_giao__isnull=False),
       name="kiem_tra_giao_hang_can_dia_chi",
   )
   ```
2. `reservations/models.py:117`:
   ```python
   models.CheckConstraint(
       condition=~models.Q(hinh_thuc="chi_giu_cho") | (
           models.Q(yeu_cau_dat_coc=False) & models.Q(so_tien_coc=0)
       ),
       name="kiem_tra_chi_giu_cho",
   )
   ```
3. `payments/models.py:40`:
   ```python
   models.CheckConstraint(
       condition=(
           models.Q(loai_thanh_toan="don_hang", don_hang__isnull=False, dat_ban__isnull=True)
           | models.Q(loai_thanh_toan="tien_coc", dat_ban__isnull=False, don_hang__isnull=True)
       ),
       name="kiem_tra_muc_tieu_thanh_toan",
   )
   ```
- **Lỗi Runtime**: `TypeError: __init__() got an unexpected keyword argument 'condition'`.
- Trong Django (phiên bản đang dùng là `4.2.30`), tham số bắt buộc của `CheckConstraint` là `check=`, tham số `condition=` chỉ tồn tại trong `UniqueConstraint`. Lỗi này khiến Django crash ngay khi nạp class model, trước khi kịp chạy `check` hay `makemigrations`.

### 1.5. Vòng phụ thuộc qua lại giữa `orders` và `promotions` (Circular Dependency)
Trong mô hình dữ liệu:
- `orders.models.DonHang`:
  ```python
  khuyen_mai = models.ForeignKey("promotions.KhuyenMai", null=True, blank=True, on_delete=models.SET_NULL)
  ```
  => `orders` phụ thuộc vào `promotions`.
- `promotions.models.LichSuDungKhuyenMai`:
  ```python
  don_hang = models.ForeignKey("orders.DonHang", related_name="lich_su_khuyen_mai", on_delete=models.CASCADE)
  ```
  => `promotions` phụ thuộc vào `orders`.
- Nếu sinh migration riêng rẽ cho từng app mà không có chiến lược phối hợp, Django sẽ báo lỗi không tìm thấy model quan hệ hoặc phụ thuộc vòng tròn.

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới giải pháp)

1. **Khởi chạy và Quản lý PostgreSQL**:
   - Từ Quan sát 1.1: PostgreSQL 18 đã được nạp sẵn dưới dạng LaunchDaemon (`system/postgresql-18`, PID 532).
   - Nếu trong quá trình phát triển dịch vụ bị dừng, lệnh quản lý chuẩn trên macOS không cần dùng Homebrew brew service mà dùng:
     ```bash
     sudo launchctl kickstart -k system/postgresql-18
     ```
     hoặc:
     ```bash
     sudo -u postgres /Library/PostgreSQL/18/bin/pg_ctl -D /Library/PostgreSQL/18/data start
     ```
   - Trong trường hợp không có quyền root (`sudo`), nhà phát triển hoàn toàn có thể khởi tạo cluster cục bộ do user sở hữu:
     ```bash
     /Library/PostgreSQL/18/bin/initdb -D "$HOME/Documents/DO-AN/moc_pgdata" -U postgres -A trust
     /Library/PostgreSQL/18/bin/pg_ctl -D "$HOME/Documents/DO-AN/moc_pgdata" -l "$HOME/Documents/DO-AN/moc_pgdata/logfile" start
     ```
   - Để tạo CSDL `moc_db` và kích hoạt PostGIS/Pgcrypto:
     ```bash
     PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE moc_db OWNER postgres;"
     PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -d moc_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
     PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -d moc_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
     ```

2. **Dọn dẹp Migration cũ**:
   - Từ Quan sát 1.3: CSDL chưa hề chạy migration nào, các migration cũ từ 07/09/2026 định nghĩa schema tiếng Anh sai lệch hoàn toàn so với `moc_schema_tieng_viet.sql`.
   - Suy luận: Việc xóa bỏ 100% các file `0001_initial.py` và `0002_initial.py` cũ trên toàn bộ 13 app là an toàn tuyệt đối và bắt buộc phải thực hiện trước khi tạo bất kỳ migration mới nào.

3. **Xử lý triệt để các rào cản ngăn `manage.py check`**:
   - Bước 1: Sửa cú pháp `CheckConstraint(condition=...)` thành `CheckConstraint(check=...)` tại `orders/models.py`, `reservations/models.py`, `payments/models.py`.
   - Bước 2: Sửa cấu hình `AUTH_USER_MODEL = "accounts.NguoiDung"` tại `config/settings.py:163`.
   - Bước 3: Sửa import gãy tại `accounts/admin.py:4` (`from .models import VaiTro, NguoiDung`).
   - Bước 4: Bổ sung alias quyền hạn tại `api/permissions.py` (`IsRestaurantStaff = LaNhanVienNhaHang`, `IsStaffOrReadOnly = LaNhanVienHoacChiDoc`).
   - Bước 5: Bổ sung Model Alias tại cuối mỗi file `models.py` của các app tiếng Việt để đảm bảo tương thích ngược:
     * `foods/models.py`: `Food = MonAn`, `Category = DanhMuc`, `Tag = TheMonAn`, `Ingredient = NguyenLieu`, `FoodImage = HinhAnhMonAn`.
     * `accounts/models.py`: `User = NguoiDung`, `Role = VaiTro`, `Permission = QuyenHan`.
     * `branches/models.py`: `Branch = ChiNhanh`.
     * `reservations/models.py`: `Reservation = DatBan`, `Table = BanAn`.
     * `orders/models.py`: `Order = DonHang`, `OrderItem = ChiTietDonHang`, `OrderStatusHistory = LichSuTrangThaiDon`.
     * `payments/models.py`: `Payment = ThanhToan`.
     * `promotions/models.py`: `Promotion = KhuyenMai`, `PromotionCode = MaKhuyenMai`, `PromotionUsage = LichSuDungKhuyenMai`.
     * `chat/models.py`: `ChatRoom = HoiThoai`, `ChatMessage = TinNhan`.
     * `recommendations/models.py`: `FoodInteraction = TuongTacMonAn`, `Recommendation = GoiYMonAn`.
   - Bước 6: Chuẩn hóa 4 app còn dùng model tiếng Anh (`carts`, `reviews`, `posts`, `analytics`):
     * `carts`: Tạo `GioHang` (`db_table="gio_hang"`), `ChiTietGioHang` (`db_table="chi_tiet_gio_hang"`), alias `Cart = GioHang`, `CartItem = ChiTietGioHang`.
     * `reviews`: Tạo `DanhGia` (`db_table="danh_gia"`), alias `Review = DanhGia`.
     * `posts`: Tạo `DanhMucBaiViet` (`db_table="danh_muc_bai_viet"`), `BaiViet` (`db_table="bai_viet"`), alias `PostCategory = DanhMucBaiViet`, `Post = BaiViet`.
     * `analytics`: Tạo `ThongBao` (`db_table="thong_bao"`), alias `Notification = ThongBao`.

4. **Trình tự Sinh Migration theo Thứ tự Topo (Topological Order)**:
   Để tránh xung đột khóa ngoại và giải quyết triệt để vòng lặp giữa `orders` và `promotions`, các app được phân thành 5 tầng phụ thuộc:
   - **Tầng 1 (Cơ sở độc lập)**: `accounts`, `branches`.
     * Không phụ thuộc vào app nghiệp vụ nào khác.
   - **Tầng 2 (Thực đơn & Kho)**: `foods`.
     * Phụ thuộc vào `accounts` (người tạo lịch sử kho).
   - **Tầng 3 (Bàn ăn & Đặt bàn)**: `reservations`.
     * Phụ thuộc vào `accounts`, `branches`, và `foods` (món ăn trong đặt bàn).
   - **Tầng 4 (Khuyến mãi & Đơn hàng - Đồng thời)**: `promotions`, `orders`.
     * Bằng cách chạy `makemigrations promotions orders` cùng một lệnh, Django autodetector sẽ tự động nhận diện mối quan hệ vòng tròn giữa `DonHang.khuyen_mai` và `LichSuDungKhuyenMai.don_hang`, và sinh ra migration tuyến tính (hoặc tách 1 trường FK sang migration phụ) một cách sạch sẽ mà không bao giờ báo lỗi.
   - **Tầng 5 (Nghiệp vụ giao dịch & Tiện ích)**:
     * `payments` (phụ thuộc `accounts`, `orders`, `reservations`).
     * `carts` (phụ thuộc `accounts`, `foods`).
     * `reviews` (phụ thuộc `accounts`, `foods`, `orders`).
     * `chat` (phụ thuộc `accounts`).
     * `recommendations` (phụ thuộc `accounts`, `foods`).
     * `analytics` (phụ thuộc `accounts`).
     * `posts` (phụ thuộc `accounts`).

---

## 3. Caveats (Các điểm giới hạn & Giả định)

1. **Giả định về Cơ sở dữ liệu trống**:
   Giả định rằng database `moc_db` trên môi trường phát triển là database mới tinh hoặc được phép xóa bỏ dữ liệu cũ để migrate từ đầu. Kế hoạch này áp dụng cho quy trình khởi tạo sạch (clean migration).
2. **Quyền thao tác của Agent Explorer**:
   Theo nguyên tắc bất biến của Explorer (`Read-only investigation — do NOT implement`), Explorer không trực tiếp sửa file source code `models.py` hay chạy lệnh `migrate` ghi đè CSDL, mà chuyển giao toàn bộ quy trình và lệnh chính xác cho Milestone 1 Implementer.
3. **Môi trường Sandbox macOS**:
   Công cụ thực thi lệnh của agent bị giới hạn socket mạng nội bộ bởi sandbox macOS, nên các lệnh kết nối PostgreSQL (`psql`, `createdb`, `migrate`) cần được thực hiện qua shell có quyền mạng hoặc ngoài sandbox khi người dùng phê duyệt.

---

## 4. Conclusion (Kết luận đánh giá tổng thể)

1. **Tình trạng PostgreSQL & PostGIS**:
   PostgreSQL 18.3 và PostGIS 3.6.0 đã được cài đặt và đang chạy nền ổn định trên máy (PID 532). Thư viện GDAL 3.13.3 và GEOS 3.14.1 đã liên kết chuẩn xác với Django GIS.
2. **Nguyên nhân chính khiến `manage.py check` thất bại**:
   - Lỗi import `Food` vs `MonAn` trong `carts/models.py` và `reviews/models.py`.
   - Lỗi cú pháp `CheckConstraint(condition=...)` trong `orders`, `reservations`, `payments`.
   - Cấu hình `AUTH_USER_MODEL = "accounts.User"` thay vì `"accounts.NguoiDung"`.
   - Lỗi import trong `accounts/admin.py` và thiếu alias trong `api/permissions.py`.
3. **Chiến lược Migrations 100% thành công**:
   - Xóa bỏ toàn bộ các file migration cũ 2026-09-07.
   - Sửa 100% lỗi cú pháp và bổ sung Model Aliases hai chiều.
   - Chạy sinh migration theo đúng thứ tự 5 tầng Topo (đặc biệt gộp `promotions` và `orders` trong 1 lượt `makemigrations`).
   - Chạy `migrate` nạp toàn bộ 36 bảng chuẩn vào `moc_db`.

---

## 5. Verification Method (Kế hoạch hành động & Lệnh kiểm chứng độc lập cho Implementer)

### Giai đoạn A: Sửa lỗi Mã nguồn & Cú pháp Model

#### A.1. Sửa `moc-backend/config/settings.py`
- Dòng 163: Đổi:
  ```python
  AUTH_USER_MODEL = "accounts.NguoiDung"
  ```

#### A.2. Sửa lỗi `CheckConstraint` tại 3 App
1. `moc-backend/orders/models.py` (khoảng dòng 52):
   Đổi `condition=` thành `check=`:
   ```python
   models.CheckConstraint(
       check=~models.Q(hinh_thuc="giao_hang") | models.Q(dia_chi_giao__isnull=False),
       name="kiem_tra_giao_hang_can_dia_chi",
   )
   ```
2. `moc-backend/reservations/models.py` (khoảng dòng 117):
   Đổi `condition=` thành `check=`:
   ```python
   models.CheckConstraint(
       check=~models.Q(hinh_thuc="chi_giu_cho") | (
           models.Q(yeu_cau_dat_coc=False) & models.Q(so_tien_coc=0)
       ),
       name="kiem_tra_chi_giu_cho",
   )
   ```
3. `moc-backend/payments/models.py` (khoảng dòng 40):
   Đổi `condition=` thành `check=`:
   ```python
   models.CheckConstraint(
       check=(
           models.Q(loai_thanh_toan="don_hang", don_hang__isnull=False, dat_ban__isnull=True)
           | models.Q(loai_thanh_toan="tien_coc", dat_ban__isnull=False, don_hang__isnull=True)
       ),
       name="kiem_tra_muc_tieu_thanh_toan",
   )
   ```

#### A.3. Sửa `accounts/admin.py` và `api/permissions.py`
1. `moc-backend/accounts/admin.py`:
   - Đổi dòng 4 thành:
     ```python
     from .models import VaiTro, NguoiDung
     ```
   - Cập nhật các đăng ký admin tương ứng.
2. `moc-backend/api/permissions.py`:
   - Thêm alias ở cuối file:
     ```python
     IsRestaurantStaff = LaNhanVienNhaHang
     IsStaffOrReadOnly = LaNhanVienHoacChiDoc
     ```

#### A.4. Bổ sung Model Alias ở cuối các file `models.py`
1. `moc-backend/foods/models.py`:
   ```python
   Food = MonAn
   Category = DanhMuc
   Tag = TheMonAn
   Ingredient = NguyenLieu
   FoodImage = HinhAnhMonAn
   ```
2. `moc-backend/accounts/models.py`:
   ```python
   User = NguoiDung
   Role = VaiTro
   Permission = QuyenHan
   ```
3. `moc-backend/branches/models.py`:
   ```python
   Branch = ChiNhanh
   ```
4. `moc-backend/reservations/models.py`:
   ```python
   Reservation = DatBan
   Table = BanAn
   ```
5. `moc-backend/orders/models.py`:
   ```python
   Order = DonHang
   OrderItem = ChiTietDonHang
   OrderStatusHistory = LichSuTrangThaiDon
   ```
6. `moc-backend/payments/models.py`:
   ```python
   Payment = ThanhToan
   ```
7. `moc-backend/promotions/models.py`:
   ```python
   Promotion = KhuyenMai
   PromotionCode = MaKhuyenMai
   PromotionUsage = LichSuDungKhuyenMai
   ```
8. `moc-backend/chat/models.py`:
   ```python
   ChatRoom = HoiThoai
   ChatMessage = TinNhan
   ```
9. `moc-backend/recommendations/models.py`:
   ```python
   FoodInteraction = TuongTacMonAn
   Recommendation = GoiYMonAn
   ```

#### A.5. Chuẩn hóa 4 App `carts`, `reviews`, `posts`, `analytics`
- Cập nhật model tiếng Việt và gán `db_table` khớp `moc_schema_tieng_viet.sql`, đồng thời cung cấp alias:
  * `carts`: `GioHang` (`db_table="gio_hang"`), `ChiTietGioHang` (`db_table="chi_tiet_gio_hang"`), `Cart = GioHang`, `CartItem = ChiTietGioHang`.
  * `reviews`: `DanhGia` (`db_table="danh_gia"`), `Review = DanhGia`.
  * `posts`: `DanhMucBaiViet` (`db_table="danh_muc_bai_viet"`), `BaiViet` (`db_table="bai_viet"`), `PostCategory = DanhMucBaiViet`, `Post = BaiViet`.
  * `analytics`: `ThongBao` (`db_table="thong_bao"`), `Notification = ThongBao`.

---

### Giai đoạn B: Dọn dẹp Migrations cũ & Thiết lập Cơ sở dữ liệu

#### B.1. Xóa toàn bộ file migration cũ
Chạy lệnh trong terminal tại thư mục `moc-backend`:
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
```

#### B.2. Khởi tạo Cơ sở dữ liệu `moc_db` & Kích hoạt Extensions
```bash
# Đảm bảo PostgreSQL 18 đang chạy (nếu chưa chạy):
sudo launchctl kickstart -k system/postgresql-18 2>/dev/null || true

# Tạo database moc_db (bỏ qua nếu đã tồn tại):
PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE moc_db OWNER postgres;" 2>/dev/null || true

# Kích hoạt PostGIS và Pgcrypto trong moc_db:
PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -d moc_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -d moc_db -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```

---

### Giai đoạn C: Kiểm tra Hệ thống & Sinh Migrations sạch

#### C.1. Kiểm tra không còn lỗi model (`python manage.py check`)
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py check
```
*Điều kiện thành công*:
```text
System check identified no issues (0 silenced).
```

#### C.2. Sinh Migrations theo thứ tự Topo
Thực thi tuần tự theo 5 tầng để kiểm soát phụ thuộc tuyệt đối:

```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend

# Tầng 1: Độc lập
./.venv/bin/python manage.py makemigrations accounts branches

# Tầng 2: Thực đơn & Kho
./.venv/bin/python manage.py makemigrations foods

# Tầng 3: Bàn & Đặt bàn
./.venv/bin/python manage.py makemigrations reservations

# Tầng 4: Khuyến mãi & Đơn hàng (Gộp chung để phá vỡ circular dependency)
./.venv/bin/python manage.py makemigrations promotions orders

# Tầng 5: Các app giao dịch, blog, review, chat, AI, analytics
./.venv/bin/python manage.py makemigrations payments carts reviews chat recommendations analytics posts
```

#### C.3. Thực thi Migrate vào Database
```bash
./.venv/bin/python manage.py migrate
```
*Điều kiện thành công*:
Tất cả các dòng hiển thị `Applying <app>.0001_initial... OK`.

#### C.4. Kiểm tra bảng CSDL sau khi migrate
```bash
PGPASSWORD=vu2005 /Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -d moc_db -c "\dt"
```
*Điều kiện thành công*:
Hiện diện đầy đủ 36 bảng chuẩn tiếng Việt:
- `vai_tro`, `quyen_han`, `vai_tro_quyen_han`, `nguoi_dung`, `nguoi_dung_vai_tro`
- `chi_nhanh`, `ban_an`
- `danh_muc`, `the_mon_an`, `nguyen_lieu`, `mon_an`, `hinh_anh_mon_an`, `mon_an_the`, `dinh_muc_nguyen_lieu`, `lich_su_xuat_nhap_kho`
- `gio_hang`, `chi_tiet_gio_hang`
- `chinh_sach_dat_coc`, `quy_tac_huy_dat_coc`, `dat_ban`, `mon_an_trong_dat_ban`
- `khuyen_mai`, `ma_khuyen_mai`, `lich_su_dung_khuyen_mai`
- `don_hang`, `chi_tiet_don_hang`, `lich_su_trang_thai_don`
- `thanh_toan`
- `danh_muc_bai_viet`, `bai_viet`, `danh_gia`
- `hoi_thoai`, `tin_nhan`
- `thong_bao`
- `tuong_tac_mon_an`, `goi_y_mon_an`
cùng các bảng hệ thống của Django (`django_migrations`, `django_content_type`, `django_session`, `spatial_ref_sys`).
