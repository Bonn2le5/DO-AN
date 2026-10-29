# Handoff Report: Milestone 4 — Bug 2 & Interaction Weight Audit (Feature 20)

- **Agent**: `m4_r2_explorer_2`
- **Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2`
- **Target Recipient**: Parent Orchestrator (`e1a47f66-ae44-4e72-ae56-b7ecb23a0048`) & Backend Worker M4
- **Date**: 2026-10-14T16:32:00Z
- **Verdict**: **INVESTIGATION_COMPLETE — REMEDIATION_READY**

---

## 1. Observation (Quan sát thực nghiệm)

### 1.1 Khảo sát Bug 2 tại `moc-backend/orders/services.py`
Tại `moc-backend/orders/services.py`, hàm `DichVuDonHang.tao_don_hang` (dòng 80–84):
```python
80:             from recommendations.models import TuongTacMonAn
81:             TuongTacMonAn.objects.create(
82:                 nguoi_dung=nguoi_dung, mon_an=mon_an,
83:                 loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=6
84:             )
```
- Lệnh chạy kiểm thử tái hiện lỗi:
  ```bash
  PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py
  ```
- Kết quả và lỗi hiển thị verbatim:
  ```text
  FAIL: test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4 (__main__.TestMilestone4BugReproduction)
  Traceback (most recent call last):
    File "/Users/VuVan/Documents/DO-AN/tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py", line 116, in test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4
      self.assertEqual(
  AssertionError: Decimal('6.00') != Decimal('4.00') : HIGH BUG REPRODUCED: orders/services.py:83 created TuongTacMonAn with trong_so=6.00, expected 4.00 per Feature 20
  ```

### 1.2 Kiểm toán toàn diện tất cả các vị trí tạo và chỉnh sửa `TuongTacMonAn` (Feature 20 Compliance Audit)
Theo tài liệu đặc tả hệ thống (`PROJECT.md` Feature 20 và `moc_schema_tieng_viet.sql`):
Quy chuẩn trọng số tương tác:
$$\text{xem}=1,\quad \text{yeu\_thich}=2,\quad \text{them\_gio\_hang}=3,\quad \text{dat\_mon}=4,\quad \text{danh\_gia}=5$$

Kết quả kiểm toán trên toàn bộ codebase:

| STT | Tập tin & Dòng lệnh | Hành vi ghi nhận | Trọng số thực tế | Đánh giá tuân thủ Feature 20 |
|:---:|:---|:---|:---:|:---:|
| 1 | `moc-backend/orders/services.py:80-84` | Tạo tương tác khi đặt đơn (`tao_don_hang`) | `trong_so=6` | **VI PHẠM (BUG 2)** — Phải là `4` |
| 2 | `moc-backend/reviews/views.py:38-43` | Tạo tương tác khi đánh giá món (`perform_create`) | `trong_so=5` | **ĐẠT CHUẨN** (`danh_gia=5`) |
| 3 | `moc-backend/recommendations/services.py:17-23` | Bảng tra cứu trọng số `TRONG_SO_TUONG_TAC` | `xem:1, yeu_thich:2, them_gio_hang:3, dat_mon:4, danh_gia:5` | **ĐẠT CHUẨN** |
| 4 | `moc-backend/recommendations/services.py:26-38` | Bảng bí danh `ALIAS_TRONG_SO` (`order:4, cart:3, ...`) | Phù hợp tương ứng 1, 2, 3, 4, 5 | **ĐẠT CHUẨN** |
| 5 | `moc-backend/recommendations/serializers.py:48-50` | Mặc định gán `trong_so` từ `TRONG_SO_TUONG_TAC` nếu thiếu hoặc bằng 1 | Tra cứu đúng `TRONG_SO_TUONG_TAC` | **ĐẠT CHUẨN** |
| 6 | `moc-backend/recommendations/models.py:7-13, 19` | Định nghĩa ENUM `LoaiTuongTac` & trường `trong_so` | `default=1` | **ĐẠT CHUẨN** |
| 7 | `moc-backend/recommendations/views.py:27-31` | `TuongTacMonAnViewSet.perform_create` | Dùng serializer validation | **ĐẠT CHUẨN** |
| 8 | `moc-backend/foods/views.py` | Xem thực đơn & món liên quan | Không tự động ghi DB (frontend gửi request view riêng) | **ĐẠT CHUẨN** |
| 9 | `moc-backend/carts/views.py` | Thêm vào giỏ hàng (`add_item`) | Quản lý giỏ hàng; tương tác gọi qua `/api/tuong-tac/` | **ĐẠT CHUẨN** |

**Kết luận kiểm toán**: Trong toàn bộ codebase, chỉ duy nhất `moc-backend/orders/services.py:83` vi phạm quy chuẩn trọng số Feature 20 do hardcode `trong_so=6`.

---

## 2. Logic Chain (Chuỗi lập luận kỹ thuật)

1. **Từ Quan sát 1.1**:
   - `DichVuDonHang.tao_don_hang` khởi tạo `TuongTacMonAn` khi khách hàng đặt món thông qua ORM:
     `TuongTacMonAn.objects.create(nguoi_dung=nguoi_dung, mon_an=mon_an, loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=6)`.
2. **Từ Quan sát 1.2 & `moc-backend/recommendations/services.py:227-230`**:
   - Khi tính toán vector khẩu vị người dùng (`vector_khau_vi`), thuật toán đọc:
     `trong_so = float(tt.trong_so) if tt.trong_so else lay_trong_so_tuong_tac(tt.loai_tuong_tac)`
   - Do `tt.trong_so` lưu giá trị `6.00`, thuật toán gán hệ số 6.0 thay vì 4.0, làm lệch tỷ trọng đóng góp của hành vi đặt món so với đánh giá (`5.0`), giỏ hàng (`3.0`), yêu thích (`2.0`), và xem (`1.0`).
3. **Từ kiểm thử thực nghiệm đối kháng**:
   - Khi mô phỏng sửa `trong_so=4` tại vị trí tạo đơn, `test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4` lập tức chuyển từ `FAIL` sang `PASS`.
   - Khi tích hợp đồng thời 3 giải pháp khắc phục (Bug 1: bổ sung `queryset`/`get_queryset` vào `GoiYMonAnViewSet`; Bug 2: `trong_so=4` tại `orders/services.py:83`; Bug 3: `post_save`/`post_delete` signal xóa cache `GoiYMonAn`), toàn bộ 3/3 tests trong `test_adversarial_challenger_m4_bug_reproduction.py` đều chuyển sang `PASS` (100% OK).

---

## 3. Caveats (Lưu ý & Điểm biên kỹ thuật)

1. **Dữ liệu tương tác cũ (nếu có)**: Các bản ghi `TuongTacMonAn` đã tạo trước đó trong DB thử nghiệm với `trong_so=6.00` sẽ vẫn giữ nguyên 6.00 trừ khi có câu lệnh cập nhật `TuongTacMonAn.objects.filter(loai_tuong_tac="dat_mon", trong_so=6).update(trong_so=4)`. Trong môi trường kiểm thử CI/CD, database test được dựng mới hoàn toàn nên không bị ảnh hưởng.
2. **Nguyên tắc Read-only Explorer**: Là Explorer, tôi không trực tiếp ghi đè lên file sản phẩm mà bàn giao file patch độc lập và hướng dẫn chi tiết để Worker/Implementer áp dụng an toàn.

---

## 4. Conclusion (Kết luận & Đề xuất hành động)

### 4.1 Đánh giá chung
Bug 2 hoàn toàn cô lập tại một dòng code duy nhất: `moc-backend/orders/services.py:83`. Toàn bộ các module khác (`reviews`, `recommendations`, `serializers`, `models`) đều đã tuân thủ chuẩn xác Feature 20.

### 4.2 Mã sửa chữa đề xuất (Code Diff)

#### File: `moc-backend/orders/services.py` (Dòng 80–85)
```diff
--- a/moc-backend/orders/services.py
+++ b/moc-backend/orders/services.py
@@ -80,5 +80,5 @@ class DichVuDonHang:
             from recommendations.models import TuongTacMonAn
             TuongTacMonAn.objects.create(
                 nguoi_dung=nguoi_dung, mon_an=mon_an,
-                loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=6
+                loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=4
             )
```

File patch đã được chuẩn bị sẵn tại:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/remediation_bug2_orders_services.patch`

File patch toàn diện cho cả 3 bugs M4 (Bug 1, Bug 2, Bug 3) được lưu tại:
`/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_2/remediation_m4_all_bugs.patch`

---

## 5. Verification Method (Phương pháp kiểm chứng độc lập)

Sau khi Worker áp dụng sửa đổi vào `moc-backend/orders/services.py`, thực hiện các bước kiểm tra sau:

### Lệnh 1: Chạy kiểm chứng độc lập Bug 2 và toàn bộ bộ Bug Reproduction Harness
```bash
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py
```
- **Kỳ vọng cho Bug 2**: `test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4` vượt qua (`ok`).
- **Kỳ vọng tổng thể khi cả 3 bug được sửa**:
  ```text
  test_reproduce_bug_1_detail_endpoint_assertion_error ... ok
  test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4 ... ok
  test_reproduce_bug_3_order_creation_fails_to_invalidate_cache ... ok

  ----------------------------------------------------------------------
  Ran 3 tests in 0.877s

  OK
  ```

### Lệnh 2: Kiểm tra trực tiếp bằng Python REPL
```bash
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python -c '
import os, sys, django
os.environ["TESTING"] = "1"
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()
from django.contrib.auth import get_user_model
from foods.models import DanhMuc, MonAn
from orders.services import DichVuDonHang
from recommendations.models import TuongTacMonAn
from decimal import Decimal

User = get_user_model()
u = User.objects.create_user(username="check_u", email="check@moc.vn", password="pwd")
dm = DanhMuc.objects.create(ten="CheckDM", duong_dan="check-dm")
m = MonAn.objects.create(danh_muc=dm, ten="CheckMon", duong_dan="check-mon", don_gia=Decimal("50000"))
DichVuDonHang.tao_don_hang(nguoi_dung=u, du_lieu={"items": [{"mon_an": m, "so_luong": 1}], "hinh_thuc": "mang_ve"})
tt = TuongTacMonAn.objects.filter(nguoi_dung=u, mon_an=m).first()
assert tt.trong_so == Decimal("4.00"), f"Expected 4.00, got {tt.trong_so}"
print("VERIFICATION SUCCESSFUL: trong_so is 4.00")
'
```
Kỳ vọng in ra: `VERIFICATION SUCCESSFUL: trong_so is 4.00`.
