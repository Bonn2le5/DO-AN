# API Contract — Mộc Restaurant

Tài liệu liệt kê mọi endpoint backend: **body gửi lên / dữ liệu trả về**, **code xử lý ở file nào, dòng nào** và **frontend gọi từ đâu**.

> Đối chiếu với commit `cfd0bbc` (nhánh `feat/trang-tai-khoan`), sau khi bỏ lớp bí danh tiếng Anh. Từ commit này, **tên trường trong body và JSON trả về là tiếng Việt**. Chỉ còn URL là song ngữ. Số dòng sẽ lệch khi sửa code, nên tìm theo tên hàm.

## 1. Quy ước chung

| Mục | Giá trị | Nằm ở đâu |
|---|---|---|
| Base URL | `/api/` (frontend: `VITE_API_URL`, mặc định `/api`) | [config/urls.py:37](moc-backend/config/urls.py:37), [client.ts:5](moc-frontend/src/api/client.ts:5) |
| Khai báo route | Toàn bộ route REST nằm trong **một file** | [api/urls.py](moc-backend/api/urls.py) |
| Xác thực | JWT (SimpleJWT), header `Authorization: Bearer <access>` | [settings.py:228](moc-backend/config/settings.py:228) |
| Quyền mặc định | `IsAuthenticatedOrReadOnly` (phần lớn ViewSet ghi đè lại) | [settings.py:231](moc-backend/config/settings.py:231) |
| Lớp quyền tự viết | `LaNhanVienNhaHang`, `LaNhanVienHoacChiDoc` | [api/permissions.py](moc-backend/api/permissions.py) |
| Tự làm mới token | Khi gặp 401, interceptor axios gọi `/auth/refresh/` | [client.ts:41](moc-frontend/src/api/client.ts:41) |
| Tên trường | snake_case **tiếng Việt** cho cả body lẫn response (`ten`, `so_dien_thoai`, `tao_luc`…) | serializers của từng app |
| Tên route | Song ngữ: phần lớn route có tên tiếng Anh và tiếng Việt, **trỏ vào cùng một ViewSet** (vd. `/foods/` = `/mon-an/`). Frontend dùng tên tiếng Anh. | [api/urls.py:25-102](moc-backend/api/urls.py:25) |
| Lỗi | `400` trả về `{ "<tên_trường>": ["thông báo"] }` hoặc `{ "detail": "..." }`. Một số action viết tay trả về `{ "chi_tiet": "..." }`. | — |
| Phân trang | Không bật mặc định: danh sách trả về mảng. Frontend vẫn xử lý `results` nếu sau này bật. | — |

**Ký hiệu quyền dùng trong các bảng:**

- **Public**: không cần đăng nhập (`AllowAny`).
- **User**: cần đăng nhập (`IsAuthenticated`).
- **Staff**: nhân viên nhà hàng (`LaNhanVienNhaHang`). Nhân viên hoặc quản lý chi nhánh chỉ thao tác được dữ liệu của chi nhánh mình; quản trị viên thấy tất cả.
- **Đọc public / Ghi staff**: `LaNhanVienHoacChiDoc`, ai cũng GET được, còn thêm/sửa/xoá cần nhân viên.

**CRUD chuẩn** của một `ModelViewSet` đăng ký ở `/x/` gồm:

- `GET /x/`: danh sách.
- `POST /x/`: tạo mới.
- `GET /x/{id}/`: xem chi tiết.
- `PUT` hoặc `PATCH /x/{id}/`: sửa.
- `DELETE /x/{id}/`: xoá.

Body của các lệnh tạo/sửa dùng **đúng tên cột của model** (xem mục 17).

---

## 2. Hệ thống

| Method | Endpoint | Quyền | Backend | Ghi chú |
|---|---|---|---|---|
| GET | `/` | Public | [config/urls.py:35](moc-backend/config/urls.py:35) `home_view` | Thông tin project |
| GET | `/api/health/` | Public | [api/views.py:5](moc-backend/api/views.py:5) `health_check` | Kiểm tra server |
| GET | `/media/<path>` | Public | [config/urls.py:38](moc-backend/config/urls.py:38) | Ảnh upload |
| — | `/admin/` | Superuser | [config/urls.py:36](moc-backend/config/urls.py:36) | Django admin |

---

## 3. Xác thực & Tài khoản — app `accounts`

**ViewSet:** `XacThucViewSet` ([accounts/views.py:32](moc-backend/accounts/views.py:32)) · Route: `/auth/` = `/xac-thuc/` ([api/urls.py:28-29](moc-backend/api/urls.py:28))

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| POST | `/auth/login/` (= `/auth/dang-nhap/`) | Public | [accounts/views.py:26](moc-backend/accounts/views.py:26) `DangNhapTokenView` · route [api/urls.py:106](moc-backend/api/urls.py:106) | [auth.api.ts:21](moc-frontend/src/api/auth.api.ts:21) `login` |
| POST | `/auth/refresh/` (= `/auth/lam-moi/`) | Public | SimpleJWT `TokenRefreshView` · route [api/urls.py:108](moc-backend/api/urls.py:108) | [client.ts:50](moc-frontend/src/api/client.ts:50) |
| POST | `/auth/register/` (= `/auth/dang_ky/`, `/auth/dang-ky/`) | Public | [accounts/views.py:34](moc-backend/accounts/views.py:34) `dang_ky` | [auth.api.ts:28](moc-frontend/src/api/auth.api.ts:28) `register` |
| POST | `/auth/gui-ma-xac-thuc/` | Public | [accounts/views.py:67](moc-backend/accounts/views.py:67) `gui_ma_xac_thuc` | [auth.api.ts:51](moc-frontend/src/api/auth.api.ts:51) `resendVerificationEmail` |
| POST | `/auth/xac-thuc-email/` | Public | [accounts/views.py:94](moc-backend/accounts/views.py:94) `xac_thuc_email` | [auth.api.ts:37](moc-frontend/src/api/auth.api.ts:37) `verifyEmail` |
| GET / PATCH / PUT | `/auth/profile/` (= `/auth/ho_so/`, `/auth/ho-so/`) | User | [accounts/views.py:139](moc-backend/accounts/views.py:139) `ho_so` | [auth.api.ts:23](moc-frontend/src/api/auth.api.ts:23), [auth.api.ts:55](moc-frontend/src/api/auth.api.ts:55) `updateProfile` |
| POST | `/auth/change-password/` (= `/auth/change_password/`, `/auth/doi_mat_khau/`, `/auth/doi-mat-khau/`) | User | [accounts/views.py:161](moc-backend/accounts/views.py:161) `doi_mat_khau` | [auth.api.ts:60](moc-frontend/src/api/auth.api.ts:60), [admin/api/admin.api.ts:243](moc-frontend/src/admin/api/admin.api.ts:243) |

**Body / trả về**

| Endpoint | Body gửi lên | Trả về |
|---|---|---|
| `login` | `{ thu_dien_tu, password }` (email được đưa về chữ thường) | `{ access, refresh }`; frontend gọi tiếp `GET /auth/profile/` |
| `refresh` | `{ refresh }` | `{ access, refresh? }` |
| `register` | `{ ho_ten, thu_dien_tu, so_dien_thoai, mat_khau }` | `201 { message, email }`: tài khoản tạo ở trạng thái `is_active=false` và OTP được gửi qua email |
| `gui-ma-xac-thuc` | `{ email }` | `{ message }` |
| `xac-thuc-email` | `{ email, ma_xac_thuc }` | `{ message, nguoi_dung: NguoiDung, access, refresh }` (đăng nhập luôn) |
| `profile` GET | — | `NguoiDung` |
| `profile` PATCH | Các trường của `NguoiDung`. Nếu đổi `thu_dien_tu` thì phải kèm `mat_khau_hien_tai`. | `NguoiDung` |
| `change-password` | `{ mat_khau_cu, mat_khau_moi }` (`mat_khau_moi` tối thiểu 6 ký tự) | `{ thong_bao }` |

`NguoiDung` ([accounts/serializers.py:24](moc-backend/accounts/serializers.py:24)) có các trường sau:

- `id`, `thu_dien_tu`, `username`, `first_name`, `last_name`;
- `ho_ten` (chỉ đọc);
- `so_dien_thoai`, `anh_dai_dien`, `ngay_sinh`, `gioi_tinh` (`nam` | `nu` | `khac`);
- `chi_nhanh_quan_ly`, `danh_sach_vai_tro` (mảng tên vai trò);
- `is_active`, `date_joined`, `la_nhan_vien_nha_hang`, `is_superuser`.

**Người dùng / Vai trò / Quyền hạn** (tất cả cần Staff)

| Method | Endpoint | Backend | Frontend gọi |
|---|---|---|---|
| GET / DELETE | `/users/` (= `/nguoi-dung/`) | [accounts/views.py:181](moc-backend/accounts/views.py:181) `NguoiDungViewSet` | [admin/api/admin.api.ts:170](moc-frontend/src/admin/api/admin.api.ts:170) `usersStore` |
| POST | `/users/admin_create/` | [accounts/views.py:225](moc-backend/accounts/views.py:225) | [admin/api/admin.api.ts:21](moc-frontend/src/admin/api/admin.api.ts:21) |
| PATCH | `/users/{id}/admin_update/` | [accounts/views.py:280](moc-backend/accounts/views.py:280) | [admin/api/admin.api.ts:22](moc-frontend/src/admin/api/admin.api.ts:22) |
| CRUD | `/roles/` (= `/vai-tro/`) | [accounts/views.py:336](moc-backend/accounts/views.py:336) `VaiTroViewSet` | [admin/api/admin.api.ts:246](moc-frontend/src/admin/api/admin.api.ts:246) |
| GET / PUT | `/roles/{id}/permissions/` | [accounts/views.py:342](moc-backend/accounts/views.py:342) | [admin/api/admin.api.ts:247-248](moc-frontend/src/admin/api/admin.api.ts:247) |
| CRUD | `/permissions/` | [accounts/views.py:374](moc-backend/accounts/views.py:374) `QuyenHanViewSet` | — |

- `admin_create` nhận body `{ email, password, name, role, phone, branch_id, active }` và trả về `NguoiDung`.
  - `role` nhận một trong: `admin` | `branch_manager` | `staff` | `customer`. Backend cũng chấp nhận tên vai trò tiếng Việt (`quan_tri_vien`, `quan_ly_chi_nhanh`, `nhan_vien_ban_hang`, `khach_hang`).
  - Khi người tạo là quản lý chi nhánh, backend luôn đặt `role=staff` và gán vào chi nhánh của quản lý đó.
- `admin_update` nhận cùng các trường như `admin_create`, gửi trường nào thì sửa trường đó.
- Đây là **chỗ duy nhất** body dùng tên tiếng Anh: không có bản tiếng Việt nào trùng nghĩa nên giữ nguyên.

---

## 4. Món ăn & Kho — app `foods`

Route: [api/urls.py:37-47](moc-backend/api/urls.py:37). `foods`, `categories` và `tags` tra cứu theo **slug** (`duong_dan`), không theo id.

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| CRUD | `/foods/{slug}/` (= `/mon-an/`) | Đọc public / Ghi staff | [foods/views.py:194](moc-backend/foods/views.py:194) `MonAnViewSet` | [foods.api.ts:33](moc-frontend/src/api/foods.api.ts:33), [foods.api.ts:43](moc-frontend/src/api/foods.api.ts:43), [admin/api/admin.api.ts:157](moc-frontend/src/admin/api/admin.api.ts:157) |
| POST | `/foods/import-file/` (multipart, trường `file`) | Staff | [foods/views.py:199](moc-backend/foods/views.py:199) `import_file` | [admin/api/admin.api.ts:161](moc-frontend/src/admin/api/admin.api.ts:161) |
| GET | `/foods/{slug}/mon_lien_quan/?gioi_han=3` | Public | [foods/views.py:465](moc-backend/foods/views.py:465) | — (chưa dùng) |
| CRUD | `/categories/{slug}/` (= `/danh-muc/`) | Đọc public / Ghi staff | [foods/views.py:98](moc-backend/foods/views.py:98) `DanhMucViewSet` | [foods.api.ts:62](moc-frontend/src/api/foods.api.ts:62), [admin/api/admin.api.ts:164](moc-frontend/src/admin/api/admin.api.ts:164) |
| CRUD | `/tags/{slug}/` (= `/the-mon-an/`) | Đọc public / Ghi staff | [foods/views.py:105](moc-backend/foods/views.py:105) `TheMonAnViewSet` | [admin/api/admin.api.ts:165](moc-frontend/src/admin/api/admin.api.ts:165) |
| CRUD | `/ingredients/` (= `/nguyen-lieu/`) | Đọc public / Ghi staff | [foods/views.py:112](moc-backend/foods/views.py:112) `NguyenLieuViewSet` | [admin/api/admin.api.ts:166](moc-frontend/src/admin/api/admin.api.ts:166) |
| GET / POST | `/inventory-transactions/` (= `/kho/`), không cho sửa/xoá | Staff | [foods/views.py:130](moc-backend/foods/views.py:130) `LichSuKhoViewSet` | [admin/api/admin.api.ts:212](moc-frontend/src/admin/api/admin.api.ts:212) |
| CRUD | `/dinh-muc-nguyen-lieu/` | Staff | [foods/views.py:179](moc-backend/foods/views.py:179) `DinhMucNguyenLieuViewSet` | [admin/api/admin.api.ts:218-220](moc-frontend/src/admin/api/admin.api.ts:218) |

**Query lọc**

- **`/foods/`** ([foods/views.py:424](moc-backend/foods/views.py:424)):
  - `danh_muc` (slug hoặc id), `tim_kiem`;
  - `la_mon_chay=true`, `con_hang=true`, `co_cay=true`, `gia_toi_da`;
  - `sap_xep`.
- **`/inventory-transactions/`**: `nguyen_lieu`, `loai_giao_dich` (`nhap` | `xuat` | `dieu_chinh`).
- **`/dinh-muc-nguyen-lieu/`**: `nguyen_lieu`, `mon_an`.

**Body / trả về**

- **`MonAn`**: các cột của model, cộng thêm:
  - `the_mon_an`: mảng slug;
  - `don_gia_hien_tai`: chỉ đọc;
  - chỉ đọc: `duong_dan`, `diem_danh_gia`, `so_luot_danh_gia`.
- **`NguyenLieu`**: các cột của model, cộng thêm `so_mon_dinh_muc` và `sap_het`.
- **Phiếu kho**:
  - Body: `{ nguyen_lieu, loai_giao_dich, so_luong, ghi_chu }`.
  - Trả thêm `ten_nguyen_lieu`, `don_vi`, `ten_nguoi_tao`, `ton_kho_truoc`, `ton_kho_sau`.
- **Định mức**:
  - Body: `{ mon_an, nguyen_lieu, so_luong_can }`.
  - Trả thêm `ten_mon`, `ten_nguyen_lieu`, `don_vi`.
- **File import** (CSV/Excel): các cột tiêu đề **tiếng Anh**, gồm `name`, `category`, `price`, `stock`, `spicy`, `description`, `vegetarian`, `available`, `image_url`. Đây là định dạng file, không phải API.

---

## 5. Chi nhánh — app `branches`

Route: [api/urls.py:50-51](moc-backend/api/urls.py:50)

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| CRUD | `/branches/` (= `/chi-nhanh/`) | Đọc public / Ghi staff | [branches/views.py:11](moc-backend/branches/views.py:11) `ChiNhanhViewSet` | [locations.api.ts:5](moc-frontend/src/api/locations.api.ts:5), [reservations.api.ts:27](moc-frontend/src/api/reservations.api.ts:27), [admin/api/admin.api.ts:176](moc-frontend/src/admin/api/admin.api.ts:176) |
| GET | `/branches/nearest/` (= `/branches/tim-gan-nhat/`) | Public | [branches/views.py:81](moc-backend/branches/views.py:81) | — |

- **Query**:
  - `vi_do`, `kinh_do`: khi có, danh sách được sắp theo khoảng cách;
  - `ban_kinh`, `so_luong`;
  - `all=true` (chỉ cho `nearest`): trả mảng thay vì một chi nhánh.
- **`ChiNhanh`** ([branches/serializers.py:5](moc-backend/branches/serializers.py:5)) gồm:
  - `id`, `ten`, `dia_chi`, `so_dien_thoai`, `toa_do_gis`, `kinh_do`, `vi_do`, `con_hoat_dong`, `tao_luc`, `cap_nhat_luc`;
  - `khoang_cach_km` và `khoang_cach_m`: chỉ có giá trị khi gửi toạ độ, ngược lại là `null`.
- **Tạo/sửa**: gửi `vi_do` và `kinh_do`; backend tự dựng `toa_do_gis`.

---

## 6. Bàn, Phòng, Đặt bàn, Phiên phục vụ — app `reservations`

Route: [api/urls.py:54-60](moc-backend/api/urls.py:54)

**Bàn & phòng riêng**

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| CRUD | `/tables/` (= `/ban-an/`) | Đọc public / Ghi staff | [reservations/views.py:23](moc-backend/reservations/views.py:23) `BanAnViewSet` | [reservations.api.ts:17](moc-frontend/src/api/reservations.api.ts:17), [admin/api/admin.api.ts:74-95](moc-frontend/src/admin/api/admin.api.ts:74) |
| CRUD | `/rooms/` | Đọc public / Ghi staff | [reservations/views.py:99](moc-backend/reservations/views.py:99) `PhongRiengViewSet` | [admin/api/admin.api.ts:78-87](moc-frontend/src/admin/api/admin.api.ts:78) |

- **Body bàn**: `{ chi_nhanh, so_ban, khu_vuc, suc_chua, trang_thai, phong_rieng }`. Response có thêm `phien_phuc_vu_hien_tai`.
- **Query bàn**: `chi_nhanh`, `include_archived=true` (chỉ staff); để lọc bàn trống còn có `guest_count`, `reservation_date`, `start_time`.
- **Body phòng**: `{ chi_nhanh, ten_phong, tang, suc_chua, con_hoat_dong }`.
- **Query phòng**: `chi_nhanh`, `include_inactive=true`.

**Đặt bàn**: `DatBanViewSet` ([reservations/views.py:146](moc-backend/reservations/views.py:146)), quyền xác định ở `get_permissions` ([reservations/views.py:166](moc-backend/reservations/views.py:166)). Route: `/reservations/` = `/dat-ban/`.

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| GET | `/reservations/` (`?mine=1` = của tôi) | User (staff thấy theo chi nhánh) | [reservations/views.py:149](moc-backend/reservations/views.py:149) `get_queryset` | [reservations.api.ts:138](moc-frontend/src/api/reservations.api.ts:138), [admin/api/admin.api.ts:59](moc-frontend/src/admin/api/admin.api.ts:59) |
| POST | `/reservations/` | User | [reservations/views.py:181](moc-backend/reservations/views.py:181) `create` | [reservations.api.ts:128](moc-frontend/src/api/reservations.api.ts:128) `taoDatBan` |
| GET | `/reservations/{id}/` | User | (CRUD chuẩn) | [reservations.api.ts:133](moc-frontend/src/api/reservations.api.ts:133) |
| PATCH | `/reservations/{id}/` | Staff | (CRUD chuẩn) | [admin/api/admin.api.ts:202](moc-frontend/src/admin/api/admin.api.ts:202) |
| GET | `/reservations/khung-gio-trong/` | Public | [reservations/views.py:363](moc-backend/reservations/views.py:363) | [reservations.api.ts:49](moc-frontend/src/api/reservations.api.ts:49) |
| GET / PUT | `/reservations/chinh_sach_coc/` | GET public, PUT staff | [reservations/views.py:214](moc-backend/reservations/views.py:214) | [reservations.api.ts:65](moc-frontend/src/api/reservations.api.ts:65), [admin/api/admin.api.ts:190-193](moc-frontend/src/admin/api/admin.api.ts:190) |
| POST | `/reservations/{id}/cancel/` (= `/huy_dat_ban/`) | User | [reservations/views.py:248](moc-backend/reservations/views.py:248) | [api/admin.api.ts:75](moc-frontend/src/api/admin.api.ts:75) |
| PATCH | `/reservations/{id}/trang_thai/` | Staff | [reservations/views.py:280](moc-backend/reservations/views.py:280) | [admin/api/admin.api.ts:200](moc-frontend/src/admin/api/admin.api.ts:200), [api/admin.api.ts:66](moc-frontend/src/api/admin.api.ts:66) |
| POST | `/reservations/{id}/check-in/` | Staff | [reservations/views.py:304](moc-backend/reservations/views.py:304) | [admin/api/admin.api.ts:109](moc-frontend/src/admin/api/admin.api.ts:109) |
| POST | `/reservations/{id}/seat/` | Staff | [reservations/views.py:315](moc-backend/reservations/views.py:315) | [admin/api/admin.api.ts:115](moc-frontend/src/admin/api/admin.api.ts:115) |
| POST | `/reservations/{id}/record-refund/` | Staff | [reservations/views.py:327](moc-backend/reservations/views.py:327) | [admin/api/admin.api.ts:204](moc-frontend/src/admin/api/admin.api.ts:204) |

**Body / trả về của đặt bàn**

| Endpoint | Body / query | Trả về |
|---|---|---|
| POST `/reservations/` | Các trường:<br>• `chi_nhanh`, `ngay_dat` (YYYY-MM-DD), `gio_bat_dau` (HH:MM), `so_luong_khach`<br>• `hinh_thuc`<br>• `danh_sach_mon: [{ mon_an_id, so_luong }]`<br>• `ten_khach`, `sdt_khach`, `ghi_chu`<br>• `ban_an` (tuỳ chọn) | `201 DatBan` |
| GET `khung-gio-trong` | `?chi_nhanh_id=&ngay=YYYY-MM-DD&so_khach=1..12` | `{ chi_nhanh_id, ten_chi_nhanh, ngay, slots: [{ khung_gio, con_trong, so_khach_hien_tai, suc_chua_toi_da, so_cho_con_lai }] }` |
| GET `chinh_sach_coc` | `?branch=<id>` (tuỳ chọn) | `ChinhSachDatCoc` kèm danh sách quy tắc huỷ |
| PUT `chinh_sach_coc` | Các cột của `ChinhSachDatCoc`, kèm `quy_tac_huy: [{ moc_thoi_gian, phan_tram_hoan_tien }]` | Chính sách sau khi lưu |
| POST `cancel` | `{ ly_do, is_no_show }` (`is_no_show` chỉ staff dùng được) | Kết quả hoàn cọc, kèm `dat_ban` |
| PATCH `trang_thai` | `{ status, version, ghi_chu }` (`version` = `phien_ban` để chống ghi đè) | `DatBan` |
| POST `check-in` | `{ version }` | `DatBan` |
| POST `seat` | `{ ban_an }` | Phiên phục vụ vừa mở |
| POST `record-refund` | `{ percent, reference, bucket, note }` | `DatBan` (có `refund_record`) |

**Các trường của `DatBan`** ([reservations/serializers.py:104](moc-backend/reservations/serializers.py:104))

- **Cột của model:**
  - `ma_dat_ban`, `chi_nhanh`, `ban_an`, `ngay_dat`, `gio_bat_dau`, `gio_ket_thuc`, `so_luong_khach`;
  - `hinh_thuc`, `trang_thai`;
  - `yeu_cau_dat_coc`, `so_tien_coc`, `trang_thai_coc`, `thanh_toan_coc_luc`;
  - `check_in_luc`, `ten_khach`, `sdt_khach`, `ghi_chu`;
  - `huy_luc`, `ly_do_huy`, `phien_ban`.
- **Trường tính thêm:**
  - `so_ban`, `ten_ban`, `ban_an_id`, `ten_chi_nhanh`;
  - `danh_sach_mon` (`[{ id, mon_an_id, mon_an, so_luong, don_gia_luc_dat }]`);
  - `phien_phuc_vu_id`, `don_hang_id`, `ma_don_hang`;
  - `refund_record` (`{ percent, amount, reference, note, at, by }` hoặc `null`).

> Body của `trang_thai` và `record-refund`, cùng nội dung của `refund_record`, vẫn dùng tên tiếng Anh vì không có bản tiếng Việt trùng nghĩa.

**Phiên phục vụ (tại bàn)**: `PhienPhucVuViewSet` ([reservations/views.py:428](moc-backend/reservations/views.py:428)) chỉ cho đọc và gọi action, toàn bộ cần **Staff**. Route: `/dining-sessions/` = `/phien-phuc-vu/`.

| Method | Endpoint | Body | Backend | Frontend gọi |
|---|---|---|---|---|
| GET | `/dining-sessions/`, `/dining-sessions/{id}/` | Query `chi_nhanh`, `ban_an`, `trang_thai` | [reservations/views.py:434](moc-backend/reservations/views.py:434) | [admin/api/admin.api.ts:97](moc-frontend/src/admin/api/admin.api.ts:97), [:101](moc-frontend/src/admin/api/admin.api.ts:101) |
| POST | `/dining-sessions/walk-in/` | `{ ban_an, so_luong_khach, ten_khach, sdt_khach, ghi_chu }` | [reservations/views.py:459](moc-backend/reservations/views.py:459) | [admin/api/admin.api.ts:105](moc-frontend/src/admin/api/admin.api.ts:105) |
| POST | `/dining-sessions/from-reservation/` | `{ dat_ban, ban_an }` | [reservations/views.py:475](moc-backend/reservations/views.py:475) | — |
| POST / PUT | `/dining-sessions/{id}/items/` (POST thêm món, PUT thay toàn bộ) | `{ danh_sach_mon: [{ mon_an_id, so_luong, ghi_chu }] }` | [reservations/views.py:491](moc-backend/reservations/views.py:491) | [admin/api/admin.api.ts:119](moc-frontend/src/admin/api/admin.api.ts:119), [:131](moc-frontend/src/admin/api/admin.api.ts:131) |
| POST | `/dining-sessions/{id}/cancel/` (huỷ bàn) | `{ ly_do }` | [reservations/views.py:516](moc-backend/reservations/views.py:516) | [admin/api/admin.api.ts:144](moc-frontend/src/admin/api/admin.api.ts:144) |
| GET | `/dining-sessions/canh-bao-kho/` | — | [reservations/views.py:527](moc-backend/reservations/views.py:527) | [admin/api/admin.api.ts:149](moc-frontend/src/admin/api/admin.api.ts:149) |
| POST | `/dining-sessions/{id}/move-table/` | `{ ban_an }` | [reservations/views.py:535](moc-backend/reservations/views.py:535) | [admin/api/admin.api.ts:135](moc-frontend/src/admin/api/admin.api.ts:135) |
| POST | `/dining-sessions/{id}/checkout/` | `{ phuong_thuc, ma_tham_chieu }` | [reservations/views.py:545](moc-backend/reservations/views.py:545) | [admin/api/admin.api.ts:139](moc-frontend/src/admin/api/admin.api.ts:139) |
| POST | `/dining-sessions/{id}/confirm-cleaned/` | — | [reservations/views.py:558](moc-backend/reservations/views.py:558) | [admin/api/admin.api.ts:153](moc-frontend/src/admin/api/admin.api.ts:153) |

**`PhienPhucVu`** ([reservations/serializers.py:207](moc-backend/reservations/serializers.py:207)) gồm các cột của model, cộng thêm `so_ban`, `ten_ban`, `don_hang_id`, `ma_don_hang` và `tien_coc_da_tra`. Riêng `items` trả thêm `canh_bao_kho`.

---

## 7. Đơn hàng — app `orders`

`DonHangViewSet` ([orders/views.py:13](moc-backend/orders/views.py:13)) · Route: `/orders/` = `/don-hang/` ([api/urls.py:63-64](moc-backend/api/urls.py:63)). **Không có POST tạo đơn** (`http_method_names` [orders/views.py:16](moc-backend/orders/views.py:16)); đơn được sinh ra từ phiên phục vụ.

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| GET / PUT / PATCH / DELETE | `/orders/`, `/orders/{id}/` | User (staff thấy theo chi nhánh) | [orders/views.py:41](moc-backend/orders/views.py:41) `get_queryset` | [admin/api/admin.api.ts:48](moc-frontend/src/admin/api/admin.api.ts:48) `ordersStore` |
| PATCH | `/orders/{id}/status/` (= `/trang_thai/`, `/chuyen_trang_thai/`, `/cap_nhat_trang_thai/`) | User | [orders/views.py:72](moc-backend/orders/views.py:72) `trang_thai` | [admin/api/admin.api.ts:196](moc-frontend/src/admin/api/admin.api.ts:196) |

- **Body `status`**: backend nhận cả `trang_thai` lẫn `status`/`to_status`, cả `ghi_chu` lẫn `note`. Frontend hiện gửi `{ status, note }`.
- **`DonHang`** gồm:
  - các cột của model;
  - `ma_khuyen_mai`;
  - `danh_sach_mon: [{ id, mon_an_id, mon_an, don_gia_luc_dat, so_luong, thanh_tien, ghi_chu }]`;
  - `lich_su_trang_thai: [{ tu_trang_thai, sang_trang_thai, ghi_chu, tao_luc }]`.

---

## 8. Thanh toán — app `payments`

`ThanhToanViewSet` ([payments/views.py:24](moc-backend/payments/views.py:24)), quyền xác định ở `get_permissions` ([payments/views.py:28](moc-backend/payments/views.py:28)). Route: `/payments/` = `/thanh-toan/` ([api/urls.py:67-70](moc-backend/api/urls.py:67)); các route VNPay khai báo tường minh ở [api/urls.py:114-121](moc-backend/api/urls.py:114).

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| CRUD | `/payments/` | User (staff thấy tất cả) | [payments/views.py:43](moc-backend/payments/views.py:43) | [admin/api/admin.api.ts:178-180](moc-frontend/src/admin/api/admin.api.ts:178) |
| POST | `/payments/{id}/mark_success/` (= `/xac_nhan_thanh_cong/`) | Staff | [payments/views.py:82](moc-backend/payments/views.py:82) | [admin/api/admin.api.ts:22](moc-frontend/src/admin/api/admin.api.ts:22) |
| POST | `/payments/vnpay/create/` (= `/vnpay/tao-phien/`) | User | [payments/views.py:102](moc-backend/payments/views.py:102) `vnpay_create` | [reservations.api.ts:145](moc-frontend/src/api/reservations.api.ts:145) |
| GET | `/payments/vnpay/return/` | Public (VNPay chuyển hướng về) | [payments/views.py:161](moc-backend/payments/views.py:161) | — (VNPay gọi) |
| GET | `/payments/vnpay/ipn/` | Public (webhook của VNPay) | [payments/views.py:176](moc-backend/payments/views.py:176) | — (VNPay gọi) |
| GET | `/refund-receipts/` (= `/phieu-hoan-tien/`), chỉ đọc | User | [payments/views.py:182](moc-backend/payments/views.py:182) `PhieuHoanTienViewSet` | — |

- **Tạo hoá đơn** (`POST /payments/`): body `{ don_hang | dat_ban, loai_thanh_toan, phuong_thuc, so_tien }`. `so_tien` phải đúng bằng số tiền phải trả.
- **`vnpay/create`**:
  - Body: `{ loai_thanh_toan: "tien_coc" | "don_hang", dat_ban_id | don_hang_id, so_tien?, order_info?, ip_addr? }`.
  - Trả về: `{ duong_dan_thanh_toan, ma_giao_dich, so_tien, het_han_luc, thanh_toan_id }`.
- **`vnpay/return`**: chuyển hướng về frontend kèm `?status=<kết quả>`.
- **`vnpay/ipn`**: trả `{ RspCode, Message }` theo chuẩn VNPay. Tham số `vnp_*` do VNPay đặt tên.

---

## 9. Khuyến mãi — app `promotions`

Route: [api/urls.py:73-76](moc-backend/api/urls.py:73)

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| CRUD | `/promotions/` (= `/khuyen-mai/`), `?con_han=1` để lọc khuyến mãi còn hạn | Đọc public / Ghi staff | [promotions/views.py:11](moc-backend/promotions/views.py:11) `KhuyenMaiViewSet` | [promotions.api.ts:6](moc-frontend/src/api/promotions.api.ts:6), [admin/api/admin.api.ts:167](moc-frontend/src/admin/api/admin.api.ts:167) |
| CRUD | `/promotion-codes/` | Đọc public / Ghi staff | [promotions/views.py:23](moc-backend/promotions/views.py:23) `MaKhuyenMaiViewSet` | — |
| GET | `/promotion-usages/`, chỉ đọc | Staff | [promotions/views.py:29](moc-backend/promotions/views.py:29) | — |

**Body `KhuyenMai`** (`so_lan_da_dung` chỉ đọc; response có thêm `danh_sach_ma`):

- `ma_giam_gia`, `ten`, `mo_ta`;
- `kieu_giam` (`phan_tram` | `so_tien_co_dinh`), `gia_tri_giam`;
- `don_hang_toi_thieu`, `giam_toi_da`;
- `bat_dau_luc`, `ket_thuc_luc`;
- `gioi_han_su_dung`, `con_hoat_dong`.

---

## 10. Đánh giá — app `reviews`

`DanhGiaViewSet` ([reviews/views.py:11](moc-backend/reviews/views.py:11)) · Route: `/reviews/` = `/danh-gia/` ([api/urls.py:79-80](moc-backend/api/urls.py:79)). Quyền đặt ở [reviews/views.py:14](moc-backend/reviews/views.py:14): ai cũng đọc được, tạo/sửa/xoá cần đăng nhập, staff có toàn quyền.

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| GET | `/reviews/?mon_an={id}` | Public | [reviews/views.py:21](moc-backend/reviews/views.py:21) `get_queryset` | [reviews.api.ts:6](moc-frontend/src/api/reviews.api.ts:6) |
| GET | `/reviews/?mine=1` (gồm cả đánh giá bị ẩn của mình) | User | [reviews/views.py:26](moc-backend/reviews/views.py:26) | [reviews.api.ts:11](moc-frontend/src/api/reviews.api.ts:11) |
| POST | `/reviews/` | User | (CRUD chuẩn) | [reviews.api.ts:17](moc-frontend/src/api/reviews.api.ts:17) |
| PATCH / DELETE | `/reviews/{id}/` (ẩn/hiện, xoá) | Staff | (CRUD chuẩn) | [admin/api/admin.api.ts:169](moc-frontend/src/admin/api/admin.api.ts:169), [api/admin.api.ts:207-212](moc-frontend/src/api/admin.api.ts:207) |

- **Body**: `{ mon_an, diem_danh_gia, nhan_xet, don_hang?, chi_tiet_don_hang? }`. Staff gửi `{ hien_thi }` để ẩn/hiện.
- **Response** có thêm `ten_nguoi_dung` và `food_name` (tên tiếng Anh còn sót lại, xem mục 19).

---

## 11. Bài viết — app `posts`

Route: [api/urls.py:83-86](moc-backend/api/urls.py:83). Tra cứu theo **slug** (`duong_dan`).

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| CRUD | `/posts/{slug}/` (= `/bai-viet/`), `?tim_kiem=` | Đọc public / Ghi staff | [posts/views.py:14](moc-backend/posts/views.py:14) `BaiVietViewSet` | [blog.api.ts:6](moc-frontend/src/api/blog.api.ts:6), [blog.api.ts:11](moc-frontend/src/api/blog.api.ts:11), [admin/api/admin.api.ts:168](moc-frontend/src/admin/api/admin.api.ts:168) |
| CRUD | `/post-categories/{slug}/` (= `/danh-muc-bai-viet/`) | Đọc public / Ghi staff | [posts/views.py:7](moc-backend/posts/views.py:7) | — |

- **Body**: `{ tieu_de, danh_muc, noi_dung, anh_dai_dien, trang_thai }`, với `trang_thai` là `nhap` | `da_dang` | `luu_tru`.
- **Response** có thêm `ten_danh_muc` và `ten_tac_gia`.

---

## 12. Chat — app `chat`

`HoiThoaiViewSet` ([chat/views.py:21](moc-backend/chat/views.py:21)) · Route: `/chat/conversations/` = `/chat/rooms/` = `/hoi-thoai/` ([api/urls.py:89-91](moc-backend/api/urls.py:89)). Quyền: User; staff có toàn quyền ([chat/views.py:27](moc-backend/chat/views.py:27)).

| Method | Endpoint | Backend | Frontend gọi |
|---|---|---|---|
| GET / PATCH | `/chat/conversations/`, `/chat/conversations/{id}/` | [chat/views.py:32](moc-backend/chat/views.py:32) `get_queryset` | [useChatInbox.ts:61](moc-frontend/src/hooks/useChatInbox.ts:61), [ChatPage.tsx:76](moc-frontend/src/admin/pages/ChatPage.tsx:76) |
| GET | `/chat/conversations/active/` | [chat/views.py:51](moc-backend/chat/views.py:51) | [useWebSocketChat.ts:192](moc-frontend/src/hooks/useWebSocketChat.ts:192) |
| GET / POST | `/chat/conversations/{id}/messages/` | [chat/views.py:71](moc-backend/chat/views.py:71) | [useWebSocketChat.ts:154](moc-frontend/src/hooks/useWebSocketChat.ts:154), [:358](moc-frontend/src/hooks/useWebSocketChat.ts:358) |
| POST | `/chat/conversations/{id}/gui_tin_nhan/` | [chat/views.py:67](moc-backend/chat/views.py:67) | — |
| POST | `/chat/conversations/{id}/mark_read/` | [chat/views.py:98](moc-backend/chat/views.py:98) | [admin/api/admin.api.ts:22](moc-frontend/src/admin/api/admin.api.ts:22) |

- **`messages` POST**: body `{ noi_dung, loai_tin_nhan: "van_ban" | "hinh_anh" | "he_thong", client_id }`.
- **`messages` GET**: phân trang bằng `?after_id=` hoặc `?before_id=`.
- **`TinNhan`** gồm các cột của model, cộng thêm `sender_name` và `is_staff`.
- **Danh sách hội thoại**: `{ id, customer_name, trang_thai, tin_nhan_cuoi_luc, last_message, unread_count }`.

---

## 13. Gợi ý món — app `recommendations`

Route: [api/urls.py:94-97](moc-backend/api/urls.py:94) và các route tường minh ở [api/urls.py:124-128](moc-backend/api/urls.py:124)

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| GET | `/recommendations/?limit=` (= `/goi-y/`) | Public | [recommendations/views.py:66](moc-backend/recommendations/views.py:66) `list` | [recommendations.api.ts:24](moc-frontend/src/api/recommendations.api.ts:24) |
| GET | `/recommendations/tuong-tu/?mon_an=&limit=` | Public | [recommendations/views.py:110](moc-backend/recommendations/views.py:110) | [recommendations.api.ts:34](moc-frontend/src/api/recommendations.api.ts:34) |
| POST | `/recommendations/su-kien/` | Public | [recommendations/views.py:120](moc-backend/recommendations/views.py:120) | [recommendations.api.ts:57](moc-frontend/src/api/recommendations.api.ts:57) |
| GET / POST | `/recommendations/refresh/` (= `/lam-moi/`) | User | [recommendations/views.py:97](moc-backend/recommendations/views.py:97) | — |
| GET / POST | `/interactions/` (= `/tuong-tac/`, `/recommendations/tuong-tac/`) | User | [recommendations/views.py:18](moc-backend/recommendations/views.py:18) `TuongTacMonAnViewSet` | [recommendations.api.ts:45](moc-frontend/src/api/recommendations.api.ts:45) |

- **`GoiYMonAn`** gồm:
  - `id`, `nguoi_dung`, `mon_an`;
  - `diem_tuong_dong`, `ly_do_goi_y`, `phien_ban_model`;
  - `is_cold_start`;
  - `chi_tiet_mon` và `chi_tiet_mon_an`;
  - `tao_luc`.
- **Body `su-kien`**: `{ loai_su_kien: "hien_thi" | "nhap", vi_tri, mon_an_ids: [id], phien_ban_model }`.
- **Body tương tác**: `{ mon_an, loai_tuong_tac }`. Backend tự tính `trong_so`.

---

## 14. Thống kê & Thông báo — app `analytics`

| Method | Endpoint | Quyền | Backend | Frontend gọi |
|---|---|---|---|---|
| GET | `/analytics/dashboard/?days=1..90` | Staff | [analytics/views.py:47](moc-backend/analytics/views.py:47) `DashboardViewSet.list` | [admin/api/admin.api.ts:234](moc-frontend/src/admin/api/admin.api.ts:234) |
| GET | `/analytics/ai/` | Staff | `DashboardViewSet.ai` · route [api/urls.py:110](moc-backend/api/urls.py:110) | [admin/api/admin.api.ts:242](moc-frontend/src/admin/api/admin.api.ts:242) |
| GET / PUT | `/analytics/settings/` | Staff | `DashboardViewSet.restaurant_settings` · route [api/urls.py:111](moc-backend/api/urls.py:111) | [admin/api/admin.api.ts:244-245](moc-frontend/src/admin/api/admin.api.ts:244) |
| CRUD | `/notifications/` (= `/thong-bao/`), chỉ thông báo của mình | User | [analytics/views.py:21](moc-backend/analytics/views.py:21) `ThongBaoViewSet` | — |
| POST | `/notifications/{id}/read/` (= `/da_doc/`) | User | [analytics/views.py:31](moc-backend/analytics/views.py:31) | — |

- **`dashboard`** trả về các trường tiếng Việt `doanh_thu`, `so_don_hang`, `so_dat_ban`, `so_khach_hang`, `don_hang_theo_trang_thai`, cùng khối "Lúc này" (`today_revenue`, `range_revenue`…).
- **`ai`** trả về `{ overview, positions, top, recent }`.
- **`settings`** nhận và trả về `{ name, email, weekday, weekend }`.
- Các khối thống kê này là JSON tự dựng cho trang admin và còn dùng tên tiếng Anh, xem mục 19.

---

## 15. WebSocket (Django Channels)

Route được gom ở [config/routing.py](moc-backend/config/routing.py) và nạp trong [config/asgi.py](moc-backend/config/asgi.py). Xác thực bằng `?token=<access>`, do frontend tự gắn trong [services/websocket.ts](moc-frontend/src/services/websocket.ts).

| Endpoint | Consumer | Khai báo | Frontend dùng |
|---|---|---|---|
| `ws/chat/inbox/` | `InboxConsumer` (staff nhận tin mới) | [chat/routing.py:5](moc-backend/chat/routing.py:5) | [useChatInbox.ts:88](moc-frontend/src/hooks/useChatInbox.ts:88) |
| `ws/chat/{conversation_id}/` (= `ws/hoi-thoai/{id}/`) | `ChatConsumer` | [chat/routing.py:6-7](moc-backend/chat/routing.py:6) | [useWebSocketChat.ts:225](moc-frontend/src/hooks/useWebSocketChat.ts:225) |
| `ws/orders/staff/` (= `ws/don-hang/nhan-vien/`) | `StaffOrderConsumer` | [orders/routing.py:6-7](moc-backend/orders/routing.py:6) | [useStaffOrderStream.ts:48](moc-frontend/src/hooks/useStaffOrderStream.ts:48) |
| `ws/orders/{order_id}/` (= `ws/don-hang/{id}/`) | `OrderTrackingConsumer` | [orders/routing.py:10-11](moc-backend/orders/routing.py:10) | — |

---

## 16. Bản đồ file frontend

| File | Vai trò |
|---|---|
| [src/api/client.ts](moc-frontend/src/api/client.ts) | Tạo instance axios, lưu token, tự làm mới token |
| [src/api/auth.api.ts](moc-frontend/src/api/auth.api.ts) | Đăng nhập, đăng ký, xác thực email, hồ sơ, đổi mật khẩu |
| [src/api/foods.api.ts](moc-frontend/src/api/foods.api.ts) | Món ăn và danh mục (trang khách) |
| [src/api/reservations.api.ts](moc-frontend/src/api/reservations.api.ts) | Bàn, khung giờ, đặt bàn, cọc VNPay |
| [src/api/reviews.api.ts](moc-frontend/src/api/reviews.api.ts) | Đánh giá |
| [src/api/recommendations.api.ts](moc-frontend/src/api/recommendations.api.ts) | Gợi ý món, ghi tương tác và sự kiện |
| [src/api/blog.api.ts](moc-frontend/src/api/blog.api.ts) · [promotions.api.ts](moc-frontend/src/api/promotions.api.ts) · [locations.api.ts](moc-frontend/src/api/locations.api.ts) | Bài viết · khuyến mãi · chi nhánh |
| [src/api/mappers.ts](moc-frontend/src/api/mappers.ts) | Chuyển JSON backend sang type frontend (`MonAn`, `ChiNhanh`, `ThongTinDatBan`…) |
| [src/types/index.ts](moc-frontend/src/types/index.ts), [src/types/auth.ts](moc-frontend/src/types/auth.ts) | Type tiếng Việt dùng ở trang khách |
| [src/admin/api/admin.api.ts](moc-frontend/src/admin/api/admin.api.ts) | API cho trang quản trị mới (`src/admin/*`) |
| [src/api/admin.api.ts](moc-frontend/src/api/admin.api.ts) | API cho trang quản trị cũ (`src/pages/admin/*`) |

---

## 17. Trường dữ liệu & giá trị enum

Các ViewSet dùng `fields = "__all__"` sẽ nhận và trả **đúng các cột dưới đây**. Mọi model đều có `id`, `tao_luc` và `cap_nhat_luc`.

| Model | Cột chính |
|---|---|
| `BanAn` | `chi_nhanh`, `so_ban`, `khu_vuc`, `suc_chua`, `trang_thai`, `da_luu_tru`, `phong_rieng` |
| `PhongRieng` | `chi_nhanh`, `ten_phong`, `tang`, `suc_chua`, `con_hoat_dong` |
| `ChinhSachDatCoc` | `chi_nhanh`, `phan_tram_coc`, `thoi_gian_giu_cho_phut`, `han_thanh_toan_phut`, `so_dien_thoai_lien_he`, `noi_dung_huong_dan`, `con_ap_dung` |
| `MonAn` | `danh_muc`, `ten`, `duong_dan`, `mo_ta_ngan`, `mo_ta_chi_tiet`, `don_gia`, `ton_kho_cache`, `con_hang`, `hien_thi`, `noi_bat`, `la_mon_chay`, `do_cay`, `quan_ly_kho`, `diem_danh_gia`, `so_luot_danh_gia` |
| `DanhMuc` | `ten`, `duong_dan`, `mo_ta`, `anh_dai_dien`, `con_hoat_dong` |
| `NguyenLieu` | `ten`, `don_vi`, `ton_kho_hien_tai`, `ton_kho_toi_thieu`, `con_hoat_dong` |
| `DonHang` | `ma_don_hang`, `khach_hang`, `chi_nhanh`, `dat_ban`, `phien_phuc_vu`, `hinh_thuc`, `trang_thai`, `ten_khach`, `sdt_khach`, `ghi_chu`, `tien_hang`, `tien_giam`, `tong_tien`, `khuyen_mai` |
| `ThanhToan` | `nguoi_dung`, `don_hang`, `dat_ban`, `loai_thanh_toan`, `phuong_thuc`, `so_tien`, `ma_giao_dich`, `trang_thai`, `thanh_toan_luc`, `hoan_tien_luc` |
| `PhieuHoanTien` | `ma_phieu_hoan`, `dat_ban`, `thanh_toan`, `so_tien_coc_goc`, `phan_tram_hoan`, `so_tien_hoan`, `so_tien_phat`, `moc_thoi_gian`, `so_gio_truoc_gio_hen`, `ly_do_huy`, `trang_thai`, `phuong_thuc_hoan`, `du_lieu_chi_tiet` |
| `MaKhuyenMai` | `khuyen_mai`, `ma`, `gioi_han`, `da_dung`, `con_hoat_dong` |
| `DanhGia` | `nguoi_dung`, `mon_an`, `don_hang`, `chi_tiet_don_hang`, `diem_danh_gia`, `nhan_xet`, `hien_thi` |
| `BaiViet` | `danh_muc`, `tac_gia`, `tieu_de`, `duong_dan`, `anh_dai_dien`, `noi_dung`, `trang_thai`, `dang_luc` |
| `HoiThoai` / `TinNhan` | `khach_hang`, `nhan_vien`, `trang_thai`, `tin_nhan_cuoi_luc` / `hoi_thoai`, `nguoi_gui`, `loai_tin_nhan`, `noi_dung`, `da_doc`, `doc_luc` |
| `ThongBao` | `nguoi_dung`, `loai`, `tieu_de`, `noi_dung`, `loai_tham_chieu`, `id_tham_chieu`, `da_doc`, `doc_luc` |

**Giá trị enum**

| Trường | Giá trị |
|---|---|
| `DatBan.hinh_thuc` | `chi_giu_cho` · `dat_ban_va_goi_mon` · `dat_ban_goi_mon_chinh_sua` |
| `DatBan.trang_thai` | `cho_xac_nhan` · `cho_thanh_toan` · `da_xac_nhan` · `khach_da_den` · `hoan_tat` · `da_huy` · `khach_khong_den` |
| `DatBan.trang_thai_coc` | `chua_thanh_toan` · `dang_xu_ly` · `thanh_cong` · `that_bai` · `da_hoan_tien` · `hoan_tien_mot_phan` |
| `BanAn.trang_thai` | `trong` · `dang_giu` · `da_dat` · `dang_phuc_vu` · `cho_don` · `bao_tri` |
| `PhienPhucVu.trang_thai` | `dang_phuc_vu` · `cho_don` · `da_dong` |
| `DonHang.trang_thai` | `cho_tiep_nhan` · `da_xac_nhan` · `dang_che_bien` · `san_sang` · `hoan_tat` · `da_huy` |
| `ThanhToan.loai_thanh_toan` / `trang_thai` | `don_hang` · `tien_coc` / `cho_xu_ly` · `thanh_cong` · `that_bai` · `da_hoan_tien` |
| `moc_thoi_gian` (quy tắc huỷ, phiếu hoàn) | `truoc_24h` · `tu_6_den_24h` · `trong_6h` · `khach_khong_den` |
| `KhuyenMai.kieu_giam` | `phan_tram` · `so_tien_co_dinh` |
| `LichSuXuatNhapKho.loai_giao_dich` | `nhap` · `xuat` · `dieu_chinh` |
| `BaiViet.trang_thai` | `nhap` · `da_dang` · `luu_tru` |

---

## 18. Thay đổi so với bản contract trước

Client cũ (Postman, app khác) dùng tên trường tiếng Anh **sẽ bị lỗi** cho tới khi đổi sang các tên dưới đây. **URL không đổi.**

| Trước | Bây giờ |
|---|---|
| Body đăng nhập `email` / `username` | `thu_dien_tu` |
| Body đăng ký `email`, `password`, `name`, `phone` | `thu_dien_tu`, `mat_khau`, `ho_ten`, `so_dien_thoai` |
| Body đổi mật khẩu `old_password`, `new_password` | `mat_khau_cu`, `mat_khau_moi`; response `{ thong_bao }` |
| Response người dùng `name`, `email`, `phone`, `roles`, `is_restaurant_staff` | Chỉ còn `ho_ten`, `thu_dien_tu`, `so_dien_thoai`, `danh_sach_vai_tro`, `la_nhan_vien_nha_hang` |
| Response xác thực email `user` | `nguoi_dung` |
| VNPay `payment_type`, `reservation_id`, `order_id`, `amount` → `payment_url`, `transaction_id`, `expires_at` | `loai_thanh_toan`, `dat_ban_id`, `don_hang_id`, `so_tien` → `duong_dan_thanh_toan`, `ma_giao_dich`, `het_han_luc` |
| Đặt bàn `food_items`, đơn hàng `items` / `order_items`, khuyến mãi `codes` | `danh_sach_mon`, `danh_sach_mon`, `danh_sach_ma` |
| Query chi nhánh `lat`, `lng`, `radius`, `limit` | `vi_do`, `kinh_do`, `ban_kinh`, `so_luong` |
| Query `?food=`, `?active=` | `?mon_an=`, `?con_han=` |
| Body chi nhánh, bàn, món, khuyến mãi, bài viết… bằng tiếng Anh (`name`, `address`, `code`…) | Tên cột tiếng Việt (mục 17) |
| Chính sách cọc `rules: [{ time_milestone, refund_percentage }]` | `quy_tac_huy: [{ moc_thoi_gian, phan_tram_hoan_tien }]` |

---

## 19. Lưu ý phát hiện khi rà soát

- **Tên tiếng Anh còn sót lại**: không có bản tiếng Việt trùng nghĩa nên chưa bỏ. Muốn bỏ thì phải đổi đồng thời backend và frontend.
  - Body `users/admin_create` và `admin_update`.
  - Body `reservations/{id}/trang_thai` (`status`, `version`) và `record-refund`.
  - `refund_record`.
  - Chat: `sender_name`, `customer_name`, `last_message`, `unread_count`.
  - Đánh giá: `food_name`.
  - Gợi ý món: `is_cold_start`.
  - Toàn bộ JSON của `analytics/*`.
- **Backend vẫn đọc song song tên cũ ở vài chỗ**:
  - [orders/views.py:74-80](moc-backend/orders/views.py:74): `status`/`to_status`, `note`.
  - [foods/views.py:432-438](moc-backend/foods/views.py:432): `category`, `search`.
  - [recommendations/views.py:59-71](moc-backend/recommendations/views.py:59): `gioi_han` cùng với `limit`, `lam_moi` cùng với `refresh`.
  - [reservations/views.py:523](moc-backend/reservations/views.py:523): `reason`.

  Các chỗ này không gây lỗi. Riêng `status`/`note` của đơn hàng **đang được frontend dùng**, nên đừng xoá trước khi sửa [admin/api/admin.api.ts:196](moc-frontend/src/admin/api/admin.api.ts:196).
- **Mapper admin vẫn đọc dự phòng tên tiếng Anh**: [admin/api/admin.api.ts](moc-frontend/src/admin/api/admin.api.ts) có các lời gọi kiểu `val(r, "name", "ten")`. Tên tiếng Anh giờ luôn rỗng nên mapper rơi về tên tiếng Việt; vô hại nhưng có thể dọn.
- **File `urls.py` thừa**: [payments/urls.py](moc-backend/payments/urls.py) và [recommendations/urls.py](moc-backend/recommendations/urls.py) **không được include** ở đâu; mọi route thật nằm trong [api/urls.py](moc-backend/api/urls.py). Hai file này có thể xoá.
- **Hai module admin API song song**: `src/api/admin.api.ts` và `src/admin/api/admin.api.ts` cùng gọi các endpoint giống nhau; nên gộp về một.
- **Endpoint backend có nhưng frontend chưa dùng**:
  - `/foods/{slug}/mon_lien_quan/`, `/branches/nearest/`;
  - `/dining-sessions/from-reservation/`;
  - `/notifications/`, `/promotion-codes/`, `/refund-receipts/`;
  - `ws/orders/{id}/`.
