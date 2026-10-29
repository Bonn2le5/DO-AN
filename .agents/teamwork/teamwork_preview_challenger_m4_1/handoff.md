# Báo Cáo Đánh Giá Đối Kháng (Challenger Handoff Report)
## Milestone 4: AI Recommendation Engine & PostGIS GIS Spatial Queries
- **Challenger**: `m4_challenger_1`
- **Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_challenger_m4_1`
- **Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`
- **Verdict**: **REQUEST_CHANGES** (Yêu cầu khắc phục 3 khiếm khuyết được chứng minh bằng thực nghiệm)

---

## 1. Observation (Quan sát thực nghiệm)

### 1.1 Khảo sát các thành phần đã hoàn thành tốt
1. **Thuật toán Pure-Python TF-IDF & Cosine Similarity**:
   - `moc-backend/recommendations/services.py`: Sublinear TF ($1 + \ln(f)$), Smoothed IDF ($\ln(\frac{N+1}{\text{DF}+1}) + 1$), chuẩn hóa độ dài vector L2 ($\|\hat{V}_d\| = 1$) hoạt động chính xác.
   - Khi chạy bộ kiểm thử đối kháng `tests/e2e/test_adversarial_challenger_m4_recommendations.py`:
     - 13/13 tests PASS.
     - Xử lý ổn định trường hợp từ vựng rời rạc (Cosine Similarity = 0.0), món ăn không có mô tả (không crash), món ăn trong lịch sử tương tác bị ẩn/xóa (loại trừ sạch sẽ).
2. **Cold-Start Popularity Fallback & PostgreSQL Constraints**:
   - Công thức $0.6 \times \frac{\text{reviews}}{\max(\text{reviews}, 1)} + 0.4 \times \frac{\text{rating}}{5.0}$ được kẹp chặt trong đoạn $[0.0, 1.0]$.
   - Kiểu `Decimal(str(score))` tương thích hoàn toàn với `NUMERIC(5,4)` và ràng buộc `CHECK (diem_tuong_dong BETWEEN 0 AND 1)`.
3. **Khách vãng lai (Anonymous User)**:
   - Truy vấn `GET /api/recommendations/` và `GET /api/goi-y/` trả về HTTP 200 kèm `is_cold_start=True` và `reason="Phổ biến hôm nay"`. Không lưu vào database và không vi phạm ràng buộc NOT NULL của `nguoi_dung_id`.

---

### 1.2 Khiếm khuyết được phát hiện & tái hiện bằng thực nghiệm

#### Lỗi 1 (CRITICAL): `GoiYMonAnViewSet` gây lỗi HTTP 500 `AssertionError` khi truy vấn chi tiết `GET /api/recommendations/<pk>/`
- **File**: `moc-backend/recommendations/views.py`, dòng 33–50.
- **Quan sát thực tế**:
  `GoiYMonAnViewSet` kế thừa từ `viewsets.ReadOnlyModelViewSet` (bao gồm `mixins.RetrieveModelMixin` và `mixins.ListModelMixin`), nhưng lớp này **không hề khai báo thuộc tính `queryset`** và **không ghi đè phương thức `get_queryset()`**.
- **Lệnh thực thi kiểm chứng**:
  ```bash
  PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py
  ```
- **Lỗi hiển thị verbatim**:
  ```text
  Internal Server Error: /api/recommendations/1/
  File "/Users/VuVan/Documents/DO-AN/moc-backend/.venv/lib/python3.9/site-packages/rest_framework/generics.py", line 67, in get_queryset
    assert self.queryset is not None, (
  AssertionError: 'GoiYMonAnViewSet' should either include a `queryset` attribute, or override the `get_queryset()` method.
  ```

#### Lỗi 2 (HIGH): Sai lệch trọng số tương tác khi đặt món trong `orders/services.py`: gán `trong_so=6` thay vì `trong_so=4`
- **File**: `moc-backend/orders/services.py`, dòng 80–84.
- **Quan sát thực tế**:
  ```python
  from recommendations.models import TuongTacMonAn
  TuongTacMonAn.objects.create(
      nguoi_dung=nguoi_dung, mon_an=mon_an,
      loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=6
  )
  ```
  Trong khi đó, tài liệu đặc tả Feature 20 và `recommendations/services.py:17-23` quy định chuẩn:
  `xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`.
  Vì `recommendations/services.py:227` ưu tiên lấy giá trị `float(tt.trong_so)`, các đơn đặt món phát sinh từ luồng checkout bị gán trọng số 6.00 thay vì 4.00, làm sai lệch mô hình tính toán khẩu vị người dùng.
- **Lỗi hiển thị verbatim trong kiểm thử**:
  ```text
  AssertionError: Decimal('6.00') != Decimal('4.00') : HIGH BUG REPRODUCED: orders/services.py:83 created TuongTacMonAn with trong_so=6.00, expected 4.00 per Feature 20
  ```

#### Lỗi 3 (MEDIUM): Thiếu cơ chế vô hiệu hóa Cache `GoiYMonAn` khi người dùng đặt hàng (`/api/orders/`) hoặc đánh giá (`/api/reviews/`)
- **File**: `moc-backend/recommendations/views.py`, dòng 27–31; `moc-backend/orders/services.py`, dòng 81; `moc-backend/reviews/views.py`, dòng 38.
- **Quan sát thực tế**:
  Hành động xóa cache `GoiYMonAn.objects.filter(nguoi_dung=self.request.user).delete()` chỉ được viết riêng lẻ trong `TuongTacMonAnViewSet.perform_create`.
  Khi người dùng phát sinh tương tác cốt lõi quan trọng nhất là Đặt món qua `/api/orders/` hoặc Đánh giá qua `/api/reviews/`, hệ thống tạo `TuongTacMonAn` trực tiếp qua ORM mà không xóa cache `GoiYMonAn`. Dẫn đến lượt gọi `GET /api/recommendations/` tiếp theo của người dùng vẫn nhận lại danh sách gợi ý cũ (stale cache), không phản ánh món vừa đặt/đánh giá.
- **Lỗi hiển thị verbatim trong kiểm thử**:
  ```text
  AssertionError: 1 != 0 : MEDIUM BUG REPRODUCED: Cache was not invalidated after placing order (still has 1 cached items)
  ```

---

## 2. Logic Chain (Chuỗi lập luận kỹ thuật)

1. Từ **Quan sát 1.2 (Lỗi 1)**: `GoiYMonAnViewSet` là một DRF `ReadOnlyModelViewSet`. Router tự động sinh route `^recommendations/{pk}/$`. Bất kỳ yêu cầu xem chi tiết nào tới route này đều kích hoạt `GenericAPIView.get_object()`, gọi `get_queryset()`. Do thiếu `queryset = GoiYMonAn.objects.all()` hoặc `get_queryset()`, DRF kích hoạt assert fail và server phản hồi HTTP 500.
2. Từ **Quan sát 1.2 (Lỗi 2)**: Worker M4 đã cập nhật bảng trọng số `TRONG_SO_TUONG_TAC` trong `recommendations/services.py` sang chuẩn `dat_mon=4`, nhưng chưa đồng bộ hóa lệnh gọi tạo tương tác trong `orders/services.py:83` (vốn vẫn giữ giá trị cũ `trong_so=6`). Khi người dùng hoàn tất đặt hàng, cơ sở dữ liệu lưu tương tác với trọng số 6.00, phá vỡ hợp đồng nghiệp vụ Feature 20.
3. Từ **Quan sát 1.2 (Lỗi 3)**: Vô hiệu hóa cache chỉ đặt tại endpoint `TuongTacMonAnViewSet`, trong khi luồng kinh doanh thực tế tạo tương tác tại `orders/services.py` và `reviews/views.py`. Giải pháp kiến trúc bền vững là kích hoạt tín hiệu Django `post_save` trên model `TuongTacMonAn`, đảm bảo mọi tương tác dù sinh ra từ đâu cũng tự động xóa sạch cache gợi ý của người dùng tương ứng.

---

## 3. Caveats (Lưu ý & Điểm biên kỹ thuật)

1. **Celery Worker**: Môi trường hiện tại không kích hoạt Celery daemon ngầm, toàn bộ quá trình tái tính toán gợi ý chạy đồng bộ in-process.
2. **Tương thích PostGIS / SQLite**: Bộ kiểm thử không gian `branches` đã được kiểm tra độc lập và pass 18/18 bài test với cả cơ chế PostGIS (khi có DB) và Haversine fallback (trên SQLite).
3. **Phạm vi quyền**: Challenger tuân thủ nghiêm ngặt nguyên tắc review-only, không tự ý sửa đổi mã nguồn sản phẩm mà cung cấp bộ test và phương án sửa chữa chi tiết cho Worker M4.

---

## 4. Conclusion (Kết luận & Đề xuất hành động)

**Verdict**: **REQUEST_CHANGES**

Worker M4 cần thực hiện 3 chỉnh sửa khắc phục cụ thể:

1. **Khắc phục Lỗi 1 trong `moc-backend/recommendations/views.py`**:
   Thêm khai báo `queryset` và phương thức `get_queryset()` cho `GoiYMonAnViewSet`:
   ```python
   class GoiYMonAnViewSet(viewsets.ReadOnlyModelViewSet):
       queryset = GoiYMonAn.objects.all()
       serializer_class = GoiYMonAnSerializer
       permission_classes = [AllowAny]

       def get_queryset(self):
           user = self.request.user
           if user and user.is_authenticated:
               return GoiYMonAn.objects.filter(nguoi_dung=user).select_related("mon_an", "mon_an__danh_muc")
           return GoiYMonAn.objects.none()
   ```

2. **Khắc phục Lỗi 2 trong `moc-backend/orders/services.py` dòng 80–85**:
   Sửa `trong_so=6` thành `trong_so=4` (khớp chuẩn Feature 20):
   ```python
   from recommendations.models import TuongTacMonAn
   TuongTacMonAn.objects.create(
       nguoi_dung=nguoi_dung, mon_an=mon_an,
       loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=4
   )
   ```

3. **Khắc phục Lỗi 3 bằng tín hiệu tự động xóa cache**:
   Trong `moc-backend/recommendations/models.py` (hoặc `signals.py`), bổ sung:
   ```python
   from django.db.models.signals import post_save, post_delete
   from django.dispatch import receiver

   @receiver(post_save, sender=TuongTacMonAn)
   @receiver(post_delete, sender=TuongTacMonAn)
   def xoa_cache_goi_y_khi_co_tuong_tac(sender, instance, **kwargs):
       if instance.nguoi_dung_id:
           GoiYMonAn.objects.filter(nguoi_dung_id=instance.nguoi_dung_id).delete()
   ```

---

## 5. Verification Method (Phương pháp kiểm chứng độc lập)

Sau khi Worker M4 thực hiện 3 bản sửa đổi trên, chạy lại các lệnh kiểm thử sau:

1. **Bộ tái hiện lỗi của Challenger (Bắt buộc phải chuyển từ 3 FAILED sang 3 PASSED)**:
   ```bash
   PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py
   ```
   *Kỳ vọng sau khi sửa*: `Ran 3 tests ... OK`.

2. **Bộ kiểm thử đối kháng Recommendation Engine đầy đủ**:
   ```bash
   PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py
   ```
   *Kết quả hiện tại*: `Ran 13 tests ... OK` (100% pass).

3. **Bộ kiểm thử GIS & Branches**:
   ```bash
   PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py
   ```
   *Kết quả hiện tại*: `Ran 18 tests ... OK` (100% pass).

4. **Bộ kiểm thử toàn diện Regression của Django**:
   ```bash
   moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders
   ```
   *Kết quả hiện tại*: `Ran 58 tests ... OK` (100% pass).

5. **Bộ kiểm thử Master E2E Runner (Tiers 1-4)**:
   ```bash
   moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Kết quả hiện tại*: `Ran 60 tests ... OK` (100% pass).
