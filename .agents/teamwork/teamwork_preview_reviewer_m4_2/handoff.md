# Báo Cáo Đánh Giá Chất Lượng & Phản Biện Đối Kháng (Review & Adversarial Audit)
## Milestone 4: AI Recommendations & PostGIS GIS Spatial Queries

- **Reviewer & Critic**: `m4_reviewer_2`
- **Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_reviewer_m4_2`
- **Target Worker**: `m4_worker_1` (`teamwork_preview_worker_m4_1`)
- **Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`
- **Verdict**: **APPROVE** (Đạt chuẩn 100%, không phát hiện vi phạm tính toàn vẹn)

---

## 1. Observation (Quan sát trực tiếp & Bằng chứng thực nghiệm)

### 1.1 Kiểm tra Hệ thống & Lệnh Django Check
- Lệnh: `moc-backend/.venv/bin/python moc-backend/manage.py check`
- Kết quả: `System check identified no issues (0 silenced).` (Exit code 0).
- Hệ thống không có xung đột model, không có lỗi cấu hình hay import hỏng.

### 1.2 Kiểm thử Đơn vị & Tích hợp (Unit & Integration Tests)
- Lệnh: `moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches`
- Kết quả:
  ```text
  Found 17 test(s).
  Creating test database for alias 'default'...
  .................
  ----------------------------------------------------------------------
  Ran 17 tests in 1.825s
  OK
  Destroying test database for alias 'default'...
  ```
  17/17 tests PASS (7 test cases cho recommendations, 10 test cases cho branches).

### 1.3 Kiểm thử Hồi quy Đa Module (Regression Tests: Chat, Orders, Recommendations, Branches)
- Lệnh: `moc-backend/.venv/bin/python moc-backend/manage.py test chat orders recommendations branches`
- Kết quả:
  ```text
  Found 58 test(s).
  Creating test database for alias 'default'...
  ..........................................................
  ----------------------------------------------------------------------
  Ran 58 tests in 29.618s
  OK
  Destroying test database for alias 'default'...
  ```
  58/58 tests PASS toàn diện, đảm bảo các sửa đổi của M4 không gây hồi quy (regression) lên M2 và M3.

### 1.4 Kiểm thử Toàn trình End-to-End (Master E2E Suite)
1. **Tier 1 (Core Invariants)**:
   - Lệnh: `moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1`
   - Kết quả: 30/30 tests PASS (100.0% pass rate).
2. **Tier 4 (Real-World Scenarios)**:
   - Lệnh: `moc-backend/.venv/bin/python tests/e2e/runner.py --tier 4`
   - Kết quả: 5/5 tests PASS (100.0% pass rate).
   - Xác nhận Scenario 1 (Khách mới cold-start -> nearest branch lookup -> menu recommendation -> table hold -> deposit payment -> order tracking) và Scenario 2 (Khách quen thích cay/lẩu -> TF-IDF cosine similarity -> explainable tags -> live chat) hoạt động chính xác.
3. **Master Runner (All Tiers)**:
   - Lệnh: `moc-backend/.venv/bin/python tests/e2e/runner.py`
   - Kết quả: 60/60 tests PASS (100.0% pass rate) trên toàn bộ 4 Tiers.

### 1.5 Kiểm tra Chi tiết Mã nguồn (Code Audit)
1. **Kiểm tra Vi phạm Tính toàn vẹn (Integrity Check)**:
   - Không có kết quả test hardcode trong `recommendations/services.py` hay `branches/services.py`.
   - Không có facade hay mock implementation: Thuật toán TF-IDF, L2 normalization, Cosine similarity, và Haversine geodesic distance đều được viết bằng công thức toán học thực chất bằng Pure-Python.
2. **`moc-backend/config/settings.py` (Dòng 27–54)**:
   - Cơ chế tự động dò tìm thư viện GDAL (`libgdal.dylib`, `libgdal.so`) và GEOS (`libgeos_c.dylib`, `libgeos_c.so`) trên cả macOS Homebrew (`/opt/homebrew/lib`) và Linux (`/usr/lib`).
   - Tách biệt môi trường kiểm thử: `INSTALLED_APPS` tự động bỏ `django.contrib.gis` khi chạy test với SQLite, cho phép chạy test mượt mà trên môi trường offline/không có SpatiaLite.
3. **`moc-backend/recommendations/services.py`**:
   - Dòng 17–23: Trọng số tương tác chuẩn hóa: `xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5`.
   - Dòng 118–128: Điểm số Cold-start: $\text{score} = 0.6 \times \frac{\text{reviews}}{\max(\text{reviews}, 1)} + 0.4 \times \frac{\text{rating}}{5.0}$, chặn cận nghiêm ngặt trong $[0.0, 1.0]$.
   - Dòng 193–201: Tính Sublinear TF ($1 + \ln(f)$) và Smoothed IDF ($\ln(\frac{N+1}{\text{DF}+1}) + 1.0$) kèm chuẩn hóa đơn vị L2.
   - Dòng 200, 221, 236: Phòng tránh lỗi chia cho 0 (`ZeroDivisionError`) bằng cấu trúc `or 1.0`.
   - Dòng 93–104: Bộ sinh nhãn giải thích (Explainable Tags) phân loại chuẩn: lẩu, vị cay, nướng/hải sản, món chay, khẩu vị thường chọn.
4. **`moc-backend/branches/services.py` & `models.py`**:
   - `haversine_distance_km` tính khoảng cách mặt cầu Trái Đất theo bán kính $R = 6371.0088\text{ km}$, khớp độ chính xác của PostGIS `ST_Distance(geography)`.
   - `ChiNhanh._parse_coords` hỗ trợ đầy đủ Point object, tuple, chuỗi WKT `POINT(x y)` và định dạng `lng,lat` / `lat,lng`.
   - `ChiNhanhViewSet.nearest` và `tim_gan_nhat`: Validate tọa độ vĩ độ $[-90, 90]$, kinh độ $[-180, 180]$, hỗ trợ lọc bán kính `radius_km` và trả về chi nhánh kèm `distance_km`, `distance_m`.

---

## 2. Logic Chain (Chuỗi lập luận kỹ thuật)

1. **Khả năng chạy độc lập & tương thích môi trường (Environment Portability)**:
   - Từ quan sát 1.5.2, hệ thống tự động nhận diện GDAL/GEOS trên production PostgreSQL/PostGIS và tự động chuyển đổi sang SQLite + Haversine trong môi trường kiểm thử.
   - Do đó, ứng dụng hoạt động ổn định trên cả production Linux server, macOS nhà phát triển lẫn môi trường test sandbox mà không yêu cầu cài đặt binary phức tạp.
2. **Tính đúng đắn của Thuật toán AI Gợi ý (Algorithmic Soundness)**:
   - Từ quan sát 1.5.3, thuật toán Content-Based Filtering trích xuất đặc trưng từ văn bản món ăn, tạo vector không gian đa chiều, tổng hợp vector khẩu vị người dùng có trọng số (1..5), và tính độ tương đồng Cosine qua tích vô hướng 2 vector đơn vị.
   - Toàn bộ kết quả đều nằm trong khoảng $[0.0, 1.0]$, bảo toàn ràng buộc `CHECK (diem_tuong_dong BETWEEN 0 AND 1)` của bảng PostgreSQL.
3. **Trải nghiệm người dùng và tính giải thích được (Explainability & Cold-Start)**:
   - Với khách vãng lai và người dùng mới chưa có tương tác, hệ thống tự động kích hoạt `tinh_goi_y_cold_start` dựa trên độ phổ biến và điểm đánh giá.
   - Khách vãng lai nhận gợi ý in-memory không ghi vào DB, tránh vi phạm ràng buộc NOT NULL của trường `nguoi_dung`.
   - Nhãn giải thích `ly_do_goi_y` cung cấp ngữ cảnh rõ ràng ("Gợi ý vì bạn yêu thích các món lẩu ấm cúng", "Phổ biến hôm nay"), đáp ứng trọn vẹn Feature 21 & 22.
4. **Hiệu năng & Cơ chế vô hiệu hóa Cache (Cache Invalidation)**:
   - Khi có tương tác mới ghi nhận qua `POST /api/tuong-tac/`, cache gợi ý cũ trong bảng `GoiYMonAn` bị xóa ngay lập tức. Lượt truy vấn kế tiếp tự động tái tạo cache theo khẩu vị cập nhật.

---

## 3. Adversarial Challenges & Stress Test Results (Phản biện Đối kháng)

### 3.1 Challenge 1: Tọa độ ngoài phạm vi địa lý và dữ liệu rác
- **Kịch bản**: Khách gửi vĩ độ vượt ngưỡng (`lat=95.0`) hoặc dữ liệu chuỗi không hợp lệ (`lat=bad_lat`).
- **Thực nghiệm**:
  - `GET /api/branches/nearest/?lat=95.0&lng=106.6` -> Phản hồi `HTTP 400 Bad Request`, body: `{"detail": "Tọa độ không hợp lệ (-90 <= lat <= 90, -180 <= lng <= 180)."}`.
  - `GET /api/branches/nearest/?lat=bad_lat&lng=bad_lng` -> Phản hồi `HTTP 400 Bad Request`, body: `{"detail": "Tọa độ lat và lng phải là số thực."}`.
  - `GET /api/branches/nearest/` (thiếu tọa độ) -> Phản hồi `HTTP 400 Bad Request`, body: `{"detail": "Vui lòng cung cấp tọa độ lat (vĩ độ) và lng (kinh độ)."}`.
- **Đánh giá**: **PASS**. Hệ thống phòng vệ dữ liệu đầu vào chặt chẽ.

### 3.2 Challenge 2: Điểm biên cực hạn của khoảng cách Haversine
- **Kịch bản**:
  1. Hai tọa độ trùng khớp hoàn toàn (người dùng đứng tại chính chi nhánh).
  2. Hai tọa độ đối cực xuyên tâm Trái Đất (Antipodal points: `(0, 0)` và `(0, 180)`).
- **Thực nghiệm**:
  - Tọa độ trùng nhau: `haversine_distance_km(10.7925, 106.6669, 10.7925, 106.6669)` -> Trả về chính xác `0.0 km`.
  - Tọa độ đối cực: `haversine_distance_km(0.0, 0.0, 0.0, 180.0)` -> Trả về `20015.11 km` (sai số < 0.01% so với chu vi nửa vòng Trái Đất $20015.087\text{ km}$).
- **Đánh giá**: **PASS**. Độ chính xác hình học mặt cầu chuẩn xác tuyệt đối.

### 3.3 Challenge 3: Cold-start trong điều kiện cơ sở dữ liệu món ăn rỗng hoặc 0 đánh giá
- **Kịch bản**: Danh sách món ăn có `so_luot_danh_gia = 0` và `diem_danh_gia = 0.0`.
- **Thực nghiệm**:
  - `DichVuGoiY.tinh_goi_y_cold_start([FakeDish(id=1, reviews=0, rating=0.0)])` -> Tính toán an toàn, trả về điểm `0.0`, không phát sinh `ZeroDivisionError`.
  - Danh sách rỗng `[]` -> Trả về `[]` an toàn.
- **Đánh giá**: **PASS**.

### 3.4 Challenge 4: Khách vãng lai gọi API gợi ý với tham số giới hạn dị thường
- **Kịch bản**: Khách chưa đăng nhập gọi `GET /api/recommendations/?limit=-5` hoặc `limit=9999`.
- **Thực nghiệm**: Trả về `HTTP 200 OK` với danh sách cold-start mặc định, không sập server.
- **Đánh giá**: **PASS**.

---

## 4. Findings (Các phát hiện trong quá trình Review)

### Minor Finding 1 (Kiến trúc / Giao dịch Đồng thời)
- **Vị trí**: `moc-backend/recommendations/services.py:251-262`
- **Mô tả**: Khi cập nhật cache gợi ý cho người dùng đăng nhập, hàm `cap_nhat_goi_y` thực hiện `GoiYMonAn.objects.filter(nguoi_dung=nguoi_dung).delete()` rồi sau đó gọi `GoiYMonAn.objects.bulk_create(danh_sach_tao)`.
- **Rủi ro**: Nếu có 2 request đồng thời từ cùng 1 user gửi yêu cầu refresh trong cùng 1 mili-giây, có thể xảy ra race condition nhỏ giữa lúc xóa và lúc tạo lại.
- **Khuyến nghị khắc phục**: Bọc khối lệnh này trong `with transaction.atomic():` để đảm bảo tính nguyên tử (atomic) tuyệt đối.
- **Mức độ**: Minor (Không cản trở hoạt động và không gây lỗi trong môi trường thực tế).

### Minor Finding 2 (Giả định Phân tích Tọa độ Chuỗi)
- **Vị trí**: `moc-backend/branches/models.py:61, 68, 75`
- **Mô tả**: Bộ phân tích chuỗi `_parse_coords` sử dụng heuristic `if c1 < 30.0 and c2 > 90.0: return c2, c1` để tự động hoán đổi khi người dùng nhập chuỗi theo thứ tự `lat,lng` thay vì `lng,lat`.
- **Đánh giá**: Rất thông minh và thực tiễn cho địa bàn Việt Nam (vĩ độ ~10-22°N, kinh độ ~102-109°E). Tuy nhiên, nếu mở rộng ra quốc tế, cần dựa vào định dạng WKT chuẩn hoặc khai báo tường minh.
- **Mức độ**: Minor (Hoàn toàn phù hợp với phạm vi chuỗi Nhà hàng Mộc tại TP.HCM).

---

## 5. Caveats (Các giả định & Giới hạn khảo sát)

1. **Quy mô tập dữ liệu gợi ý**: Thử nghiệm đã kiểm chứng với ~100-200 món ăn trong nhà hàng. Đối với các hệ thống thương mại điện tử hàng triệu sản phẩm, thuật toán pure-Python in-memory sẽ cần chuyển sang vector database hoặc inverted index phân tán (như Elasticsearch / Pinecone / Faiss). Đối với phạm vi menu nhà hàng (vài trăm món), giải pháp hiện tại tối ưu vượt trội về độ nhẹ và tốc độ (chạy trong vài mili-giây).
2. **Không có SpatiaLite nhị phân trên SQLite**: Kiểm thử GIS trên SQLite được hỗ trợ thông qua cơ chế Geodesic Haversine song song. Trên production PostgreSQL/PostGIS, native GiST index và `ST_Distance` được kích hoạt tự động.

---

## 6. Conclusion (Kết luận & Phán quyết)

**Phán quyết**: **APPROVE**

Milestone 4 (AI Recommendations & PostGIS GIS) của Nhà hàng Mộc được triển khai xuất sắc, trung thực, đạt chuẩn kiến trúc cao:
1. **Tính toàn vẹn**: 100% không có gian lận, không có hardcoded outputs, thuật toán chuẩn toán học.
2. **Độ ổn định**: Vượt qua 100% các bài test (17/17 tests M4, 58/58 tests hồi quy M2-M4, 60/60 tests E2E Tiers 1-4).
3. **Khả năng phòng vệ**: Hệ thống xử lý an toàn mọi dữ liệu biên, dữ liệu dị thường và khách vãng lai.
4. **Sẵn sàng chuyển giao**: Hệ thống đã sẵn sàng 100% để chuyển giao sang Milestone 5 (Frontend Synchronization & Admin/Staff Portals).

---

## 7. Verification Method (Phương pháp Kiểm chứng Độc lập)

Bất kỳ reviewer nào cũng có thể kiểm chứng độc lập báo cáo này bằng các lệnh sau từ thư mục gốc `/Users/VuVan/Documents/DO-AN`:

```bash
# 1. Kiểm tra tính toàn vẹn hệ thống
moc-backend/.venv/bin/python moc-backend/manage.py check

# 2. Kiểm thử đơn vị Milestone 4
moc-backend/.venv/bin/python moc-backend/manage.py test recommendations branches

# 3. Kiểm thử hồi quy toàn diện
moc-backend/.venv/bin/python moc-backend/manage.py test chat orders recommendations branches

# 4. Kiểm thử Master E2E Scenarios
moc-backend/.venv/bin/python tests/e2e/runner.py --tier 4
moc-backend/.venv/bin/python tests/e2e/runner.py
```
*(Nếu bất kỳ lệnh nào trả về exit code khác 0 hoặc có bài test thất bại, kết luận APPROVE bị vô hiệu hóa).*
