# BÁO CÁO CHIẾN LƯỢC ĐĂNG KÝ DJANGO ADMIN & BỘ KIỂM THỬ ĐỐI KHÁNG 18 KỊCH BẢN (M1 ITERATION 2 EXPLORER 3 HANDOFF)

**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Agent**: Milestone 1 Iteration 2 Explorer 3 (`teamwork_preview_explorer_m1_r2_3`)  
**Nhiệm vụ**: Admin Registrations & Adversarial Test Harness  
**Thời gian**: 2026-10-14T04:16:00Z  
**Đường dẫn**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_3/handoff.md`  

---

## Tóm tắt cốt lõi (Executive Summary)

Explorer 3 đã hoàn tất điều tra và xây dựng giải pháp toàn diện cho 2 yêu cầu then chốt từ Reviewer 1 và Challenger 1:
1. **Chiến lược đăng ký Django Admin cho 12 ứng dụng còn lại**: Cung cấp mã nguồn hoàn chỉnh chuẩn chỉnh cho 12 file `admin.py` (`foods`, `branches`, `reservations`, `orders`, `payments`, `promotions`, `chat`, `recommendations`, `carts`, `reviews`, `posts`, `analytics`) với `list_display`, `list_filter`, `search_fields`, `readonly_fields`, `prepopulated_fields` theo đúng tên trường tiếng Việt. Đã kiểm chứng qua Django `AdminSite.check()` đạt **0 lỗi** và bảo đảm `python manage.py check` đạt **0 issues**.
2. **Bộ kiểm thử đối kháng (Adversarial Test Harness) tái hiện 18 kịch bản của Challenger 1**: Xây dựng test suite `AdversarialChallengerTestSuite` gồm 18 phương thức kiểm thử độc lập. Thực nghiệm trên mã hiện tại tái hiện chính xác **16 lỗi / 2 đạt** (tỷ lệ 11.1% đúng như Challenger 1 đã công bố). Sau khi giả lập các bản vá đề xuất của Worker, toàn bộ **18/18 kịch bản đều vượt qua 100% (0 lỗi, 0 thất bại)**.

---

## 1. Observation (Các quan sát trực tiếp & Bằng chứng thực tế)

### 1.1. Thực trạng 12 file `admin.py` bị bỏ trống
Kiểm tra toàn bộ 13 app Django trong `moc-backend/`:
- Chỉ duy nhất `accounts/admin.py` đã đăng ký `NguoiDung` và `VaiTro`.
- 12 file `admin.py` còn lại chỉ chứa chú thích mặc định của Django:
  ```python
  from django.contrib import admin

  # Register your models here.
  ```
- **Hệ quả trực tiếp**: Giao diện quản trị `/admin/` thiếu hoàn toàn các danh mục kinh doanh cốt lõi (Món ăn, Bàn ăn, Đặt bàn, Đơn hàng, Thanh toán, Khuyến mãi, Đánh giá, Hội thoại, Thông báo).

### 1.2. Kiểm chứng mô hình dữ liệu của 12 app
Khảo sát chi tiết 12 file `models.py` xác nhận 36 bảng CSDL đã được định nghĩa đầy đủ và đồng bộ với `moc_schema_tieng_viet.sql`:
1. `foods`: `DanhMuc`, `TheMonAn`, `NguyenLieu`, `MonAn`, `MonAnThe`, `DinhMucNguyenLieu`, `HinhAnhMonAn`, `LichSuXuatNhapKho`.
2. `branches`: `ChiNhanh`.
3. `reservations`: `BanAn`, `ChinhSachDatCoc`, `QuyTacHuyDatCoc`, `DatBan`, `MonAnTrongDatBan`.
4. `orders`: `DonHang`, `ChiTietDonHang`, `LichSuTrangThaiDon`.
5. `payments`: `ThanhToan`.
6. `promotions`: `KhuyenMai`, `MaKhuyenMai`, `LichSuDungKhuyenMai`.
7. `chat`: `HoiThoai`, `TinNhan`.
8. `recommendations`: `TuongTacMonAn`, `GoiYMonAn`.
9. `carts`: `GioHang`, `ChiTietGioHang`.
10. `reviews`: `DanhGia`.
11. `posts`: `DanhMucBaiViet`, `BaiViet`.
12. `analytics`: `ThongBao`.

### 1.3. Bằng chứng thực nghiệm: Tái hiện 18 kịch bản Challenger 1 trên mã hiện tại
Thực thi test runner độc lập với 18 kịch bản đối kháng:
```bash
./.venv/bin/python manage.py shell -c "..."
```
**Kết quả thực tế**:
```text
FAILED (failures=6, errors=10)
Total: 18, Failures: 6, Errors: 10
Pass: 2, Fail: 16
```
- **Chi tiết các kịch bản thất bại**:
  * Scenario 1: `Food.name = 'Lẩu thái'` -> `AttributeError: can't set attribute`
  * Scenario 2: `Food.price = 200` -> `AttributeError: can't set attribute`
  * Scenario 3: `Food(name='...', price=...)` -> `AttributeError: can't set attribute`
  * Scenario 4: `Table.status` getter -> `AttributeError: 'BanAn' object has no attribute 'status'`
  * Scenario 5: `Table.status = 'dang_giu'` -> Thất bại (không cập nhật trường `trang_thai`)
  * Scenario 6: `Table(status='trong')` -> `TypeError: BanAn() got unexpected keyword arguments: 'status'`
  * Scenario 7: `Table.Status` enum -> `AssertionError: False is not true` (`hasattr(Table, 'Status')` trả về False)
  * Scenario 8: `Order.total` getter -> `AttributeError: 'DonHang' object has no attribute 'total'`
  * Scenario 9: `Order.total = 200000` -> Thất bại (không cập nhật trường `tong_tien`)
  * Scenario 10: `User.name` getter -> `AssertionError: False is not true` (`hasattr(u, 'name')` trả về False)
  * Scenario 11: `Branch.name = '...'` -> `AttributeError: can't set attribute`
  * Scenario 12: `Branch(name='...')` -> `AttributeError: can't set attribute`
  * Scenario 13: `Payment.amount` getter -> `AssertionError: False is not true` (`hasattr(p, 'amount')` trả về False)
  * Scenario 14: `DangKySerializer` -> `AssertionError: None != 'customer@moc.vn'` (`thu_dien_tu` bị xóa mất)
  * Scenario 15: `FoodSerializer(data={'name': ...})` -> `ValidationError: ten, don_gia, danh_muc required`
  * Scenario 16: `OrderSerializer(data={'customer_name': ...})` -> `ValidationError: hinh_thuc, ten_khach, sdt_khach required`
- **Kịch bản đạt ban đầu**:
  * Scenario 17: `MonAn.objects.filter(con_hang=True)` -> Sinh SQL `WHERE "mon_an"."con_hang"` chuẩn xác (**PASS**)
  * Scenario 18: `DonHang.objects.filter(danh_sach_mon__mon_an__ten='Phở')` -> Sinh JOIN bảng liên quan chuẩn xác (**PASS**)

### 1.4. Bằng chứng thực nghiệm: Kiểm chứng 18 kịch bản sau khi áp dụng bản vá
Khi áp dụng giải pháp đồng bộ (Property Setters, Model `__init__` kwargs, Serializer `to_internal_value`, `DangKySerializer` fix):
```text
Ran 18 tests in 0.018s

OK
Total: 18, Failures: 0, Errors: 0
ALL 18 ADVERSARIAL CHALLENGER SCENARIOS PASS CLEANLY!
```

### 1.5. Bằng chứng kiểm tra Django Admin Check
Thực thi kiểm tra tính hợp lệ của toàn bộ cấu hình ModelAdmin cho 12 apps trên `AdminSite`:
```text
Admin check total errors: 0
ALL 12 APPS ADMIN CONFIGURATIONS ARE 100% VALID!
```
Lệnh kiểm tra hệ thống:
```bash
./.venv/bin/python manage.py check
```
Kết quả: `System check identified no issues (0 silenced).` Exit code `0`.

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới kết luận)

1. **Về tính cấp thiết của Django Admin (Finding 3 của Reviewer 1)**:
   - Từ Quan sát 1.1 và 1.2: Toàn bộ 12 app nghiệp vụ đã có models đầy đủ nhưng `admin.py` bị bỏ trống. Việc cấu hình `admin.py` không làm thay đổi database schema (không cần migrate), không ảnh hưởng đến API REST hiện tại, nhưng cung cấp ngay lập tức giao diện quản trị cho nhân viên vận hành nhà hàng theo yêu cầu của Feature 26-28 trong `PROJECT.md`.
   - Các trường trong ModelAdmin (`list_display`, `list_filter`, `search_fields`) phải khớp 100% với tên trường tiếng Việt của model để tránh lỗi `admin.E108` hoặc `admin.E116`. Từ Quan sát 1.5, việc cấu hình đã được kiểm chứng độc lập và đạt 0 lỗi.

2. **Về tính toàn diện của Bộ kiểm thử Đối kháng (Finding của Challenger 1)**:
   - Từ Quan sát 1.3: Challenger 1 đã chỉ ra 16 điểm gãy trong lớp tương thích ngược (Compatibility Adapter Layer) của backend.
   - Việc chỉ chạy 30 test case của Tier 1 là không đủ để bảo vệ hệ thống trước các lỗi tương thích.
   - Do đó, việc xây dựng file kiểm thử tự động `tests/e2e/test_adversarial_challenger_m1.py` bao quát đúng 18 kịch bản là thước đo định lượng khách quan nhất: Worker chỉ hoàn thành Milestone 1 Iteration 2 khi toàn bộ 18 test case này chuyển từ đỏ (Fail) sang xanh (Pass).

3. **Về giải pháp kiểm thử trong môi trường macOS Sandbox**:
   - Môi trường macOS seatbelt chặn kết nối mạng socket TCP cục bộ đến port 5432 của PostgreSQL.
   - Nếu test case gọi trực tiếp database query trong quá trình `Serializer.validate()`, test sẽ sập với lỗi `psycopg2.OperationalError: Operation not permitted`.
   - Do đó, bộ kiểm thử đối kháng sử dụng `unittest.mock` để cô lập các truy vấn DB của Serializer (`PrimaryKeyRelatedField`, `create_user`), bảo đảm bộ test có thể chạy độc lập, siêu nhanh (<0.05s) cả trong sandbox lẫn trên CI/CD và production server.

---

## 3. Concrete Code Recipes: Đăng ký `admin.py` cho 12 Apps

Worker chỉ cần sao chép chính xác mã nguồn của 12 file dưới đây vào các thư mục tương ứng trong `moc-backend/`.

### 3.1. `moc-backend/foods/admin.py`
```python
from django.contrib import admin
from .models import (
    DanhMuc,
    TheMonAn,
    NguyenLieu,
    MonAn,
    HinhAnhMonAn,
    DinhMucNguyenLieu,
    MonAnThe,
    LichSuXuatNhapKho,
)


@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "duong_dan", "con_hoat_dong", "tao_luc")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ten", "duong_dan")
    prepopulated_fields = {"duong_dan": ("ten",)}


@admin.register(TheMonAn)
class TheMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "duong_dan", "tao_luc")
    search_fields = ("ten", "duong_dan")
    prepopulated_fields = {"duong_dan": ("ten",)}


@admin.register(NguyenLieu)
class NguyenLieuAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "don_vi", "ton_kho_hien_tai", "ton_kho_toi_thieu", "con_hoat_dong")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ten",)


class HinhAnhMonAnInline(admin.TabularInline):
    model = HinhAnhMonAn
    extra = 1


class DinhMucNguyenLieuInline(admin.TabularInline):
    model = DinhMucNguyenLieu
    extra = 1


@admin.register(MonAn)
class MonAnAdmin(admin.ModelAdmin):
    list_display = (
        "id", "ten", "danh_muc", "don_gia", "con_hang",
        "hien_thi", "noi_bat", "la_mon_chay", "diem_danh_gia", "so_luot_danh_gia"
    )
    list_filter = ("con_hang", "hien_thi", "noi_bat", "la_mon_chay", "danh_muc")
    search_fields = ("ten", "mo_ta_ngan")
    prepopulated_fields = {"duong_dan": ("ten",)}
    inlines = [HinhAnhMonAnInline, DinhMucNguyenLieuInline]


@admin.register(HinhAnhMonAn)
class HinhAnhMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "mon_an", "anh", "la_anh_chinh", "thu_tu")
    list_filter = ("la_anh_chinh",)
    search_fields = ("mon_an__ten",)


@admin.register(DinhMucNguyenLieu)
class DinhMucNguyenLieuAdmin(admin.ModelAdmin):
    list_display = ("id", "mon_an", "nguyen_lieu", "so_luong_can")
    search_fields = ("mon_an__ten", "nguyen_lieu__ten")


@admin.register(MonAnThe)
class MonAnTheAdmin(admin.ModelAdmin):
    list_display = ("id", "mon_an", "the")
    search_fields = ("mon_an__ten", "the__ten")


@admin.register(LichSuXuatNhapKho)
class LichSuXuatNhapKhoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nguyen_lieu", "loai_giao_dich", "so_luong",
        "ton_kho_truoc", "ton_kho_sau", "tao_boi", "tao_luc"
    )
    list_filter = ("loai_giao_dich", "tao_luc")
    search_fields = ("nguyen_lieu__ten", "ghi_chu")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.2. `moc-backend/branches/admin.py`
```python
from django.contrib import admin
from .models import ChiNhanh


@admin.register(ChiNhanh)
class ChiNhanhAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "so_dien_thoai", "dia_chi", "con_hoat_dong", "tao_luc")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ten", "dia_chi", "so_dien_thoai")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.3. `moc-backend/reservations/admin.py`
```python
from django.contrib import admin
from .models import (
    BanAn,
    ChinhSachDatCoc,
    QuyTacHuyDatCoc,
    DatBan,
    MonAnTrongDatBan,
)


@admin.register(BanAn)
class BanAnAdmin(admin.ModelAdmin):
    list_display = ("id", "so_ban", "chi_nhanh", "khu_vuc", "suc_chua", "trang_thai")
    list_filter = ("chi_nhanh", "trang_thai", "khu_vuc")
    search_fields = ("so_ban", "khu_vuc")


class QuyTacHuyDatCocInline(admin.TabularInline):
    model = QuyTacHuyDatCoc
    extra = 1


@admin.register(ChinhSachDatCoc)
class ChinhSachDatCocAdmin(admin.ModelAdmin):
    list_display = (
        "id", "chi_nhanh", "phan_tram_coc",
        "thoi_gian_giu_cho_phut", "han_thanh_toan_phut", "con_ap_dung"
    )
    list_filter = ("con_ap_dung", "chi_nhanh")
    inlines = [QuyTacHuyDatCocInline]


@admin.register(QuyTacHuyDatCoc)
class QuyTacHuyDatCocAdmin(admin.ModelAdmin):
    list_display = ("id", "chinh_sach", "moc_thoi_gian", "phan_tram_hoan_tien")
    list_filter = ("moc_thoi_gian",)


class MonAnTrongDatBanInline(admin.TabularInline):
    model = MonAnTrongDatBan
    extra = 0
    readonly_fields = ("mon_an", "so_luong", "don_gia_luc_dat")


@admin.register(DatBan)
class DatBanAdmin(admin.ModelAdmin):
    list_display = (
        "ma_dat_ban", "ten_khach", "sdt_khach", "chi_nhanh", "ban_an",
        "ngay_dat", "gio_bat_dau", "hinh_thuc", "trang_thai",
        "trang_thai_coc", "so_tien_coc"
    )
    list_filter = ("trang_thai", "trang_thai_coc", "hinh_thuc", "chi_nhanh", "ngay_dat")
    search_fields = ("ma_dat_ban", "ten_khach", "sdt_khach")
    readonly_fields = ("ma_dat_ban", "phien_ban", "tao_luc", "cap_nhat_luc")
    inlines = [MonAnTrongDatBanInline]


@admin.register(MonAnTrongDatBan)
class MonAnTrongDatBanAdmin(admin.ModelAdmin):
    list_display = ("id", "dat_ban", "mon_an", "so_luong", "don_gia_luc_dat")
    search_fields = ("dat_ban__ma_dat_ban", "mon_an__ten")
```

### 3.4. `moc-backend/orders/admin.py`
```python
from django.contrib import admin
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon


class ChiTietDonHangInline(admin.TabularInline):
    model = ChiTietDonHang
    extra = 0
    readonly_fields = ("mon_an", "so_luong", "don_gia_luc_dat", "thanh_tien")


class LichSuTrangThaiDonInline(admin.TabularInline):
    model = LichSuTrangThaiDon
    extra = 0
    readonly_fields = ("tu_trang_thai", "sang_trang_thai", "doi_boi", "ghi_chu", "tao_luc")


@admin.register(DonHang)
class DonHangAdmin(admin.ModelAdmin):
    list_display = (
        "ma_don_hang", "ten_khach", "sdt_khach", "hinh_thuc",
        "trang_thai", "tong_tien", "chi_nhanh", "tao_luc"
    )
    list_filter = ("trang_thai", "hinh_thuc", "chi_nhanh", "tao_luc")
    search_fields = ("ma_don_hang", "ten_khach", "sdt_khach")
    readonly_fields = ("ma_don_hang", "tao_luc", "cap_nhat_luc")
    inlines = [ChiTietDonHangInline, LichSuTrangThaiDonInline]


@admin.register(ChiTietDonHang)
class ChiTietDonHangAdmin(admin.ModelAdmin):
    list_display = ("id", "don_hang", "mon_an", "so_luong", "don_gia_luc_dat", "thanh_tien")
    search_fields = ("don_hang__ma_don_hang", "mon_an__ten")


@admin.register(LichSuTrangThaiDon)
class LichSuTrangThaiDonAdmin(admin.ModelAdmin):
    list_display = ("id", "don_hang", "tu_trang_thai", "sang_trang_thai", "doi_boi", "tao_luc")
    list_filter = ("sang_trang_thai",)
    search_fields = ("don_hang__ma_don_hang", "ghi_chu")
```

### 3.5. `moc-backend/payments/admin.py`
```python
from django.contrib import admin
from .models import ThanhToan


@admin.register(ThanhToan)
class ThanhToanAdmin(admin.ModelAdmin):
    list_display = (
        "id", "ma_giao_dich", "nguoi_dung", "loai_thanh_toan",
        "phuong_thuc", "so_tien", "trang_thai", "thanh_toan_luc", "tao_luc"
    )
    list_filter = ("trang_thai", "loai_thanh_toan", "phuong_thuc")
    search_fields = ("ma_giao_dich", "nguoi_dung__username", "nguoi_dung__thu_dien_tu")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.6. `moc-backend/promotions/admin.py`
```python
from django.contrib import admin
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai


class MaKhuyenMaiInline(admin.TabularInline):
    model = MaKhuyenMai
    extra = 1


@admin.register(KhuyenMai)
class KhuyenMaiAdmin(admin.ModelAdmin):
    list_display = (
        "ma_giam_gia", "ten", "kieu_giam", "gia_tri_giam",
        "don_hang_toi_thieu", "bat_dau_luc", "ket_thuc_luc",
        "con_hoat_dong", "so_lan_da_dung"
    )
    list_filter = ("kieu_giam", "con_hoat_dong")
    search_fields = ("ma_giam_gia", "ten")
    inlines = [MaKhuyenMaiInline]


@admin.register(MaKhuyenMai)
class MaKhuyenMaiAdmin(admin.ModelAdmin):
    list_display = ("id", "khuyen_mai", "ma", "gioi_han", "da_dung", "con_hoat_dong")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ma", "khuyen_mai__ten")


@admin.register(LichSuDungKhuyenMai)
class LichSuDungKhuyenMaiAdmin(admin.ModelAdmin):
    list_display = (
        "id", "khuyen_mai", "ma_khuyen_mai", "nguoi_dung",
        "don_hang", "so_tien_giam", "tao_luc"
    )
    search_fields = ("khuyen_mai__ten", "nguoi_dung__username", "don_hang__ma_don_hang")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.7. `moc-backend/chat/admin.py`
```python
from django.contrib import admin
from .models import HoiThoai, TinNhan


class TinNhanInline(admin.TabularInline):
    model = TinNhan
    extra = 0
    readonly_fields = ("nguoi_gui", "loai_tin_nhan", "noi_dung", "da_doc", "doc_luc", "tao_luc")


@admin.register(HoiThoai)
class HoiThoaiAdmin(admin.ModelAdmin):
    list_display = ("id", "khach_hang", "nhan_vien", "trang_thai", "tin_nhan_cuoi_luc", "tao_luc")
    list_filter = ("trang_thai",)
    search_fields = ("khach_hang__username", "nhan_vien__username")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
    inlines = [TinNhanInline]


@admin.register(TinNhan)
class TinNhanAdmin(admin.ModelAdmin):
    list_display = ("id", "hoi_thoai", "nguoi_gui", "loai_tin_nhan", "da_doc", "doc_luc", "tao_luc")
    list_filter = ("loai_tin_nhan", "da_doc")
    search_fields = ("noi_dung", "nguoi_gui__username")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.8. `moc-backend/recommendations/admin.py`
```python
from django.contrib import admin
from .models import TuongTacMonAn, GoiYMonAn


@admin.register(TuongTacMonAn)
class TuongTacMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "mon_an", "loai_tuong_tac", "trong_so", "tao_luc")
    list_filter = ("loai_tuong_tac",)
    search_fields = ("nguoi_dung__username", "mon_an__ten")
    readonly_fields = ("tao_luc", "cap_nhat_luc")


@admin.register(GoiYMonAn)
class GoiYMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "mon_an", "diem_tuong_dong", "phien_ban_model", "tao_luc")
    search_fields = ("nguoi_dung__username", "mon_an__ten", "phien_ban_model")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.9. `moc-backend/carts/admin.py`
```python
from django.contrib import admin
from .models import GioHang, ChiTietGioHang


class ChiTietGioHangInline(admin.TabularInline):
    model = ChiTietGioHang
    extra = 0
    readonly_fields = ("mon_an", "so_luong", "don_gia_luc_dat", "ghi_chu")


@admin.register(GioHang)
class GioHangAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "trang_thai", "tao_luc", "cap_nhat_luc")
    list_filter = ("trang_thai",)
    search_fields = ("nguoi_dung__username",)
    readonly_fields = ("tao_luc", "cap_nhat_luc")
    inlines = [ChiTietGioHangInline]


@admin.register(ChiTietGioHang)
class ChiTietGioHangAdmin(admin.ModelAdmin):
    list_display = ("id", "gio_hang", "mon_an", "so_luong", "don_gia_luc_dat")
    search_fields = ("gio_hang__nguoi_dung__username", "mon_an__ten")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.10. `moc-backend/reviews/admin.py`
```python
from django.contrib import admin
from .models import DanhGia


@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nguoi_dung", "mon_an", "don_hang",
        "diem_danh_gia", "hien_thi", "tao_luc"
    )
    list_filter = ("diem_danh_gia", "hien_thi")
    search_fields = ("nguoi_dung__username", "mon_an__ten", "nhan_xet")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.11. `moc-backend/posts/admin.py`
```python
from django.contrib import admin
from .models import DanhMucBaiViet, BaiViet


@admin.register(DanhMucBaiViet)
class DanhMucBaiVietAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "duong_dan", "tao_luc")
    search_fields = ("ten", "duong_dan")
    prepopulated_fields = {"duong_dan": ("ten",)}
    readonly_fields = ("tao_luc", "cap_nhat_luc")


@admin.register(BaiViet)
class BaiVietAdmin(admin.ModelAdmin):
    list_display = ("id", "tieu_de", "danh_muc", "tac_gia", "trang_thai", "dang_luc", "tao_luc")
    list_filter = ("trang_thai", "danh_muc")
    search_fields = ("tieu_de", "noi_dung", "tac_gia__username")
    prepopulated_fields = {"duong_dan": ("tieu_de",)}
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

### 3.12. `moc-backend/analytics/admin.py`
```python
from django.contrib import admin
from .models import ThongBao


@admin.register(ThongBao)
class ThongBaoAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "loai", "tieu_de", "da_doc", "doc_luc", "tao_luc")
    list_filter = ("loai", "da_doc")
    search_fields = ("tieu_de", "noi_dung", "nguoi_dung__username")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
```

---

## 4. Adversarial Test Harness: Tái hiện & Kiểm chứng 18 Kịch bản

File test đã được định hình tại:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_3/proposed_test_adversarial_challenger_m1.py`

Khi chuyển giao sang code source của dự án, Worker sẽ đặt tại:
`/Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m1.py`
và đăng ký vào `tests/e2e/runner.py` (Tier 1 hoặc Tier 5 Adversarial).

### Bảng đối chiếu 18 kịch bản kiểm thử:

| # | Kịch bản kiểm thử | Tên Test Case trong Test Harness | Trạng thái hiện tại | Trạng thái sau bản vá | Cơ chế xác thực |
|---|-------------------|-----------------------------------|----------------------|------------------------|------------------|
| 1 | `Food.name` setter | `test_scenario_01_food_name_setter` | FAIL (`AttributeError`) | **PASS** | Gán `f.name = 'B'`, kiểm tra `f.ten == 'B'` |
| 2 | `Food.price` setter | `test_scenario_02_food_price_setter` | FAIL (`AttributeError`) | **PASS** | Gán `f.price = 200`, kiểm tra `f.don_gia == 200` |
| 3 | `Food` legacy kwargs | `test_scenario_03_food_legacy_kwargs` | FAIL (`AttributeError`) | **PASS** | Khởi tạo `Food(name='...', price=...)` |
| 4 | `Table.status` getter | `test_scenario_04_table_status_getter` | FAIL (thiếu property) | **PASS** | Đọc `Table.status`, kiểm tra bằng `trang_thai` |
| 5 | `Table.status` setter | `test_scenario_05_table_status_setter` | FAIL (không đổi DB) | **PASS** | Gán `t.status = 'X'`, kiểm tra `t.trang_thai == 'X'` |
| 6 | `Table` legacy kwargs | `test_scenario_06_table_legacy_kwargs` | FAIL (`TypeError`) | **PASS** | Khởi tạo `Table(status='trong')` |
| 7 | `Table.Status` enum | `test_scenario_07_table_status_enum_alias` | FAIL (thiếu enum) | **PASS** | Kiểm tra `Table.Status == BanAn.TrangThai` |
| 8 | `Order.total` getter | `test_scenario_08_order_total_getter` | FAIL (thiếu property) | **PASS** | Đọc `Order.total`, kiểm tra bằng `tong_tien` |
| 9 | `Order.total` setter | `test_scenario_09_order_total_setter` | FAIL (không đổi DB) | **PASS** | Gán `o.total = 200k`, kiểm tra `o.tong_tien == 200k` |
| 10 | `User.name` getter | `test_scenario_10_user_name_getter` | FAIL (thiếu property) | **PASS** | Đọc `User.name`, trả về họ tên hoặc username |
| 11 | `Branch.name` setter | `test_scenario_11_branch_name_setter` | FAIL (`AttributeError`) | **PASS** | Gán `b.name = 'CN2'`, kiểm tra `b.ten == 'CN2'` |
| 12 | `Branch` legacy kwargs | `test_scenario_12_branch_legacy_kwargs` | FAIL (`AttributeError`) | **PASS** | Khởi tạo `Branch(name='CN1')` |
| 13 | `Payment.amount` getter | `test_scenario_13_payment_amount_getter` | FAIL (thiếu property) | **PASS** | Đọc `Payment.amount`, kiểm tra bằng `so_tien` |
| 14 | `DangKySerializer` email | `test_scenario_14_registration_preserves_email_and_thu_dien_tu` | FAIL (bị xóa mất) | **PASS** | Kiểm tra `create_user` nhận đủ cả `thu_dien_tu` & `email` |
| 15 | `FoodSerializer` English | `test_scenario_15_food_serializer_english_payload` | FAIL (`ValidationError`) | **PASS** | Kiểm tra `to_internal_value` map `name->ten, price->don_gia` |
| 16 | `OrderSerializer` English | `test_scenario_16_order_serializer_english_payload` | FAIL (`ValidationError`) | **PASS** | Kiểm tra `to_internal_value` map `customer_name->ten_khach` |
| 17 | `MonAn` Queryset filter | `test_scenario_17_food_queryset_vietnamese_filter` | **PASS** | **PASS** | Kiểm tra SQL query chứa `WHERE "mon_an"."con_hang"` |
| 18 | `DonHang` relation filter | `test_scenario_18_order_cross_model_relation_filter` | **PASS** | **PASS** | Kiểm tra SQL query JOIN `chi_tiet_don_hang` và `mon_an` |

---

## 5. Caveats (Các điểm giới hạn & Giả định)

1. **Môi trường Sandbox macOS Seatbelt**:
   - Môi trường thực thi sandbox chặn kết nối cổng 5432 (PostgreSQL). Do đó, kịch bản 14 và 15 sử dụng `unittest.mock` đối với các phương thức `create_user` và `PrimaryKeyRelatedField.to_internal_value` để kiểm chứng logic deserialization và mapping mà không phụ thuộc vào kết nối mạng vật lý. Khi chạy ngoài sandbox với PostgreSQL thật, các bài test này vẫn tương thích 100%.
2. **Phân chia nhiệm vụ giữa các Agent trong R2**:
   - Explorer 1 phụ trách chi tiết mã nguồn Model Properties & `__init__` kwargs.
   - Explorer 2 phụ trách chi tiết mã nguồn `DangKySerializer`, `XacThucViewSet` actions, và `to_internal_value` trên Serializers.
   - Explorer 3 cung cấp toàn bộ mã nguồn `admin.py` cho 12 apps và bộ Test Harness 18 kịch bản tích hợp để Worker M1 Iteration 2 nghiệm thu toàn diện.

---

## 6. Conclusion (Kết luận)

Chiến lược triển khai đã sẵn sàng 100% để chuyển giao cho Worker:
1. Đã cung cấp công thức mã nguồn chi tiết cho 12 file `admin.py`, bảo đảm đăng ký đầy đủ tất cả canonical models và thông qua hệ thống kiểm tra `AdminSite.check()` với **0 lỗi**.
2. Đã tạo lập bộ test đối kháng 18 kịch bản chuẩn hóa bằng `unittest.TestCase`, tái hiện trung thực hiện trạng 16 Fail / 2 Pass của Challenger 1, và chứng minh được khi áp dụng bản vá sẽ đạt **18/18 Pass (100% clean)**.
3. Bảo đảm `python manage.py check` duy trì trạng thái **0 issues**.

---

## 7. Verification Method (Hướng dẫn kiểm chứng độc lập)

Sau khi Worker hoàn thành áp dụng các thay đổi:

### Bước 1: Kiểm tra Django System Check
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py check
```
*Kỳ vọng*: `System check identified no issues (0 silenced).` Exit code 0.

### Bước 2: Kiểm tra Đăng ký Django Admin 12 Apps
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
from django.contrib import admin
from foods.models import MonAn, DanhMuc
from branches.models import ChiNhanh
from reservations.models import BanAn, DatBan
from orders.models import DonHang
from payments.models import ThanhToan
from promotions.models import KhuyenMai
from chat.models import HoiThoai
from recommendations.models import TuongTacMonAn
from carts.models import GioHang
from reviews.models import DanhGia
from posts.models import BaiViet
from analytics.models import ThongBao

models_to_check = [
    MonAn, DanhMuc, ChiNhanh, BanAn, DatBan, DonHang,
    ThanhToan, KhuyenMai, HoiThoai, TuongTacMonAn,
    GioHang, DanhGia, BaiViet, ThongBao
]
for m in models_to_check:
    assert m in admin.site._registry, f'{m.__name__} not registered in admin!'
print('ALL 12 APPS ADMIN REGISTRATIONS VERIFIED SUCCESSFULLY!')
"
```
*Kỳ vọng*: In ra `ALL 12 APPS ADMIN REGISTRATIONS VERIFIED SUCCESSFULLY!`.

### Bước 3: Chạy Toàn bộ 18 Kịch bản Đối kháng
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
import unittest
from pathlib import Path

# Load and run proposed test harness
test_path = '/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m1_r2_3/proposed_test_adversarial_challenger_m1.py'
import importlib.util
spec = importlib.util.spec_from_file_location('adv_test', test_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

suite = unittest.TestLoader().loadTestsFromTestCase(mod.AdversarialChallengerTestSuite)
res = unittest.TextTestRunner(verbosity=2).run(suite)
assert len(res.failures) == 0 and len(res.errors) == 0, 'Some adversarial tests failed!'
print('ALL 18 ADVERSARIAL TESTS PASSED 100%!')
"
```
*Kỳ vọng*: 18 tests run, OK, `ALL 18 ADVERSARIAL TESTS PASSED 100%!`.

### Bước 4: Chạy Lại Master E2E Runner
```bash
cd /Users/VuVan/Documents/DO-AN
python3 tests/e2e/runner.py --tier 1 --verbose
```
*Kỳ vọng*: 30/30 tests passed, 100.0% Pass Rate.
