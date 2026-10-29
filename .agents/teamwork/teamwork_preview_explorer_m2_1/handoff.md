# BÁO CÁO NGHIÊN CỨU KỸ THUẬT & KIẾN TRÚC THIẾT KẾ (HANDOFF REPORT)
**Dự án**: Web App Nhà hàng Mộc (Smart Restaurant Management & Food Ordering)  
**Agent**: Technical Explorer 1 for Milestone 2 (`teamwork_preview_explorer_m2_1`)  
**Nhiệm vụ**: Nghiên cứu & Thiết kế Kỹ thuật cho:  
1. **Kiểm soát Tranh chấp Đặt bàn 2 Giai đoạn (2-Phase Table Concurrency Control)**:
   - Phase 1: Redis Temporary Hold (`SET NX EX 600`, trả về HTTP 409 Conflict khi trùng).
   - Phase 2: Chốt đặt bàn với Khóa bi quan Database (`select_for_update()`), đối soát token Redis và dọn dẹp khóa.
2. **Khấu trừ Tồn kho Nguyên liệu theo Định mức (BOM - Bill of Materials)**:
   - Khóa bi quan nguyên liệu `NguyenLieu.objects.select_for_update()` chống deadlock.
   - Kiểm tra tồn kho, trừ kho và ghi nhật ký xuất kho `LichSuXuatNhapKho`.  
**Đường dẫn báo cáo**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m2_1/handoff.md`

---

## 1. Observation (Các quan sát trực tiếp & Bằng chứng thực nghiệm)

### 1.1. Hiện trạng Cấu hình Redis & CACHES
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-backend/config/settings.py`
  - Trong `settings.py`, biến `CACHES` hoàn toàn chưa được khai báo.
  - Khi `CACHES` không được cấu hình, Django mặc định sử dụng `django.core.cache.backends.locmem.LocMemCache`. Đây là bộ nhớ cục bộ theo tiến trình (in-memory per process). Nếu chạy nhiều worker (Gunicorn/Uvicorn/Celery), khóa giữ bàn trên worker A sẽ không được worker B nhìn thấy, gây vỡ cơ chế chống tranh chấp phân tán.
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-backend/.env`
  - Dòng 13 có ghi chú: `## REDIS_URL=redis://localhost:6379/0`.
- **Môi trường Python & Thư viện**:
  - Python interpreter chính của backend tại: `/Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python`.
  - Kiểm tra qua lệnh:
    ```bash
    /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -c "import django, redis; print(django.__version__, redis.__version__)"
    ```
    Kết quả trả về: `Django: 4.2.30 Redis: 7.0.1`.
  - Thư viện `redis` (7.0.1) đã được cài đặt sẵn. Trong Django 4.0+, backend `django.core.cache.backends.redis.RedisCache` đã được tích hợp sẵn trong nhân Django, không cần thêm thư viện ngoài `django-redis`.
    ```bash
    /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -c "from django.core.cache.backends.redis import RedisCache; print('RedisCache OK')"
    ```
    Kết quả: `RedisCache OK`.

### 1.2. Hiện trạng Xử lý Giữ bàn (Phase 1)
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-backend/reservations/views.py` (dòng 39–59):
  ```python
  @action(detail=True, methods=["post"], permission_classes=[AllowAny])
  def giu_ban(self, request, pk=None):
      ban = self.get_object()
      ngay = request.data.get("ngay_dat")
      gio = request.data.get("gio_bat_dau")
      so_khach = request.data.get("so_luong_khach")

      if not ngay or not gio or not so_khach:
          return Response({"chi_tiet": "Thiếu thông tin ngày, giờ hoặc số lượng khách."}, status=400)
      if ban.suc_chua < int(so_khach) or ban.trang_thai == BanAn.TrangThai.BAO_TRI:
          return Response({"chi_tiet": "Bàn không đủ chỗ hoặc đang bảo trì."}, status=400)

      khoa = DichVuDatBan._tao_khoa_giu_ban(ban.id, ngay, gio)
      if not cache.add(khoa, f"GIU{uuid.uuid4().hex[:12].upper()}", timeout=600):
          return Response({"chi_tiet": "Bàn đang có người giữ hoặc đặt."}, status=409)

      return Response({
          "id_giu_ban": cache.get(khoa),
          "thoi_han_giu_cho": (timezone.now() + timedelta(minutes=10)).isoformat()
      })
  ```
  **Các hạn chế và lỗ hổng phát hiện được**:
  1. *Thiếu trường `thoi_gian_con_lai_giay: 600`* trong payload phản hồi theo hợp đồng `PROJECT.md` (Interface Contract 1).
  2. *Định dạng token*: Hiện sinh `f"GIU{uuid.uuid4().hex[:12].upper()}"` thay vì chuẩn UUIDv4 (`str(uuid.uuid4())`).
  3. *Thiếu kiểm tra lịch đã đặt trong CSDL*: Hàm `giu_ban` chỉ kiểm tra `cache.add`. Nếu một bàn đã được chốt đặt thành công trong CSDL (`DatBan` có trạng thái `da_xac_nhan` hoặc `cho_thanh_toan`), khóa Redis của người đặt trước đã bị xóa. Khi khách hàng mới bấm giữ bàn ở khung giờ này, `cache.add` vẫn trả về `True` (vì key Redis trống), dẫn đến cấp quyền giữ bàn cho một bàn đã có người chốt đặt trong DB!
  4. *Định dạng lỗi xung đột 409*: Hợp đồng quy định trả về `{"detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt", "code": "BAN_DANG_BAN"}`, nhưng code hiện tại trả về `{"chi_tiet": "Bàn đang có người giữ hoặc đặt."}`.
  5. *Định dạng Key Redis*: `services.py:11` đang dùng `f"giu-ban:{id_ban}:{ngay}:{gio}"` thay vì quy chuẩn `table_hold:{id_ban}:{ngay}:{gio}`. Hơn nữa, `gio` chưa được chuẩn hóa chuỗi (ví dụ `"18:00"` vs `"18:00:00"`).

### 1.3. Khảo sát Endpoint từ Phía Frontend Caller
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-frontend/src/api/reservations.api.ts` (dòng 36–55):
  ```typescript
  export async function giuBan(params: {
    idBan: string;
    ngayDat: string;
    gioDat: string;
    soLuongKhach: number;
  }): Promise<{ idGiuBan: string; thoiHanGiuCho: string }> {
    const res = await fetch("/api/dat-ban/giu-ban/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ban_an_id: params.idBan,
        ngay_dat: params.ngayDat,
        gio_bat_dau: params.gioDat,
        so_luong_khach: params.soLuongKhach,
      }),
    });
    if (!res.ok) throw new Error("Không thể giữ bàn");
    const data = await res.json();
    return { idGiuBan: data.id_giu_ban, thoiHanGiuCho: data.thoi_han_giu_cho };
  }
  ```
  **Phát hiện bất đối xứng nghiêm trọng giữa Frontend và Backend**:
  - `PROJECT.md` quy định: `POST /api/tables/{id}/giu_ban/` và `POST /api/ban-an/{id}/giu_ban/` (Detail action trên `BanAnViewSet`).
  - Frontend `reservations.api.ts` gọi: `POST /api/dat-ban/giu-ban/` (List action trên `DatBanViewSet` với `ban_an_id` truyền trong body JSON).
  - Nếu backend chỉ có `@action(detail=True)` trên `BanAnViewSet`, lời gọi của frontend tới `/api/dat-ban/giu-ban/` sẽ bị lỗi **404 Not Found**.
  - Frontend gọi `taoDatBan` (dòng 92–93) đọc `data.ban_an_id` và `data.ten_ban`, trong khi `DatBanSerializer` chỉ serialize `ban_an` (ID) và `so_ban`.

### 1.4. Hiện trạng Xử lý Chốt đặt bàn (Phase 2)
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-backend/reservations/services.py` (dòng 14–67):
  ```python
  @staticmethod
  @transaction.atomic
  def tao_dat_ban(*, nguoi_dung, du_lieu):
      danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])
      id_giu_ban = du_lieu.pop("id_giu_ban", "")
      du_lieu.pop("expected_version", None)

      ban, chi_nhanh = du_lieu["ban_an"], du_lieu["chi_nhanh"]
      if ban.chi_nhanh_id != chi_nhanh.id or ban.trang_thai == BanAn.TrangThai.BAO_TRI or du_lieu["so_luong_khach"] > ban.suc_chua:
          raise ValidationError({"ban_an": "Bàn không phù hợp với sức chứa hoặc chi nhánh."})

      tranh_chap = DatBan.objects.select_for_update().filter(
          ban_an=ban, ngay_dat=du_lieu["ngay_dat"], gio_bat_dau=du_lieu["gio_bat_dau"],
          trang_thai__in=[
              DatBan.TrangThai.CHO_THANH_TOAN,
              DatBan.TrangThai.DA_XAC_NHAN,
              DatBan.TrangThai.KHACH_DA_DEN
          ]
      )
      if tranh_chap.exists():
          raise ValidationError({"ban_an": "Bàn đã có người đặt trong khung giờ này."})
  ```
  **Lỗ hổng kiểm soát tranh chấp**:
  - Dòng 24: `DatBan.objects.select_for_update().filter(...)` cố gắng khóa bi quan các bản ghi `DatBan` hiện có. Tuy nhiên, nếu bàn đó **chưa có ai đặt trước** (chưa có dòng nào trong bảng `dat_ban`), câu lệnh `select_for_update()` trên tập rỗng **hoàn toàn không tạo bất kỳ row-level lock nào trong PostgreSQL**!
  - Hai transaction đến đồng thời cùng lúc đều thấy `tranh_chap.exists() == False` và cùng tạo 2 bản ghi `DatBan` cho cùng 1 bàn và 1 khung giờ.
  - **Khắc phục chuẩn**: Phải khóa bi quan bản ghi gốc của bàn ăn: `ban_an_locked = BanAn.objects.select_for_update().get(id=ban.id)`. Khóa trên dòng `BanAn` đóng vai trò là một khóa tuần tự hóa (Mutex) cho mọi thao tác đặt bàn trên chiếc bàn đó!

### 1.5. Hiện trạng Mô hình Định mức Nguyên liệu (BOM) & Tồn kho
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-backend/foods/models.py`:
  - `NguyenLieu` (dòng 164–225): `ten`, `don_vi`, `ton_kho_hien_tai`, `ton_kho_toi_thieu`, `con_hoat_dong`.
  - `MonAn` (dòng 240, 244): `quan_ly_kho = models.BooleanField(default=False)`, `nguyen_lieu = models.ManyToManyField(NguyenLieu, through="DinhMucNguyenLieu", blank=True)`.
  - `DinhMucNguyenLieu` (dòng 419–427): `mon_an`, `nguyen_lieu`, `so_luong_can`.
  - `LichSuXuatNhapKho` (dòng 481–501): `nguyen_lieu`, `loai_giao_dich` (`nhap`, `xuat`, `dieu_chinh`), `so_luong`, `ton_kho_truoc`, `ton_kho_sau`, `loai_tham_chieu`, `id_tham_chieu`, `ghi_chu`, `tao_boi`.
- **File quan sát**: `/Users/VuVan/Documents/DO-AN/moc-backend/orders/services.py` (dòng 68–71):
  - Hiện tại hàm `tao_don_hang` chỉ có logic đơn sơ:
    ```python
    if mon_an.ton_kho_cache is not None and not mon_an.quan_ly_kho:
        mon_an.ton_kho_cache -= so_luong
        mon_an.save(update_fields=["ton_kho_cache", "cap_nhat_luc"])
    ```
  - Khi đơn hàng được chuyển trạng thái sang `DA_XAC_NHAN` (`doi_trang_thai`), **hoàn toàn chưa có cơ chế khấu trừ kho nguyên liệu theo BOM (`DinhMucNguyenLieu`)** và chưa ghi vào `LichSuXuatNhapKho`.

---

## 2. Logic Chain (Chuỗi suy luận từ quan sát tới giải pháp kiến trúc)

### 2.1. Kiến trúc Bộ nhớ đệm Redis & Khóa phân tán
1. Từ Quan sát 1.1: Để phục vụ giữ bàn tạm thời với TTL và Channels WebSocket cho các milestone kế tiếp, cấu hình `CACHES` trong `config/settings.py` cần chuyển sang sử dụng `django.core.cache.backends.redis.RedisCache` với `REDIS_URL`.
2. Lệnh `cache.add(key, value, timeout=600)` của `RedisCache` thực thi lệnh Redis nguyên tử `SET key value NX EX 600`.
   - Nếu key chưa có: Redis gán giá trị và trả về True.
   - Nếu key đã có (bàn đang bị giữ): Redis không ghi đè và trả về False.
   - TTL 600 giây (10 phút) đảm bảo khóa tự động tiêu hủy nếu khách hàng đóng trình duyệt hoặc không hoàn tất đặt bàn.

### 2.2. Kiến trúc Kiểm soát Tranh chấp 2 Giai đoạn (2-Phase Concurrency Control)

#### Giai đoạn 1: Giữ chỗ tạm thời trên Redis (Soft Reservation Lock)
```
[Client Request: POST giu_ban]
               │
               ▼
   [1. Validate Table & Maintenance] ──── Fail ───► [HTTP 400 Bad Request]
               │ Pass
               ▼
   [2. Check DB Active Bookings] ──────── Exists ─► [HTTP 409 Conflict: BAN_DANG_BAN]
               │ None
               ▼
   [3. Redis SET NX EX 600] ───────────── Exists ─► [HTTP 409 Conflict: BAN_DANG_BAN]
               │ Acquired
               ▼
[HTTP 200: id_giu_ban (UUIDv4), thoi_han_giu_cho, thoi_gian_con_lai_giay=600]
```
- **Chuẩn hóa Redis Key**:
  `table_hold:{ban_an_id}:{ngay_dat}:{gio_bat_dau}` (ví dụ: `table_hold:5:2026-10-15:18:00`).
  Chuẩn hóa chuỗi thời gian đảm bảo không lệch giữa `"18:00"` và `"18:00:00"`.
- **Khắc phục lỗ hổng DB**: Trước khi gọi Redis `cache.add`, hàm bắt buộc truy vấn bảng `dat_ban` trong CSDL với trạng thái hoạt động (`CHO_THANH_TOAN`, `DA_XAC_NHAN`, `KHACH_DA_DEN`). Nếu đã tồn tại đơn đặt bàn trong khung giờ đó, trả ngay về HTTP 409 `{"detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt", "code": "BAN_DANG_BAN"}`.
- **Tương thích Routing đa kênh**:
  - Hỗ trợ cả 3 dạng URL:
    1. `POST /api/tables/{id}/giu_ban/`
    2. `POST /api/ban-an/{id}/giu_ban/`
    3. `POST /api/dat-ban/giu-ban/` (và `/api/reservations/giu-ban/` - phục vụ trực tiếp `moc-frontend`).

#### Giai đoạn 2: Chốt đặt bàn với Khóa bi quan CSDL (Hard DB Lock & Token Consume)
```
[Client Request: POST /api/dat-ban/ with id_giu_ban]
               │
               ▼
       [@transaction.atomic]
               │
               ▼
   [1. BanAn.objects.select_for_update().get(id=ban_an_id)]  <── Mutex row-level lock
               │
               ▼
   [2. Check DB overlapping active reservations] ── Overlap ──► [HTTP 400 / 409 Error]
               │ Valid
               ▼
   [3. Validate Redis Hold Token] ──────────────── Mismatch ─► [HTTP 400 Token Invalid]
       (cache.get(key) == id_giu_ban)
               │ Valid
               ▼
   [4. Create DatBan & MonAnTrongDatBan in PostgreSQL]
               │
               ▼
   [5. Delete Redis Hold Key] ──────────────────── (Safe atomic release)
               │
               ▼
      [Commit Transaction & Return HTTP 201]
```
- **Ý nghĩa sống còn của `BanAn.objects.select_for_update()`**:
  Khi hai người cùng gửi yêu cầu chốt đặt bàn cho cùng một bàn ở cùng một khung giờ:
  Người thứ nhất vào transaction -> chiếm khóa `select_for_update()` trên dòng `BanAn`. Người thứ hai phải chờ (wait on lock).
  Sau khi người thứ nhất tạo xong `DatBan` và giải phóng token Redis, transaction thứ nhất commit.
  Người thứ hai nhận được khóa: lúc này kiểm tra `cache.get(khoa_redis) == id_giu_ban` bị thất bại (token đã bị người thứ nhất xóa), VÀ kiểm tra DB thấy `DatBan` của người thứ nhất đã tồn tại -> Yêu cầu thứ hai bị chặn đứng an toàn 100%, không xảy ra tình trạng đặt trùng lặp (double booking).

### 2.3. Kiến trúc Khấu trừ Tồn kho Nguyên liệu theo BOM (Bill of Materials)

#### Phân tích Thuật toán Khấu trừ Tồn kho
1. **Tổng hợp nhu cầu nguyên liệu**:
   - Duyệt qua toàn bộ món ăn trong đơn hàng hoặc đặt bàn.
   - Tìm các bản ghi `DinhMucNguyenLieu` tương ứng với từng món ăn.
   - Tính tổng định mức cần thiết: $\text{Tổng cần}(nl) = \sum (\text{Số lượng cần từng món} \times \text{Số lượng món đặt})$.
2. **Ngăn chặn triệt để Deadlock bằng Strict Global Ordering (Sắp xếp ID tăng dần)**:
   - Trong môi trường xử lý đồng thời, nếu Đơn 1 cần khóa Nguyên liệu A (ID=10) rồi B (ID=20), trong khi Đơn 2 cần khóa B (ID=20) rồi A (ID=10), hệ cơ sở dữ liệu sẽ rơi vào bế tắc (Deadlock).
   - **Giải pháp**: Toàn bộ ID của nguyên liệu cần khóa được sắp xếp tăng dần:
     `sorted_ids = sorted(tong_can.keys())`
   - Truy vấn khóa: `NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")`.
   - Mọi tiến trình đều xin khóa theo cùng một thứ tự duy nhất, triệt tiêu hoàn toàn khả năng xảy ra chu trình chờ đợi (circular wait) -> Không bao giờ bị deadlock!
3. **Kiểm tra khả năng đáp ứng (Availability Check trước khi trừ)**:
   - Duyệt qua danh sách nguyên liệu đã bị khóa. Nếu có bất kỳ nguyên liệu nào có `ton_kho_hien_tai < tong_can`, toàn bộ transaction bị hủy (rollback), báo lỗi rõ ràng tên nguyên liệu thiếu và số lượng thiếu.
4. **Khấu trừ và Ghi vết Lịch sử Xuất nhập kho (`LichSuXuatNhapKho`)**:
   - Cập nhật `ton_kho_hien_tai = ton_kho_truoc - tong_can`.
   - Tạo bản ghi `LichSuXuatNhapKho` với `loai_giao_dich="xuat"`, ghi rõ `loai_tham_chieu="don_hang"` (hoặc `"dat_ban"`), `id_tham_chieu`, `ton_kho_truoc`, `ton_kho_sau`, và người thực hiện.
5. **Tính Idempotent (Chống trừ kho lặp lại)**:
   - Trước khi thực hiện trừ kho cho đơn hàng `don_hang_id`, kiểm tra xem đã có giao dịch xuất kho tham chiếu đến đơn hàng này chưa (`LichSuXuatNhapKho.objects.filter(loai_tham_chieu="don_hang", id_tham_chieu=don_hang.id, loai_giao_dich="xuat").exists()`). Nếu đã trừ rồi thì bỏ qua, tránh trường hợp FSM chuyển đổi nhiều lần làm trừ kho kép.

---

## 3. Thiết kế Kỹ thuật Chi tiết cho Implementation Worker

### 3.1. Cấu hình `moc-backend/config/settings.py`
Thêm cấu hình `CACHES` sử dụng Redis chuẩn của Django:
```python
# Cấu hình Caching Redis (Dual purpose: Table Hold Concurrency & Channels Layer)
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/1")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 600,
    }
}
```
*Lưu ý dự phòng*: Khi chạy test suite đơn vị hoặc môi trường không bật Redis port 6379, test runner có thể ghi đè với `LocMemCache`.

### 3.2. Cải tiến Dịch vụ Đặt bàn `moc-backend/reservations/services.py`
```python
import uuid
from decimal import Decimal
from datetime import timedelta
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import DatBan, MonAnTrongDatBan, BanAn, ChinhSachDatCoc

class DichVuDatBan:
    HOLD_TIMEOUT_SECONDS = 600  # 10 phút

    @staticmethod
    def _chuan_hoa_thoi_gian(ngay, gio):
        ngay_str = str(ngay).strip()
        gio_str = str(gio).strip()
        if len(gio_str) > 5:
            gio_str = gio_str[:5]  # Chuẩn hóa HH:MM
        return ngay_str, gio_str

    @staticmethod
    def _tao_khoa_giu_ban(id_ban, ngay, gio):
        ngay_str, gio_str = DichVuDatBan._chuan_hoa_thoi_gian(ngay, gio)
        return f"table_hold:{id_ban}:{ngay_str}:{gio_str}"

    @classmethod
    def giu_ban_tam_thoi(cls, *, ban_id, ngay, gio, so_khach):
        """
        Phase 1: Giữ bàn tạm thời với Redis SET NX EX 600
        """
        ngay_str, gio_str = cls._chuan_hoa_thoi_gian(ngay, gio)

        # 1. Kiểm tra bàn ăn
        try:
            ban = BanAn.objects.select_related("chi_nhanh").get(id=ban_id)
        except BanAn.DoesNotExist:
            raise ValidationError({"ban_an": "Bàn ăn không tồn tại."})

        if ban.trang_thai == BanAn.TrangThai.BAO_TRI:
            raise ValidationError({"ban_an": "Bàn đang trong trạng thái bảo trì."})

        if ban.suc_chua < int(so_khach):
            raise ValidationError({"so_luong_khach": f"Bàn chỉ có sức chứa tối đa {ban.suc_chua} khách."})

        # 2. Kiểm tra bàn đã được chốt trong CSDL chưa
        da_dat_db = DatBan.objects.filter(
            ban_an=ban,
            ngay_dat=ngay_str,
            gio_bat_dau__startswith=gio_str,
            trang_thai__in=[
                DatBan.TrangThai.CHO_THANH_TOAN,
                DatBan.TrangThai.DA_XAC_NHAN,
                DatBan.TrangThai.KHACH_DA_DEN
            ]
        ).exists()

        if da_dat_db:
            return False, {
                "detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt",
                "code": "BAN_DANG_BAN",
                "chi_tiet": "Bàn này đã được đặt trong khung giờ đã chọn."
            }

        # 3. Thực hiện khóa Redis SET NX EX 600
        khoa_redis = cls._tao_khoa_giu_ban(ban.id, ngay_str, gio_str)
        token_giu_ban = str(uuid.uuid4())

        # cache.add thực thi Redis SET NX EX
        khoa_thanh_cong = cache.add(khoa_redis, token_giu_ban, timeout=cls.HOLD_TIMEOUT_SECONDS)

        if not khoa_thanh_cong:
            return False, {
                "detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt",
                "code": "BAN_DANG_BAN",
                "chi_tiet": "Bàn này đang được người khác giữ chỗ tạm thời."
            }

        thoi_han = timezone.now() + timedelta(seconds=cls.HOLD_TIMEOUT_SECONDS)
        return True, {
            "id_giu_ban": token_giu_ban,
            "thoi_han_giu_cho": thoi_han.isoformat(),
            "thoi_gian_con_lai_giay": cls.HOLD_TIMEOUT_SECONDS
        }

    @classmethod
    @transaction.atomic
    def tao_dat_ban(cls, *, nguoi_dung, du_lieu):
        """
        Phase 2: Chốt đặt bàn với Khóa bi quan select_for_update() và xác minh token Redis
        """
        danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])
        id_giu_ban = du_lieu.pop("id_giu_ban", None)
        du_lieu.pop("expected_version", None)

        ban = du_lieu["ban_an"]
        ngay = du_lieu["ngay_dat"]
        gio = du_lieu["gio_bat_dau"]
        so_khach = du_lieu["so_luong_khach"]
        chi_nhanh = du_lieu.get("chi_nhanh") or ban.chi_nhanh
        du_lieu["chi_nhanh"] = chi_nhanh

        ngay_str, gio_str = cls._chuan_hoa_thoi_gian(ngay, gio)

        # 1. KHÓA BI QUAN ROW BÀN ĂN (Mutex để serialize các request cùng bàn)
        ban_locked = BanAn.objects.select_for_update().get(id=ban.id)

        if ban_locked.trang_thai == BanAn.TrangThai.BAO_TRI:
            raise ValidationError({"ban_an": "Bàn đang trong trạng thái bảo trì."})
        if so_khach > ban_locked.suc_chua:
            raise ValidationError({"so_luong_khach": "Số lượng khách vượt quá sức chứa của bàn."})
        if ban_locked.chi_nhanh_id != chi_nhanh.id:
            raise ValidationError({"ban_an": "Bàn không thuộc chi nhánh đã chọn."})

        # 2. Kiểm tra xung đột đặt bàn trong CSDL với khóa bi quan
        tranh_chap = DatBan.objects.select_for_update().filter(
            ban_an=ban_locked,
            ngay_dat=ngay,
            gio_bat_dau__startswith=gio_str,
            trang_thai__in=[
                DatBan.TrangThai.CHO_THANH_TOAN,
                DatBan.TrangThai.DA_XAC_NHAN,
                DatBan.TrangThai.KHACH_DA_DEN
            ]
        )
        if tranh_chap.exists():
            raise ValidationError({"ban_an": "Bàn đã có người đặt trong khung giờ này."})

        # 3. Đối soát Token giữ bàn trên Redis
        khoa_redis = cls._tao_khoa_giu_ban(ban_locked.id, ngay_str, gio_str)
        token_hien_tai = cache.get(khoa_redis)

        if id_giu_ban:
            if token_hien_tai != str(id_giu_ban):
                raise ValidationError({"id_giu_ban": "Phiên giữ bàn đã hết hạn hoặc không hợp lệ."})
        else:
            # Nếu đặt trực tiếp mà không có token: bàn không được đang bị giữ bởi người khác
            if token_hien_tai is not None:
                raise ValidationError({"ban_an": "Bàn hiện đang được giữ chỗ tạm thời bởi khách hàng khác."})

        # 4. Tính toán tiền món ăn và tiền đặt cọc
        tien_mon_an = Decimal("0")
        for item in danh_sach_item:
            mon_an = item["mon_an"]
            so_luong = item["so_luong"]
            tien_mon_an += mon_an.don_gia_hien_tai * so_luong

        hinh_thuc = du_lieu.get("hinh_thuc")
        if not hinh_thuc:
            hinh_thuc = DatBan.HinhThuc.DAT_BAN_VA_GOI_MON if danh_sach_item else DatBan.HinhThuc.CHI_GIU_CHO
            du_lieu["hinh_thuc"] = hinh_thuc

        chinh_sach = ChinhSachDatCoc.objects.filter(
            con_ap_dung=True, chi_nhanh__in=[chi_nhanh, None]
        ).order_by("-chi_nhanh_id").first()

        can_coc = (hinh_thuc != DatBan.HinhThuc.CHI_GIU_CHO)
        so_tien_coc = Decimal("0")
        if can_coc and chinh_sach:
            so_tien_coc = tien_mon_an * (chinh_sach.phan_tram_coc / Decimal("100"))

        # 5. Tạo bản ghi DatBan
        dat_ban = DatBan.objects.create(
            nguoi_dung=nguoi_dung if (nguoi_dung and nguoi_dung.is_authenticated) else None,
            yeu_cau_dat_coc=can_coc,
            so_tien_coc=so_tien_coc,
            trang_thai_coc=DatBan.TrangThaiCoc.CHUA_THANH_TOAN if can_coc else DatBan.TrangThaiCoc.THANH_CONG,
            trang_thai=DatBan.TrangThai.CHO_THANH_TOAN if can_coc else DatBan.TrangThai.DA_XAC_NHAN,
            **du_lieu
        )

        # 6. Tạo các món ăn đính kèm
        for item in danh_sach_item:
            MonAnTrongDatBan.objects.create(
                dat_ban=dat_ban,
                mon_an=item["mon_an"],
                so_luong=item["so_luong"],
                don_gia_luc_dat=item["mon_an"].don_gia_hien_tai
            )

        # 7. Xóa an toàn khóa Redis nếu token trùng khớp
        if cache.get(khoa_redis) == id_giu_ban:
            cache.delete(khoa_redis)

        return dat_ban
```

### 3.3. Cải tiến Views trong `moc-backend/reservations/views.py`
Hỗ trợ cả endpoint theo chuẩn `PROJECT.md` và endpoint theo frontend caller:
```python
class BanAnViewSet(viewsets.ModelViewSet):
    serializer_class = BanAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    @action(detail=True, methods=["post"], url_path="giu_ban", permission_classes=[AllowAny])
    def giu_ban(self, request, pk=None):
        return self._xu_ly_giu_ban(request, ban_id=pk)

    @action(detail=True, methods=["post"], url_path="giu-ban", permission_classes=[AllowAny])
    def giu_ban_hyphen(self, request, pk=None):
        return self._xu_ly_giu_ban(request, ban_id=pk)

    def _xu_ly_giu_ban(self, request, ban_id):
        ngay = request.data.get("ngay") or request.data.get("ngay_dat") or request.data.get("date")
        gio = request.data.get("gio") or request.data.get("gio_bat_dau") or request.data.get("time")
        so_khach = request.data.get("so_luong_khach") or request.data.get("guest_count") or request.data.get("guests")

        if not ngay or not gio or not so_khach:
            return Response({"detail": "Thiếu thông tin ngày, giờ hoặc số lượng khách.", "code": "THIEU_THONG_TIN"}, status=400)

        thanh_cong, ket_qua = DichVuDatBan.giu_ban_tam_thoi(
            ban_id=ban_id, ngay=ngay, gio=gio, so_khach=so_khach
        )
        if not thanh_cong:
            return Response(ket_qua, status=409)

        return Response(ket_qua, status=200)


class DatBanViewSet(viewsets.ModelViewSet):
    serializer_class = DatBanSerializer

    @action(detail=False, methods=["post"], url_path="giu-ban", permission_classes=[AllowAny])
    def giu_ban_frontend(self, request):
        """Hỗ trợ trực tiếp cho fetch('/api/dat-ban/giu-ban/') từ frontend"""
        ban_id = request.data.get("ban_an_id") or request.data.get("idBan") or request.data.get("table_id")
        ngay = request.data.get("ngay") or request.data.get("ngay_dat") or request.data.get("date")
        gio = request.data.get("gio") or request.data.get("gio_bat_dau") or request.data.get("time")
        so_khach = request.data.get("so_luong_khach") or request.data.get("guest_count")

        if not ban_id or not ngay or not gio or not so_khach:
            return Response({"detail": "Thiếu thông tin bàn, ngày, giờ hoặc số lượng khách."}, status=400)

        thanh_cong, ket_qua = DichVuDatBan.giu_ban_tam_thoi(
            ban_id=ban_id, ngay=ngay, gio=gio, so_khach=so_khach
        )
        if not thanh_cong:
            return Response(ket_qua, status=409)
        return Response(ket_qua, status=200)
```

### 3.4. Cải tiến Serializer `moc-backend/reservations/serializers.py`
```python
class DatBanSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "chi_nhanh_id": "chi_nhanh",
        "table": "ban_an",
        "table_id": "ban_an",
        "ban_an_id": "ban_an",
        "customer_name": "ten_khach",
        "name": "ten_khach",
        "customer_phone": "sdt_khach",
        "phone": "sdt_khach",
        "customer_email": "email_khach",
        "email": "email_khach",
        "guest_count": "so_luong_khach",
        "number_of_guests": "so_luong_khach",
        "party_size": "so_luong_khach",
        "date": "ngay_dat",
        "reservation_date": "ngay_dat",
        "start_time": "gio_bat_dau",
        "time": "gio_bat_dau",
        "end_time": "gio_ket_thuc",
        "note": "ghi_chu",
        "notes": "ghi_chu",
        "hold_token": "id_giu_ban",
        "items": "danh_sach_mon",
        "food_items": "danh_sach_mon",
        "type": "hinh_thuc",
        "reservation_type": "hinh_thuc",
    }
    danh_sach_mon = MonAnDatBanSerializer(many=True, required=False)
    food_items = MonAnDatBanSerializer(many=True, source="danh_sach_mon", read_only=True)
    so_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    ten_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    ban_an_id = serializers.IntegerField(source="ban_an.id", read_only=True)
    id_giu_ban = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = DatBan
        fields = "__all__"
        read_only_fields = (
            "nguoi_dung", "ma_dat_ban", "trang_thai",
            "yeu_cau_dat_coc", "so_tien_coc", "trang_thai_coc",
            "thanh_toan_coc_luc", "huy_luc", "phien_ban"
        )

    def validate(self, attrs):
        ban = attrs.get("ban_an")
        chi_nhanh = attrs.get("chi_nhanh")
        if ban and not chi_nhanh:
            attrs["chi_nhanh"] = ban.chi_nhanh
        elif ban and chi_nhanh and ban.chi_nhanh_id != chi_nhanh.id:
            raise serializers.ValidationError({"ban_an": "Bàn không thuộc chi nhánh đã chọn."})
        return attrs
```

---

### 3.5. Xây dựng Module Dịch vụ Khấu trừ Tồn kho BOM `moc-backend/foods/services.py`
Tạo mới file `foods/services.py` cung cấp lớp dịch vụ quản lý xuất/nhập kho:
```python
from decimal import Decimal
from collections import defaultdict
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho, MonAn

class DichVuKho:
    @staticmethod
    @transaction.atomic
    def khau_tru_nguyen_lieu_bom(*, danh_sach_mon, loai_tham_chieu, id_tham_chieu, nguoi_dung=None, ghi_chu=""):
        """
        Khấu trừ tồn kho nguyên liệu theo định mức (BOM) với Khóa bi quan select_for_update().
        Áp dụng thuật toán Strict Global ID Ordering để triệt tiêu hoàn toàn nguy cơ Deadlock.
        
        :param danh_sach_mon: Danh sách dict [{'mon_an': MonAn, 'so_luong': int}, ...] hoặc QuerySet
        :param loai_tham_chieu: "don_hang" hoặc "dat_ban"
        :param id_tham_chieu: ID của DonHang hoặc DatBan
        :param nguoi_dung: User thực hiện hành động
        :param ghi_chu: Ghi chú cho giao dịch xuất kho
        :return: Danh sách bản ghi LichSuXuatNhapKho đã tạo
        """
        # Kiểm tra tính Idempotent: nếu đơn hàng/đặt bàn này đã xuất kho rồi thì bỏ qua
        da_xuat = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu=loai_tham_chieu,
            id_tham_chieu=id_tham_chieu,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT
        ).exists()
        if da_xuat:
            return []

        # 1. Tổng hợp nhu cầu nguyên liệu cần dùng
        tong_nhu_cau = defaultdict(Decimal)

        for item in danh_sach_mon:
            mon_an = item.get("mon_an") if isinstance(item, dict) else getattr(item, "mon_an")
            so_luong = item.get("so_luong") if isinstance(item, dict) else getattr(item, "so_luong")

            # Tra cứu định mức của món ăn
            dinh_muc_qs = DinhMucNguyenLieu.objects.filter(mon_an=mon_an).select_related("nguyen_lieu")
            for dm in dinh_muc_qs:
                tong_nhu_cau[dm.nguyen_lieu_id] += dm.so_luong_can * Decimal(str(so_luong))

        if not tong_nhu_cau:
            return []  # Các món ăn không có cấu hình BOM

        # 2. STRICT RESOURCE ORDERING: Sắp xếp ID nguyên liệu tăng dần để tránh Deadlock
        sorted_ids = sorted(tong_nhu_cau.keys())

        # 3. Khóa bi quan các dòng nguyên liệu trong PostgreSQL
        nguyen_lieu_locked = list(
            NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")
        )

        # 4. Kiểm tra tồn kho trước khi trừ
        danh_sach_loi = []
        for nl in nguyen_lieu_locked:
            can_dung = tong_nhu_cau[nl.id]
            if nl.ton_kho_hien_tai < can_dung:
                danh_sach_loi.append(
                    f"Nguyên liệu '{nl.ten}' không đủ tồn kho (hiện có: {nl.ton_kho_hien_tai} {nl.don_vi}, cần: {can_dung} {nl.don_vi})."
                )

        if danh_sach_loi:
            raise ValidationError({"kho": danh_sach_loi})

        # 5. Thực hiện trừ kho và ghi lịch sử giao dịch
        danh_sach_giao_dich = []
        for nl in nguyen_lieu_locked:
            so_luong_xuat = tong_nhu_cau[nl.id]
            ton_truoc = nl.ton_kho_hien_tai
            ton_sau = ton_truoc - so_luong_xuat

            nl.ton_kho_hien_tai = ton_sau
            nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

            giao_dich = LichSuXuatNhapKho.objects.create(
                nguyen_lieu=nl,
                loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT,
                so_luong=so_luong_xuat,
                ton_kho_truoc=ton_truoc,
                ton_kho_sau=ton_sau,
                loai_tham_chieu=loai_tham_chieu,
                id_tham_chieu=id_tham_chieu,
                ghi_chu=ghi_chu or f"Xuất kho nguyên liệu tự động cho {loai_tham_chieu} #{id_tham_chieu}",
                tao_boi=nguoi_dung if (nguoi_dung and nguoi_dung.is_authenticated) else None
            )
            danh_sach_giao_dich.append(giao_dich)

        return danh_sach_giao_dich

    @staticmethod
    @transaction.atomic
    def hoan_tra_nguyen_lieu_bom(*, loai_tham_chieu, id_tham_chieu, nguoi_dung=None, ghi_chu=""):
        """
        Hoàn trả tồn kho khi đơn hàng hoặc đặt bàn bị hủy sau khi đã trừ kho.
        """
        giao_dich_xuat = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu=loai_tham_chieu,
            id_tham_chieu=id_tham_chieu,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT
        ).select_related("nguyen_lieu")

        if not giao_dich_xuat.exists():
            return []

        sorted_ids = sorted([gd.nguyen_lieu_id for gd in giao_dich_xuat])
        nl_map = {nl.id: nl for nl in NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")}

        danh_sach_hoan = []
        for gd in giao_dich_xuat:
            nl = nl_map[gd.nguyen_lieu_id]
            ton_truoc = nl.ton_kho_hien_tai
            ton_sau = ton_truoc + gd.so_luong

            nl.ton_kho_hien_tai = ton_sau
            nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

            giao_dich_nhap = LichSuXuatNhapKho.objects.create(
                nguyen_lieu=nl,
                loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
                so_luong=gd.so_luong,
                ton_kho_truoc=ton_truoc,
                ton_kho_sau=ton_sau,
                loai_tham_chieu=loai_tham_chieu,
                id_tham_chieu=id_tham_chieu,
                ghi_chu=ghi_chu or f"Hoàn kho nguyên liệu do hủy {loai_tham_chieu} #{id_tham_chieu}",
                tao_boi=nguoi_dung if (nguoi_dung and nguoi_dung.is_authenticated) else None
            )
            danh_sach_hoan.append(giao_dich_nhap)

        return danh_sach_hoan

# Alias tương thích ngược
InventoryService = DichVuKho
```

### 3.6. Tích hợp Khấu trừ Kho vào Vòng đời Đơn hàng & Đặt bàn
1. **Trong `orders/services.py`**:
   Khi nhân viên hoặc hệ thống đổi trạng thái đơn sang `DA_XAC_NHAN`:
   ```python
   # orders/services.py: doi_trang_thai
   if trang_thai_moi == DonHang.TrangThai.DA_XAC_NHAN:
       from foods.services import DichVuKho
       DichVuKho.khau_tru_nguyen_lieu_bom(
           danh_sach_mon=don_hang.danh_sach_mon.all(),
           loai_tham_chieu="don_hang",
           id_tham_chieu=don_hang.id,
           nguoi_dung=nguoi_dung,
           ghi_chu=f"Xuất kho khi xác nhận đơn hàng {don_hang.ma_don_hang}"
       )
   elif trang_thai_moi == DonHang.TrangThai.DA_HUY and trang_thai_cu in [DonHang.TrangThai.DA_XAC_NHAN, DonHang.TrangThai.DANG_CHE_BIEN]:
       from foods.services import DichVuKho
       DichVuKho.hoan_tra_nguyen_lieu_bom(
           loai_tham_chieu="don_hang",
           id_tham_chieu=don_hang.id,
           nguoi_dung=nguoi_dung,
           ghi_chu=f"Hoàn kho do hủy đơn hàng {don_hang.ma_don_hang}"
       )
   ```
2. **Trong `reservations/services.py`**:
   Khi đặt bàn có món ăn đi kèm được xác nhận hoặc khách đến ăn:
   ```python
   if trang_thai_moi in [DatBan.TrangThai.DA_XAC_NHAN, DatBan.TrangThai.KHACH_DA_DEN]:
       from foods.services import DichVuKho
       DichVuKho.khau_tru_nguyen_lieu_bom(
           danh_sach_mon=dat_ban.danh_sach_mon.all(),
           loai_tham_chieu="dat_ban",
           id_tham_chieu=dat_ban.id,
           nguoi_dung=nguoi_dung,
           ghi_chu=f"Xuất kho cho đặt bàn {dat_ban.ma_dat_ban}"
       )
   ```

---

## 4. Caveats (Các giả định & Vùng biên kiến trúc)

1. **Môi trường Sandbox Socket Limitation**:
   - Trong quá trình khảo sát thực tế, việc mở kết nối TCP trực tiếp tới Redis qua Python script bị chặn trong môi trường sandbox (`Operation not permitted`). Cấu hình `CACHES` sử dụng `django.core.cache.backends.redis.RedisCache` là chuẩn xác theo tài liệu Django 4.2+ và redis-py 7.0.1.
   - Để kiểm thử tự động trong CI/CD hoặc môi trường kiểm thử unit test không có Redis server, các unit test có thể sử dụng `@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}})` mà vẫn kiểm chứng được 100% logic `cache.add` và `select_for_update`.
2. **Quản lý đơn vị đo lường trong BOM**:
   - Định mức trong `DinhMucNguyenLieu` hiện lưu `DecimalField(max_digits=14, decimal_places=3)` tính theo đơn vị gốc của nguyên liệu (`kg`, `lít`). Giả định tất cả công thức món ăn đều đã quy đổi về cùng đơn vị cơ sở với nguyên liệu trong kho (như đã nạp trong `seed_data.py`).
3. **Phạm vi Milestone 2**:
   - Nhiệm vụ VNPay Sandbox & Hoàn cọc (Features 6–10) được khảo sát bởi Explorer 2. Thiết kế của Explorer 1 tích hợp sẵn trường `so_tien_coc` và `trang_thai_coc` để bàn giao trơn tru cho luồng thanh toán VNPay.

---

## 5. Conclusion (Kết luận Đánh giá & Khuyến nghị)

1. **Cơ chế Kiểm soát Tranh chấp 2 Giai đoạn** là giải pháp tối ưu, giải quyết triệt để vấn đề đặt bàn trùng lặp:
   - Giai đoạn 1 giữ bàn 10 phút trên Redis với `SET NX EX 600`, trả về HTTP 409 Conflict khi bàn đang bận.
   - Giai đoạn 2 chốt đơn với `@transaction.atomic` và khóa bi quan `BanAn.objects.select_for_update()`, đối soát và xóa token Redis.
   - Bổ sung định tuyến kép và serializer alias để khớp hoàn hảo cả với đặc tả hợp đồng lẫn mã nguồn `moc-frontend` hiện tại.
2. **Module Khấu trừ Tồn kho Nguyên liệu BOM** được thiết kế hoàn chỉnh:
   - Áp dụng kỹ thuật sắp xếp ID tài nguyên tăng dần (Strict Global Ordering) trước khi gọi `NguyenLieu.objects.select_for_update()`, đảm bảo **không bao giờ xảy ra Deadlock**.
   - Kiểm tra tồn kho trước khi trừ, ghi vết đầy đủ vào `LichSuXuatNhapKho`.
   - Đảm bảo tính Idempotent và hỗ trợ hoàn kho tự động khi hủy đơn.

---

## 6. Verification Method (Phương pháp Kiểm chứng Độc lập)

### 6.1. Kiểm tra Cú pháp & Tương thích Django
```bash
cd /Users/VuVan/Documents/DO-AN/moc-backend
./.venv/bin/python manage.py check
```
*Điều kiện thành công*: Thoát mã `0`, hiển thị `System check identified no issues (0 silenced)`.

### 6.2. Kiểm chứng Kiểm soát Tranh chấp Đặt bàn (Test Script / Unit Test)
Chạy kịch bản kiểm thử tranh chấp mô phỏng:
1. **Kiểm thử Phase 1 (Redis Hold)**:
   - Gửi yêu cầu `POST /api/tables/{id}/giu_ban/` lần 1: Mong đợi mã `200 OK`, có `id_giu_ban` và `thoi_gian_con_lai_giay: 600`.
   - Gửi yêu cầu `POST /api/tables/{id}/giu_ban/` lần 2 với cùng bàn và giờ: Mong đợi mã `409 Conflict`, mã lỗi `BAN_DANG_BAN`.
2. **Kiểm thử Phase 2 (Pessimistic DB Lock & Confirm)**:
   - Gửi `POST /api/reservations/` với `id_giu_ban` sai hoặc đã hết hạn: Mong đợi mã `400 Bad Request` ("Phiên giữ bàn đã hết hạn hoặc không hợp lệ").
   - Gửi `POST /api/reservations/` với đúng `id_giu_ban`: Mong đợi mã `201 Created`. Token Redis bị xóa.
   - Gửi lại cùng request: Mong đợi bị từ chối do bàn đã có đơn trong DB.

### 6.3. Kiểm chứng Khấu trừ Tồn kho BOM
1. Nạp dữ liệu mẫu:
   ```bash
   ./.venv/bin/python manage.py seed_data
   ```
2. Tạo đơn hàng chứa món "Lẩu Thái Mộc" (yêu cầu 0.3 kg Tôm, 0.2 kg Mực, 1.0 lít Nước dùng lẩu).
3. Đổi trạng thái đơn hàng sang `da_xac_nhan`:
   - Kiểm tra `ton_kho_hien_tai` của Tôm giảm chính xác 0.3 kg.
   - Kiểm tra bảng `lich_su_xuat_nhap_kho` có 3 dòng mới với `loai_giao_dich='xuat'` và `loai_tham_chieu='don_hang'`.
4. Tạo đơn hàng với số lượng vượt quá tồn kho (ví dụ 500 phần):
   - Mong đợi trả về lỗi ValidationError cảnh báo không đủ tồn kho, số tồn kho giữ nguyên không đổi.
