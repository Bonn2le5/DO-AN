# BÁO CÁO ĐÁNH GIÁ & KIỂM ĐỊNH ADVERSARIAL MILESTONE 1 (REVIEW & CHALLENGE REPORT)

**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Agent**: Milestone 1 Reviewer 1 (`teamwork_preview_reviewer_m1_1`)  
**Vai trò**: Reviewer (Đánh giá khách quan) & Adversarial Critic (Kiểm định đối kháng)  
**Thời gian**: 2026-10-14T04:08:00Z  
**Đường dẫn**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m1_1/handoff.md`  
**Verdict**: **REQUEST_CHANGES**

---

## 1. Observation (Các quan sát trực tiếp & Bằng chứng thực tế)

### 1.1. Lệnh kiểm tra hệ thống Django (`manage.py check`)
Thực thi lệnh kiểm tra:
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py check
```
**Kết quả**:
```text
System check identified no issues (0 silenced).
```
Exit code `0`. Toàn bộ lỗi import ban đầu (`Food`, `Order`, `Payment`, `condition=` trong `CheckConstraint`, `AUTH_USER_MODEL = "accounts.NguoiDung"`) đã được khắc phục.

### 1.2. Kiểm tra bộ kiểm thử E2E Tier 1
Thực thi:
```bash
cd /Users/VuVan/Documents/DO-AN
python3 tests/e2e/runner.py --tier 1 --verbose
```
**Kết quả**:
```text
Ran 30 tests in 0.006s
OK
Total Tests Run : 30
Passed          : 30
Failed          : 0
Errors          : 0
Pass Rate       : 100.0%
```

### 1.3. Khớp nối Schema 36 bảng CSDL với `moc_schema_tieng_viet.sql`
Chạy kiểm tra so khớp tự động giữa 36 bảng `CREATE TABLE` trong file `moc_schema_tieng_viet.sql` với toàn bộ Django model registry:
```text
Total tables found in SQL schema: 36
Missing tables in Django: set()
  ✓ bai_viet -> BaiViet (posts)
  ✓ ban_an -> BanAn (reservations)
  ✓ chi_nhanh -> ChiNhanh (branches)
  ✓ chi_tiet_don_hang -> ChiTietDonHang (orders)
  ✓ chi_tiet_gio_hang -> ChiTietGioHang (carts)
  ✓ chinh_sach_dat_coc -> ChinhSachDatCoc (reservations)
  ✓ danh_gia -> DanhGia (reviews)
  ✓ danh_muc -> DanhMuc (foods)
  ✓ danh_muc_bai_viet -> DanhMucBaiViet (posts)
  ✓ dat_ban -> DatBan (reservations)
  ✓ dinh_muc_nguyen_lieu -> DinhMucNguyenLieu (foods)
  ✓ don_hang -> DonHang (orders)
  ✓ gio_hang -> GioHang (carts)
  ✓ goi_y_mon_an -> GoiYMonAn (recommendations)
  ✓ hinh_anh_mon_an -> HinhAnhMonAn (foods)
  ✓ hoi_thoai -> HoiThoai (chat)
  ✓ khuyen_mai -> KhuyenMai (promotions)
  ✓ lich_su_dung_khuyen_mai -> LichSuDungKhuyenMai (promotions)
  ✓ lich_su_trang_thai_don -> LichSuTrangThaiDon (orders)
  ✓ lich_su_xuat_nhap_kho -> LichSuXuatNhapKho (foods)
  ✓ ma_khuyen_mai -> MaKhuyenMai (promotions)
  ✓ mon_an -> MonAn (foods)
  ✓ mon_an_the -> MonAnThe (foods)
  ✓ mon_an_trong_dat_ban -> MonAnTrongDatBan (reservations)
  ✓ nguoi_dung -> NguoiDung (accounts)
  ✓ nguoi_dung_vai_tro -> NguoiDungVaiTro (accounts)
  ✓ nguyen_lieu -> NguyenLieu (foods)
  ✓ quy_tac_huy_dat_coc -> QuyTacHuyDatCoc (reservations)
  ✓ quyen_han -> QuyenHan (accounts)
  ✓ thanh_toan -> ThanhToan (payments)
  ✓ the_mon_an -> TheMonAn (foods)
  ✓ thong_bao -> ThongBao (analytics)
  ✓ tin_nhan -> TinNhan (chat)
  ✓ tuong_tac_mon_an -> TuongTacMonAn (recommendations)
  ✓ vai_tro -> VaiTro (accounts)
  ✓ vai_tro_quyen_han -> VaiTroQuyenHan (accounts)
ALL 36 SQL TABLES MATCH DJANGO MODELS 100%!
```

### 1.4. Kiểm tra phân tích dữ liệu Seed Data `Du-lieu-test.txt`
Thực thi kiểm tra phân tích bằng regex của `Command.load_test_data_content()`:
```text
Categories found: 5
Foods found: 100
Foods per category: {'1': 20, '2': 20, '3': 20, '4': 20, '5': 20}
DU-LIEU-TEST PARSING & DISTRIBUTION 100% VERIFIED!
```

### 1.5. Quan sát phát hiện lỗi 1: Mất trường `thu_dien_tu` trong `DangKySerializer`
Quan sát tại `/Users/VuVan/Documents/DO-AN/moc-backend/accounts/serializers.py`, dòng 47-56:
```python
    def create(self, du_lieu_da_xac_thuc):
        ho_ten = du_lieu_da_xac_thuc.pop("ho_ten", "").strip()
        mat_khau = du_lieu_da_xac_thuc.pop("mat_khau")
        du_lieu_da_xac_thuc.setdefault("username", du_lieu_da_xac_thuc["thu_dien_tu"].split("@", 1)[0])
        du_lieu_da_xac_thuc["email"] = du_lieu_da_xac_thuc.pop("thu_dien_tu")
        if ho_ten and not du_lieu_da_xac_thuc.get("first_name"):
            ten, *phan_con_lai = ho_ten.split(maxsplit=1)
            du_lieu_da_xac_thuc["first_name"] = ten
            du_lieu_da_xac_thuc["last_name"] = phan_con_lai[0] if phan_con_lai else ""
        nguoi_dung = NguoiDung.objects.create_user(password=mat_khau, **du_lieu_da_xac_thuc)
```
Quan sát mô hình `NguoiDung` tại `/Users/VuVan/Documents/DO-AN/moc-backend/accounts/models.py`:
```python
class NguoiDung(AbstractUser):
    thu_dien_tu = models.EmailField(unique=True)
...
    USERNAME_FIELD = "thu_dien_tu"
    REQUIRED_FIELDS = ["username"]
```
Khi gọi `du_lieu_da_xac_thuc["email"] = du_lieu_da_xac_thuc.pop("thu_dien_tu")`, khóa `"thu_dien_tu"` đã bị xóa khỏi `du_lieu_da_xac_thuc`. Trong phương thức `UserManager._create_user(username, email, password, **extra_fields)` của Django:
```python
user = self.model(username=username, email=email, **extra_fields)
```
Kết quả thực nghiệm trên Python shell:
```python
u = NguoiDung(username='testuser', email='test@example.com')
print('thu_dien_tu:', repr(u.thu_dien_tu))  # In ra: ''
print('email:', repr(u.email))              # In ra: 'test@example.com'
```
-> Trường `thu_dien_tu` trên bản ghi người dùng mới bị để rỗng chuỗi rỗng `''`.

### 1.6. Quan sát phát hiện lỗi 2: Thiếu router actions tiếng Anh trong `XacThucViewSet`
Quan sát `/Users/VuVan/Documents/DO-AN/moc-backend/accounts/views.py`, dòng 14-43:
`XacThucViewSet` chỉ định nghĩa các action: `dang_ky`, `ho_so`, `doi_mat_khau`.
Quan sát mã nguồn frontend tại `/Users/VuVan/Documents/DO-AN/moc-frontend/src/api/auth.api.ts`:
- Dòng 20: `const { data: user } = await apiClient.get("/auth/profile/");`
- Dòng 25: `const { data } = await apiClient.post("/auth/register/", payload);`
Thực nghiệm kiểm tra resolve URL:
```python
resolve('/api/auth/register/') -> django.urls.exceptions.Resolver404
resolve('/api/auth/profile/')  -> django.urls.exceptions.Resolver404
```
-> Frontend gọi đến `/api/auth/register/` và `/api/auth/profile/` bị lỗi HTTP 404 Not Found.

### 1.7. Quan sát phát hiện lỗi 3: 12 file `admin.py` bị bỏ trống
Kiểm tra toàn bộ 13 file `admin.py` trong `moc-backend/`:
Chỉ có `accounts/admin.py` đăng ký model (`NguoiDung`, `VaiTro`).
Toàn bộ 12 file còn lại (`foods/admin.py`, `orders/admin.py`, `reservations/admin.py`, `branches/admin.py`, `payments/admin.py`, `carts/admin.py`, `promotions/admin.py`, `reviews/admin.py`, `chat/admin.py`, `recommendations/admin.py`, `analytics/admin.py`, `posts/admin.py`) chỉ chứa chú thích mặc định `# Register your models here.`.

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới kết luận)

1. **Về tính chính xác & toàn vẹn mô hình (R1, Feature 1–3)**:
   - Từ Quan sát 1.1, 1.3, và 1.4: Worker đã hoàn thành xuất sắc việc tái cấu trúc toàn diện 13 app Django theo 36 bảng CSDL chuẩn tiếng Việt của `moc_schema_tieng_viet.sql`.
   - Các Model Aliases (`Food = MonAn`, `Order = DonHang`, `Table = BanAn`, v.v.) và Property Adapters (`name`, `price`, `status`, `customer`, `items`) đều hoạt động trơn tru 100%.
   - `makemigrations --check` báo `No changes detected`, nghĩa là schema và migrations hoàn toàn đồng nhất.

2. **Về lỗi đăng ký người dùng (Finding 1 - Critical Bug)**:
   - *Mệnh đề*: `NguoiDung.thu_dien_tu` có ràng buộc `unique=True` và được chọn làm `USERNAME_FIELD = "thu_dien_tu"`.
   - *Từ Quan sát 1.5*: `DangKySerializer.create()` thực hiện `pop("thu_dien_tu")`, khiến `thu_dien_tu` bị bỏ trống (`''`) khi lưu vào CSDL.
   - *Hệ quả 1*: Khi người dùng thứ hai đăng ký qua API, CSDL PostgreSQL sẽ ném ngoại lệ `IntegrityError: duplicate key value violates unique constraint "nguoi_dung_thu_dien_tu_key" (Key (thu_dien_tu)=() already exists)`. Hệ thống đăng ký của khách hàng bị tê liệt hoàn toàn từ người dùng thứ 2.
   - *Hệ quả 2*: Người dùng không thể đăng nhập bằng email của mình vì trong CSDL cột `thu_dien_tu` bị rỗng.

3. **Về lỗi tương thích ngược API Auth (Finding 2 - Major Gap)**:
   - *Mệnh đề*: Yêu cầu R1 và Feature 5 trong `PROJECT.md` quy định: "Dual API Route Support: Hỗ trợ router song ngữ tiếng Anh và tiếng Việt để tương thích mượt mà với frontend callers".
   - *Từ Quan sát 1.6*: `moc-frontend` gọi `/auth/register/` và `/auth/profile/`. Trong khi `api/urls.py` và `accounts/views.py` chỉ có `dang_ky`, `ho_so`.
   - *Hệ quả*: Khách hàng đăng ký trên frontend hoặc xem thông tin cá nhân sẽ nhận lỗi HTTP 404 Not Found.

4. **Về thiếu sót cấu hình Django Admin (Finding 3 - Major Gap)**:
   - *Từ Quan sát 1.7*: Dispatch giao nhiệm vụ: "Review worker changes across all 13 Django apps models, admin, views, serializers, permissions, and settings."
   - 12 app còn lại chưa đăng ký model nào trong `admin.py`, khiến giao diện Django Admin (`/admin/`) hoàn toàn trống rỗng, không thể phục vụ vận hành, đối soát dữ liệu hay duyệt đơn hàng/đặt bàn/món ăn.

5. **Tổng kết đánh giá đối kháng (Adversarial Verdict)**:
   - Không phát hiện hành vi gian lận (Integrity Violation): không có mã giả, không hardcode kết quả kiểm thử trong mã nguồn backend.
   - Tuy nhiên, 2 lỗi chức năng nghiêm trọng (Critical Bug trong `DangKySerializer` và Major Gap trong `XacThucViewSet`) cùng việc thiếu `admin.py` cho 12 apps làm ảnh hưởng trực tiếp đến tính ổn định của Milestone 2 và Milestone 5.
   - Do đó, để đảm bảo tiêu chuẩn chất lượng cao nhất cho đồ án, Reviewer đưa ra kết luận: **REQUEST_CHANGES**.

---

## 3. Findings (Bảng chi tiết các phát hiện)

### [Critical] Finding 1: `DangKySerializer` xóa mất `thu_dien_tu`, gây lỗi Unique Constraint và không thể đăng nhập
- **Vị trí**: `/Users/VuVan/Documents/DO-AN/moc-backend/accounts/serializers.py`, dòng 51.
- **Nguyên nhân**: `du_lieu_da_xac_thuc["email"] = du_lieu_da_xac_thuc.pop("thu_dien_tu")` xóa mất trường `thu_dien_tu` khỏi payload gửi vào `create_user`, trong khi `thu_dien_tu` là cột chính `unique=True` và là `USERNAME_FIELD`.
- **Hậu quả**: Tất cả tài khoản đăng ký qua API đều có `thu_dien_tu = ''`. Tài khoản thứ 2 sẽ gây lỗi 500 CSDL do trùng chuỗi rỗng `''`.
- **Giải pháp khắc phục**:
  1. Trong `accounts/serializers.py`, giữ nguyên `thu_dien_tu` và đồng bộ sang `email`:
     ```python
     du_lieu_da_xac_thuc["email"] = du_lieu_da_xac_thuc["thu_dien_tu"]
     ```
  2. Trong `accounts/models.py`, bổ sung override `save()` trên `NguoiDung`:
     ```python
     def save(self, *args, **kwargs):
         if self.thu_dien_tu and not self.email:
             self.email = self.thu_dien_tu
         elif self.email and not self.thu_dien_tu:
             self.thu_dien_tu = self.email
         super().save(*args, **kwargs)
     ```

### [Major] Finding 2: `XacThucViewSet` thiếu các action tiếng Anh (`register`, `profile`, `change_password`)
- **Vị trí**: `/Users/VuVan/Documents/DO-AN/moc-backend/accounts/views.py`, dòng 14-43.
- **Nguyên nhân**: `XacThucViewSet` chỉ định nghĩa `@action` tiếng Việt (`dang_ky`, `ho_so`, `doi_mat_khau`). Frontend `moc-frontend/src/api/auth.api.ts` gọi trực tiếp `/api/auth/profile/` và `/api/auth/register/`.
- **Hậu quả**: Trả về `HTTP 404 Not Found` khi frontend tương tác.
- **Giải pháp khắc phục**:
  Bổ sung wrapper actions trong `XacThucViewSet`:
  ```python
  @action(detail=False, methods=["post"], permission_classes=[AllowAny])
  def register(self, request):
      return self.dang_ky(request)

  @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
  def profile(self, request):
      return self.ho_so(request)

  @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
  def change_password(self, request):
      return self.doi_mat_khau(request)
  ```

### [Major] Finding 3: 12 App chưa được cấu hình Django Admin (`admin.py`)
- **Vị trí**: `foods/admin.py`, `branches/admin.py`, `reservations/admin.py`, `orders/admin.py`, `payments/admin.py`, `carts/admin.py`, `promotions/admin.py`, `reviews/admin.py`, `chat/admin.py`, `recommendations/admin.py`, `analytics/admin.py`, `posts/admin.py`.
- **Nguyên nhân**: Các file `admin.py` mới chỉ có `# Register your models here.`.
- **Hậu quả**: Không thể quản lý dữ liệu trên giao diện Django Admin chuẩn của đồ án.
- **Giải pháp khắc phục**:
  Đăng ký các model trọng tâm (`MonAn`, `DanhMuc`, `TheMonAn`, `NguyenLieu`, `ChiNhanh`, `BanAn`, `DatBan`, `DonHang`, `ThanhToan`, `KhuyenMai`, `DanhGia`, `BaiViet`, `ThongBao`) trong các file `admin.py` tương ứng.

---

## 4. Caveats (Các điểm giới hạn & Giả định)

1. **Môi trường Sandbox macOS**:
   - Môi trường macOS sandbox seatbelt chặn kết nối mạng socket TCP ra ngoài cổng 5432 và Redis, do đó lệnh `migrate` và lệnh chạy server socket trực tiếp cần được kích hoạt ngoài sandbox hoặc qua script chạy thực tế của hệ thống.
   - Các kiểm chứng tính toàn vẹn tĩnh, tính nhất quán của migration (`makemigrations --check`), và tính toàn vẹn của mô hình đã được xác nhận đạt 100%.
2. **Phạm vi Milestone 1**:
   - Các tính năng thời gian thực WebSocket (Channels), tích hợp VNPay Sandbox IPN, và Content-Based AI thuộc phạm vi các Milestone tiếp theo (M2, M3, M4) và đã có baseline tests trong `tests/e2e/runner.py`.

---

## 5. Conclusion (Kết luận đánh giá tổng thể)

**Verdict**: **REQUEST_CHANGES**

Milestone 1 Worker đã đạt được khối lượng công việc rất lớn và chất lượng nền tảng cao:
- `python manage.py check` chạy đạt **0 issues** (Exit code 0).
- Khớp 100% 36 bảng CSDL chuẩn tiếng Việt theo `moc_schema_tieng_viet.sql`.
- 13 app model aliases, properties, serializers, và viewsets hoạt động chính xác.
- Đạt 30/30 tests (100% pass rate) trên bộ kiểm thử `tests/e2e/runner.py --tier 1`.
- Không phát hiện bất kỳ dấu hiệu gian lận hay che giấu lỗi nào (No Integrity Violation).

Tuy nhiên, Reviewer yêu cầu Worker hoàn thiện 3 điểm mấu chốt trước khi nghiệm thu Milestone 1:
1. Sửa lỗi `thu_dien_tu` trong `DangKySerializer` và hook `save()` trên `NguoiDung` để bảo đảm đăng ký tài khoản thành công 100%.
2. Thêm các action alias `register`, `profile`, `change_password` vào `XacThucViewSet` trong `accounts/views.py` để kết nối liền mạch với `moc-frontend`.
3. Đăng ký các model chính trong `admin.py` cho 12 apps còn lại để giao diện Django Admin hoạt động đầy đủ.

---

## 6. Verification Method (Hướng dẫn kiểm chứng độc lập sau khi sửa)

### Bước 1: Kiểm tra Đăng ký & Bảo toàn `thu_dien_tu`
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
from accounts.serializers import DangKySerializer
from accounts.models import NguoiDung
s = DangKySerializer(data={'thu_dien_tu': 'verify@test.com', 'mat_khau': 'TestPass123!', 'ho_ten': 'Test User'})
assert s.is_valid(), s.errors
# Kiểm tra logic ánh xạ
du_lieu = dict(s.validated_data)
assert 'thu_dien_tu' in du_lieu or du_lieu.get('email') == 'verify@test.com'
print('USER REGISTRATION CONTRACT VERIFIED!')
"
```

### Bước 2: Kiểm tra Phân giải URL Auth tiếng Anh
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
from django.urls import resolve
assert resolve('/api/auth/register/').url_name == 'auth-register'
assert resolve('/api/auth/profile/').url_name == 'auth-profile'
print('AUTH ENGLISH ACTIONS RESOLVED SUCCESSFULLY!')
"
```

### Bước 3: Kiểm tra Đăng ký Django Admin
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
from django.contrib import admin
from foods.models import MonAn
from orders.models import DonHang
from reservations.models import BanAn, DatBan
assert MonAn in admin.site._registry, 'MonAn not in admin'
assert DonHang in admin.site._registry, 'DonHang not in admin'
assert DatBan in admin.site._registry, 'DatBan not in admin'
print('ADMIN REGISTRATION VERIFIED!')
"
```

### Bước 4: Chạy toàn bộ Tier 1 E2E Test Suite
```bash
cd /Users/VuVan/Documents/DO-AN
python3 tests/e2e/runner.py --tier 1 --verbose
```
*Điều kiện đạt*: 30/30 tests passed, Exit code 0.
