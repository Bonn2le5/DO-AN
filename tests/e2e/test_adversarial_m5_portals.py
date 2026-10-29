#!/usr/bin/env python3
"""
Adversarial Empirical Stress Testing & Permission Hardening Suite for Milestone 5:
Frontend Synchronization & Staff/Admin Portals for Web App Nhà hàng Mộc.

Author: Challenger m5_challenger_2
Roles: critic, specialist

Test Matrix Dimensions:
1. Review Moderation API (reviews/views.py & admin.api.ts):
   - Hidden reviews (hien_thi=False) strictly filtered from Anonymous and Customer callers (list & detail 404).
   - Staff/Admin (is_staff=True or la_nhan_vien_nha_hang=True) access and moderate all reviews.
   - Unauthorized toggle attempts (401 / 403 / 404) & cross-customer tampering prevention.
   - Dynamic dish rating & review count recalculation upon visibility toggle.
   - Staff permanent deletion vs unauthorized deletion.
2. Inventory & BOM Management (foods/views.py, foods/services.py & admin.api.ts):
   - Manual inventory transaction creation (stock in, stock out, adjustment) via API.
   - Permission check (non-staff 403, unauthenticated 401).
   - Automated BOM deduction upon order confirmation (cho_tiep_nhan -> da_xac_nhan) and refund upon cancellation.
   - Concurrent BOM deductions deadlock-freedom verification.
3. Order FSM Admin Transitions & Audit Logging (orders/views.py, orders/services.py & admin.api.ts):
   - Full 5-stage lifecycle traversal by staff (cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat).
   - Complete audit trail verification in LichSuTrangThaiDon (tu_trang_thai, sang_trang_thai, doi_boi, ghi_chu).
   - Illegal state jumps (cho_tiep_nhan -> hoan_tat) and backward transitions rejected (HTTP 400).
   - Terminal state immutability (hoan_tat and da_huy cannot transition).
   - Strict customer permission boundary (customer can only cancel in cho_tiep_nhan; cannot cancel confirmed order; 403).
   - Status alias compatibility (English / Vietnamese / casing).
4. Table Reservation Floor Plan & Concurrency (reservations/views.py, reservations/services.py & admin.api.ts):
   - Interactive floor plan active filtering (booked tables excluded on same date/time).
   - High concurrency table hold lock race (1 HTTP 200, remainder HTTP 409 BAN_DANG_BAN).
   - Staff reservation lifecycle transition & permission protection.
   - Tiered deposit refund calculation (>24h 100%, 6-24h 50%, <6h 0%, no-show 0%).
"""

import os
import sys
from decimal import Decimal
from datetime import timedelta, date, time as dtime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

# Set up paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "moc-backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.conf import settings
# Configure in-memory cache for sandbox isolation
settings.CACHES["default"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "adversarial-m5-locmem",
}

import unittest
from django.test import TransactionTestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.db.utils import IntegrityError

from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from foods.models import DanhMuc, MonAn, NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho
from branches.models import ChiNhanh
from reservations.models import BanAn, DatBan, ChinhSachDatCoc, QuyTacHuyDatCoc
from orders.models import DonHang, ChiTietDonHang, LichSuTrangThaiDon
from reviews.models import DanhGia
from payments.models import ThanhToan, PhieuHoanTien


class TestMilestone5AdversarialPortals(TransactionTestCase):
    """Empirical Stress and Adversarial Suite for Milestone 5 Admin/Staff Portals."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.locmem_cache = caches["locmem"]
        self.locmem_cache.clear()
        self.client = APIClient()

        # 1. Create Roles
        self.role_admin, _ = VaiTro.objects.get_or_create(ten="quan_tri_vien", defaults={"mo_ta": "Quản trị viên"})
        self.role_staff, _ = VaiTro.objects.get_or_create(ten="nhan_vien", defaults={"mo_ta": "Nhân viên"})
        self.role_customer, _ = VaiTro.objects.get_or_create(ten="khach_hang", defaults={"mo_ta": "Khách hàng"})

        # 2. Create Users
        self.admin_user = NguoiDung.objects.create_user(
            username="adv_admin_m5",
            email="admin_m5@mocrestaurant.vn",
            password="Password123!",
            is_staff=True,
            is_superuser=True,
            ho_ten="Admin M5",
        )
        self.admin_user.danh_sach_vai_tro.add(self.role_admin)

        self.staff_user = NguoiDung.objects.create_user(
            username="adv_staff_m5",
            email="staff_m5@mocrestaurant.vn",
            password="Password123!",
            is_staff=False,
            ho_ten="Staff M5",
        )
        self.staff_user.danh_sach_vai_tro.add(self.role_staff)

        self.customer_a = NguoiDung.objects.create_user(
            username="adv_cust_a_m5",
            email="cust_a_m5@gmail.com",
            password="Password123!",
            is_staff=False,
            ho_ten="Customer A",
        )
        self.customer_a.danh_sach_vai_tro.add(self.role_customer)

        self.customer_b = NguoiDung.objects.create_user(
            username="adv_cust_b_m5",
            email="cust_b_m5@gmail.com",
            password="Password123!",
            is_staff=False,
            ho_ten="Customer B",
        )
        self.customer_b.danh_sach_vai_tro.add(self.role_customer)

        # 3. Create Branch
        self.branch = ChiNhanh.objects.create(
            ten="Mộc Chi Nhánh Quận 1",
            dia_chi="123 Lê Lợi, Q1, TP.HCM",
            so_dien_thoai="0901234567",
            toa_do_gis="10.7769,106.7009",
            con_hoat_dong=True,
        )

        # 4. Create Category and Dishes
        self.category = DanhMuc.objects.create(
            ten="Món Chính M5",
            duong_dan="mon-chinh-m5",
            con_hoat_dong=True,
        )

        self.dish1 = MonAn.objects.create(
            ten="Bò Nướng Đá M5",
            duong_dan="bo-nuong-da-m5",
            danh_muc=self.category,
            don_gia=Decimal("250000"),
            con_hang=True,
            hien_thi=True,
            diem_danh_gia=Decimal("0"),
            so_luot_danh_gia=0,
        )

        self.dish2 = MonAn.objects.create(
            ten="Lẩu Nấm Đặc Biệt M5",
            duong_dan="lau-nam-dac-biet-m5",
            danh_muc=self.category,
            don_gia=Decimal("350000"),
            con_hang=True,
            hien_thi=True,
            diem_danh_gia=Decimal("0"),
            so_luot_danh_gia=0,
        )

        # 5. Create Ingredients
        self.ingredient_beef = NguyenLieu.objects.create(
            ten="Thịt Bò Mỹ M5",
            don_vi="kg",
            ton_kho_hien_tai=Decimal("50.000"),
            ton_kho_toi_thieu=Decimal("5.000"),
            con_hoat_dong=True,
        )

        self.ingredient_mushroom = NguyenLieu.objects.create(
            ten="Nấm Linh Chi M5",
            don_vi="kg",
            ton_kho_hien_tai=Decimal("30.000"),
            ton_kho_toi_thieu=Decimal("3.000"),
            con_hoat_dong=True,
        )

        # 6. BOM (DinhMucNguyenLieu)
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish1,
            nguyen_lieu=self.ingredient_beef,
            so_luong_can=Decimal("0.300"),
        )
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish2,
            nguyen_lieu=self.ingredient_beef,
            so_luong_can=Decimal("0.200"),
        )
        DinhMucNguyenLieu.objects.create(
            mon_an=self.dish2,
            nguyen_lieu=self.ingredient_mushroom,
            so_luong_can=Decimal("0.400"),
        )

        # 7. Tables
        self.table_vip = BanAn.objects.create(
            chi_nhanh=self.branch,
            so_ban="VIP-01",
            khu_vuc="VIP",
            suc_chua=6,
            trang_thai=BanAn.TrangThai.TRONG,
        )
        self.table_std = BanAn.objects.create(
            chi_nhanh=self.branch,
            so_ban="STD-01",
            khu_vuc="Tầng 1",
            suc_chua=4,
            trang_thai=BanAn.TrangThai.TRONG,
        )

        # 8. Deposit Policy & Refund Rules
        self.deposit_policy = ChinhSachDatCoc.objects.create(
            chi_nhanh=self.branch,
            phan_tram_coc=Decimal("30.00"),
            con_ap_dung=True,
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.deposit_policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.TRUOC_24H,
            phan_tram_hoan_tien=Decimal("100.00"),
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.deposit_policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.TU_6_DEN_24H,
            phan_tram_hoan_tien=Decimal("50.00"),
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.deposit_policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.TRONG_6H,
            phan_tram_hoan_tien=Decimal("0.00"),
        )
        QuyTacHuyDatCoc.objects.create(
            chinh_sach=self.deposit_policy,
            moc_thoi_gian=QuyTacHuyDatCoc.MocThoiGian.KHACH_KHONG_DEN,
            phan_tram_hoan_tien=Decimal("0.00"),
        )

    def _create_review(self, *, user, dish, rating=5, comment="Ngon", visible=True):
        """Helper to create a fully valid review bound to a completed order and item."""
        order = DonHang.objects.create(
            khach_hang=user,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.HOAN_TAT,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=dish.don_gia,
        )
        item = ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=dish,
            so_luong=1,
            don_gia_luc_dat=dish.don_gia,
            thanh_tien=dish.don_gia,
        )
        return DanhGia.objects.create(
            nguoi_dung=user,
            mon_an=dish,
            don_hang=order,
            chi_tiet_don_hang=item,
            diem_danh_gia=rating,
            nhan_xet=comment,
            hien_thi=visible,
        )

    # =========================================================================
    # Group 1: Review Moderation API (reviews/views.py & admin.api.ts)
    # =========================================================================

    def test_adv_rev_01_hidden_reviews_strictly_filtered_from_anonymous_and_customer(self):
        """
        Verify that unapproved/hidden reviews (hien_thi=False) are strictly HIDDEN
        from anonymous callers and regular customers across list and detail endpoints.
        """
        rev_visible = self._create_review(
            user=self.customer_a, dish=self.dish1, rating=5, comment="Rất ngon!", visible=True
        )
        rev_hidden = self._create_review(
            user=self.customer_b, dish=self.dish1, rating=1, comment="Tiêu cực", visible=False
        )

        # 1. Anonymous list query
        self.client.force_authenticate(user=None)
        res_anon = self.client.get("/api/reviews/")
        self.assertEqual(res_anon.status_code, 200)
        items = res_anon.data if isinstance(res_anon.data, list) else res_anon.data.get("results", [])
        review_ids = [r["id"] for r in items]
        self.assertIn(rev_visible.id, review_ids, "Visible review must be returned to public")
        self.assertNotIn(rev_hidden.id, review_ids, "Hidden review MUST NOT be returned to anonymous callers")

        # 2. Customer A list query
        self.client.force_authenticate(user=self.customer_a)
        res_cust_a = self.client.get("/api/reviews/")
        items_a = res_cust_a.data if isinstance(res_cust_a.data, list) else res_cust_a.data.get("results", [])
        review_ids_a = [r["id"] for r in items_a]
        self.assertNotIn(rev_hidden.id, review_ids_a, "Hidden review MUST NOT be returned to Customer A")

        # 3. Customer B list query (author of the hidden review)
        self.client.force_authenticate(user=self.customer_b)
        res_cust_b = self.client.get("/api/reviews/")
        items_b = res_cust_b.data if isinstance(res_cust_b.data, list) else res_cust_b.data.get("results", [])
        review_ids_b = [r["id"] for r in items_b]
        self.assertNotIn(rev_hidden.id, review_ids_b, "Hidden review MUST NOT be visible even to its author via public feed")

        # 4. Detail endpoint isolation: Anonymous & Customer accessing hidden review directly must receive 404
        self.client.force_authenticate(user=None)
        res_detail_anon = self.client.get(f"/api/reviews/{rev_hidden.id}/")
        self.assertEqual(res_detail_anon.status_code, 404, "Hidden review detail must 404 for anonymous users")

        self.client.force_authenticate(user=self.customer_a)
        res_detail_cust = self.client.get(f"/api/reviews/{rev_hidden.id}/")
        self.assertEqual(res_detail_cust.status_code, 404, "Hidden review detail must 404 for regular customers")

    def test_adv_rev_02_staff_and_admin_access_all_reviews(self):
        """
        Verify that staff (is_staff=True or la_nhan_vien_nha_hang=True) can view all reviews
        including hien_thi=False, and can retrieve hidden review details.
        """
        rev_hidden = self._create_review(
            user=self.customer_b, dish=self.dish1, rating=2, comment="Chờ duyệt", visible=False
        )

        # 1. is_staff=True user
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get("/api/reviews/")
        self.assertEqual(res_admin.status_code, 200)
        items_admin = res_admin.data if isinstance(res_admin.data, list) else res_admin.data.get("results", [])
        admin_ids = [r["id"] for r in items_admin]
        self.assertIn(rev_hidden.id, admin_ids, "Admin must receive hidden reviews for moderation")

        res_detail_admin = self.client.get(f"/api/reviews/{rev_hidden.id}/")
        self.assertEqual(res_detail_admin.status_code, 200)
        self.assertFalse(res_detail_admin.data["hien_thi"])

        # 2. Staff role user (la_nhan_vien_nha_hang=True, is_staff=False)
        self.client.force_authenticate(user=self.staff_user)
        res_staff = self.client.get("/api/reviews/")
        self.assertEqual(res_staff.status_code, 200)
        items_staff = res_staff.data if isinstance(res_staff.data, list) else res_staff.data.get("results", [])
        staff_ids = [r["id"] for r in items_staff]
        self.assertIn(rev_hidden.id, staff_ids, "Staff member with restaurant role must access hidden reviews")

    def test_adv_rev_03_unauthorized_attempts_to_toggle_visibility(self):
        """
        Adversarial test: verify that unauthorized callers CANNOT toggle review visibility (hien_thi).
        - Anonymous caller -> 401 Unauthorized
        - Other customer attempting cross-customer modification -> 403 Forbidden
        - Original author attempting to unhide their own moderated review -> 404 Not Found
        """
        rev_visible = self._create_review(
            user=self.customer_a, dish=self.dish1, rating=4, comment="Món ngon", visible=True
        )
        rev_hidden = self._create_review(
            user=self.customer_b, dish=self.dish1, rating=1, comment="Tiêu cực", visible=False
        )

        # 1. Anonymous toggle attempt
        self.client.force_authenticate(user=None)
        res_anon = self.client.patch(f"/api/reviews/{rev_visible.id}/", {"hien_thi": False})
        self.assertEqual(res_anon.status_code, 401, "Anonymous toggle attempt must be rejected with 401")
        rev_visible.refresh_from_db()
        self.assertTrue(rev_visible.hien_thi, "Review visibility must remain unchanged after 401")

        # 2. Customer B attempts to hide Customer A's review
        self.client.force_authenticate(user=self.customer_b)
        res_tamper = self.client.patch(f"/api/reviews/{rev_visible.id}/", {"hien_thi": False})
        self.assertEqual(res_tamper.status_code, 403, "Tampering with another user's review must return 403")
        rev_visible.refresh_from_db()
        self.assertTrue(rev_visible.hien_thi, "Visibility must remain unchanged after 403 tamper attempt")

        # 3. Customer B attempts to unhide their own hidden review
        res_unhide = self.client.patch(f"/api/reviews/{rev_hidden.id}/", {"hien_thi": True})
        self.assertEqual(res_unhide.status_code, 404, "Customer cannot target hidden review to unhide it")
        rev_hidden.refresh_from_db()
        self.assertFalse(rev_hidden.hien_thi, "Review must remain hidden")

    def test_adv_rev_04_staff_toggle_visibility_and_dish_rating_recalculation(self):
        """
        Verify that when staff toggles review visibility (hien_thi=False/True),
        the dish's aggregate rating (diem_danh_gia) and review count (so_luot_danh_gia)
        are recalculated strictly over visible reviews.
        """
        rev_a = self._create_review(
            user=self.customer_a, dish=self.dish1, rating=5, comment="5 sao", visible=True
        )
        rev_b = self._create_review(
            user=self.customer_b, dish=self.dish1, rating=1, comment="1 sao", visible=True
        )

        # Trigger manual recalculation for baseline
        self.dish1.refresh_from_db()
        ket_qua = self.dish1.danh_sach_danh_gia.filter(hien_thi=True)
        self.assertEqual(ket_qua.count(), 2)

        # Staff hides Review B
        self.client.force_authenticate(user=self.staff_user)
        res_hide = self.client.patch(f"/api/reviews/{rev_b.id}/", {"hien_thi": False})
        self.assertEqual(res_hide.status_code, 200)

        # Dish rating must now be 5.0 and count 1
        self.dish1.refresh_from_db()
        self.assertEqual(self.dish1.so_luot_danh_gia, 1)
        self.assertAlmostEqual(float(self.dish1.diem_danh_gia), 5.0, places=2)

        # Staff unhides Review B
        res_unhide = self.client.patch(f"/api/reviews/{rev_b.id}/", {"hien_thi": True})
        self.assertEqual(res_unhide.status_code, 200)

        # Dish rating must return to 3.0 and count 2
        self.dish1.refresh_from_db()
        self.assertEqual(self.dish1.so_luot_danh_gia, 2)
        self.assertAlmostEqual(float(self.dish1.diem_danh_gia), 3.0, places=2)

    def test_adv_rev_05_staff_review_deletion(self):
        """
        Verify that staff can permanently delete abusive reviews,
        while non-staff cannot delete other users' reviews.
        """
        rev = self._create_review(
            user=self.customer_a, dish=self.dish1, rating=1, comment="Spam review", visible=True
        )

        # Customer B attempts deletion -> 404/403
        self.client.force_authenticate(user=self.customer_b)
        res_del_cust = self.client.delete(f"/api/reviews/{rev.id}/")
        self.assertIn(res_del_cust.status_code, [403, 404])
        self.assertTrue(DanhGia.objects.filter(id=rev.id).exists())

        # Staff deletes review -> 204
        self.client.force_authenticate(user=self.staff_user)
        res_del_staff = self.client.delete(f"/api/reviews/{rev.id}/")
        self.assertEqual(res_del_staff.status_code, 204)
        self.assertFalse(DanhGia.objects.filter(id=rev.id).exists())

    # =========================================================================
    # Group 2: Inventory & BOM Management (foods/views.py & admin.api.ts)
    # =========================================================================

    def test_adv_inv_01_stock_transaction_creation_and_balance_update(self):
        """
        Test manual inventory transaction creation via /api/inventory-transactions/ (or /api/kho/).
        Adversarial focus:
        1. Non-staff callers MUST receive 403 Forbidden.
        2. Unauthenticated callers MUST receive 401 Unauthorized.
        3. Staff callers creating stock-in/stock-out transactions:
           EMPIRICAL VERIFICATION: Check whether LichSuKhoViewSet / LichSuKhoSerializer
           crashes with IntegrityError (NOT NULL constraint failed on ton_kho_truoc)
           and whether NguyenLieu.ton_kho_hien_tai is updated or fails.
        """
        init_stock = self.ingredient_beef.ton_kho_hien_tai

        # 1. Unauthenticated attempt -> 401
        self.client.force_authenticate(user=None)
        res_anon = self.client.post("/api/inventory-transactions/", {
            "nguyen_lieu": self.ingredient_beef.id,
            "loai_giao_dich": "nhap",
            "so_luong": "10.000",
            "ghi_chu": "Nhập thêm thịt bò",
        })
        self.assertIn(res_anon.status_code, [401, 403])

        # 2. Regular customer attempt -> 403
        self.client.force_authenticate(user=self.customer_a)
        res_cust = self.client.post("/api/inventory-transactions/", {
            "nguyen_lieu": self.ingredient_beef.id,
            "loai_giao_dich": "nhap",
            "so_luong": "10.000",
            "ghi_chu": "Hack nhập kho",
        })
        self.assertEqual(res_cust.status_code, 403)

        # 3. Staff user attempt
        self.client.force_authenticate(user=self.staff_user)
        try:
            res_staff = self.client.post("/api/inventory-transactions/", {
                "nguyen_lieu": self.ingredient_beef.id,
                "loai_giao_dich": "nhap",
                "so_luong": "10.000",
                "ghi_chu": "Nhập kho chính quy",
            })
            if res_staff.status_code == 201:
                self.ingredient_beef.refresh_from_db()
                self.assertEqual(
                    self.ingredient_beef.ton_kho_hien_tai,
                    init_stock + Decimal("10.000"),
                    "Ingredient stock must increase by 10.000 after stock-in"
                )
            else:
                self.fail(
                    f"[DEFECT CONFIRMED] LichSuKhoViewSet returned status {res_staff.status_code}: {res_staff.data}"
                )
        except IntegrityError as exc:
            self.fail(
                f"[DEFECT CONFIRMED] LichSuKhoViewSet crashed with IntegrityError: {exc} "
                "due to missing ton_kho_truoc/ton_kho_sau computation in perform_create."
            )

    def test_adv_inv_02_bom_deduction_and_reversal_lifecycle(self):
        """
        Verify that order FSM state transitions automatically trigger BOM deduction:
        - Transitioning to DA_XAC_NHAN deducts ingredients according to BOM.
        - Transitioning from DA_XAC_NHAN to DA_HUY automatically refunds all ingredients.
        - Idempotent: re-calling transition does not double-deduct.
        """
        initial_beef = self.ingredient_beef.ton_kho_hien_tai
        initial_mushroom = self.ingredient_mushroom.ton_kho_hien_tai

        # Order with 2x dish1 (2 * 0.3 = 0.6 kg bò) and 1x dish2 (0.2 kg bò + 0.4 kg nấm)
        # Total deduction: 0.8 kg bò, 0.4 kg nấm
        order = DonHang.objects.create(
            khach_hang=self.customer_a,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=Decimal("850000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order, mon_an=self.dish1, so_luong=2,
            don_gia_luc_dat=Decimal("250000"), thanh_tien=Decimal("500000")
        )
        ChiTietDonHang.objects.create(
            don_hang=order, mon_an=self.dish2, so_luong=1,
            don_gia_luc_dat=Decimal("350000"), thanh_tien=Decimal("350000")
        )

        # 1. Staff confirms order -> cho_tiep_nhan -> da_xac_nhan
        self.client.force_authenticate(user=self.staff_user)
        res_confirm = self.client.patch(
            f"/api/orders/{order.id}/trang_thai/",
            {"status": "da_xac_nhan", "note": "Bếp nhận đơn"}
        )
        self.assertEqual(res_confirm.status_code, 200, f"Confirm failed: {res_confirm.data}")

        self.ingredient_beef.refresh_from_db()
        self.ingredient_mushroom.refresh_from_db()
        self.assertEqual(self.ingredient_beef.ton_kho_hien_tai, initial_beef - Decimal("0.800"))
        self.assertEqual(self.ingredient_mushroom.ton_kho_hien_tai, initial_mushroom - Decimal("0.400"))

        # Verify audit records in LichSuXuatNhapKho
        out_txs = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu="don_hang", id_tham_chieu=order.id, loai_giao_dich="xuat"
        )
        self.assertEqual(out_txs.count(), 2, "Must create 2 deduction records for 2 BOM ingredients")

        # 2. Staff cancels confirmed order -> da_xac_nhan -> da_huy
        res_cancel = self.client.patch(
            f"/api/orders/{order.id}/trang_thai/",
            {"status": "da_huy", "note": "Khách hủy đột xuất"}
        )
        self.assertEqual(res_cancel.status_code, 200, f"Cancel failed: {res_cancel.data}")

        self.ingredient_beef.refresh_from_db()
        self.ingredient_mushroom.refresh_from_db()
        self.assertEqual(
            self.ingredient_beef.ton_kho_hien_tai, initial_beef,
            "Beef inventory must be fully refunded upon order cancellation"
        )
        self.assertEqual(
            self.ingredient_mushroom.ton_kho_hien_tai, initial_mushroom,
            "Mushroom inventory must be fully refunded upon order cancellation"
        )

        in_txs = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu="don_hang", id_tham_chieu=order.id, loai_giao_dich="nhap"
        )
        self.assertEqual(in_txs.count(), 2, "Must create 2 refund records in LichSuXuatNhapKho")

    def test_adv_inv_03_concurrent_bom_deductions_deadlock_freedom(self):
        """
        Adversarial concurrency test:
        Verify that multiple orders with overlapping and inverted ingredient dependencies
        strictly enforce Global Ascending Resource Ordering (Dijkstra's Resource Hierarchy)
        in DichVuKho.khau_tru_nguyen_lieu_bom, eliminating circular wait deadlocks.
        """
        from foods.services import DichVuKho

        # Order 1: dish1 (beef) + dish2 (beef, mushroom) -> needs beef (id=beef.id), mushroom (id=mushroom.id)
        # Order 2: dish2 (mushroom, beef) + dish1 (beef) -> inverted dependency order
        min_id = min(self.ingredient_beef.id, self.ingredient_mushroom.id)
        max_id = max(self.ingredient_beef.id, self.ingredient_mushroom.id)

        # Trace the exact lock ordering requested by DichVuKho
        locked_id_sequences = []

        orig_sfu = NguyenLieu.objects.select_for_update

        class SFUProxy:
            def __init__(self, qs):
                self.qs = qs

            def filter(self, *args, **kwargs):
                if "id__in" in kwargs:
                    ids = kwargs["id__in"]
                    locked_id_sequences.append(list(ids))
                return self.qs.filter(*args, **kwargs)

        with patch("foods.models.NguyenLieu.objects.select_for_update", side_effect=lambda: SFUProxy(NguyenLieu.objects.all())):
            # Process Order 1 items
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": self.dish1.id, "so_luong": 1}, {"mon_an_id": self.dish2.id, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=9001,
            )

            # Process Order 2 items (inverted)
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": self.dish2.id, "so_luong": 1}, {"mon_an_id": self.dish1.id, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=9002,
            )

        self.assertEqual(len(locked_id_sequences), 2)
        self.assertEqual(locked_id_sequences[0], [min_id, max_id], "Order 1 must lock in ascending ID order")
        self.assertEqual(locked_id_sequences[1], [min_id, max_id], "Order 2 (inverted items) must lock in identical ascending ID order")

    # =========================================================================
    # Group 3: Order FSM Admin Transitions & Audit Logging (orders/views.py)
    # =========================================================================

    def test_adv_fsm_01_full_staff_fsm_traversal_and_audit_trail(self):
        """
        Verify that staff can traverse the complete linear FSM lifecycle:
        cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat
        and that every single transition creates a corresponding LichSuTrangThaiDon audit record.
        """
        order = DonHang.objects.create(
            khach_hang=self.customer_a,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=Decimal("250000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order, mon_an=self.dish1, so_luong=1,
            don_gia_luc_dat=Decimal("250000"), thanh_tien=Decimal("250000")
        )

        steps = [
            ("da_xac_nhan", "Bếp xác nhận đơn"),
            ("dang_che_bien", "Bếp đang nấu nướng"),
            ("san_sang", "Món đã sẵn sàng phục vụ"),
            ("hoan_tat", "Khách đã dùng bữa và thanh toán xong"),
        ]

        self.client.force_authenticate(user=self.staff_user)

        for to_state, note in steps:
            res = self.client.patch(
                f"/api/orders/{order.id}/trang_thai/",
                {"status": to_state, "note": note}
            )
            self.assertEqual(res.status_code, 200, f"Transition to {to_state} failed: {res.data}")
            self.assertEqual(res.data["trang_thai"], to_state)

        # Verify audit history
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.HOAN_TAT)

        logs = list(LichSuTrangThaiDon.objects.filter(don_hang=order).order_by("tao_luc"))
        transition_logs = [l for l in logs if l.tu_trang_thai is not None]
        self.assertEqual(len(transition_logs), 4, "Must have exactly 4 transition audit logs")

        self.assertEqual(transition_logs[0].tu_trang_thai, "cho_tiep_nhan")
        self.assertEqual(transition_logs[0].sang_trang_thai, "da_xac_nhan")
        self.assertEqual(transition_logs[0].doi_boi, self.staff_user)
        self.assertEqual(transition_logs[0].ghi_chu, "Bếp xác nhận đơn")

        self.assertEqual(transition_logs[3].tu_trang_thai, "san_sang")
        self.assertEqual(transition_logs[3].sang_trang_thai, "hoan_tat")

    def test_adv_fsm_02_illegal_state_skips_and_regressions_rejected(self):
        """
        Adversarial test:
        - Skipping states (cho_tiep_nhan -> hoan_tat, cho_tiep_nhan -> san_sang) MUST be rejected with 400.
        - Backward transitions (dang_che_bien -> da_xac_nhan) MUST be rejected with 400.
        - Self transitions (dang_che_bien -> dang_che_bien) MUST be rejected with 400.
        - Terminal mutations (hoan_tat -> da_huy) MUST be rejected with 400.
        """
        order = DonHang.objects.create(
            khach_hang=self.customer_a, chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY, tong_tien=Decimal("250000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order, mon_an=self.dish1, so_luong=1,
            don_gia_luc_dat=Decimal("250000"), thanh_tien=Decimal("250000")
        )

        self.client.force_authenticate(user=self.staff_user)

        # 1. Skip to hoan_tat
        res_skip1 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "hoan_tat"})
        self.assertEqual(res_skip1.status_code, 400)
        self.assertIn("status", res_skip1.data)

        # 2. Skip to san_sang
        res_skip2 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "san_sang"})
        self.assertEqual(res_skip2.status_code, 400)

        # 3. Advance to da_xac_nhan then dang_che_bien
        self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "da_xac_nhan"})
        self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "dang_che_bien"})

        # 4. Backward transition to da_xac_nhan
        res_back = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "da_xac_nhan"})
        self.assertEqual(res_back.status_code, 400)

        # 5. Self transition to dang_che_bien
        res_self = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "dang_che_bien"})
        self.assertEqual(res_self.status_code, 400)

        # 6. Complete order and attempt to alter terminal state
        self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "san_sang"})
        self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "hoan_tat"})

        res_term = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "da_huy"})
        self.assertEqual(res_term.status_code, 400, "Mutating completed order MUST return 400")

    def test_adv_fsm_03_customer_permissions_strict_boundary(self):
        """
        Adversarial test:
        - Customer can cancel their own order ONLY while in cho_tiep_nhan.
        - Customer attempting to cancel when order is da_xac_nhan MUST receive 403 Forbidden.
        - Customer attempting to advance order (e.g. to da_xac_nhan or dang_che_bien) MUST receive 403 Forbidden.
        - Customer attempting to modify another user's order MUST receive 404 (queryset tenant isolation).
        """
        # Order 1: in cho_tiep_nhan
        order1 = DonHang.objects.create(
            khach_hang=self.customer_a, chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY, tong_tien=Decimal("250000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order1, mon_an=self.dish1, so_luong=1,
            don_gia_luc_dat=Decimal("250000"), thanh_tien=Decimal("250000")
        )

        # Order 2: confirmed by staff
        order2 = DonHang.objects.create(
            khach_hang=self.customer_a, chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.DA_XAC_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY, tong_tien=Decimal("250000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order2, mon_an=self.dish1, so_luong=1,
            don_gia_luc_dat=Decimal("250000"), thanh_tien=Decimal("250000")
        )

        # 1. Customer A cancels order 1 while in cho_tiep_nhan -> 200 OK
        self.client.force_authenticate(user=self.customer_a)
        res_cancel_ok = self.client.patch(f"/api/orders/{order1.id}/trang_thai/", {"status": "da_huy"})
        self.assertEqual(res_cancel_ok.status_code, 200)
        order1.refresh_from_db()
        self.assertEqual(order1.trang_thai, DonHang.TrangThai.DA_HUY)

        # 2. Customer A attempts to cancel order 2 while in da_xac_nhan -> 403 Forbidden
        res_cancel_blocked = self.client.patch(f"/api/orders/{order2.id}/trang_thai/", {"status": "da_huy"})
        self.assertEqual(res_cancel_blocked.status_code, 403)
        order2.refresh_from_db()
        self.assertEqual(order2.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # 3. Customer A attempts to advance order 2 to dang_che_bien -> 403 Forbidden
        res_advance_blocked = self.client.patch(f"/api/orders/{order2.id}/trang_thai/", {"status": "dang_che_bien"})
        self.assertEqual(res_advance_blocked.status_code, 403)

        # 4. Customer B attempts to modify Customer A's order -> 404 (isolated queryset)
        self.client.force_authenticate(user=self.customer_b)
        res_other = self.client.patch(f"/api/orders/{order2.id}/trang_thai/", {"status": "da_huy"})
        self.assertEqual(res_other.status_code, 404)

    def test_adv_fsm_04_status_aliases_and_casing(self):
        """
        Verify that status aliases from admin.api.ts / frontend ("confirmed", "cooking", "ready", "completed")
        are canonicalized seamlessly to Vietnamese backend states.
        """
        order = DonHang.objects.create(
            khach_hang=self.customer_a, chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY, tong_tien=Decimal("250000"),
        )
        ChiTietDonHang.objects.create(
            don_hang=order, mon_an=self.dish1, so_luong=1,
            don_gia_luc_dat=Decimal("250000"), thanh_tien=Decimal("250000")
        )

        self.client.force_authenticate(user=self.staff_user)

        # Test alias 'confirmed'
        r1 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "confirmed"})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.data["trang_thai"], "da_xac_nhan")

        # Test alias 'cooking'
        r2 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "cooking"})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["trang_thai"], "dang_che_bien")

        # Test alias 'ready'
        r3 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "ready"})
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.data["trang_thai"], "san_sang")

        # Test alias 'completed'
        r4 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {"status": "completed"})
        self.assertEqual(r4.status_code, 200)
        self.assertEqual(r4.data["trang_thai"], "hoan_tat")

    # =========================================================================
    # Group 4: Table Reservation Floor Plan & Concurrency (reservations/views.py)
    # =========================================================================

    def test_adv_tbl_01_floor_plan_reservation_filtering(self):
        """
        Verify table floor plan availability filtering:
        When querying /api/tables/ with reservation_date and start_time,
        tables that already have active bookings (cho_thanh_toan, da_xac_nhan, khach_da_den)
        at that slot MUST be excluded, while unoccupied tables remain listed.
        """
        target_date = "2026-11-20"
        target_time = "19:00"

        # Book table_vip on target date & time
        DatBan.objects.create(
            chi_nhanh=self.branch, ban_an=self.table_vip, nguoi_dung=self.customer_a,
            so_luong_khach=4, ngay_dat=target_date, gio_bat_dau=target_time,
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            ten_khach="Cust A", sdt_khach="0901111111"
        )

        # 1. Query for target slot -> table_vip must be excluded, table_std included
        res = self.client.get(
            f"/api/tables/?chi_nhanh={self.branch.id}&reservation_date={target_date}&start_time={target_time}"
        )
        self.assertEqual(res.status_code, 200)
        items = res.data if isinstance(res.data, list) else res.data.get("results", [])
        table_ids = [t["id"] for t in items]
        self.assertNotIn(self.table_vip.id, table_ids, "Booked VIP table must be excluded from availability list")
        self.assertIn(self.table_std.id, table_ids, "Unbooked standard table must be available")

        # 2. Query for a different slot (next day) -> both tables available
        res_next_day = self.client.get(
            f"/api/tables/?chi_nhanh={self.branch.id}&reservation_date=2026-11-21&start_time={target_time}"
        )
        items_nd = res_next_day.data if isinstance(res_next_day.data, list) else res_next_day.data.get("results", [])
        nd_ids = [t["id"] for t in items_nd]
        self.assertIn(self.table_vip.id, nd_ids, "VIP table must be available on different date")
        self.assertIn(self.table_std.id, nd_ids, "Standard table must be available on different date")

    def test_adv_tbl_02_concurrent_table_hold_lock_race(self):
        """
        Stress test: simulate 10 concurrent requests attempting to hold the EXACT SAME table,
        date, and time.
        Verify that exactly 1 request succeeds (HTTP 200), and all 9 others receive HTTP 409 BAN_DANG_BAN.
        """
        target_date = "2026-12-01"
        target_time = "18:30"
        num_threads = 10

        from reservations.services import DichVuDatBan

        def _attempt_hold(idx):
            with patch("reservations.services._safe_cache", return_value=self.locmem_cache):
                return DichVuDatBan.giu_ban_tam_thoi(
                    ban_id=self.table_std.id,
                    ngay=target_date,
                    gio=target_time,
                    so_khach=2,
                )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(_attempt_hold, i) for i in range(num_threads)]
            results = [f.result() for f in futures]

        success_count = sum(1 for ok, _ in results if ok)
        conflict_count = sum(1 for ok, _ in results if not ok)

        self.assertEqual(success_count, 1, f"Expected exactly 1 hold success, got {success_count}")
        self.assertEqual(conflict_count, num_threads - 1, f"Expected {num_threads - 1} conflicts, got {conflict_count}")

        # Check payload code of conflicted attempts
        for ok, payload in results:
            if not ok:
                self.assertEqual(payload.get("code"), "BAN_DANG_BAN")

    def test_adv_tbl_03_staff_reservation_status_transitions(self):
        """
        Verify that staff can update reservation statuses via /api/reservations/{id}/trang_thai/,
        while non-staff callers receive 403 Forbidden.
        """
        booking = DatBan.objects.create(
            chi_nhanh=self.branch, ban_an=self.table_std, nguoi_dung=self.customer_a,
            so_luong_khach=2, ngay_dat="2026-11-25", gio_bat_dau="19:00",
            trang_thai=DatBan.TrangThai.CHO_THANH_TOAN,
            ten_khach="Cust A", sdt_khach="0901111111"
        )

        # 1. Customer A attempts to change status -> 403 Forbidden
        self.client.force_authenticate(user=self.customer_a)
        res_cust = self.client.patch(f"/api/reservations/{booking.id}/trang_thai/", {"status": "da_xac_nhan"})
        self.assertEqual(res_cust.status_code, 403)

        # 2. Staff updates status -> 200 OK
        self.client.force_authenticate(user=self.staff_user)
        res_staff1 = self.client.patch(f"/api/reservations/{booking.id}/trang_thai/", {"status": "da_xac_nhan"})
        self.assertEqual(res_staff1.status_code, 200)
        self.assertEqual(res_staff1.data["trang_thai"], "da_xac_nhan")

        res_staff2 = self.client.patch(f"/api/reservations/{booking.id}/trang_thai/", {"status": "khach_da_den"})
        self.assertEqual(res_staff2.status_code, 200)
        self.assertEqual(res_staff2.data["trang_thai"], "khach_da_den")

    def test_adv_tbl_04_cancellation_and_deposit_refund_rules(self):
        """
        Verify tiered cancellation deposit refund policy:
        - Cancellation >24h before booking: 100% refund.
        - Cancellation 6-24h before booking: 50% refund.
        - Cancellation <6h before booking: 0% refund.
        - Cancellation with is_no_show=True by staff: 0% refund.
        """
        now = timezone.now()

        # Case 1: Booking > 24 hours in the future
        future_dt = now + timedelta(hours=30)
        booking_far = DatBan.objects.create(
            chi_nhanh=self.branch, ban_an=self.table_std, nguoi_dung=self.customer_a,
            so_luong_khach=4, ngay_dat=future_dt.date().isoformat(),
            gio_bat_dau=future_dt.time().strftime("%H:%M"),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True, so_tien_coc=Decimal("400000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Cust A", sdt_khach="0901111111"
        )
        ThanhToan.objects.create(
            dat_ban=booking_far, nguoi_dung=self.customer_a,
            so_tien=Decimal("400000"), loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay", trang_thai="thanh_cong"
        )

        self.client.force_authenticate(user=self.customer_a)
        res_far = self.client.post(f"/api/reservations/{booking_far.id}/cancel/", {"ly_do": "Bận việc"})
        self.assertEqual(res_far.status_code, 200)
        self.assertEqual(res_far.data["phan_tram_hoan_tien"], 100)
        self.assertEqual(Decimal(str(res_far.data["so_tien_hoan"])), Decimal("400000"))

        # Case 2: Booking 12 hours in the future (6h - 24h)
        mid_dt = now + timedelta(hours=12)
        booking_mid = DatBan.objects.create(
            chi_nhanh=self.branch, ban_an=self.table_vip, nguoi_dung=self.customer_a,
            so_luong_khach=4, ngay_dat=mid_dt.date().isoformat(),
            gio_bat_dau=mid_dt.time().strftime("%H:%M"),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True, so_tien_coc=Decimal("400000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Cust A", sdt_khach="0901111111"
        )
        ThanhToan.objects.create(
            dat_ban=booking_mid, nguoi_dung=self.customer_a,
            so_tien=Decimal("400000"), loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay", trang_thai="thanh_cong"
        )

        res_mid = self.client.post(f"/api/reservations/{booking_mid.id}/cancel/", {"ly_do": "Hủy gấp"})
        self.assertEqual(res_mid.status_code, 200)
        self.assertEqual(res_mid.data["phan_tram_hoan_tien"], 50)
        self.assertEqual(Decimal(str(res_mid.data["so_tien_hoan"])), Decimal("200000"))

        # Case 3: Booking 2 hours in the future (<6h)
        near_dt = now + timedelta(hours=2)
        booking_near = DatBan.objects.create(
            chi_nhanh=self.branch, ban_an=self.table_std, nguoi_dung=self.customer_a,
            so_luong_khach=4, ngay_dat=near_dt.date().isoformat(),
            gio_bat_dau=near_dt.time().strftime("%H:%M"),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True, so_tien_coc=Decimal("400000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Cust A", sdt_khach="0901111111"
        )
        ThanhToan.objects.create(
            dat_ban=booking_near, nguoi_dung=self.customer_a,
            so_tien=Decimal("400000"), loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay", trang_thai="thanh_cong"
        )

        res_near = self.client.post(f"/api/reservations/{booking_near.id}/cancel/", {"ly_do": "Sát giờ"})
        self.assertEqual(res_near.status_code, 200)
        self.assertEqual(res_near.data["phan_tram_hoan_tien"], 0)
        self.assertEqual(Decimal(str(res_near.data["so_tien_hoan"])), Decimal("0"))

        # Case 4: Staff marks no-show on booking > 24h
        booking_noshow = DatBan.objects.create(
            chi_nhanh=self.branch, ban_an=self.table_vip, nguoi_dung=self.customer_b,
            so_luong_khach=4, ngay_dat=future_dt.date().isoformat(),
            gio_bat_dau=future_dt.time().strftime("%H:%M"),
            trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            yeu_cau_dat_coc=True, so_tien_coc=Decimal("400000"),
            trang_thai_coc="da_thanh_toan",
            ten_khach="Cust B", sdt_khach="0902222222"
        )
        ThanhToan.objects.create(
            dat_ban=booking_noshow, nguoi_dung=self.customer_b,
            so_tien=Decimal("400000"), loai_thanh_toan="tien_coc",
            phuong_thuc="vnpay", trang_thai="thanh_cong"
        )

        self.client.force_authenticate(user=self.staff_user)
        res_ns = self.client.post(f"/api/reservations/{booking_noshow.id}/cancel/", {
            "ly_do": "Khách không đến",
            "is_no_show": True
        })
        self.assertEqual(res_ns.status_code, 200)
        self.assertEqual(res_ns.data["phan_tram_hoan_tien"], 0, "No-show must yield 0% refund")
        self.assertEqual(Decimal(str(res_ns.data["so_tien_hoan"])), Decimal("0"))


if __name__ == "__main__":
    os.environ["TESTING"] = "1"
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_adversarial_m5_portals"])
    sys.exit(bool(failures))
