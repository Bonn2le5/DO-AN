# Báo Cáo Chuyển Giao Triển Khai (Handoff Report)
## Milestone 4: AI Recommendation Engine & PostGIS GIS Spatial Queries
- **Worker**: `m4_worker_1`
- **Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_worker_m4_1`
- **Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`
- **Status**: Completed (Hard Handoff)

---

## 1. Observation (Quan sát thực tế)

### 1.1 Khảo sát hiện trạng trước khi triển khai
1. **Môi trường Python Offline**:
   - Môi trường ảo `moc-backend/.venv` hoạt động hoàn toàn offline (air-gapped), không có `scikit-learn` hay `numpy`. Bắt buộc thuật toán TF-IDF và Cosine Similarity phải chạy bằng Pure-Python thư viện chuẩn (`math`, `re`, `collections`, `decimal`).
2. **Khiếm khuyết trong module recommendations cũ**:
   - Tệp `moc-backend/recommendations/services.py` định nghĩa sai bảng trọng số tương tác (`xem=1, yeu_thich=3, them_gio_hang=4, dat_mon=6, danh_gia=5`) không khớp với chuẩn thiết kế (`xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`).
   - Cold-start score gán trực tiếp bằng `mon.so_luot_danh_gia` (ví dụ: 85), gây lỗi tràn số và vi phạm ràng buộc database `CHECK (diem_tuong_dong BETWEEN 0 AND 1)` trong PostgreSQL.
   - Dòng 104 `if mon.id in tap_mon_da_tuong_tac: continue` loại trừ sai món ăn đã từng tương tác, làm hỏng kịch bản kiểm thử E2E Scenario 2 nơi khách hàng cũ kỳ vọng món yêu thích được gợi ý lại Top 1.
   - Chưa hỗ trợ khách vãng lai (Cold-start Homepage) vì `GoiYMonAnViewSet` yêu cầu `permission_classes = [IsAuthenticated]`.
3. **Khiếm khuyết trong module branches (GIS) cũ**:
   - `moc-backend/config/settings.py` hardcode đường dẫn GDAL/GEOS tĩnh trên macOS `/opt/homebrew/...`, thiếu cơ chế auto-detect qua nhiều nền tảng Linux và Homebrew.
   - `ChiNhanh` model thiếu các accessor properties (`kinh_do`, `vi_do`, `lng`, `lat`, `longitude`, `latitude`) và bộ parser tọa độ từ chuỗi WKT/CSV.
   - Khi chạy test trên SQLite (`manage.py test`), GeoDjango spatial function `Distance` báo lỗi `TypeError: Distance function requires a GeometryField`.
   - `ChiNhanhViewSet` thiếu action `nearest` và `tim-gan-nhat`, khiến gọi `GET /api/branches/nearest/` trả về HTTP 404.

---

## 2. Logic Chain (Chuỗi lập luận kỹ thuật)

1. **Thuật toán Content-Based Filtering Pure-Python (O(D * T))**:
   - Trích xuất corpus từ khóa cho từng món ăn từ: tên, danh mục, mô tả ngắn/chi tiết, danh sách nguyên liệu (tận dụng prefetch cache tránh N+1 queries), thẻ món ăn, và thuộc tính chay/độ cay.
   - Tính toán Document Frequency (DF), Sublinear TF ($1 + \ln(f)$) và Smoothed IDF ($\ln(\frac{N+1}{\text{DF}+1}) + 1$).
   - Vector hóa TF-IDF chuẩn hóa đơn vị L2 ($\|\hat{V}_d\| = 1$).
   - Tổng hợp Vector Khẩu vị Người dùng từ lịch sử tương tác có trọng số:
     $$U_u = \sum_{(d_i, a_i) \in \mathcal{I}_u} w(a_i) \times \hat{V}_{d_i}$$
     với $w(\text{xem})=1, w(\text{yeu\_thich})=2, w(\text{them\_gio\_hang})=3, w(\text{dat\_mon})=4, w(\text{danh\_gia})=5$.
   - Tính Cosine Similarity bằng tích vô hướng $\hat{U}_u \cdot \hat{V}_d \in [0.0, 1.0]$.
2. **Cold-Start Popularity Fallback chuẩn hóa**:
   - Với khách hàng mới chưa có tương tác hoặc khách vãng lai chưa đăng nhập:
     $$\text{Score}_{\text{cold}}(d) = 0.6 \times \frac{d.\text{so\_luot\_danh\_gia}}{\max(\text{reviews}, 1)} + 0.4 \times \frac{d.\text{diem\_danh\_gia}}{5.0}$$
   - Điểm số đảm bảo nghiêm ngặt trong khoảng $[0.0, 1.0]$, bảo vệ an toàn ràng buộc database `CHECK (diem_tuong_dong BETWEEN 0 AND 1)`.
   - Gán nhãn giải thích: `ly_do_goi_y = "Phổ biến hôm nay"`, cờ `is_cold_start = True`.
3. **Bộ sinh nhãn giải thích Explainable Recommendation Tags**:
   - Tự động phân tích đặc trưng món gợi ý để gắn nhãn trực quan: lẩu ("Gợi ý vì bạn yêu thích các món lẩu ấm cúng"), cay ("Phù hợp với khẩu vị thích món cay nồng của bạn"), nướng & hải sản ("Được gợi ý dựa trên sở thích món nướng & hải sản của bạn"), món chay ("Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"), hoặc mặc định.
4. **Chiến lược Caching & Cache Invalidation**:
   - `GoiYMonAn` lưu kết quả gợi ý làm cache DB. Khi gọi `GET /api/recommendations/`, nếu cache tồn tại và không có cờ `?refresh=true`, trả về kết quả ngay lập tức.
   - Khi có tương tác mới ghi nhận qua `POST /api/tuong-tac/` hoặc `/api/recommendations/tuong-tac/`, hệ thống tự động xóa cache `GoiYMonAn` của người dùng để lần truy vấn tiếp theo tái tính toán theo khẩu vị mới.
   - Khách vãng lai được tính toán in-memory không ghi vào database, tránh vi phạm ràng buộc NOT NULL của `nguoi_dung`.
5. **Kiến trúc Hybrid PostGIS GIS cho Chi nhánh**:
   - Môi trường Production (PostgreSQL 14+ / PostGIS): Sử dụng truy vấn không gian native `ST_Distance` và chỉ mục không gian GiST `idx_chi_nhanh_toa_do`.
   - Môi trường Test / SQLite: Tự động chuyển tiếp sang thuật toán Haversine geodesic tính khoảng cách mặt cầu Trái Đất ($R = 6371.0088\text{ km}$), lọc chi nhánh đang hoạt động (`con_hoat_dong=True`), sắp xếp tăng dần theo khoảng cách và lọc theo bán kính `radius_km`.
   - Cung cấp dual endpoints: `/api/branches/nearest/`, `/api/chi-nhanh/nearest/`, và `/api/chi-nhanh/tim-gan-nhat/`.

---

## 3. Caveats (Lưu ý & Điểm biên kỹ thuật)

1. **Ràng buộc khóa ngoại Many-to-Many giữa MonAn và NguyenLieu**:
   - Model `MonAn.nguyen_lieu` sử dụng qua bảng trung gian `DinhMucNguyenLieu` có trường bắt buộc `so_luong_can`. Khi tạo dữ liệu mẫu kiểm thử, cần truyền `through_defaults={"so_luong_can": Decimal("1.0")}`.
2. **Khách vãng lai không lưu DB**:
   - Khách vãng lai (`request.user.is_authenticated == False`) nhận gợi ý cold-start được khởi tạo động dưới dạng các model instance ảo không qua `save()`, bảo toàn toàn vẹn dữ liệu người dùng.
3. **Môi trường chạy không có SpatiaLite C-extension**:
   - Nhờ kiến trúc hybrid, toàn bộ bài test nhánh GIS chạy độc lập hoàn toàn trên SQLite mà không yêu cầu cài đặt SpatiaLite extension nhị phân.

---

## 4. Conclusion (Kết luận)

Tất cả 11 mục tiêu của Milestone 4 đã được triển khai hoàn chỉnh, đúng quy chuẩn kiến trúc và đạt 100% tỷ lệ kiểm thử thành công:
1. `moc-backend/config/settings.py`: Đã bổ sung auto-detect GDAL và GEOS đa nền tảng.
2. `moc-backend/recommendations/services.py`: Đã triển khai thuật toán Pure-Python TF-IDF & Cosine Similarity, chuẩn hóa trọng số tương tác (1..5), bounded cold-start [0, 1], explainable tags, và caching.
3. `moc-backend/recommendations/views.py`: Hỗ trợ `AllowAny`, khách vãng lai, cờ refresh, và tự động xóa cache khi có tương tác.
4. `moc-backend/recommendations/serializers.py`: Hỗ trợ `DualPayloadMixin`, auto-fill trọng số, và trường `is_cold_start`.
5. `moc-backend/recommendations/urls.py` & `moc-backend/api/urls.py`: Khai báo router và các endpoint `/api/recommendations/tuong-tac/`, `/api/recommendations/lam-moi/`.
6. `moc-backend/recommendations/tests.py`: 7 bài test bao phủ toàn diện Features 19-22.
7. `moc-backend/branches/models.py`: Tích hợp các thuộc tính tọa độ, parser tọa độ chuỗi và khai báo GiST index.
8. `moc-backend/branches/services.py`: Cung cấp dịch vụ `find_nearest_branches` hybrid PostGIS + Haversine.
9. `moc-backend/branches/serializers.py`: Bổ sung các trường khoảng cách (`distance_km`, `distance_m`) và tọa độ.
10. `moc-backend/branches/views.py`: Cung cấp các action `nearest`, `tim-gan-nhat`, và sắp xếp theo khoảng cách.
11. `moc-backend/branches/tests.py`: 10 bài test kiểm thử không gian GIS.

---

## 5. Verification Method (Phương pháp kiểm chứng)

Các lệnh kiểm thử đã được chạy và xác nhận độc lập:

1. **Django System Check**:
   ```bash
   moc-backend/.venv/bin/python moc-backend/manage.py check
   ```
   *Kết quả*: `System check identified no issues (0 silenced).` (Exit code 0).

2. **Unit & Integration Tests (Recommendations & Branches)**:
   ```bash
   moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches
   ```
   *Kết quả*: 17/17 tests PASS trong 1.537s.

3. **Regression Tests (Chat, Orders, Recommendations, Branches)**:
   ```bash
   moc-backend/.venv/bin/python moc-backend/manage.py test chat orders recommendations branches
   ```
   *Kết quả*: 58/58 tests PASS trong 24.249s.

4. **E2E Tier 1 Runner**:
   ```bash
   moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1
   ```
   *Kết quả*: 30/30 tests PASS (100.0% pass rate).

5. **E2E Tier 4 Runner**:
   ```bash
   moc-backend/.venv/bin/python tests/e2e/runner.py --tier 4
   ```
   *Kết quả*: 5/5 tests PASS (100.0% pass rate).

6. **Master E2E Test Suite (All Tiers)**:
   ```bash
   moc-backend/.venv/bin/python tests/e2e/runner.py
   ```
   *Kết quả*: 60/60 tests PASS (100.0% pass rate).
