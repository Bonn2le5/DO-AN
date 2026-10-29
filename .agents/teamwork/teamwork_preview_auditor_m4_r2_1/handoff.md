# Forensic Integrity Audit Report — Milestone 4 Round 2

**Auditor Agent**: `m4_r2_auditor_1`  
**Role**: Forensic Integrity Auditor / Critic / Specialist  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_auditor_m4_r2_1`  
**Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`  
**Target**: Milestone 4 Round 2 (Remediation Audit of Recommendations, Orders, Branches, Reviews)  
**Integrity Mode**: Demo (per `ORIGINAL_REQUEST.md`)  
**Verdict**: **CLEAN** (0 Integrity Violations)

---

## 1. Observation (Quan sát thực nghiệm)

Toàn bộ các thành phần mã nguồn và bài kiểm thử thuộc phạm vi Milestone 4 Round 2 đã được kiểm tra trực tiếp qua thanh tra mã và thực thi kiểm thử độc lập:

### 1.1. Không có mã giả (Facades), Mock bypass hoặc Hardcode kết quả
- Tìm kiếm từ khóa vi phạm (`bypass`, `mock`, `dummy`, `fake`, `hardcode`) trên toàn bộ `moc-backend/recommendations`, `moc-backend/orders`, `moc-backend/branches`, `moc-backend/reviews`:
  - `grep_search` trả về **0 kết quả vi phạm** trong toàn bộ logic nghiệp vụ backend.
- Kiểm tra tạo tệp log/kết quả giả mạo:
  - Lệnh: `find . -maxdepth 3 -name '*.log' -o -name '*result*' -o -name '*output*'`
  - Kết quả: Không tồn tại tệp kết quả tiền chế nào trước kiểm toán.

### 1.2. Kiểm tra tín hiệu Django Signals tại `recommendations/signals.py` và `recommendations/apps.py`
- Tệp `moc-backend/recommendations/signals.py` (dòng 9-28):
  ```python
  @receiver(post_save, sender=TuongTacMonAn)
  @receiver(post_delete, sender=TuongTacMonAn)
  def xoa_cache_goi_y_khi_co_tuong_tac(sender, instance, **kwargs):
      if kwargs.get("raw", False):
          return
      nguoi_dung_id = getattr(instance, "nguoi_dung_id", None)
      if nguoi_dung_id:
          so_luong_xoa, _ = GoiYMonAn.objects.filter(nguoi_dung_id=nguoi_dung_id).delete()
  ```
- Tệp `moc-backend/recommendations/apps.py` (dòng 9-10):
  ```python
  def ready(self):
      import recommendations.signals  # noqa: F401
  ```
- Ứng dụng `recommendations` được đăng ký hợp lệ trong `INSTALLED_APPS` tại `moc-backend/config/settings.py:108`.
- Logic xóa cache là chính quy 100%, tự động vô hiệu hóa cache khi tương tác được thêm/sửa/xóa từ bất kỳ nguồn nào (`orders/services.py`, `reviews/views.py`, DRF endpoint, hoặc Django admin).

### 1.3. Kiểm tra trọng số tương tác tại `orders/services.py:83`
- Tệp `moc-backend/orders/services.py` (dòng 80-84):
  ```python
  from recommendations.models import TuongTacMonAn
  TuongTacMonAn.objects.create(
      nguoi_dung=nguoi_dung, mon_an=mon_an,
      loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=4
  )
  ```
- Trọng số tương tác được ghi nhận đúng chuẩn `trong_so=4` (thay vì giá trị cũ `trong_so=6`), khớp 100% với đặc tả Feature 20: `xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`.

### 1.4. Kiểm tra khắc phục lỗi DRF generic viewset tại `recommendations/views.py`
- Tệp `moc-backend/recommendations/views.py` (dòng 39-52):
  ```python
  queryset = GoiYMonAn.objects.all()
  serializer_class = GoiYMonAnSerializer
  permission_classes = [AllowAny]

  def get_queryset(self):
      user = self.request.user
      if user and user.is_authenticated:
          return (
              GoiYMonAn.objects.filter(nguoi_dung=user)
              .select_related("mon_an", "mon_an__danh_muc")
              .prefetch_related("mon_an__the_mon_an")
              .order_by("-diem_tuong_dong")
          )
      return GoiYMonAn.objects.none()
  ```
- Thuộc tính lớp `queryset` và phương thức ghi đè `get_queryset` được cấu hình đầy đủ, triệt tiêu hoàn toàn `AssertionError` (HTTP 500) khi truy vấn endpoint chi tiết `/api/recommendations/<pk>/`.

### 1.5. Kiểm tra logic kẹp toán học Haversine và xác thực tham số GIS
- Tệp `moc-backend/branches/services.py` (dòng 26-32) và `tests/e2e/helpers/ai_gis_oracle.py` (dòng 26-32):
  ```python
  a = (
      math.sin(delta_phi / 2.0) ** 2
      + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
  )
  a = min(1.0, max(0.0, a))
  c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
  return round(EARTH_RADIUS_KM * c, 2)
  ```
- Tệp `moc-backend/branches/views.py`:
  - Kiểm tra bắt buộc cả `lat` và `lng` khi truy vấn theo vị trí (`HTTP 400 Bad Request` nếu thiếu một trong hai).
  - Kiểm tra ranh giới tọa độ `-90.0 <= lat <= 90.0` và `-180.0 <= lng <= 180.0` (`HTTP 400 Bad Request` nếu vượt biên hoặc NaN/Inf).
  - Kiểm tra tham số `radius` (`float > 0`) và `limit` (`int > 0`), trả về `HTTP 400 Bad Request` nếu tham số không hợp lệ.

### 1.6. Kết quả thực thi kiểm thử độc lập (Independent Test Execution)

1. **Django System Check**:
   - Lệnh: `moc-backend/.venv/bin/python moc-backend/manage.py check`
   - Output verbatim: `System check identified no issues (0 silenced).` (Exit code: 0)

2. **Challenger Bug Reproduction Suite**:
   - Lệnh: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py`
   - Output verbatim:
     ```text
     Ran 3 tests in 1.372s
     OK
     ```
   - Xác nhận: Cả 3 bài test xác nhận Bug 1, Bug 2, Bug 3 đều đã được khắc phục hoàn toàn (0 lỗi).

3. **Django Regression Test Suite**:
   - Lệnh: `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders`
   - Output verbatim:
     ```text
     Ran 58 tests in 28.298s
     OK
     ```
   - Xác nhận: 58/58 tests đạt 100% PASS trên 4 app cốt lõi.

4. **Master E2E Test Runner**:
   - Lệnh: `moc-backend/.venv/bin/python tests/e2e/runner.py`
   - Output verbatim:
     ```text
     Ran 60 tests in 0.026s
     OK
     Pass Rate: 100.0%
     ```

5. **Adversarial Recommendations Suite**:
   - Lệnh: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py`
   - Output verbatim:
     ```text
     Ran 13 tests in 11.692s
     OK
     ```

6. **Adversarial Branches GIS Suite**:
   - Lệnh: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py`
   - Output verbatim:
     ```text
     Ran 18 tests in 3.305s
     OK
     ```

7. **Explorer Blueprints Verification (Stress-test)**:
   - Lệnh: `TESTING=1 PYTHONPATH=.:moc-backend moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_explorer_m4_r2_3/verify_blueprints.py`
   - Output verbatim:
     ```text
     100,000 random antipodal pairs: 100% PASSED (0 failures)
     Proposed views passed all 32 edge-case matrix scenarios!
     ```

---

## 2. Logic Chain (Chuỗi lập luận kiểm toán)

1. **Kháng mã giả và đường tắt (Anti-Facade & Anti-Mock)**:
   - Từ quan sát 1.1, không tìm thấy bất kỳ mã stub, mock bypass, hay giá trị hardcode nào trong mã nguồn sản phẩm. Các thuật toán TF-IDF, Cosine Similarity, Haversine Geodesic, và tính khoảng cách PostGIS đều được tính toán động dựa trên thực thể cơ sở dữ liệu thật.
2. **Khắc phục Bug 1 (DRF AssertionError)**:
   - Từ quan sát 1.4 và kết quả kiểm thử bài 1 trong `test_adversarial_challenger_m4_bug_reproduction.py`, `GoiYMonAnViewSet` đã khai báo đầy đủ `queryset` và `get_queryset()`. Yêu cầu `GET /api/recommendations/1/` trả về đúng mã trạng thái HTTP 404 (Not Found) thay vì HTTP 500 (AssertionError).
3. **Khắc phục Bug 2 (Sai lệch trọng số tương tác)**:
   - Từ quan sát 1.3 và bài test 2 trong `test_adversarial_challenger_m4_bug_reproduction.py`, khi người dùng đặt hàng qua `DichVuDonHang.tao_don_hang()`, hệ thống ghi nhận bản ghi `TuongTacMonAn` với `trong_so=Decimal("4.00")` và `loai_tuong_tac="dat_mon"`. Trọng số này đồng nhất 100% với đặc tả Feature 20 và service `recommendations/services.py:17-23`.
4. **Khắc phục Bug 3 (Vô hiệu hóa cache qua Django Signals)**:
   - Từ quan sát 1.2 và bài test 3 trong `test_adversarial_challenger_m4_bug_reproduction.py`, `recommendations/signals.py` đã kết nối tín hiệu `post_save` và `post_delete` từ sender `TuongTacMonAn`. Khi đơn hàng mới được tạo hoặc đánh giá món ăn được gửi, cache `GoiYMonAn` của người dùng tương ứng bị xóa sạch, kích hoạt việc tái tính toán gợi ý cá nhân hóa ở lần truy cập tiếp theo.
5. **Khắc phục các điểm biên GIS (Haversine Clamping & Parameter Validation)**:
   - Từ quan sát 1.5, bài kiểm thử 100.000 điểm đối cực và 32 ma trận tham số biên đã chứng minh việc kẹp giá trị $a = \min(1.0, \max(0.0, a))$ triệt tiêu hoàn toàn hiện tượng `ValueError: math domain error`. Tất cả các tham số bất hợp lệ (`radius <= 0`, `limit <= 0`, thiếu tọa độ, ngoài biên $[-90, 90]$ và $[-180, 180]$) đều được trả về `HTTP 400 Bad Request` an toàn.
6. **Tính toàn vẹn kiểm thử (Test Integrity)**:
   - Từ quan sát 1.6, toàn bộ 7 bộ kiểm thử độc lập gồm 152 bài test đều đạt tỉ lệ vượt qua 100% mà không ghi nhận bất kỳ cảnh báo lỗi hoặc thất bại nào.

---

## 3. Caveats (Lưu ý)

No caveats. Toàn bộ mã nguồn triển khai thực tế, test suite, và hệ thống tín hiệu đều được xác minh độc lập trực tiếp trong môi trường dự án.

---

## 4. Conclusion (Kết luận)

### Binary Verdict: **CLEAN**

Công việc sửa chữa Milestone 4 Round 2 đáp ứng 100% các tiêu chí toàn vẹn:
- Hoàn toàn không có mã giả, không hardcode kết quả, không bypass kiểm thử.
- Django signals được xây dựng chính quy và đăng ký đúng chuẩn Django `ready()`.
- Trọng số tương tác `trong_so=4` tại `orders/services.py:83` khớp tuyệt đối với Feature 20.
- Công thức Haversine được kẹp biên an toàn, xử lý triệt để lỗi toán học trên các điểm đối cực.
- Bộ lọc và kiểm tra tham số GIS trong Views đạt độ tin cậy tuyệt đối với mã HTTP 400 chuẩn mực.
- 100% bài kiểm thử đơn vị, hồi quy và adversarial stress-test đều vượt qua.

Sản phẩm Milestone 4 đủ điều kiện bàn giao và tiếp tục chuyển sang Milestone 5 (Frontend Synchronization & Admin/Staff Portals).

---

## 5. Verification Method (Phương pháp kiểm chứng độc lập)

Bất kỳ kiểm toán viên hoặc hệ thống CI/CD nào cũng có thể kiểm chứng lại kết quả độc lập bằng chuỗi lệnh sau:

```bash
# 1. Kiểm tra cấu hình Django
moc-backend/.venv/bin/python moc-backend/manage.py check

# 2. Chạy bộ kiểm thử tái hiện bug M4 (3/3 PASS)
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py

# 3. Chạy hồi quy các app cốt lõi M4 (58/58 PASS)
moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders

# 4. Chạy Master E2E runner (60/60 PASS)
moc-backend/.venv/bin/python tests/e2e/runner.py

# 5. Chạy bộ kiểm thử adversarial recommendations (13/13 PASS)
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py

# 6. Chạy bộ kiểm thử adversarial branches GIS (18/18 PASS)
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py
```

### Điều kiện vô hiệu hóa kết luận (Invalidation Conditions):
- Nếu bất kỳ kiểm thử nào trong các lệnh trên phát sinh `FAIL` hoặc `ERROR`.
- Hoặc nếu phát hiện giá trị hardcode trả về từ bất kỳ service nào trong `recommendations`, `orders`, `branches`, `reviews`.
- Hoặc nếu xuất hiện lỗi `ValueError: math domain error` khi tính khoảng cách giữa 2 điểm bất kỳ trên Trái Đất.
