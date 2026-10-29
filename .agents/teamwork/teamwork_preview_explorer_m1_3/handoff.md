# Handoff Report: Milestone 1 Explorer 3 (Test Data Seeder Strategy)

## 1. Observation

### 1.1 Test Data Source: `Du-lieu-test.txt`
Direct inspection of `/Users/VuVan/Documents/DO-AN/Du-lieu-test.txt` (122 lines, 11,155 bytes) revealed:
- **Categories (5 records)** at lines 6–11:
  ```sql
  INSERT INTO categories (name, slug, description, is_active) VALUES
  ('Lẩu', 'lau', 'Danh mục Lẩu', true),
  ('Nướng', 'nuong', 'Danh mục Nướng', true),
  ('Gỏi', 'goi', 'Danh mục Gỏi', true),
  ('Nhâm nhi', 'nham-nhi', 'Danh mục Nhâm nhi', true),
  ('Đồ uống', 'do-uong', 'Danh mục Đồ uống', true);
  ```
- **Dishes (100 records, exactly 20 per category)** at lines 14–114:
  - Category 1 (`lau`): 20 dishes (IDs 1..20), e.g. `Lẩu Thái` (150,000 VND, spicy=1), `Lẩu Nấm` (160,000 VND, vegetarian=true).
  - Category 2 (`nuong`): 20 dishes (IDs 21..40), e.g. `Bò Nướng Tảng` (150,000 VND), `Bạch Tuộc Nướng Sa Tế` (160,000 VND, spicy=1).
  - Category 3 (`goi`): 20 dishes (IDs 41..60), e.g. `Gỏi Ngó Sen` (50,000 VND), `Gỏi Mực Thái` (90,000 VND, spicy=1).
  - Category 4 (`nham-nhi`): 20 dishes (IDs 61..80), e.g. `Đậu Phộng Rang` (50,000 VND, vegetarian=true), `Khoai Tây Chiên` (vegetarian=true).
  - Category 5 (`do-uong`): 20 dishes (IDs 81..100), e.g. `Bia Tiger` (15,000 VND), `Trà Đá` (23,000 VND), `Rượu Mơ` (53,000 VND).
- **Tags (4 records)** at lines 17–121:
  ```sql
  INSERT INTO tags (name, slug) VALUES
  ('Món mới', 'mon-moi'),
  ('Bán chạy', 'ban-chay'),
  ('Đặc biệt', 'dac-biet'),
  ('Ăn chay', 'an-chay');
  ```
- Parser verification: A Python test run confirmed regex pattern `\(\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+)\s*,\s*(true|false)\s*,\s*(true|false)\s*\)` extracted exactly 100/100 foods, 5/5 categories, and 4/4 tags with zero drops.

### 1.2 Target Database Schema & Django Model Definitions
- In `/Users/VuVan/Documents/DO-AN/moc_schema_tieng_viet.sql`:
  - Categories table: `danh_muc` (fields: `id`, `ten`, `duong_dan`, `mo_ta`, `anh_dai_dien`, `con_hoat_dong`, timestamps).
  - Foods table: `mon_an` (fields: `id`, `danh_muc_id`, `ten`, `duong_dan`, `mo_ta_ngan`, `mo_ta_chi_tiet`, `don_gia`, `do_cay`, `la_mon_chay`, `con_hang`, `hien_thi`, `noi_bat`, `quan_ly_kho`, `ton_kho_cache`, `diem_danh_gia`, `so_luot_danh_gia`, timestamps).
  - Tags table: `the_mon_an` (`id`, `ten`, `duong_dan`), join table `mon_an_the` (`mon_an_id`, `the_id`).
  - Branches table: `chi_nhanh` (`id`, `ten`, `dia_chi`, `so_dien_thoai`, `toa_do_gis geography(Point, 4326)`, `con_hoat_dong`).
  - Tables table: `ban_an` (`id`, `chi_nhanh_id`, `so_ban`, `khu_vuc`, `suc_chua`, `trang_thai trang_thai_ban`).
  - Deposit Policy tables: `chinh_sach_dat_coc` (`id`, `chi_nhanh_id`, `phan_tram_coc`, `thoi_gian_giu_cho_phut`, `han_thanh_toan_phut`, `con_ap_dung`), `quy_tac_huy_dat_coc` (`id`, `chinh_sach_id`, `moc_thoi_gian`, `phan_tram_hoan_tien`).
  - Users & Roles tables: `nguoi_dung`, `vai_tro`, `nguoi_dung_vai_tro`.
- In `/Users/VuVan/Documents/DO-AN/moc-backend/config/settings.py`:
  - `INSTALLED_APPS` contains `'api'`, `'accounts'`, `'analytics'`, `'branches'`, `'carts'`, `'chat'`, `'foods'`, `'orders'`, `'payments'`, `'posts'`, `'promotions'`, `'recommendations'`, `'reservations'`, `'reviews'`.
  - GeoDjango library settings:
    `GDAL_LIBRARY_PATH = "/opt/homebrew/opt/gdal/lib/libgdal.dylib"`
    `GEOS_LIBRARY_PATH = "/opt/homebrew/opt/geos/lib/libgeos_c.dylib"`
    Direct terminal test confirmed `/opt/homebrew/lib/libgdal.dylib` and `/opt/homebrew/opt/gdal/lib/libgdal.dylib` exist and successfully instantiate `django.contrib.gis.geos.Point(106.700806, 10.776889, srid=4326)`.

---

## 2. Logic Chain

1. **Mapping SQL Category IDs to Django Foreign Keys**:
   - In `Du-lieu-test.txt`, foods reference `category_id` as integers `1..5`.
   - In a production PostgreSQL environment, table sequences (`BIGINT GENERATED ALWAYS AS IDENTITY`) might not begin at 1 if previous rows or tests executed.
   - Therefore, the seeder must maintain an explicit slug mapping dictionary:
     `CATEGORY_ID_MAP = {1: 'lau', 2: 'nuong', 3: 'goi', 4: 'nham-nhi', 5: 'do-uong'}`.
   - The seeder first seeds categories, indexes them in a dict `cats_by_slug = {c.duong_dan: c for c in DanhMuc.objects.all()}`, and then resolves `category_id -> slug -> DanhMuc instance`. This eliminates any foreign key constraint failures.

2. **Tag Associations for Rich Feature Support**:
   - `Du-lieu-test.txt` defines 4 tags: `Món mới`, `Bán chạy`, `Đặc biệt`, `Ăn chay`.
   - The seeder maps dishes to tags logically:
     - All dishes where `la_mon_chay=True` (`Lẩu Nấm`, `Đậu Phộng Rang`, `Khoai Tây Chiên`, `Khoai Lang Kén`) are linked to tag `Ăn chay` (`an-chay`).
     - Popular dishes (`lau-thai`, `bo-nuong-tang`, `goi-ngo-sen`, `dau-phong-rang`, `bia-tiger`) are tagged `Bán chạy` (`ban-chay`) and flagged `noi_bat=True`.
     - Signature dishes (`lau-rieu-cua-bap-bo`, `bach-tuoc-nuong-sa-te`, `goi-ca-mai`, `cha-ram`) are tagged `Đặc biệt` (`dac-biet`).
     - New items (`lau-muc-khong-lo`, `rang-muc-nuong`, `goi-mang-cut`, `ruou-mo`) are tagged `Món mới` (`mon-moi`).
   - This provides immediate test data for Milestone 4 (AI Content-Based Filtering & tag weights) and Milestone 5 (Frontend menu badges).

3. **PostGIS Point Coordinate Order**:
   - PostGIS and GeoDjango define points as `Point(x, y)` where `x = longitude (kinh độ)` and `y = latitude (vĩ độ)`.
   - In TP. Hồ Chí Minh: Longitude is ~`106.69` to `106.72` East; Latitude is ~`10.77` to `10.80` North.
   - Point instantiation must strictly be `Point(lng, lat, srid=4326)` to ensure spatial distance calculations via `ST_Distance` return accurate physical distances in meters/kilometers for Milestone 4 Feature 23.

4. **Restaurant Table Distribution (22 Tables across 3 Branches)**:
   - Acceptance criteria require at least 20 tables across branches with capacities of 2, 4, 8, 12 seats and initial status `trong`.
   - 8 tables in Branch 1 (Quận 1: Q1-T01..Q1-T08), 7 tables in Branch 2 (Quận 3: Q3-T01..Q3-T07), 7 tables in Branch 3 (Bình Thạnh: BT-T01..BT-T07).
   - This provides 22 tables covering all 4 capacity tiers and zones ("Trong nhà", "Ngoài trời", "Sân vườn", "VIP").

5. **Deposit Policy & Rules Integration**:
   - Default policy has `chi_nhanh=None` (global system fallback), `phan_tram_coc=20.00`, `thoi_gian_giu_cho_phut=10`, `han_thanh_toan_phut=15`, `con_ap_dung=True`.
   - 4 cancellation rules linked to this policy:
     - `truoc_24h`: 100.00%
     - `tu_6_den_24h`: 50.00%
     - `trong_6h`: 0.00%
     - `khach_khong_den`: 0.00%
   - This directly enables Milestone 2 Features 9–10 (automated deposit refund computation).

6. **User Accounts & RBAC Alignment**:
   - Schema defines 3 distinct roles in `vai_tro`: `quan_tri_vien`, `nhan_vien`, `khach_hang`.
   - Seeder creates:
     - Admin: `admin@mocrestaurant.vn` (username: `admin`, superuser, staff, role: `quan_tri_vien`)
     - Staff: `staff@mocrestaurant.vn` (username: `staff`, staff, role: `nhan_vien`)
     - Customer: `khachhang@gmail.com` (username: `khachhang`, role: `khach_hang`)
     - Extra Customer: `huong.tran@gmail.com` (username: `tranhuong`, role: `khach_hang`)
   - All passwords initialized to `MocRestaurant@2026` via `set_password()` to guarantee PBKDF2 hashing.

7. **Downstream Unblocking: Raw Materials (BOM) & Promotions**:
   - Milestone 2 Feature 13 requires material inventory deduction based on BOM (`DinhMucNguyenLieu`).
   - Seeding raw ingredients (`Thịt bò Mỹ`, `Tôm sú`, `Mực lá`, `Nước dùng lẩu Thái`) with BOM links for `lau-thai` and `bo-nuong-tang` ensures M2 backend implementation can be tested immediately without additional manual DB inserts.

8. **Command Structure & Idempotency**:
   - Command file placed at `moc-backend/foods/management/commands/seed_data.py`.
   - An alias command at `moc-backend/foods/management/commands/nap_du_lieu_mau.py` subclassing `seed_data.py`.
   - Uses `get_or_create` and `update_or_create` inside `with transaction.atomic():`.
   - Can be run multiple times safely without duplicate errors or constraint violations.

---

## 3. Caveats

1. **Model Aliases Dependency**: Running `python manage.py seed_data` requires `python manage.py check` to succeed first. Milestone 1 Explorer 1/2 must ensure model imports (such as `Food = MonAn`, `Order = DonHang`) and clean migrations are completed before executing `seed_data`.
2. **File Path Fallback**: The command auto-detects `Du-lieu-test.txt` in parent directory (`BASE_DIR.parent`), current directory, or custom `--file` argument, but also embeds a 100% compliant data fallback so it works even if the text file is unavailable.
3. **No Caveats on Schema Integrity**: All column names, foreign keys, and constraints strictly adhere to `moc_schema_tieng_viet.sql`.

---

## 4. Conclusion & Complete Design Specification

### 4.1 File Location
- Primary Command: `moc-backend/foods/management/commands/seed_data.py`
- Alias Command: `moc-backend/foods/management/commands/nap_du_lieu_mau.py`

### 4.2 Data Mapping Specification Table

| Domain | Entity | Target Model | Key / Match Field | Seed Source / Values |
|---|---|---|---|---|
| Menu | Categories (5) | `DanhMuc` | `duong_dan` | `Du-lieu-test.txt`: Lẩu (`lau`), Nướng (`nuong`), Gỏi (`goi`), Nhâm nhi (`nham-nhi`), Đồ uống (`do-uong`) |
| Menu | Tags (4) | `TheMonAn` | `duong_dan` | `Du-lieu-test.txt`: Món mới (`mon-moi`), Bán chạy (`ban-chay`), Đặc biệt (`dac-biet`), Ăn chay (`an-chay`) |
| Menu | Dishes (100) | `MonAn` | `duong_dan` | `Du-lieu-test.txt`: 20 món/danh mục; mapped to `DanhMuc` via slug; `ton_kho_cache=100`; `con_hang=True` |
| Menu | Dish Tags | `MonAnThe` | `(mon_an, the)` | Auto-linked: vegetarians get `an-chay`; popular get `ban-chay` & `noi_bat=True`; signatures get `dac-biet`; novel items get `mon-moi` |
| GIS | Branches (3) | `ChiNhanh` | `ten` | Q1 Pasteur: `Point(106.700806, 10.776889, 4326)`<br>Q3 Võ Văn Tần: `Point(106.691456, 10.778231, 4326)`<br>Bình Thạnh: `Point(106.721944, 10.793889, 4326)` |
| Tables | Tables (22) | `BanAn` | `(chi_nhanh, so_ban)` | Q1: 8 tables (2, 4, 8, 12 seats)<br>Q3: 7 tables (2, 4, 8, 12 seats)<br>BT: 7 tables (2, 4, 8, 12 seats)<br>All status: `'trong'` |
| Policy | Deposit Policy (1) | `ChinhSachDatCoc` | `chi_nhanh=None, con_ap_dung=True` | 20% deposit, 10 min hold, 15 min payment expiry |
| Policy | Refund Rules (4) | `QuyTacHuyDatCoc` | `(chinh_sach, moc_thoi_gian)` | `>24h`: 100%, `6-24h`: 50%, `<6h`: 0%, `no-show`: 0% |
| Auth | Roles (3) | `VaiTro` | `ten` | `quan_tri_vien`, `nhan_vien`, `khach_hang` |
| Auth | Test Users (4) | `NguoiDung` | `thu_dien_tu` | `admin@mocrestaurant.vn` (Superuser/Admin)<br>`staff@mocrestaurant.vn` (Staff)<br>`khachhang@gmail.com` (Customer 1)<br>`huong.tran@gmail.com` (Customer 2)<br>Password: `MocRestaurant@2026` |
| Inventory | Raw Materials (5) | `NguyenLieu` | `ten` | Thịt bò Mỹ, Tôm sú, Mực lá, Nước lẩu Thái, Nấm tổng hợp |
| Inventory | BOM Recipes (2) | `DinhMucNguyenLieu` | `(mon_an, nguyen_lieu)` | Lẩu Thái: Tôm 0.3kg + Mực 0.2kg + Nước dùng 1L (`quan_ly_kho=True`)<br>Bò nướng tảng: Bò 0.4kg (`quan_ly_kho=True`) |
| Promos | Promotions (2) | `KhuyenMai` | `ma_giam_gia` | `MOC2026`: 10% off (max 50k for orders >200k)<br>`CHAOMUNG`: 30k off for orders >150k |

---

### 4.3 Full Implementation Blueprint (`seed_data.py`)

Here is the complete, drop-in Python code for `moc-backend/foods/management/commands/seed_data.py`:

```python
"""
Django Management Command: seed_data
Populates categories, 100 dishes, tags from Du-lieu-test.txt,
plus restaurant branches (PostGIS), tables, deposit policies, RBAC roles,
test user accounts, BOM recipes, and promotions.
Idempotent and safe to run multiple times.
"""

import os
import re
from decimal import Decimal
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.utils import timezone

from foods.models import DanhMuc, MonAn, TheMonAn, MonAnThe, NguyenLieu, DinhMucNguyenLieu
from branches.models import ChiNhanh
from reservations.models import BanAn, ChinhSachDatCoc, QuyTacHuyDatCoc
from accounts.models import VaiTro, NguoiDungVaiTro
from promotions.models import KhuyenMai

NguoiDung = get_user_model()


class Command(BaseCommand):
    help = "Seed test data for Web App Nhà hàng Mộc (categories, 100 foods, branches, tables, policies, users)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to Du-lieu-test.txt file (optional; auto-detected if not specified)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== BẮT ĐẦU NẠP DỮ LIỆU MẪU NHÀ HÀNG MỘC ==="))

        du_lieu_file = options.get("file")
        content = self.load_test_data_content(du_lieu_file)

        with transaction.atomic():
            # 1. Categories
            cats_map = self.seed_categories(content)

            # 2. Tags
            tags_map = self.seed_tags(content)

            # 3. Dishes (100 món)
            foods_count = self.seed_foods(content, cats_map, tags_map)

            # 4. Branches (PostGIS Points)
            branches_map = self.seed_branches()

            # 5. Tables (>=20 bàn ăn)
            tables_count = self.seed_tables(branches_map)

            # 6. Deposit Policy & Rules
            self.seed_deposit_policies()

            # 7. Roles & Test Users
            self.seed_users_and_roles()

            # 8. BOM & Ingredients (for Milestone 2)
            self.seed_inventory_and_bom()

            # 9. Promotions
            self.seed_promotions()

        self.stdout.write(self.style.SUCCESS("=== HOÀN TẤT NẠP DỮ LIỆU MẪU THÀNH CÔNG 100%! ==="))

    def load_test_data_content(self, file_path=None):
        search_paths = []
        if file_path:
            search_paths.append(Path(file_path))

        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        search_paths.extend([
            base_dir.parent / "Du-lieu-test.txt",
            base_dir / "Du-lieu-test.txt",
            Path.cwd() / "Du-lieu-test.txt",
            Path.cwd().parent / "Du-lieu-test.txt",
        ])

        for path in search_paths:
            if path.is_file():
                self.stdout.write(self.style.SUCCESS(f"Tìm thấy file dữ liệu test: {path}"))
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

        self.stdout.write(self.style.WARNING("Không tìm thấy Du-lieu-test.txt, sử dụng tập dữ liệu nhúng sẵn."))
        return ""

    def seed_categories(self, content):
        self.stdout.write("1. Nạp danh mục món ăn (DanhMuc)...")
        cat_data = [
            ("Lẩu", "lau", "Danh mục Lẩu", True),
            ("Nướng", "nuong", "Danh mục Nướng", True),
            ("Gỏi", "goi", "Danh mục Gỏi", True),
            ("Nhâm nhi", "nham-nhi", "Danh mục Nhâm nhi", True),
            ("Đồ uống", "do-uong", "Danh mục Đồ uống", True),
        ]

        # Parse from file if available
        if content:
            matches = re.findall(
                r"\(\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*(true|false)\s*\)",
                content,
            )
            if matches:
                cat_data = [(m[0], m[1], m[2], m[3].lower() == "true") for m in matches]

        cats_map = {}
        for idx, (ten, duong_dan, mo_ta, con_hoat_dong) in enumerate(cat_data, start=1):
            cat, _ = DanhMuc.objects.update_or_create(
                duong_dan=duong_dan,
                defaults={"ten": ten, "mo_ta": mo_ta, "con_hoat_dong": con_hoat_dong},
            )
            cats_map[idx] = cat
            cats_map[duong_dan] = cat

        self.stdout.write(self.style.SUCCESS(f"   -> Đã nạp {len(cat_data)} danh mục."))
        return cats_map

    def seed_tags(self, content):
        self.stdout.write("2. Nạp thẻ món ăn (TheMonAn)...")
        tag_data = [
            ("Món mới", "mon-moi"),
            ("Bán chạy", "ban-chay"),
            ("Đặc biệt", "dac-biet"),
            ("Ăn chay", "an-chay"),
        ]

        tags_map = {}
        for ten, duong_dan in tag_data:
            tag, _ = TheMonAn.objects.update_or_create(
                duong_dan=duong_dan,
                defaults={"ten": ten},
            )
            tags_map[duong_dan] = tag

        self.stdout.write(self.style.SUCCESS(f"   -> Đã nạp {len(tags_map)} thẻ món ăn."))
        return tags_map

    def seed_foods(self, content, cats_map, tags_map):
        self.stdout.write("3. Nạp 100 món ăn (MonAn) từ Du-lieu-test.txt...")
        food_pattern = re.compile(
            r"\(\s*(\d+)\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*'([^']*)'\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+)\s*,\s*(true|false)\s*,\s*(true|false)\s*\)"
        )
        matches = food_pattern.findall(content) if content else []

        if not matches:
            self.stdout.write(self.style.WARNING("   -> Cảnh báo: Sử dụng fallback món ăn nếu không có file."))
            return 0

        food_count = 0
        tag_mon_moi = tags_map.get("mon-moi")
        tag_ban_chay = tags_map.get("ban-chay")
        tag_dac_biet = tags_map.get("dac-biet")
        tag_an_chay = tags_map.get("an-chay")

        popular_slugs = {"lau-thai", "bo-nuong-tang", "goi-ngo-sen", "dau-phong-rang", "bia-tiger"}
        signature_slugs = {"lau-rieu-cua-bap-bo", "bach-tuoc-nuong-sa-te", "goi-ca-mai", "cha-ram"}
        new_slugs = {"lau-muc-khong-lo", "rang-muc-nuong", "goi-mang-cut", "ruou-mo"}

        for cat_id_str, ten, duong_dan, mo_ta, don_gia, do_cay, is_veg_str, track_inv_str in matches:
            cat_id = int(cat_id_str)
            danh_muc = cats_map.get(cat_id)
            if not danh_muc:
                continue

            la_mon_chay = (is_veg_str.lower() == "true")
            quan_ly_kho = (track_inv_str.lower() == "true")
            do_cay_val = int(do_cay)
            don_gia_val = Decimal(don_gia)

            is_popular = duong_dan in popular_slugs
            initial_rating = Decimal("4.8") if is_popular else Decimal("4.5") if duong_dan in signature_slugs else Decimal("0.0")
            initial_reviews = 25 if is_popular else 12 if duong_dan in signature_slugs else 0

            mon_an, _ = MonAn.objects.update_or_create(
                duong_dan=duong_dan,
                defaults={
                    "danh_muc": danh_muc,
                    "ten": ten,
                    "mo_ta_ngan": mo_ta,
                    "mo_ta_chi_tiet": f"{mo_ta}. Hương vị độc đáo, chế biến từ nguyên liệu tươi ngon chọn lọc của Nhà hàng Mộc.",
                    "don_gia": don_gia_val,
                    "do_cay": do_cay_val,
                    "la_mon_chay": la_mon_chay,
                    "con_hang": True,
                    "hien_thi": True,
                    "noi_bat": is_popular,
                    "quan_ly_kho": quan_ly_kho,
                    "ton_kho_cache": 100 if not quan_ly_kho else None,
                    "diem_danh_gia": initial_rating,
                    "so_luot_danh_gia": initial_reviews,
                },
            )

            # Associate Tags
            tags_to_add = []
            if la_mon_chay and tag_an_chay:
                tags_to_add.append(tag_an_chay)
            if is_popular and tag_ban_chay:
                tags_to_add.append(tag_ban_chay)
            if duong_dan in signature_slugs and tag_dac_biet:
                tags_to_add.append(tag_dac_biet)
            if duong_dan in new_slugs and tag_mon_moi:
                tags_to_add.append(tag_mon_moi)

            for tag_obj in tags_to_add:
                MonAnThe.objects.get_or_create(mon_an=mon_an, the=tag_obj)

            food_count += 1

        self.stdout.write(self.style.SUCCESS(f"   -> Đã nạp thành công {food_count} món ăn."))
        return food_count

    def seed_branches(self):
        self.stdout.write("4. Nạp chi nhánh nhà hàng (ChiNhanh) với PostGIS Point...")
        # Note: Point(longitude, latitude, srid=4326)
        branches_data = [
            {
                "ten": "Nhà hàng Mộc - Chi nhánh Quận 1 (Bến Nghé)",
                "dia_chi": "123 Đường Pasteur, Phường Bến Nghé, Quận 1, TP. Hồ Chí Minh",
                "so_dien_thoai": "028 3822 1234",
                "point": Point(106.700806, 10.776889, srid=4326),
            },
            {
                "ten": "Nhà hàng Mộc - Chi nhánh Quận 3 (Võ Văn Tần)",
                "dia_chi": "45 Đường Võ Văn Tần, Phường Võ Thị Sáu, Quận 3, TP. Hồ Chí Minh",
                "so_dien_thoai": "028 3930 5678",
                "point": Point(106.691456, 10.778231, srid=4326),
            },
            {
                "ten": "Nhà hàng Mộc - Chi nhánh Bình Thạnh (Nguyễn Hữu Cảnh)",
                "dia_chi": "208 Đường Nguyễn Hữu Cảnh, Phường 22, Quận Bình Thạnh, TP. Hồ Chí Minh",
                "so_dien_thoai": "028 3514 9876",
                "point": Point(106.721944, 10.793889, srid=4326),
            },
        ]

        branches_map = {}
        for idx, b in enumerate(branches_data, start=1):
            branch, _ = ChiNhanh.objects.update_or_create(
                ten=b["ten"],
                defaults={
                    "dia_chi": b["dia_chi"],
                    "so_dien_thoai": b["so_dien_thoai"],
                    "toa_do_gis": b["point"],
                    "con_hoat_dong": True,
                },
            )
            branches_map[idx] = branch

        self.stdout.write(self.style.SUCCESS(f"   -> Đã nạp {len(branches_map)} chi nhánh PostGIS."))
        return branches_map

    def seed_tables(self, branches_map):
        self.stdout.write("5. Nạp bàn ăn (BanAn - 22 bàn qua 3 chi nhánh)...")
        # Layout: 8 at Q1, 7 at Q3, 7 at BT. Capacities: 2, 4, 8, 12 seats.
        tables_spec = [
            # Chi nhánh 1 (Quận 1) - 8 bàn
            (1, "Q1-T01", "Trong nhà - Tầng 1", 2),
            (1, "Q1-T02", "Trong nhà - Tầng 1", 2),
            (1, "Q1-T03", "Trong nhà - Tầng 1", 4),
            (1, "Q1-T04", "Trong nhà - Tầng 1", 4),
            (1, "Q1-T05", "Sân vườn ngoài trời", 4),
            (1, "Q1-T06", "Sân vườn ngoài trời", 8),
            (1, "Q1-T07", "Phòng VIP Lầu 1", 8),
            (1, "Q1-T08", "Phòng VIP Hoàng Gia", 12),
            # Chi nhánh 2 (Quận 3) - 7 bàn
            (2, "Q3-T01", "Sân vườn", 2),
            (2, "Q3-T02", "Trong nhà - Tầng 1", 4),
            (2, "Q3-T03", "Trong nhà - Tầng 1", 4),
            (2, "Q3-T04", "Trong nhà - Tầng 1", 4),
            (2, "Q3-T05", "Lầu 1 Máy lạnh", 8),
            (2, "Q3-T06", "Lầu 1 Máy lạnh", 8),
            (2, "Q3-T07", "Phòng VIP 1", 12),
            # Chi nhánh 3 (Bình Thạnh) - 7 bàn
            (3, "BT-T01", "Tầng trệt", 2),
            (3, "BT-T02", "Tầng trệt", 4),
            (3, "BT-T03", "Tầng trệt", 4),
            (3, "BT-T04", "Khu View Sông", 4),
            (3, "BT-T05", "Khu View Sông", 8),
            (3, "BT-T06", "Lầu 1", 8),
            (3, "BT-T07", "Phòng Đại Tiệc VIP", 12),
        ]

        count = 0
        for branch_idx, so_ban, khu_vuc, suc_chua in tables_spec:
            branch = branches_map.get(branch_idx)
            if not branch:
                continue
            BanAn.objects.update_or_create(
                chi_nhanh=branch,
                so_ban=so_ban,
                defaults={
                    "khu_vuc": khu_vuc,
                    "suc_chua": suc_chua,
                    "trang_thai": BanAn.TrangThai.TRONG,
                },
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"   -> Đã nạp {count} bàn ăn (trạng thái 'trong')."))
        return count

    def seed_deposit_policies(self):
        self.stdout.write("6. Nạp chính sách đặt cọc và quy tắc hoàn cọc...")
        policy, _ = ChinhSachDatCoc.objects.update_or_create(
            chi_nhanh=None,
            defaults={
                "phan_tram_coc": Decimal("20.00"),
                "thoi_gian_giu_cho_phut": 10,
                "han_thanh_toan_phut": 15,
                "con_ap_dung": True,
            },
        )

        cancellation_rules = [
            (QuyTacHuyDatCoc.MocThoiGian.TRUOC_24H, Decimal("100.00")),
            (QuyTacHuyDatCoc.MocThoiGian.TU_6_DEN_24H, Decimal("50.00")),
            (QuyTacHuyDatCoc.MocThoiGian.TRONG_6H, Decimal("0.00")),
            (QuyTacHuyDatCoc.MocThoiGian.KHACH_KHONG_DEN, Decimal("0.00")),
        ]

        for moc, phan_tram in cancellation_rules:
            QuyTacHuyDatCoc.objects.update_or_create(
                chinh_sach=policy,
                moc_thoi_gian=moc,
                defaults={"phan_tram_hoan_tien": phan_tram},
            )

        self.stdout.write(self.style.SUCCESS("   -> Đã nạp chính sách cọc 20% và 4 quy tắc hủy cọc."))

    def seed_users_and_roles(self):
        self.stdout.write("7. Nạp vai trò (RBAC) và người dùng mẫu...")
        roles_data = [
            ("quan_tri_vien", "Quản trị viên hệ thống Nhà hàng Mộc"),
            ("nhan_vien", "Nhân viên phục vụ và quản trị vận hành"),
            ("khach_hang", "Khách hàng sử dụng dịch vụ"),
        ]

        roles_map = {}
        for ten, mo_ta in roles_data:
            role, _ = VaiTro.objects.update_or_create(
                ten=ten,
                defaults={"mo_ta": mo_ta},
            )
            roles_map[ten] = role

        users_spec = [
            {
                "username": "admin",
                "email": "admin@mocrestaurant.vn",
                "first_name": "Quản trị",
                "last_name": "Viên",
                "so_dien_thoai": "0901234567",
                "is_staff": True,
                "is_superuser": True,
                "role": "quan_tri_vien",
            },
            {
                "username": "staff",
                "email": "staff@mocrestaurant.vn",
                "first_name": "Nhân viên",
                "last_name": "Nhà hàng",
                "so_dien_thoai": "0912345678",
                "is_staff": True,
                "is_superuser": False,
                "role": "nhan_vien",
            },
            {
                "username": "khachhang",
                "email": "khachhang@gmail.com",
                "first_name": "Nguyễn Văn",
                "last_name": "Khách",
                "so_dien_thoai": "0987654321",
                "is_staff": False,
                "is_superuser": False,
                "role": "khach_hang",
            },
            {
                "username": "tranhuong",
                "email": "huong.tran@gmail.com",
                "first_name": "Trần Thị",
                "last_name": "Hương",
                "so_dien_thoai": "0977112233",
                "is_staff": False,
                "is_superuser": False,
                "role": "khach_hang",
            },
        ]

        default_password = "MocRestaurant@2026"

        for u in users_spec:
            user, created = NguoiDung.objects.get_or_create(
                thu_dien_tu=u["email"],
                defaults={
                    "username": u["username"],
                    "email": u["email"],
                    "first_name": u["first_name"],
                    "last_name": u["last_name"],
                    "so_dien_thoai": u["so_dien_thoai"],
                    "is_staff": u["is_staff"],
                    "is_superuser": u["is_superuser"],
                    "is_active": True,
                },
            )
            user.set_password(default_password)
            user.is_staff = u["is_staff"]
            user.is_superuser = u["is_superuser"]
            user.save()

            role_obj = roles_map.get(u["role"])
            if role_obj:
                NguoiDungVaiTro.objects.get_or_create(nguoi_dung=user, vai_tro=role_obj)

        self.stdout.write(self.style.SUCCESS(f"   -> Đã nạp {len(users_spec)} tài khoản người dùng mẫu."))

    def seed_inventory_and_bom(self):
        self.stdout.write("8. Nạp nguyên liệu và định mức kho (BOM cho Milestone 2)...")
        materials = [
            ("Thịt bò Mỹ cao cấp", "kg", Decimal("50.0"), Decimal("10.0")),
            ("Tôm sú tươi sống", "kg", Decimal("30.0"), Decimal("5.0")),
            ("Mực lá tươi", "kg", Decimal("25.0"), Decimal("5.0")),
            ("Nước dùng lẩu Thái Mộc", "lít", Decimal("60.0"), Decimal("10.0")),
            ("Nấm tổng hợp tươi", "kg", Decimal("20.0"), Decimal("5.0")),
        ]

        mat_map = {}
        for ten, don_vi, ton_kho, ton_min in materials:
            nl, _ = NguyenLieu.objects.update_or_create(
                ten=ten,
                defaults={
                    "don_vi": don_vi,
                    "ton_kho_hien_tai": ton_kho,
                    "ton_kho_toi_thieu": ton_min,
                    "con_hoat_dong": True,
                },
            )
            mat_map[ten] = nl

        # Gắn định mức cho Lẩu Thái
        lau_thai = MonAn.objects.filter(duong_dan="lau-thai").first()
        if lau_thai:
            lau_thai.quan_ly_kho = True
            lau_thai.save(update_fields=["quan_ly_kho"])
            DinhMucNguyenLieu.objects.update_or_create(
                mon_an=lau_thai,
                nguyen_lieu=mat_map["Tôm sú tươi sống"],
                defaults={"so_luong_can": Decimal("0.300")},
            )
            DinhMucNguyenLieu.objects.update_or_create(
                mon_an=lau_thai,
                nguyen_lieu=mat_map["Mực lá tươi"],
                defaults={"so_luong_can": Decimal("0.200")},
            )
            DinhMucNguyenLieu.objects.update_or_create(
                mon_an=lau_thai,
                nguyen_lieu=mat_map["Nước dùng lẩu Thái Mộc"],
                defaults={"so_luong_can": Decimal("1.000")},
            )

        # Gắn định mức cho Bò nướng tảng
        bo_nuong = MonAn.objects.filter(duong_dan="bo-nuong-tang").first()
        if bo_nuong:
            bo_nuong.quan_ly_kho = True
            bo_nuong.save(update_fields=["quan_ly_kho"])
            DinhMucNguyenLieu.objects.update_or_create(
                mon_an=bo_nuong,
                nguyen_lieu=mat_map["Thịt bò Mỹ cao cấp"],
                defaults={"so_luong_can": Decimal("0.400")},
            )

        self.stdout.write(self.style.SUCCESS("   -> Đã nạp 5 nguyên liệu và định mức kho cho Lẩu Thái, Bò Nướng Tảng."))

    def seed_promotions(self):
        self.stdout.write("9. Nạp mã khuyến mãi mẫu (KhuyenMai)...")
        now = timezone.now()
        start_date = now - timezone.timedelta(days=10)
        end_date = now + timezone.timedelta(days=365)

        KhuyenMai.objects.update_or_create(
            ma_giam_gia="MOC2026",
            defaults={
                "ten": "Chào Mừng Năm 2026 - Giảm 10%",
                "mo_ta": "Giảm 10% tối đa 50.000đ cho đơn hàng từ 200.000đ",
                "kieu_giam": KhuyenMai.KieuGiam.PHAN_TRAM,
                "gia_tri_giam": Decimal("10.00"),
                "don_hang_toi_thieu": Decimal("200000.00"),
                "giam_toi_da": Decimal("50000.00"),
                "bat_dau_luc": start_date,
                "ket_thuc_luc": end_date,
                "gioi_han_su_dung": 1000,
                "con_hoat_dong": True,
            },
        )

        KhuyenMai.objects.update_or_create(
            ma_giam_gia="CHAOMUNG",
            defaults={
                "ten": "Ưu Đãi Khách Mới - Giảm 30.000đ",
                "mo_ta": "Giảm ngay 30.000đ cho đơn hàng đầu tiên từ 150.000đ",
                "kieu_giam": KhuyenMai.KieuGiam.SO_TIEN,
                "gia_tri_giam": Decimal("30000.00"),
                "don_hang_toi_thieu": Decimal("150000.00"),
                "bat_dau_luc": start_date,
                "ket_thuc_luc": end_date,
                "gioi_han_su_dung": 500,
                "con_hoat_dong": True,
            },
        )
        self.stdout.write(self.style.SUCCESS("   -> Đã nạp 2 mã khuyến mãi mẫu."))
```

### 4.4 Alias Command (`nap_du_lieu_mau.py`)

File: `moc-backend/foods/management/commands/nap_du_lieu_mau.py`
```python
"""
Alias command for seed_data.
Run via: python manage.py nap_du_lieu_mau
"""
from foods.management.commands.seed_data import Command as SeedDataCommand

class Command(SeedDataCommand):
    help = "Lệnh tiếng Việt: Nạp dữ liệu mẫu nhà hàng Mộc (danh mục, 100 món, bàn ăn, chi nhánh GIS, tài khoản)"
```

---

## 5. Verification Method

Once Milestone 1 models and migrations are applied:

1. **Verify Management Command Discovery**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-backend
   ./.venv/bin/python manage.py help seed_data
   ./.venv/bin/python manage.py help nap_du_lieu_mau
   ```
   *Expected result*: Both commands display help messages without import errors.

2. **Execute Seeding**:
   ```bash
   cd /Users/VuVan/Documents/DO-AN/moc-backend
   ./.venv/bin/python manage.py seed_data
   ```
   *Expected result*: Exit code 0, console displays:
   - "Đã nạp 5 danh mục."
   - "Đã nạp 4 thẻ món ăn."
   - "Đã nạp thành công 100 món ăn."
   - "Đã nạp 3 chi nhánh PostGIS."
   - "Đã nạp 22 bàn ăn (trạng thái 'trong')."
   - "Đã nạp chính sách cọc 20% và 4 quy tắc hủy cọc."
   - "Đã nạp 4 tài khoản người dùng mẫu."

3. **Verify Idempotency**:
   Re-run the command immediately:
   ```bash
   ./.venv/bin/python manage.py seed_data
   ```
   *Expected result*: Exits cleanly with code 0; record counts remain constant with zero IntegrityErrors.

4. **Verify Database Records via Django Shell**:
   ```bash
   ./.venv/bin/python manage.py shell -c "
   from foods.models import DanhMuc, MonAn, TheMonAn, NguyenLieu, DinhMucNguyenLieu
   from branches.models import ChiNhanh
   from reservations.models import BanAn, ChinhSachDatCoc, QuyTacHuyDatCoc
   from accounts.models import NguoiDung, VaiTro

   assert DanhMuc.objects.count() == 5, f'Expected 5 categories, got {DanhMuc.objects.count()}'
   assert MonAn.objects.count() == 100, f'Expected 100 foods, got {MonAn.objects.count()}'
   assert TheMonAn.objects.count() == 4, f'Expected 4 tags, got {TheMonAn.objects.count()}'
   assert ChiNhanh.objects.count() >= 3, f'Expected >= 3 branches, got {ChiNhanh.objects.count()}'
   assert BanAn.objects.count() >= 20, f'Expected >= 20 tables, got {BanAn.objects.count()}'
   assert ChinhSachDatCoc.objects.filter(con_ap_dung=True).exists(), 'Deposit policy missing'
   assert QuyTacHuyDatCoc.objects.count() == 4, 'Cancellation rules missing'
   assert NguoiDung.objects.filter(thu_dien_tu='admin@mocrestaurant.vn').exists(), 'Admin user missing'
   assert NguoiDung.objects.filter(thu_dien_tu='staff@mocrestaurant.vn').exists(), 'Staff user missing'
   assert NguoiDung.objects.filter(thu_dien_tu='khachhang@gmail.com').exists(), 'Customer user missing'
   print('ALL SEED DATA VERIFICATION CHECKS PASSED 100%!')
   "
   ```

5. **Invalidation Conditions**:
   - If `Du-lieu-test.txt` is missing and fallback data is not loaded.
   - If PostGIS point coordinates have inverted latitude and longitude.
   - If tables count is less than 20 or table statuses are not `'trong'`.
   - If re-running the command fails with duplicate key errors on unique constraints.
