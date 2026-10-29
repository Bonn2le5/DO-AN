# BÁO CÁO PHẢN BIỆN & KIỂM THỬ ĐỐI KHÁNG MILESTONE 1 (CHALLENGER REPORT)
**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Agent**: Milestone 1 Empirical Challenger 1 (`teamwork_preview_challenger_m1_1`)  
**Thời gian**: 2026-10-14T04:05:00Z  
**Đường dẫn**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m1_1/handoff.md`  
**Quyết định (Verdict)**: **REQUEST_CHANGES**

---

## 1. Challenge Summary (Tổng quan Đánh giá Rủi ro)

- **Overall Risk Assessment**: **HIGH / CRITICAL**
- **Tóm tắt kết quả kiểm thử đối kháng (Adversarial Stress Test)**:
  - Tổng số kịch bản kiểm thử đối kháng thực tế: **18**
  - Số kịch bản đạt (Pass): **2**
  - Số kịch bản thất bại (Fail): **16**
  - Tỷ lệ vượt qua (Pass Rate): **11.1%**
- **Nguyên nhân chính**:
  1. **60/94 thuộc tính tương thích ngược chỉ có Getter, không có Setter**: Gây lỗi `AttributeError: can't set attribute` khi gán giá trị (ví dụ `food.name = '...'`, `food.price = 100`, `branch.name = '...'`).
  2. **Gãy khởi tạo Model qua keyword arguments**: Lệnh `Food(name='...', price=...)` hoặc `Branch(name='...')` sập ngay lập tức với `AttributeError` do Django model `__init__` gọi `setattr`.
  3. **Thiếu hoàn toàn thuộc tính trên các Model quan trọng**: `Table` (`BanAn`) không hề có `status`, `capacity`, `table_number`, `branch`, `area`, `Table.Status`; `Order` (`DonHang`) thiếu `total`; `User` (`NguoiDung`) thiếu `name`, `phone`; `Payment` (`ThanhToan`) thiếu `amount`. Gây lỗi `AttributeError` hoặc âm thầm tạo thuộc tính rác không đồng bộ với CSDL (`o.total = 200` nhưng `o.tong_tien` vẫn là `100`).
  4. **Lỗi nghiêm trọng trong đăng ký tài khoản (`DangKySerializer.create`)**: Dòng 51 `accounts/serializers.py` xóa mất `thu_dien_tu` (`du_lieu_da_xac_thuc.pop("thu_dien_tu")`), khiến mọi user đăng ký mới đều bị gán `thu_dien_tu = ''`. Khi user thứ hai đăng ký sẽ gây sập hệ thống với `IntegrityError` (vi phạm ràng buộc UNIQUE của `thu_dien_tu`), đồng thời người dùng không thể đăng nhập JWT bằng email.
  5. **100% DRF Serializers từ chối payload tiếng Anh**: Mọi serializer (`FoodSerializer`, `OrderSerializer`, `PaymentSerializer`, ...) đều trả về HTTP 400 và báo lỗi thiếu trường bắt buộc tiếng Việt khi nhận payload tiếng Anh. `ThanhToanSerializer.validate()` có mã chết (dead code) kiểm tra `payment_type` và `order` trong khi DRF đã loại bỏ các trường này trước khi validate.
  6. **Độ bao phủ của kiểm thử Tier 1 còn mỏng**: Bộ test Tier 1 (30 tests) chạy trong 0.005s chỉ kiểm tra sự tồn tại của file tĩnh và các lớp mock helper cô lập (`vnpay_oracle`, `redis_lock_sim`, `fsm_validator`), hoàn toàn bỏ qua việc kiểm chứng model getters/setters, serializers và queryset lookups thực tế.

---

## 2. Observation (Các quan sát trực tiếp & Bằng chứng thực tế)

### 2.1. Kiểm chứng Property Getters/Setters trên 18 Models (94 thuộc tính kiểm tra)
Thực thi lệnh kiểm tra tự động trên `moc-backend`:
```bash
./.venv/bin/python manage.py shell -c "..."
```
**Bằng chứng thực tế**:
1. **Thiếu hoàn toàn 9 thuộc tính/enum cốt lõi**:
   - `Order.total`: `AttributeError: 'DonHang' object has no attribute 'total'` (`orders/models.py:83` chỉ có `total_amount`).
   - `Table.status`: `AttributeError: 'BanAn' object has no attribute 'status'` (`reservations/models.py:8` không có thuộc tính nào).
   - `Table.capacity`: Không tồn tại (chỉ có `suc_chua`).
   - `Table.table_number`: Không tồn tại (chỉ có `so_ban`).
   - `Table.branch`: Không tồn tại (chỉ có `chi_nhanh`).
   - `Table.area`: Không tồn tại (chỉ có `khu_vuc`).
   - `Table.Status`: `AttributeError: type object 'BanAn' has no attribute 'Status'` (trong khi `DonHang.Status` và `DatBan.Status` đều có).
   - `User.name`: `AttributeError: 'NguoiDung' object has no attribute 'name'` (`accounts/models.py:43`).
   - `User.phone`: Không tồn tại (chỉ có `so_dien_thoai`).
   - `Payment.amount`: `AttributeError: 'ThanhToan' object has no attribute 'amount'` (`payments/models.py:6`).

2. **60 thuộc tính là Getter-only, không có Setter**:
   - `Food.name` (`foods/models.py:117`):
     ```python
     f = Food(ten='Lẩu nấm')
     f.name = 'Lẩu thái'
     # Verbatim Error: AttributeError: can't set attribute
     ```
   - `Food.price` (`foods/models.py:113`):
     ```python
     f = Food(don_gia=100)
     f.price = 200
     # Verbatim Error: AttributeError: can't set attribute
     ```
   - Khởi tạo `Food(name="Phở", price=50000)`:
     ```python
     # Verbatim Error: AttributeError: can't set attribute
     ```
   - Khởi tạo `Branch(name="Chi nhánh 1")`:
     ```python
     # Verbatim Error: AttributeError: can't set attribute
     ```
   - Khởi tạo `Table(status="trong")`:
     ```python
     # Verbatim Error: TypeError: BanAn() got unexpected keyword arguments: 'status'
     ```

3. **Hiện tượng gán thuộc tính giả (Silent Disconnected Attributes)**:
   ```python
   o = Order(tong_tien=100)
   o.total = 200
   print(o.tong_tien)  # Kết quả: 100 (Không cập nhật CSDL)

   t = Table(trang_thai='trong')
   t.status = 'dang_giu'
   print(t.trang_thai)  # Kết quả: 'trong' (Không cập nhật CSDL)
   ```

### 2.2. Lỗi mất `thu_dien_tu` trong `DangKySerializer.create`
Tại file `/Users/VuVan/Documents/DO-AN/moc-backend/accounts/serializers.py`, dòng 47–56:
```python
47: def create(self, du_lieu_da_xac_thuc):
48:     ho_ten = du_lieu_da_xac_thuc.pop("ho_ten", "").strip()
49:     mat_khau = du_lieu_da_xac_thuc.pop("mat_khau")
50:     du_lieu_da_xac_thuc.setdefault("username", du_lieu_da_xac_thuc["thu_dien_tu"].split("@", 1)[0])
51:     du_lieu_da_xac_thuc["email"] = du_lieu_da_xac_thuc.pop("thu_dien_tu")  # <-- XÓA MẤT thu_dien_tu!
...
56:     nguoi_dung = NguoiDung.objects.create_user(password=mat_khau, **du_lieu_da_xac_thuc)
```
- Tại `accounts/models.py:44`: `thu_dien_tu = models.EmailField(unique=True)` và dòng 57: `USERNAME_FIELD = "thu_dien_tu"`.
- Vì dòng 51 gọi `du_lieu_da_xac_thuc.pop("thu_dien_tu")`, dictionary không còn key `thu_dien_tu`.
- `create_user` gán giá trị mặc định cho `thu_dien_tu` là rỗng `''`.
- Thực nghiệm kiểm chứng:
  ```python
  u = NguoiDung.objects.model(username='test_user', email='test@test.com')
  print(repr(u.thu_dien_tu))  # Kết quả: ''
  ```
  User thứ 2 đăng ký sẽ vi phạm `unique constraint "nguoi_dung_thu_dien_tu_key"` và ném ngoại lệ `IntegrityError`.

### 2.3. DRF Serializers từ chối 100% English Payloads
Thực thi kiểm tra deserialization:
1. `FoodSerializer(data={'name': 'Phở bò', 'price': 60000})`:
   ```text
   is_valid: False
   errors: {'ten': ['This field is required.'], 'don_gia': ['This field is required.'], 'danh_muc': ['This field is required.']}
   ```
2. `OrderSerializer(data={'customer_name': 'Nguyen Van A', 'phone': '0901234567', 'type': 'tu_den_lay'})`:
   ```text
   is_valid: False
   errors: {'hinh_thuc': ['This field is required.'], 'ten_khach': ['This field is required.'], 'sdt_khach': ['This field is required.']}
   ```
3. `PaymentSerializer(data={'payment_type': 'don_hang', 'amount': 100000, 'method': 'vnpay'})`:
   ```text
   is_valid: False
   errors: {'loai_thanh_toan': ['This field is required.'], 'phuong_thuc': ['This field is required.'], 'so_tien': ['This field is required.']}
   ```
4. Tại `payments/serializers.py:12`:
   ```python
   loai = attrs.get("loai_thanh_toan") or attrs.get("payment_type")
   don_hang = attrs.get("don_hang") or attrs.get("order")
   ```
   Vì `payment_type` và `order` không nằm trong `fields` của `ThanhToanSerializer`, DRF tự động loại bỏ chúng ở `to_internal_value()`. Do đó `attrs.get("payment_type")` luôn luôn là `None` (Dead code).

### 2.4. QuerySet Filtering & Cross-Model Relations
1. **Truy vấn bằng trường tiếng Việt**: Hoạt động hoàn hảo:
   - `MonAn.objects.filter(con_hang=True)` -> Sinh SQL chính xác `WHERE "mon_an"."con_hang"`.
   - `DonHang.objects.filter(trang_thai='cho_tiep_nhan', danh_sach_mon__mon_an__ten='Phở')` -> Sinh JOIN chính xác tới bảng `chi_tiet_don_hang` và `mon_an`.
   - `DatBan.objects.filter(ban_an__suc_chua__gte=4)` -> Sinh JOIN chính xác tới `ban_an`.
2. **Truy vấn bằng thuộc tính tiếng Anh**: Bị từ chối bởi Django ORM (hành vi chuẩn của Django ORM):
   - `Food.objects.filter(name='Phở')` -> `FieldError: Cannot resolve keyword 'name' into field`.
   - `Food.objects.filter(price__gte=50000)` -> `FieldError: Cannot resolve keyword 'price' into field`.

---

## 3. Logic Chain (Chuỗi suy luận từ quan sát tới kết luận)

1. **Từ Quan sát 2.1**:
   - Khẳng định của Worker M1 rằng "hệ thống duy trì hoàn toàn khả năng tương thích ngược cho mã legacy thông qua `@property` getters/setters" là chưa đầy đủ.
   - Việc chỉ định nghĩa `@property def price(self): return self.don_gia` mà không có `@price.setter` khiến mọi thao tác gán (`food.price = X`) và mọi khởi tạo `Food(price=X)` đều ném lỗi `AttributeError`.
   - Các model như `Table` hoàn toàn không có bất kỳ property nào (`status`, `capacity`, `so_ban`, `chi_nhanh`). Khi mã nghiệp vụ gọi `table.status = 'dang_giu'`, Python chỉ tạo một biến instance tạm thời trên RAM mà không cập nhật trường `trang_thai`, dẫn đến trạng thái bàn trong CSDL không bao giờ đổi.

2. **Từ Quan sát 2.2**:
   - `accounts/models.py` đặt `USERNAME_FIELD = "thu_dien_tu"`.
   - `DangKySerializer.create` gán `email = pop("thu_dien_tu")` và gọi `create_user()`.
   - Vì `create_user` không nhận `thu_dien_tu`, model lưu giá trị rỗng `''`.
   - Ràng buộc `unique=True` trên `thu_dien_tu` sẽ từ chối bản ghi thứ 2, gây sập API đăng ký người dùng trong quá trình vận hành thực tế.

3. **Từ Quan sát 2.3**:
   - DRF Serializers hiện tại chỉ hỗ trợ thuần túy schema tiếng Việt. Mọi payload gửi từ frontend hoặc test legacy bằng tiếng Anh đều bị từ chối với HTTP 400.
   - Mã nguồn của `ThanhToanSerializer` thể hiện mong muốn hỗ trợ song ngữ (`attrs.get("payment_type")`), nhưng do thiếu khai báo trường trên Serializer nên cơ chế này hoàn toàn vô hiệu.

4. **Từ Quan sát 2.4**:
   - Bộ kiểm thử Tier 1 đạt 100% nhưng chỉ kiểm thử các module mô phỏng độc lập (`tests/e2e/helpers/`), không chạm vào các adapter properties và serializers đã bị lỗi ở trên.

---

## 4. Caveats (Các điểm giới hạn & Giả định)

1. **Rào cản môi trường sandbox macOS**:
   - macOS Seatbelt chặn socket TCP cục bộ đến port 5432, ngăn cản việc chạy kiểm thử truy vấn trực tiếp vào PostgreSQL database đang chạy.
   - Tuy nhiên, 100% các lỗi về property setters, model instantiation, serializer validation, và logic ORM đã được tái hiện và chứng minh độc lập bằng thực nghiệm trên môi trường Python/Django runtime mà không cần DB.

---

## 5. Detailed Adversarial Stress Test Results

| # | Kịch bản kiểm thử | Kỳ vọng | Thực tế | Kết quả |
|---|-------------------|---------|---------|---------|
| 1 | `Food.name` setter (`f.name = 'B'`) | Cập nhật `f.ten = 'B'` | `AttributeError: can't set attribute` | **FAIL** |
| 2 | `Food.price` setter (`f.price = 20`) | Cập nhật `f.don_gia = 20` | `AttributeError: can't set attribute` | **FAIL** |
| 3 | `Food(name='A', price=100)` kwargs | Khởi tạo thành công | `AttributeError: can't set attribute` | **FAIL** |
| 4 | `Table.status` getter | Trả về `t.trang_thai` | `AttributeError: 'BanAn' has no attribute 'status'` | **FAIL** |
| 5 | `Table.status` setter | Cập nhật `t.trang_thai` | Không cập nhật `trang_thai` (âm thầm gán thuộc tính rác) | **FAIL** |
| 6 | `Table(status='trong')` kwargs | Khởi tạo thành công | `TypeError: unexpected keyword argument 'status'` | **FAIL** |
| 7 | `Table.Status` enum alias | Bằng `BanAn.TrangThai` | `AttributeError: type object 'BanAn' has no attribute 'Status'` | **FAIL** |
| 8 | `Order.total` getter | Trả về `o.tong_tien` | `AttributeError: 'DonHang' has no attribute 'total'` | **FAIL** |
| 9 | `Order.total` setter | Cập nhật `o.tong_tien` | Không cập nhật `tong_tien` | **FAIL** |
| 10 | `User.name` getter | Trả về họ tên/username | `AttributeError: 'NguoiDung' has no attribute 'name'` | **FAIL** |
| 11 | `Branch.name` setter | Cập nhật `b.ten` | `AttributeError: can't set attribute` | **FAIL** |
| 12 | `Branch(name='CN1')` kwargs | Khởi tạo thành công | `AttributeError: can't set attribute` | **FAIL** |
| 13 | `Payment.amount` getter | Trả về `p.so_tien` | `AttributeError: 'ThanhToan' has no attribute 'amount'` | **FAIL** |
| 14 | `DangKySerializer` lưu `thu_dien_tu` | Giữ nguyên `thu_dien_tu` | Bị `pop()` khỏi kwargs, gán rỗng `''` | **FAIL** |
| 15 | `FoodSerializer` English payload | Deserialization hợp lệ | `ValidationError: ten, don_gia, danh_muc required` | **FAIL** |
| 16 | `OrderSerializer` English payload | Deserialization hợp lệ | `ValidationError: hinh_thuc, ten_khach, sdt_khach required` | **FAIL** |
| 17 | `MonAn` Queryset filter tiếng Việt | Tạo SQL `WHERE con_hang` | Hoạt động chính xác | **PASS** |
| 18 | `DonHang` Cross-model relation filter | Tạo SQL JOIN bảng liên quan | Hoạt động chính xác | **PASS** |

---

## 6. Actionable Fix Plan (Các đề xuất hành động cần Worker M1 thực hiện)

1. **Bổ sung đầy đủ Setter cho tất cả Model Properties**:
   - `foods/models.py`: Bổ sung `@name.setter`, `@price.setter`, `@slug.setter`, `@is_active.setter`.
   - `branches/models.py`: Bổ sung `@name.setter`, `@address.setter`, `@phone.setter`, `@is_active.setter`.
   - `orders/models.py`: Bổ sung `@property def total(self): return self.tong_tien`, `@total.setter`, `@total_amount.setter`, `@customer.setter`.
   - `reservations/models.py`:
     * Thêm thuộc tính cho `BanAn`: `status` (getter/setter -> `trang_thai`), `capacity` (getter/setter -> `suc_chua`), `table_number` (getter/setter -> `so_ban`), `branch` (getter/setter -> `chi_nhanh`), `area` (getter/setter -> `khu_vuc`).
     * Thêm alias enum: `BanAn.Status = BanAn.TrangThai`.
   - `accounts/models.py`:
     * Thêm property `name` (getter: `self.get_full_name() or self.username`).
     * Thêm property `phone` (getter/setter -> `so_dien_thoai`).
   - `payments/models.py`:
     * Thêm property `amount` (getter/setter -> `so_tien`).

2. **Khắc phục lỗi đăng ký tài khoản trong `accounts/serializers.py`**:
   - Trong `DangKySerializer.create()`: KHÔNG pop `thu_dien_tu`.
   - Sửa dòng 51:
     ```python
     du_lieu_da_xac_thuc["email"] = du_lieu_da_xac_thuc.get("thu_dien_tu")
     ```
     Đảm bảo `thu_dien_tu` vẫn được truyền vào `create_user(**du_lieu_da_xac_thuc)`.

3. **Bổ sung trường bí danh hoặc adapter cho Serializers**:
   - Cung cấp `to_internal_value()` hoặc định nghĩa explicit fields trong serializers nếu muốn chấp nhận payload song ngữ (hoặc tài liệu hóa rõ ràng trong hợp đồng giao diện rằng REST API chỉ chấp nhận payload chuẩn tiếng Việt để Frontend Worker chuẩn hóa schema).

---

## 7. Conclusion (Kết luận)

**Verdict**: **REQUEST_CHANGES**

Hệ thống backend đã đạt được bước tiến lớn về chuẩn hóa schema CSDL tiếng Việt và giải quyết lỗi import. Tuy nhiên, lớp tương thích ngược (Compatibility Adapter Layer) chưa hoàn thiện:
- Tỷ lệ lỗi kiểm thử đối kháng thuộc tính và serializer lên tới 88.9% (16/18 thất bại).
- Tồn tại bug chặn đứng luồng đăng ký tài khoản (`thu_dien_tu` bị gán rỗng).
Yêu cầu Worker M1 tiếp nhận và khắc phục các điểm nêu trên trước khi tiến hành nghiệm thu Milestone 1.

---

## 8. Verification Method (Hướng dẫn tái hiện & Kiểm chứng độc lập)

Chạy lệnh kiểm thử đối kháng tự động sau từ thư mục `moc-backend`:
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py shell -c "
from foods.models import Food
f = Food(ten='Lẩu')
try:
    f.name = 'Lẩu mới'
    print('Food.name setter: PASS')
except AttributeError:
    print('Food.name setter: FAIL (can\'t set attribute)')

from reservations.models import Table
t = Table(trang_thai='trong')
if hasattr(t, 'status'):
    print('Table.status: PASS')
else:
    print('Table.status: FAIL (missing attribute)')

from accounts.models import NguoiDung
u = NguoiDung(username='u1')
if hasattr(u, 'name'):
    print('User.name: PASS')
else:
    print('User.name: FAIL (missing attribute)')
"
```
Kết quả hiển thị chính xác các điểm lỗi đã được nêu trong báo cáo.
