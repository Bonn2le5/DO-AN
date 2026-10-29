# 🍲 HƯỚNG DẪN CÀI ĐẶT, VẬN HÀNH VÀ CHẠY THỬ

## Web App Quản Lý Nhà Hàng Tích Hợp AI Hỗ Trợ Đặt Món (Nhà Hàng Mộc)

> **Khóa luận tốt nghiệp / Đồ án Chuyên ngành Công nghệ Phần mềm**  
> **Sinh viên thực hiện**: Nguyễn Văn Vũ  
> **Giảng viên hướng dẫn**: TS. Nguyễn Duy Tuấn  
> **Công nghệ**: Django 6 (ASGI, Channels, REST Framework, PostGIS) + React 19 (TypeScript, Vite, Tailwind CSS, Leaflet)

---

## 📌 MỤC LỤC

1. [Yêu cầu Môi trường](#1-yêu-cầu-môi-trường)
2. [Hướng Dẫn Khởi Tạo Cơ Sở Dữ Liệu PostgreSQL & PostGIS](#2-hướng-dẫn-khởi-tạo-cơ-sở-dữ-liệu-postgresql--postgis)
3. [Khởi Động Nhanh Hệ Thống (Quick Start)](#3-khởi-động-nhanh-hệ-thống-quick-start)
4. [Tài Khoản Quản Trị & Hướng Dẫn Khi Chưa Có Tài Khoản Admin](#4-tài-khoản-quản-trị--hướng-dẫn-khi-chưa-có-tài-khoản-admin)
5. [Danh Sách Các Trang & Hướng Dẫn Chạy Thử](#5-danh-sách-các-trang--hướng-dẫn-chạy-thử)
6. [Kiểm Thử Các Tính Năng Nâng Cao (AI, Concurrency, Real-time)](#6-kiểm-thử-các-tính-năng-nâng-cao)
7. [Các Lệnh Kiểm Tra Hệ Thống (Health Check)](#7-các-lệnh-kiểm-tra-hệ-thống-health-check)

---

## 1. Yêu Cầu Môi Trường

Trước khi bắt đầu, máy tính của bạn cần cài đặt:

- **Python**: Phiên bản 3.10 trở lên (khuyến nghị Python 3.12 hoặc 3.13)
- **Node.js**: Phiên bản 18+ & **npm**
- **PostgreSQL**: Phiên bản 14+ kèm tiện ích mở rộng `PostGIS` (bắt buộc cho tính năng bản đồ và tìm chi nhánh theo tọa độ không gian GIS)
- **Redis** _(tùy chọn)_: Hỗ trợ Channel Layer và Cache khóa giữ bàn (hệ thống đã tích hợp sẵn cơ chế dự phòng `InMemory` và `LocMem` nếu chưa bật Redis).

---

## 2. Hướng Dẫn Khởi Tạo Cơ Sở Dữ Liệu PostgreSQL & PostGIS

Để Backend Django có thể kết nối và lưu trữ dữ liệu, bạn cần tạo database `moc_db` trên PostgreSQL trước khi khởi chạy server. Hãy thực hiện theo các bước chi tiết sau:

### 🔹 Bước 2.1: Khởi động dịch vụ PostgreSQL

Đảm bảo PostgreSQL đang chạy trên máy của bạn:

- **Trên macOS (dùng Homebrew)**:
  ```bash
  brew services start postgresql@16
  ```
- **Trên Linux (Ubuntu/Debian)**:
  ```bash
  sudo systemctl start postgresql
  ```
- **Trên Windows**:
  - Mở `Services` (dịch vụ hệ thống) $\rightarrow$ Tìm `postgresql-x64-XX` $\rightarrow$ Nhấn **Start** (hoặc mở ứng dụng **pgAdmin 4**).

---

### 🔹 Bước 2.2: Tạo Database `moc_db` và Bật Extension PostGIS

Mở Terminal và truy cập vào giao diện dòng lệnh `psql`:

```bash
# Đăng nhập vào psql với user mặc định postgres:
psql -U postgres
# (Hoặc nếu trên macOS chỉ cần gõ: psql postgres)
```

Sau khi màn hình hiện dấu nhắc lệnh `postgres=#`, lần lượt chạy các lệnh SQL sau:

```sql
-- 1. Tạo cơ sở dữ liệu mới mang tên moc_db
CREATE DATABASE moc_db;

-- 2. Kết nối vào database moc_db vừa tạo
\c moc_db

-- 3. Bật tiện ích mở rộng PostGIS (cần cho trường tọa độ không gian chi nhánh GIS)
CREATE EXTENSION IF NOT EXISTS postgis;

-- 4. Bật tiện ích pgcrypto (hỗ trợ hàm băm và bảo mật token)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 5. (Tùy chọn) Đặt mật khẩu cho user postgres nếu chưa có (khớp với file .env):
ALTER USER postgres WITH PASSWORD 'vu2005';

-- 6. Thoát khỏi psql
\q
```

> 💡 **Mẹo nếu dùng pgAdmin 4 (Giao diện đồ họa)**:
>
> 1. Kết nối vào Server PostgreSQL của bạn $\rightarrow$ Nhấp chuột phải vào `Databases` $\rightarrow$ Chọn **Create** $\rightarrow$ **Database...** $\rightarrow$ Đặt tên là `moc_db` rồi nhấn **Save**.
> 2. Mở **Query Tool** trên database `moc_db` vừa tạo và chạy câu lệnh:
>    ```sql
>    CREATE EXTENSION IF NOT EXISTS postgis;
>    CREATE EXTENSION IF NOT EXISTS pgcrypto;
>    ```

---

### 🔹 Bước 2.3: Kiểm tra cấu hình kết nối trong file `.env`

Mở file [moc-backend/.env](file:///Users/VuVan/Documents/DO-AN/moc-backend/.env) và đảm bảo các thông số khớp với tài khoản PostgreSQL trên máy của bạn:

```env
DB_NAME=moc_db
DB_USER=postgres
DB_PASSWORD=vu2005       # Thay bằng mật khẩu tài khoản postgres trên máy của bạn
DB_HOST=localhost
DB_PORT=5432
```

---

### 🔹 Bước 2.4: Tạo Bảng & Nạp Dữ Liệu Ban Đầu

Sau khi database `moc_db` đã sẵn sàng, bạn có 2 cách để tạo bảng:

#### 🌟 Cách khuyên dùng: Dùng Migration và Seed Data của Django

Chạy tự động hoàn toàn bằng lệnh Django:

```bash
cd moc-backend
source .venv/bin/activate

# Tạo toàn bộ các bảng quan hệ theo schema chuẩn
python manage.py migrate

# Nạp tự động 100 món ăn từ Du-lieu-test.txt, 3 chi nhánh GIS, 22 bàn ăn & 4 tài khoản test
python manage.py seed_data
```

#### 🛠️ Cách phụ: Nạp trực tiếp từ file SQL có sẵn

Nếu muốn nạp schema bằng file DDL gốc, bạn có thể chạy:

```bash
# Nạp cấu trúc bảng tiếng Việt:
psql -U postgres -d moc_db -f moc_schema_tieng_viet.sql

# Sau đó đồng bộ migration giả định (fake) trong Django:
python manage.py migrate --fake
```

---

## 3. Khởi Động Nhanh Hệ Thống (Quick Start)

Dự án gồm 2 phần độc lập: **Backend (`moc-backend`)** và **Frontend (`moc-frontend`)**. Bạn cần mở **2 cửa sổ Terminal** để chạy đồng thời cả hai.

### 🔹 Bước 1: Khởi động Backend (Django API & ASGI)

Mở cửa sổ Terminal thứ nhất:

```bash
# 1. Di chuyển vào thư mục backend
cd moc-backend

# 2. Kích hoạt môi trường ảo (Virtual Environment)
# Trên macOS / Linux:
source .venv/bin/activate
# Trên Windows:
# .venv\Scripts\activate

# 3. Khởi chạy server ASGI (Daphne) để hỗ trợ cả API và WebSocket
python manage.py runserver 8000
```

> `daphne` phải được cài từ `moc-backend/requirements.txt`; nếu môi trường ảo đã có từ trước, chạy `pip install -r requirements.txt` để cài bổ sung. Server Backend sẽ hoạt động tại: 👉 **`http://127.0.0.1:8000/`** (hoặc `http://localhost:8000/`). Dùng `runserver` với Daphne để endpoint `/ws/chat/<id>/` được xử lý bằng ASGI.

---

### 🔹 Bước 2: Khởi động Frontend (React + Vite)

Mở cửa sổ Terminal thứ hai:

```bash
# 1. Di chuyển vào thư mục frontend
cd moc-frontend

# 2. Cài đặt các thư viện (nếu mới clone dự án về)
npm install

# 3. Khởi chạy máy chủ phát triển Vite
npm run dev
```

> Giao diện Web App Người dùng & Quản trị sẽ khả dụng tại: 👉 **`http://localhost:5173`**

---

## 4. Tài Khoản Quản Trị & Hướng Dẫn Khi Chưa Có Tài Khoản Admin

Hệ thống hỗ trợ 2 cách tiếp cận tài khoản:

### 🟢 Cách 1: Sử dụng tài khoản mẫu có sẵn (Khuyên dùng)

Sau khi bạn chạy lệnh `python manage.py seed_data` ở Bước 1, hệ thống đã tự động tạo sẵn 4 tài khoản với đầy đủ phân quyền Role-Based Access Control (RBAC):

| Loại tài khoản            | Tên đăng nhập (Email / Username)               | Mật khẩu             | Quyền hạn & Chức năng                                                                                                              |
| :------------------------ | :--------------------------------------------- | :------------------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| **Quản trị viên (Admin)** | `admin@mocrestaurant.vn`<br>_(hoặc `admin`)_   | `MocRestaurant@2026` | Toàn quyền: Truy cập **Django Admin Backend** và **Frontend Admin Portal**, quản lý thực đơn, duyệt đơn hàng, kho nguyên liệu BOM. |
| **Nhân viên (Staff)**     | `staff@mocrestaurant.vn`<br>_(hoặc `staff`)_   | `MocRestaurant@2026` | Quyền nhân viên: Trực tổng đài Chat, xử lý đơn hàng, theo dõi sơ đồ bàn ăn.                                                        |
| **Khách hàng 1**          | `khachhang@gmail.com`<br>_(hoặc `khachhang`)_  | `MocRestaurant@2026` | Khách hàng thân thiết: Đã có lịch sử đặt bàn, đánh giá và tương tác món ăn.                                                        |
| **Khách hàng 2**          | `huong.tran@gmail.com`<br>_(hoặc `tranhuong`)_ | `MocRestaurant@2026` | Khách hàng mới: Dùng để kiểm thử thuật toán AI gợi ý món ăn (Cold-Start).                                                          |

---

### 🟡 Cách 2: Tự tạo tài khoản Admin mới bằng lệnh (Nếu chưa có tài khoản)

Nếu bạn muốn tạo một tài khoản Superuser riêng của mình, hãy chạy lệnh sau trong thư mục `moc-backend` (đã kích hoạt `.venv`):

```bash
python manage.py createsuperuser
```

> ⚠️ **LƯU Ý QUAN TRỌNG KHI NHẬP THÔNG TIN:**  
> Vì hệ thống Nhà hàng Mộc sử dụng trường Email canonical (`thu_dien_tu`) làm định danh chính:
>
> 1. **Thu dien tu**: Nhập email của bạn (Ví dụ: `admin@gmail.com`). _Không được bỏ trống._
> 2. **Username**: Nhập tên đăng nhập (Ví dụ: `admin`).
> 3. **Password**: Nhập mật khẩu bí mật (Lưu ý: Terminal sẽ không hiện ký tự khi gõ mật khẩu, cứ gõ bình thường rồi nhấn Enter).
> 4. **Password (again)**: Nhập lại mật khẩu xác nhận.

Sau khi tạo xong, tài khoản này có thể dùng để đăng nhập vào cả **Django Admin** lẫn **Frontend Admin Portal**.

---

## 5. Danh Sách Các Trang & Hướng Dẫn Chạy Thử

### 🏢 A. CÁC TRANG QUẢN TRỊ (ADMIN & STAFF)

#### 1. Trang Quản Trị Cơ Sở Dữ Liệu (Django Admin)

- **Đường dẫn**: 👉 **`http://localhost:8000/admin/`**
- **Đăng nhập**: Dùng tài khoản `admin@mocrestaurant.vn` (Mật khẩu: `MocRestaurant@2026`) hoặc tài khoản tạo qua `createsuperuser`.
- **Nội dung kiểm tra**:
  - `Thực đơn`: Danh mục món, danh sách 100 món ăn, định mức nguyên liệu BOM.
  - `Chi nhánh`: Danh sách chi nhánh kèm tọa độ PostGIS GIS.
  - `Bàn ăn & Đặt bàn`: Danh sách 22 bàn ăn theo khu vực, đơn đặt bàn, chính sách hoàn cọc.
  - `Đơn hàng & Thanh toán`: Chi tiết hóa đơn, giao dịch thanh toán VNPay Sandbox, phiếu hoàn tiền.
  - `Người dùng & Vai trò`: Quản lý phân quyền RBAC (`quan_tri_vien`, `nhan_vien`, `khach_hang`).

#### 2. Trang Quản Trị Vận Hành Web App (Frontend Admin Portal)

- **Đường dẫn**: 👉 **`http://localhost:5173/admin`**
- **Điều kiện**: Đăng nhập tài khoản có quyền `admin` hoặc `staff` tại trang `/dang-nhap`.
- **Các trang chức năng chi tiết**:
  - **Dashboard tổng quan** (`/admin`): Thống kê doanh thu, số đơn hàng đang xử lý, tỉ lệ lấp đầy bàn ăn theo thời gian thực.
  - **Quản lý đơn hàng FSM** (`/admin/orders`): Theo dõi và cập nhật trạng thái vòng đời đơn hàng (`Chờ tiếp nhận` $\rightarrow$ `Đã xác nhận` $\rightarrow$ `Đang chế biến` $\rightarrow$ `Sẵn sàng` $\rightarrow$ `Hoàn tất`/`Đã hủy`).
  - **Quản lý đặt bàn** (`/admin/reservations`): Sơ đồ 22 bàn ăn trực quan theo màu sắc (`Trống`, `Đang giữ chỗ`, `Đang sử dụng`), duyệt đơn đặt bàn và hoàn cọc.
  - **Quản trị thực đơn & Kho BOM** (`/admin/menu`): Quản lý danh sách món, bật/tắt hiển thị, cập nhật giá bán và khấu trừ nguyên liệu khi chế biến.
  - **Quản lý đánh giá** (`/admin/reviews`): Xem và duyệt bình luận, đánh giá sao từ khách hàng.
  - **Quầy chat hỗ trợ khách hàng** (`/admin/chat`): Giao diện nhân viên tiếp nhận và phản hồi tin nhắn trực tiếp qua WebSocket.

---

### 👤 B. CÁC TRANG DÀNH CHO KHÁCH HÀNG (CLIENT PORTAL)

Truy cập tại: 👉 **`http://localhost:5173`**

| Tên trang                   | Đường dẫn (URL)                                   | Nội dung & Thao tác kiểm thử                                                                                                                                                                                     |
| :-------------------------- | :------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Trang chủ**               | `/`                                               | Banner khuyến mãi, danh mục món ăn hot, đề xuất AI gợi ý hôm nay, danh sách chi nhánh gần nhất.                                                                                                                  |
| **Thực đơn**                | `/thuc-don`                                       | Duyệt 100 món ăn; tìm kiếm theo tên món; lọc theo danh mục (_Lẩu, Nướng, Gỏi, Nhâm nhi, Đồ uống_), lọc độ cay, món ăn chay.                                                                                      |
| **Chi tiết món ăn**         | `/thuc-don/:slug`<br>_(vd: `/thuc-don/lau-thai`)_ | Xem ảnh món ăn, bảng thành phần nguyên liệu, mức độ cay, các thẻ vị và mục **"Món ăn tương tự gợi ý bởi AI"**.                                                                                                   |
| **Đặt bàn trực tuyến**      | `/dat-ban`                                        | Quy trình đặt bàn 4 bước: Chọn chi nhánh $\rightarrow$ Chọn ngày giờ & số khách $\rightarrow$ **Chọn bàn trực quan trên sơ đồ** $\rightarrow$ Xác nhận & Thanh toán cọc VNPay Sandbox (giữ chỗ tự động 10 phút). |
| **Giỏ hàng & Thanh toán**   | `/thanh-toan`                                     | Xem giỏ hàng, áp dụng mã giảm giá cá nhân, chọn hình thức _Giao hàng tận nơi_ hoặc _Tự đến lấy_, chốt đơn hàng.                                                                                                  |
| **Bản đồ Chi nhánh (GIS)**  | `/chi-nhanh`                                      | Bản đồ tương tác Leaflet (OpenStreetMap); tự động xin quyền định vị hoặc nhập tọa độ để **tìm chi nhánh gần nhất kèm khoảng cách km**.                                                                           |
| **Chương trình khuyến mãi** | `/khuyen-mai`                                     | Danh sách mã voucher giảm giá, điều kiện áp dụng và thời hạn sử dụng.                                                                                                                                            |
| **Bài viết & Tin tức**      | `/bai-viet`                                       | Tin tức ẩm thực, mẹo ăn ngon, câu chuyện thương hiệu Nhà hàng Mộc.                                                                                                                                               |
| **Đăng nhập / Đăng ký**     | `/dang-nhap`, `/dang-ky`                          | Đăng nhập tài khoản bằng email/username, cấp phát token JWT bảo mật.                                                                                                                                             |
| **Tài khoản cá nhân**       | `/tai-khoan`<br>`/tai-khoan/don-hang`             | Xem lịch sử đơn đặt món, trạng thái đơn hàng thời gian thực, danh sách món yêu thích.                                                                                                                            |
| **Bong bóng Chat Realtime** | _Nút chat tròn góc dưới bên phải_                 | Bấm vào biểu tượng chat trên bất kỳ trang nào để mở cửa sổ trò chuyện trực tiếp qua WebSocket với nhân viên nhà hàng.                                                                                            |

---

## 6. Kiểm Thử Các Tính Năng Nâng Cao

### 🤖 1. Thuật toán AI Gợi ý Món ăn (Content-Based Filtering TF-IDF & Cosine Similarity)

- **Cách thử nghiệm**:
  1. Đăng nhập tài khoản khách hàng (ví dụ: `khachhang@gmail.com`).
  2. Bấm xem, thích hoặc thêm vào giỏ một vài món lẩu/món cay (hệ thống sẽ tự động ghi nhận tương tác với trọng số: xem=1, thích=2, thêm giỏ=3, đặt món=4, đánh giá=5).
  3. Mở lại trang chủ hoặc trang chi tiết món ăn, bạn sẽ thấy mục **"Gợi ý cho bạn"** hiển thị danh sách các món ăn tương đồng kèm lời giải thích rõ ràng (_"Gợi ý cho bạn vì bạn yêu thích món Lẩu/Cay"_).
  4. Nếu dùng tài khoản mới chưa tương tác, hệ thống tự động kích hoạt chiến lược **Cold-Start Fallback** đề xuất các món ăn Best-seller phổ biến nhất.

### ⏱️ 2. Kiểm soát Xung đột Đặt bàn (Concurrency Control)

- **Cơ chế**: Giữ chỗ tạm thời 10 phút trên Cache/Redis với TTL (`SET NX`), chốt đặt cọc bằng Transaction Khóa bi quan (`select_for_update`).
- **Cách thử nghiệm**:
  1. Mở 2 trình duyệt khác nhau (hoặc 1 tab thường, 1 tab ẩn danh).
  2. Ở Tab 1: Vào `/dat-ban`, chọn Bàn `Q1-T01` tại Chi nhánh Quận 1 khung giờ 19:00 và bấm giữ bàn.
  3. Ở Tab 2: Cùng truy cập vào chọn Bàn `Q1-T01` trong cùng khung giờ.
  4. **Kết quả**: Tab 2 sẽ bị từ chối ngay lập tức và thông báo bàn đang có khách giữ chỗ tạm thời (Mã lỗi HTTP 409 Conflict).

### 💳 3. Cổng Thanh Toán VNPay Sandbox

- **Cách thử nghiệm**:
  1. Khi đặt bàn có yêu cầu cọc (20%) hoặc thanh toán đơn hàng, chọn hình thức thanh toán **VNPay**.
  2. Hệ thống sẽ tự tạo URL thanh toán có gắn mã kiểm tra toàn vẹn **HMAC-SHA512** và chuyển hướng sang cổng thử nghiệm của VNPay.
  3. Nhập thông tin thẻ test Sandbox do VNPay cung cấp (Ngân hàng: NCB, Số thẻ test: `9704198526191432198`, Tên: `NGUYEN VAN A`, Ngày phát hành: `07/15`, OTP: `123456`).
  4. Khi giao dịch thành công, VNPay Return URL và IPN webhook sẽ tự động cập nhật trạng thái đơn thành `da_xac_nhan`.

### 💬 4. Giao Tiếp Thời Gian Thực (WebSocket Chat & Order FSM)

- **Cách thử nghiệm Chat**:
  1. Tab 1 mở tài khoản khách hàng tại `http://localhost:5173/`, bấm mở Chat Widget ở góc dưới.
  2. Tab 2 đăng nhập tài khoản Admin/Staff mở trang `http://localhost:5173/admin/chat`.
  3. Nhắn tin qua lại: Tin nhắn sẽ lập tức hiển thị cả 2 bên không cần reload trang và được lưu an toàn vào bảng cơ sở dữ liệu `tin_nhan`.
- **Cách thử nghiệm Order FSM**:
  1. Khách đặt một đơn hàng mới.
  2. Tab nhân viên vào `/admin/orders` đổi trạng thái từ _Chờ tiếp nhận_ sang _Đang chế biến_.
  3. Tab khách hàng tại `/tai-khoan/don-hang` sẽ thấy thanh tiến trình đơn đổi màu và cập nhật ngay lập tức qua WebSocket.

---

## 7. Các Lệnh Kiểm Tra Hệ Thống (Health Check)

Bạn có thể chạy các lệnh sau trong terminal để đảm bảo toàn bộ mã nguồn đang ở trạng thái chuẩn mực cao nhất:

```bash
# 1. Kiểm tra cấu hình và tương thích Model Django (0 lỗi)
cd moc-backend
python manage.py check

# 2. Chạy bộ kiểm thử tự động toàn diện Backend
python manage.py test chat orders recommendations

# 3. Kiểm tra kiểm dịch Type và biên dịch đóng gói Frontend (0 lỗi TypeScript)
cd ../moc-frontend
npm run build
```

---

_Chúc bạn có trải nghiệm chạy thử và nghiệm thu đồ án thành công tốt đẹp!_
