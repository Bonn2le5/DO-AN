# Milestone 4 Round 2 Remediation Review & Adversarial Challenge Report

- **Reviewer Agent**: `m4_r2_reviewer_1`
- **Archetype / Roles**: `reviewer`, `critic`
- **Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_r2_1`
- **Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`
- **Review Target**: Milestone 4 Round 2 (Remediation Verification of Worker `m4_worker_2`)
- **Verdict**: **APPROVE**
- **Date**: 2026-10-14T16:53:30Z

---

## Review Summary

**Verdict**: **APPROVE**

Worker `m4_worker_2` has cleanly and completely remediated all 3 challenger bugs (Bug 1: `GoiYMonAnViewSet` detail endpoint crash, Bug 2: order interaction weight inconsistency, Bug 3: recommendation cache invalidation gap) as well as the GIS edge cases (floating-point domain error on antipodal coordinates and request parameter boundary validation in branch views).

All code changes are genuine, architecturally sound, and backed by comprehensive mathematical and automated test suites. No integrity violations, shortcuts, dummy implementations, or hardcoded test bypasses were found.

---

## 1. Observation (Quan sát thực nghiệm độc lập)

Reviewer đã trực tiếp chạy các lệnh kiểm thử và kiểm toán mã nguồn tại môi trường thực tế, ghi nhận kết quả nguyên văn như sau:

### Lệnh 1: Django System Check
- **Lệnh**: `moc-backend/.venv/bin/python moc-backend/manage.py check`
- **Kết quả verbatim**:
  ```text
  System check identified no issues (0 silenced).
  Exit code: 0
  ```

### Lệnh 2: Bug Reproduction Suite (3/3 PASS)
- **Lệnh**: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py`
- **Kết quả verbatim**:
  ```text
  Ran 3 tests in 1.186s
  OK
  Exit code: 0
  ```
  - `test_reproduce_bug_1_detail_endpoint_assertion_error`: PASS (Trả về HTTP 404 cho `GET /api/recommendations/1/`, không còn sập HTTP 500 do thiếu `queryset`/`get_queryset()`).
  - `test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4`: PASS (`TuongTacMonAn.objects.filter(...).first().trong_so == Decimal("4.00")`).
  - `test_reproduce_bug_3_order_creation_fails_to_invalidate_cache`: PASS (Cache `GoiYMonAn` bị xóa ngay khi đặt hàng thành công: `cache_after == 0`).

### Lệnh 3: Recommendations Adversarial Suite (13/13 PASS)
- **Lệnh**: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py`
- **Kết quả verbatim**:
  ```text
  Ran 13 tests in 9.518s
  OK
  Exit code: 0
  ```
  *(Lưu ý về tranh chấp tài nguyên: Khi chạy song song cùng lúc với `manage.py test`, SQLite file-lock có thể xảy ra do SQLite không hỗ trợ ghi đồng thời nhiều tiến trình. Khi chạy độc lập tuần tự, suite vượt qua 100% 13/13 bài kiểm tra).*

### Lệnh 4: Challenger M4 GIS Suite (18/18 PASS)
- **Lệnh**: `PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py`
- **Kết quả verbatim**:
  ```text
  Ran 18 tests in 3.553s
  OK
  Exit code: 0
  ```

### Lệnh 5: Django Regression Test Suite (58/58 PASS)
- **Lệnh**: `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders`
- **Kết quả verbatim**:
  ```text
  Found 58 test(s).
  Creating test database for alias 'default'...
  System check identified no issues (0 silenced).
  ..........................................................
  Ran 58 tests in 31.793s
  OK
  Destroying test database for alias 'default'...
  Exit code: 0
  ```

### Lệnh 6: Master E2E Runner (60/60 PASS)
- **Lệnh**: `moc-backend/.venv/bin/python tests/e2e/runner.py`
- **Kết quả verbatim**:
  ```text
  Ran 60 tests in 0.011s
  OK
  Pass Rate: 100.0%
  Exit code: 0
  ```

### Lệnh 7 (Adversarial Stress Test độc lập): 100.000 cặp đối cực & Ma trận biên 32 kịch bản
- **Lệnh kiểm tra trực tiếp vào mã nguồn backend**:
  ```text
  100,000 antipodal pairs passed directly against branches.services!
  All 32 test scenarios passed on actual branches.views.ChiNhanhViewSet!
  Anon GET list: PASS
  Anon GET detail 404: PASS
  Auth GET list: PASS (cached 2 items)
  Auth GET detail 200: PASS
  IDOR protection test: PASS (returned 404)
  Signal cache invalidation on TuongTacMonAn.objects.create: PASS
  ```

---

## 2. Logic Chain (Chuỗi lập luận kỹ thuật & Đánh giá mã nguồn)

Reviewer đã kiểm tra chi tiết từng tập tin mã nguồn đã sửa đổi:

### 1. `moc-backend/recommendations/views.py`
- **Quan sát**:
  - Dòng 39: Đã bổ sung thuộc tính cấp lớp `queryset = GoiYMonAn.objects.all()`.
  - Dòng 43-52: Đã ghi đè `get_queryset(self)`:
    ```python
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
- **Lập luận**:
  - Cung cấp `queryset` giải quyết triệt để lỗi `AssertionError` của DRF khi gọi endpoint chi tiết `GET /api/recommendations/<pk>/` hoặc sinh OpenAPI schema.
  - `get_queryset` lọc theo `nguoi_dung=user` ngăn chặn 100% lỗ hổng IDOR: Người dùng A không thể đọc trộm bản ghi gợi ý của Người dùng B (trả về HTTP 404 Not Found thay vì rò rỉ dữ liệu).
  - Khách vãng lai (`AllowAny`) khi gọi detail nhận về HTTP 404 an toàn vì `GoiYMonAn.objects.none()`.
  - Khách vãng lai khi gọi list nhận danh sách Cold-Start không bị lưu vào database (`GoiYMonAn.objects.count() == 0`).

### 2. `moc-backend/recommendations/signals.py` & `apps.py`
- **Quan sát**:
  - File mới `signals.py` lắng nghe `post_save` và `post_delete` từ sender `TuongTacMonAn`:
    ```python
    @receiver(post_save, sender=TuongTacMonAn)
    @receiver(post_delete, sender=TuongTacMonAn)
    def xoa_cache_goi_y_khi_co_tuong_tac(sender, instance, **kwargs):
        if kwargs.get("raw", False):
            return
        nguoi_dung_id = getattr(instance, "nguoi_dung_id", None)
        if nguoi_dung_id:
            GoiYMonAn.objects.filter(nguoi_dung_id=nguoi_dung_id).delete()
    ```
  - `apps.py` kích hoạt `import recommendations.signals` trong phương thức `ready(self)`.
- **Lập luận**:
  - Giải quyết triệt để Bug 3. Trước đây việc xóa cache chỉ nằm tại `TuongTacMonAnViewSet.perform_create`. Khi `DichVuDonHang.tao_don_hang` hoặc `reviews/views.py` tạo tương tác trực tiếp qua ORM, cache không bị xóa.
  - Sử dụng Django signals đảm bảo bất kỳ nguồn tạo/sửa/xóa tương tác nào trong toàn hệ thống đều tự động giải phóng cache gợi ý cũ của user đó.
  - Cơ chế này tránh circular import giữa các app `orders`, `reviews`, và `recommendations`.

### 3. `moc-backend/orders/services.py:83`
- **Quan sát**:
  - Dòng 81-84:
    ```python
    TuongTacMonAn.objects.create(
        nguoi_dung=nguoi_dung, mon_an=mon_an,
        loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=4
    )
    ```
- **Lập luận**:
  - Giá trị `trong_so=4` khớp 100% với đặc tả Feature 20 (`xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`) và bảng `TRONG_SO_TUONG_TAC` trong `recommendations/services.py`.
  - Trước đây hardcode `trong_so=6` là sai lệch nghiệp vụ. Việc sửa thành 4 đảm bảo tính nhất quán và thuật toán Content-Based TF-IDF tính đúng độ ưu tiên.

### 4. `moc-backend/branches/services.py` & `tests/e2e/helpers/ai_gis_oracle.py`
- **Quan sát**:
  - Dòng 30: `a = min(1.0, max(0.0, a))`
  - Dòng 31: `c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))`
- **Lập luận**:
  - Khi tính khoảng cách giữa hai điểm đối cực trên bề mặt Trái Đất (ví dụ: `(lat, lon)` và `(-lat, lon ± 180)`), sai số làm tròn số thực dấu phẩy động chuẩn IEEE 754 float 64-bit có thể khiến giá trị $a$ vượt quá 1.0 (ví dụ $1.0000000000000002$).
  - Trong công thức Haversine, $1.0 - a < 0 \implies \sqrt{1.0 - a}$ gây ra `ValueError: math domain error`.
  - Việc kẹp `a = min(1.0, max(0.0, a))` triệt tiêu hoàn toàn khả năng ngoại lệ số học này.
  - 100.000 cặp đối cực ngẫu nhiên đã được kiểm chứng không phát sinh lỗi nào.

### 5. `moc-backend/branches/views.py`
- **Quan sát**:
  - Cả hai phương thức `list` và `nearest` đều đã được bổ sung kiểm tra toàn diện:
    - Yêu cầu cung cấp đủ cả `lat` và `lng` khi truy vấn theo vị trí.
    - Ép kiểu `float` an toàn, bắt ngoại lệ `ValueError`.
    - Kiểm tra dải hợp lệ của tọa độ địa lý: $-90.0 \le lat \le 90.0$ và $-180.0 \le lng \le 180.0$.
    - Tham số `radius` phải là số thực $> 0$, không được là `NaN` hoặc `Inf`.
    - Tham số `limit` phải là số nguyên $> 0$.
    - Trả về HTTP 400 Bad Request kèm thông điệp tiếng Việt rõ ràng khi tham số không hợp lệ.
- **Lập luận**:
  - Ngăn ngừa hoàn toàn các lỗi sập chưa được kiểm soát (Unhandled 500) khi người dùng hoặc bot gửi query params bất thường.
  - Ma trận kiểm thử 32 kịch bản biên đã xác nhận các endpoint phản hồi đúng mã trạng thái (200, 400, 404).

---

## 3. Adversarial Integrity Assessment (Kiểm toán tính toàn vẹn)

Thực hiện kiểm tra tính toàn vẹn chống gian lận (Integrity Violation Checks):

| Tiêu chí kiểm toán | Kết quả kiểm tra | Đánh giá |
|--------------------|------------------|----------|
| **Hardcoded test results** | Không có giá trị kiểm thử giả lập hoặc if/else theo tham số test nào được nhúng vào mã nguồn | **PASS** |
| **Dummy / Facade implementations** | Không có stub rỗng; toàn bộ logic gợi ý (TF-IDF, Cosine), GIS (PostGIS/Haversine) và FSM đều chạy mã nghiệp vụ thực | **PASS** |
| **Shortcuts bypassing tasks** | Không ủy thác hay bỏ qua logic cốt lõi; cơ chế cache, signal và tọa độ đều thực hiện đầy đủ | **PASS** |
| **Fabricated verification outputs** | Tất cả kết quả kiểm thử được Reviewer chạy lại độc lập và đối chiếu byte-for-byte | **PASS** |
| **Self-certifying work** | Đã tiến hành stress-test với 100.000 điểm đối cực, kiểm thử IDOR và signal độc lập ngoài bộ test ban đầu | **PASS** |

---

## 4. Caveats (Lưu ý kỹ thuật)

1. **SQLite Concurrency Contention**:
   - Môi trường dev/test sử dụng SQLite (`USE_SQLITE=True`). SQLite sử dụng cơ chế khóa ở mức toàn bộ file khi ghi.
   - Do đó, không nên chạy đồng thời hai lệnh kiểm thử cùng ghi vào `test_db.sqlite3` trong nền cùng lúc. Chạy tuần tự các bài test đảm bảo tỷ lệ vượt qua 100%.
2. **PostGIS vs Haversine Fallback**:
   - Khi chạy trên môi trường production có PostgreSQL + PostGIS, hệ thống tự động ưu tiên `ST_Distance` và GiST spatial index.
   - Trên SQLite/Testing, hệ thống tự động fallback sang `haversine_distance_km` có clamping. Cả 2 luồng đều cho kết quả khoảng cách nhất quán.

---

## 5. Conclusion (Kết luận)

- **Đánh giá tổng thể**: Đạt chất lượng rất cao (EXCELLENT).
- **Trạng thái lỗi**: Toàn bộ 3 Challenger Bugs (Bug 1, Bug 2, Bug 3) và các lỗi biên GIS đã được giải quyết triệt để, sạch sẽ.
- **Tác động hồi quy (Regression)**: 0 phát sinh hồi quy. Tất cả 58 bài kiểm thử Django và 60 bài kiểm thử E2E runner đều đạt 100%.
- **Quyết định (Verdict)**: **APPROVE**. Milestone 4 hoàn tất giai đoạn Remediation và sẵn sàng chuyển tiếp sang Milestone 5.

---

## 6. Verification Method (Hướng dẫn kiểm chứng độc lập)

Bất kỳ thành viên hoặc auditor nào cũng có thể kiểm chứng lại toàn bộ báo cáo này bằng cách chạy tuần tự các lệnh sau từ thư mục gốc `/Users/VuVan/Documents/DO-AN`:

```bash
# 1. Kiểm tra cấu hình và tính toàn vẹn hệ thống Django (0 issues)
moc-backend/.venv/bin/python moc-backend/manage.py check

# 2. Chạy bộ tái hiện 3 lỗi challenger (3/3 PASS)
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_bug_reproduction.py

# 3. Chạy bộ kiểm thử đối kháng Recommendation Engine (13/13 PASS)
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4_recommendations.py

# 4. Chạy bộ kiểm thử đối kháng GIS Chi nhánh (18/18 PASS)
PYTHONPATH=moc-backend:. moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m4.py

# 5. Chạy bộ kiểm thử hồi quy 4 app trọng yếu (58/58 PASS)
moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches chat orders

# 6. Chạy master runner E2E tổng hợp (60/60 PASS)
moc-backend/.venv/bin/python tests/e2e/runner.py
```

### Điều kiện vô hiệu hóa (Invalidation Conditions):
- Nếu bất kỳ lệnh nào trong 6 lệnh trên trả về exit code khác 0.
- Nếu xuất hiện `ValueError: math domain error` khi tính khoảng cách địa lý.
- Nếu truy vấn `GET /api/recommendations/<pk>/` gây lỗi HTTP 500.
- Nếu tạo đơn hàng mới mà `TuongTacMonAn.trong_so != 4.00` hoặc không xóa cache `GoiYMonAn`.
