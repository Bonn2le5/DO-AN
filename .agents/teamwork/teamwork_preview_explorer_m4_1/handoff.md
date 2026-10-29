# Báo Cáo Chuyển Giao Khảo Sát & Thiết Kế Kiến Trúc (Handoff Report)
## Milestone 4 (Features 19–22): Content-Based Food Recommendation Engine
**Explorer**: `m4_explorer_ai`  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/`  
**Target Milestone**: Milestone 4 (Features 19–22)  
**Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`

---

## 1. Observation (Quan sát thực tế)

### 1.1 Môi trường thực thi & Gói thư viện Python (Virtualenv Analysis)
- Đã chạy lệnh kiểm tra gói cài đặt:
  ```bash
  moc-backend/.venv/bin/pip list
  ```
  **Kết quả ghi nhận**:
  - `scikit-learn`: **KHÔNG CÓ** (Hoàn toàn không được cài đặt).
  - `numpy`: **KHÔNG CÓ** (Hoàn toàn không được cài đặt).
  - `scipy`: **KHÔNG CÓ** (Hoàn toàn không được cài đặt).
  - Các gói đã cài đặt bao gồm: `Django==4.2.30`, `djangorestframework==3.16.1`, `channels==4.3.2`, `channels_redis==4.3.0`, `redis==7.0.1`, `psycopg2-binary==2.9.12`, `pillow==11.3.0`, `requests==2.32.5`, `asgiref==3.11.1`.
- Đã chạy thử nghiệm tải gói bổ sung:
  ```bash
  moc-backend/.venv/bin/pip install --dry-run numpy
  ```
  **Kết quả ghi nhận lỗi**:
  ```text
  NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known')
  ERROR: Could not find a version that satisfies the requirement numpy (from versions: none)
  ERROR: No matching distribution found for numpy
  ```
  *Kết luận môi trường*: Hệ thống hoạt động trong môi trường **offline / air-gapped hoàn toàn** (không có internet). Bắt buộc toàn bộ thuật toán TF-IDF, Vector Khẩu vị và Cosine Similarity phải được triển khai bằng **Pure-Python (Thư viện chuẩn Python: `math`, `re`, `collections`, `typing`)**, không phụ thuộc bất kỳ thư viện bên ngoài nào.

---

### 1.2 Hiện trạng mã nguồn Backend tại `moc-backend/recommendations/`

#### A. Tệp `moc-backend/recommendations/models.py`:
- `TuongTacMonAn` (bảng `tuong_tac_mon_an`):
  - Khóa ngoại: `nguoi_dung` (`AUTH_USER_MODEL`), `mon_an` (`MonAn`).
  - Trường `loai_tuong_tac`: `models.CharField(max_length=20, choices=LoaiTuongTac.choices)` gồm:
    `xem` ('Xem'), `yeu_thich` ('Yêu thích'), `them_gio_hang` ('Thêm vào giỏ'), `dat_mon` ('Đặt món'), `danh_gia` ('Đánh giá').
  - Trường `trong_so`: `models.DecimalField(max_digits=5, decimal_places=2, default=1)`.
  - Hỗ trợ đầy đủ các thuộc tính và alias tương thích ngược: `FoodInteraction`, `user`, `food`, `interaction_type`, `weight`.
- `GoiYMonAn` (bảng `goi_y_mon_an`):
  - Khóa ngoại: `nguoi_dung`, `mon_an`.
  - Trường `diem_tuong_dong`: `models.DecimalField(max_digits=5, decimal_places=4)`.
  - Ràng buộc tại `moc_schema_tieng_viet.sql` (dòng 589):
    ```sql
    diem_tuong_dong NUMERIC(5,4) NOT NULL CHECK (diem_tuong_dong BETWEEN 0 AND 1)
    ```
  - Trường `ly_do_goi_y`: `models.TextField(blank=True)`.
  - Trường `phien_ban_model`: `models.CharField(max_length=30, blank=True)`.
  - Ràng buộc duy nhất: `unique_together = ("nguoi_dung", "mon_an", "phien_ban_model")`.

#### B. Tệp `moc-backend/recommendations/services.py`:
Quan sát các khiếm khuyết nghiêm trọng trong mã nguồn hiện tại:
1. **Sai lệch trọng số tương tác (Lines 10–16)**:
   ```python
   TRONG_SO_TUONG_TAC = {
       "xem": 1,
       "yeu_thich": 3,
       "them_gio_hang": 4,
       "dat_mon": 6,
       "danh_gia": 5,
   }
   ```
   Trong khi đó, tài liệu dự án `PROJECT.md` (Feature 20), yêu cầu gốc `ORIGINAL_REQUEST.md` (Section R4), dispatch của Orchestrator và bài test chuẩn `tests/e2e/helpers/ai_gis_oracle.py` (dòng 65–71) đều quy định thống nhất:
   - `xem`: **1**
   - `yeu_thich` / `thich`: **2**
   - `them_gio_hang` / `gio_hang`: **3**
   - `dat_mon` / `dat_hang`: **4**
   - `danh_gia`: **5**
2. **Lỗi tràn số và vi phạm ràng buộc CHECK database ở Cold-Start (Lines 91–94)**:
   ```python
   ket_qua = [
       (mon, float(mon.so_luot_danh_gia), ly_do)
       for mon, _ in mon_pho_bien
   ]
   ```
   Khi `mon.so_luot_danh_gia` $\ge 10$ (ví dụ: món có 85 lượt đánh giá trong dữ liệu seed), việc gán `diem_tuong_dong = mon.so_luot_danh_gia` sẽ:
   - Làm tràn cột `DecimalField(max_digits=5, decimal_places=4)` (giá trị tối đa chỉ là 9.9999).
   - Gây lỗi ngoại lệ `IntegrityError: CHECK constraint violated (diem_tuong_dong BETWEEN 0 AND 1)` trên PostgreSQL!
   - Giao diện frontend tại `AIRecommendationSection.tsx` (dòng 108: `{Math.round(rec.score * 100)}% phù hợp`) sẽ hiển thị thành `8500% phù hợp`!
3. **Loại trừ sai món đã từng tương tác (Lines 104–105)**:
   ```python
   if mon.id in tap_mon_da_tuong_tac:
       continue
   ```
   Việc loại trừ này trực tiếp làm hỏng kịch bản kiểm thử E2E Scenario 2 (`tests/e2e/tier4/test_t4_scenarios.py`, dòng 141), nơi khách hàng cũ đã từng đặt và đánh giá món Lẩu Thái kỳ vọng hệ thống gợi ý lại chính món Lẩu Thái này đứng vị trí Top 1 (`self.assertEqual(recs[0]["dish"]["id"], 1)`).
4. **Vấn đề N+1 queries khi trích xuất đặc trưng (Lines 21–26)**:
   `mon_an.nguyen_lieu.values_list("ten", flat=True)` và `mon_an.the_mon_an.values_list("ten", flat=True)` bỏ qua bộ nhớ đệm prefetch và sinh ra hàng trăm truy vấn SQL độc lập nếu thực đơn có nhiều món.

#### C. Tệp `moc-backend/recommendations/views.py`:
- `GoiYMonAnViewSet` đang thiết lập `permission_classes = [IsAuthenticated]`. Khi khách vãng lai truy cập trang chủ (Cold-Start Homepage), API trả về 401 Unauthorized thay vì trả về danh sách món phổ biến.
- Chưa có endpoint `/api/recommendations/tuong-tac/` theo đúng mục tiêu Objective 7 của Dispatch.

---

## 2. Logic Chain (Chuỗi lập luận kỹ thuật)

```
[Môi trường Offline, không numpy/scikit-learn]
               │
               ▼
[Xây dựng thuật toán TF-IDF & Cosine Pure-Python (O(D * T))]
               │
               ├────────────────────────────────────────┐
               ▼                                        ▼
[Chuẩn hóa Trọng số Tương tác]             [Cold-Start Popularity Chuẩn hóa]
xem=1, thích=2, giỏ=3, đặt=4, đánh giá=5   Score = 0.6*(reviews/max) + 0.4*(rating/5.0)
               │                                        │
               ▼                                        ▼
[Vector Khẩu vị Người dùng (Unit L2)]      [Điểm số đảm bảo nghiêm ngặt [0.0, 1.0]]
               │                                        │
               ▼                                        ▼
[Cosine Similarity = Dot Product]          [Không vi phạm CHECK constraint PostgreSQL]
               │                                        │
               └───────────────────┬────────────────────┘
                                   │
                                   ▼
               [Bộ sinh nhãn giải thích Explainable Tags]
               - Món lẩu: "Gợi ý vì bạn yêu thích các món lẩu ấm cúng"
               - Món cay: "Phù hợp với khẩu vị thích món cay nồng của bạn"
               - Món nướng/hải sản: "Được gợi ý dựa trên sở thích món nướng & hải sản của bạn"
               - Món chay: "Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"
               - Cold-start: "Phổ biến hôm nay"
                                   │
                                   ▼
               [Chiến lược Lưu bộ đệm Caching bảng goi_y_mon_an]
               - Đọc: Trả cache DB tức thời nếu có
               - Ghi tương tác: Xóa cache cũ -> Tái tính toán lazy
               - Khách vãng lai: Tính toán in-memory không ghi DB
```

### Bước 1: Xây dựng biểu diễn văn bản và Corpus đặc trưng món ăn
Mỗi món ăn $d \in \mathcal{D}$ (đang mở bán `con_hang=True` và `hien_thi=True`) được tổng hợp văn bản từ:
- Tên món (`ten`)
- Tên danh mục (`danh_muc.ten`)
- Mô tả ngắn và mô tả chi tiết (`mo_ta_ngan`, `mo_ta_chi_tiet`)
- Danh sách nguyên liệu (`nguyen_lieu.ten`)
- Danh sách thẻ (`the_mon_an.ten`)
- Thuộc tính mở rộng: Nếu `la_mon_chay=True` bổ sung `"món chay ăn chay thanh đạm"`; Nếu `do_cay > 0` bổ sung `"món cay vị cay sa tế"`.
Tách từ tiếng Việt qua biểu thức chính quy chuẩn hóa chữ thường và dấu tiếng Việt:
$$\text{tokens}(d) = \text{re.findall}(r'[\wÀ-ỹ]+', Text(d).\text{lower}())$$

### Bước 2: Công thức TF-IDF Pure-Python chuẩn hóa L2
1. **Sublinear Term Frequency**:
   $$\text{TF}(t, d) = 1.0 + \ln(f(t, d)) \quad (\text{với } f(t, d) > 0)$$
2. **Smooth Inverse Document Frequency**:
   $$\text{IDF}(t) = \ln\left( \frac{N + 1}{\text{DF}(t) + 1} \right) + 1.0$$
3. **Trọng số TF-IDF**:
   $$V_d(t) = \text{TF}(t, d) \times \text{IDF}(t)$$
4. **Vector chuẩn hóa L2**:
   $$\hat{V}_d(t) = \frac{V_d(t)}{\sqrt{\sum_t V_d(t)^2}}$$

### Bước 3: Vector Khẩu vị Người dùng (User Preference Profile)
Với tập lịch sử tương tác $\mathcal{I}_u$ của người dùng $u$:
$$w(\text{loai}) = \begin{cases} 
1 & \text{xem (view)} \\ 
2 & \text{yeu\_thich / thich (favorite)} \\ 
3 & \text{them\_gio\_hang / gio\_hang (cart)} \\ 
4 & \text{dat\_mon / dat\_hang (order)} \\ 
5 & \text{danh\_gia (review)} 
\end{cases}$$
Vector tổng hợp:
$$U_u(t) = \sum_{(d_i, a_i) \in \mathcal{I}_u} w(a_i) \times \hat{V}_{d_i}(t)$$
Chuẩn hóa L2:
$$\hat{U}_u(t) = \frac{U_u(t)}{\sqrt{\sum_t U_u(t)^2}}$$

### Bước 4: Độ tương đồng Cosine (Cosine Similarity)
Vì cả $\hat{U}_u$ và $\hat{V}_d$ đều là vector đơn vị L2 và không âm:
$$\text{CosineSimilarity}(u, d) = \hat{U}_u \cdot \hat{V}_d = \sum_{t} \hat{U}_u(t) \times \hat{V}_d(t)$$
Giá trị toán học nằm chính xác trong đoạn $[0.0, 1.0]$, tương thích hoàn toàn với kiểu `NUMERIC(5,4)` và ràng buộc `CHECK (diem_tuong_dong BETWEEN 0 AND 1)`.

### Bước 5: Cold-Start Popularity Fallback
Khi người dùng chưa có tương tác ($\mathcal{I}_u = \emptyset$) hoặc khách chưa đăng nhập:
$$\text{Score}_{\text{cold}}(d) = 0.6 \times \frac{d.\text{so\_luot\_danh\_gia}}{\max(\text{reviews}, 1)} + 0.4 \times \frac{d.\text{diem\_danh\_gia}}{5.0}$$
- Đảm bảo $\text{Score}_{\text{cold}}(d) \in [0.0, 1.0]$.
- Xếp hạng món theo điểm giảm dần, lấy Top-N (mặc định 6).
- Gán nhãn giải thích `ly_do_goi_y = "Phổ biến hôm nay"`.
- Đánh dấu cờ `is_cold_start = True`.

### Bước 6: Nhãn giải thích (Explainable Recommendation Tags)
Bộ phân tích nhãn ưu tiên:
1. Món có chứa từ khóa lẩu/hotpot $\to$ `"Gợi ý vì bạn yêu thích các món lẩu ấm cúng"`
2. Món có độ cay $> 0$ hoặc có sa tế/cay $\to$ `"Phù hợp với khẩu vị thích món cay nồng của bạn"`
3. Món nướng/bbq/hải sản $\to$ `"Được gợi ý dựa trên sở thích món nướng & hải sản của bạn"`
4. Món chay $\to$ `"Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"`
5. Mặc định $\to$ `"Phù hợp với khẩu vị và các món bạn thường chọn"`

### Bước 7: Chiến lược Bộ nhớ đệm (Cache Strategy)
1. **Lưu cache**: Bảng `goi_y_mon_an` lưu trữ danh sách Top-N món của từng người dùng đăng nhập (`phien_ban_model` là `"cb_tfidf_v1"` hoặc `"cold_start_v1"`).
2. **Tái sử dụng cache**: Khi gọi `GET /api/recommendations/`, nếu trong DB đã có bản ghi và không có cờ `?refresh=true`, trả về kết quả ngay lập tức mà không cần tính toán lại.
3. **Vô hiệu hóa cache (Cache Invalidation)**: Khi người dùng thực hiện một tương tác mới (thông qua `POST /api/tuong-tac/` hoặc `/api/recommendations/tuong-tac/`), hệ thống tự động xóa các dòng `GoiYMonAn` cũ của người dùng này. Lần truy vấn kế tiếp sẽ tính toán lại theo khẩu vị vừa cập nhật.
4. **Khách vãng lai (Anonymous)**: Tính toán in-memory và trả về trực tiếp, không ghi vào database để tránh lỗi vi phạm khóa ngoại `nguoi_dung_id NOT NULL`.

---

## 3. Caveats (Lưu ý & Điểm biên kỹ thuật)

1. **Số lượng món ăn quy mô vừa (< 2000 món)**:
   Thuật toán Pure-Python xử lý 100-200 món ăn trong thời gian $\approx 5\text{ms}$. Nếu thực đơn vượt quá $10.000$ món trong tương lai, việc tính toán trực tiếp trên web request có thể tốn tài nguyên và nên chuyển sang background task (Celery/RQ) hoặc sử dụng ma trận thưa. Với quy mô hiện tại của Nhà hàng Mộc (~100 món), Pure-Python là giải pháp tối ưu nhất, không cần cài thêm gói C-extension.
2. **Khách vãng lai và quyền truy cập API**:
   Viewset `GoiYMonAnViewSet` phải sử dụng `permission_classes = [AllowAny]` thay vì `[IsAuthenticated]`. Nếu không, khách chưa đăng nhập truy cập trang chủ sẽ bị lỗi 401.
3. **Dual Routing cho tương tác**:
   Cần đăng ký cả `/api/tuong-tac/` (canonical) và `/api/recommendations/tuong-tac/` để đáp ứng toàn bộ các client khác nhau.
4. **Lưu trữ Decimal trong PostgreSQL**:
   Điểm số cosine similarity và cold-start score phải luôn làm tròn 4 chữ số thập phân (`round(score, 4)`) trước khi chuyển thành `Decimal(str(...))` để tránh lỗi sai số dấu phẩy động dạng `0.9420000000000001` khi insert vào cột `NUMERIC(5,4)`.

---

## 4. Conclusion (Kết luận & Thiết kế kiến trúc cụ thể)

Toàn bộ giải pháp kiến trúc cho Milestone 4 đã được đóng gói thành các bản thiết kế mã nguồn hoàn chỉnh đặt tại thư mục làm việc của Explorer:

| Tệp thiết kế | Đường dẫn tuyệt đối | Vai trò kiến trúc |
|---|---|---|
| **Dịch vụ Pure-Python AI** | `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_services.py` | Triển khai TF-IDF, Cosine, trọng số tương tác, Cold-start fallback, explainable tags, caching. |
| **ViewSets REST API** | `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_views.py` | Quản lý endpoint recommendations, hỗ trợ khách vãng lai, cờ refresh, và tự động xóa cache khi có tương tác. |
| **Serializers Đa ngữ** | `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_serializers.py` | Tự động sinh trọng số tương tác, ánh xạ bí danh tiếng Anh/Việt, bổ sung cờ `is_cold_start`. |
| **Định tuyến URL mở rộng** | `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_urls.py` | Khai báo URL `/api/recommendations/tuong-tac/`, `/api/recommendations/lam-moi/`. |
| **Kịch bản kiểm thử độc lập** | `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/test_algo.py` | Script kiểm chứng toán học độc lập đã chạy đạt 100% kết quả. |
| **Bộ Unit Test Django** | `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_1/proposed_tests.py` | 5 bài test tự động bao phủ toàn diện Features 19–22. |

### Thông số kỹ thuật REST API chi tiết:
1. **GET `/api/recommendations/` & `/api/goi-y/`**:
   - Quyền: `AllowAny`
   - Tham số truy vấn: `limit` hoặc `gioi_han` (mặc định: 6), `refresh` hoặc `lam_moi` (mặc định: false).
   - Phản hồi: Danh sách đối tượng có trường `score`, `reason`, `is_cold_start`, `chi_tiet_mon_an`.
2. **POST `/api/recommendations/refresh/` & `/api/recommendations/lam-moi/`**:
   - Quyền: `IsAuthenticated`
   - Hành động: Bắt buộc tái tính toán và cập nhật lại cache.
3. **POST `/api/recommendations/tuong-tac/` & `/api/tuong-tac/`**:
   - Quyền: `IsAuthenticated`
   - Payload:
     ```json
     {
       "mon_an": 101,
       "loai_tuong_tac": "dat_mon"
     }
     ```
   - Tự động điền `trong_so = 4` nếu client không gửi `trong_so`.
   - Tự động xóa `GoiYMonAn` cache của user để đón nhận khẩu vị mới.

---

## 5. Verification Method (Phương pháp kiểm chứng độc lập)

### 5.1 Kiểm chứng tính toán học của thuật toán Pure-Python
Chạy lệnh kiểm thử độc lập đã tạo:
```bash
moc-backend/.venv/bin/python .agents/teamwork/teamwork_preview_explorer_m4_1/test_algo.py
```
**Điều kiện thành công**:
- Test 1 (Cold-start): Điểm số chuẩn hóa nằm nghiêm ngặt trong $[0.0, 1.0]$, món nhiều review/sao xếp đầu.
- Test 2 (Personalized): Tương tác được nhân trọng số chính xác (`dat_mon` = 4, `danh_gia` = 5), món tương đồng cao nhất xếp đầu.
- Test 3 (Explainable tags): Nhãn giải thích khớp các từ khóa "lẩu", "cay", "chay".

### 5.2 Kiểm chứng bộ test E2E Tier 1 & Tier 4 hiện hành
Chạy test runner:
```bash
moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1
moc-backend/.venv/bin/python tests/e2e/runner.py --tier 4
```
**Điều kiện thành công**:
- 30/30 bài test Tier 1 đạt kết quả `OK` (trong đó có `test_t1_recommendation_gis_04_cold_start_popularity_ranking` và `test_t1_recommendation_gis_05_explainable_tag_generation`).
- 5/5 bài test Tier 4 đạt kết quả `OK` (trong đó có kịch bản Scenario 1 khách mới và Scenario 2 khách thích lẩu chua cay).

### 5.3 Điều kiện phủ nhận (Invalidation Conditions)
Kiến trúc đề xuất sẽ bị coi là không hợp lệ nếu:
1. `diem_tuong_dong` vượt quá giá trị 1.0 hoặc âm, gây lỗi `IntegrityError` trên PostgreSQL.
2. Trọng số tương tác bị sai lệch so với bảng chuẩn `xem=1, thích=2, giỏ=3, đặt=4, đánh giá=5`.
3. Khách vãng lai gọi `GET /api/recommendations/` bị nhận mã lỗi HTTP 401 hoặc làm sập server do cố insert khóa ngoại NULL vào bảng `goi_y_mon_an`.
4. Gọi `POST /api/recommendations/tuong-tac/` bị lỗi HTTP 404.
