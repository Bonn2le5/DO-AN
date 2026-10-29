#!/usr/bin/env python3
"""
Adversarial Edge-Case Stress Harness for Milestone 5 Post-Remediation Verification.
Focus: Deep edge-case validation of:
1. LichSuKhoViewSet: Insufficient stock rejection, adjustments, balance integrity under select_for_update.
2. DanhGiaViewSet: Self-deletion by author vs cross-user attack rejection vs staff deletion rating updates.
3. DonHangViewSet: Dual lookup (numeric ID vs alphanumeric string code) in status transitions.
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

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

from django.test import TransactionTestCase
from rest_framework.test import APIClient
from accounts.models import NguoiDung, VaiTro
from foods.models import DanhMuc, MonAn, NguyenLieu, LichSuXuatNhapKho
from branches.models import ChiNhanh
from orders.models import DonHang, ChiTietDonHang
from reviews.models import DanhGia


class TestEdgeRemediationM5(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Roles
        self.role_admin, _ = VaiTro.objects.get_or_create(ten="quan_tri_vien", defaults={"mo_ta": "Quản trị viên"})
        self.role_staff, _ = VaiTro.objects.get_or_create(ten="nhan_vien", defaults={"mo_ta": "Nhân viên"})
        self.role_customer, _ = VaiTro.objects.get_or_create(ten="khach_hang", defaults={"mo_ta": "Khách hàng"})

        # Users
        self.staff_user = NguoiDung.objects.create_user(
            username="edge_staff",
            email="edge_staff@mocrestaurant.vn",
            password="Password123!",
            is_staff=True,
            ho_ten="Edge Staff",
        )
        self.staff_user.danh_sach_vai_tro.add(self.role_staff)

        self.cust_alice = NguoiDung.objects.create_user(
            username="edge_alice",
            email="edge_alice@gmail.com",
            password="Password123!",
            is_staff=False,
            ho_ten="Alice",
        )
        self.cust_alice.danh_sach_vai_tro.add(self.role_customer)

        self.cust_bob = NguoiDung.objects.create_user(
            username="edge_bob",
            email="edge_bob@gmail.com",
            password="Password123!",
            is_staff=False,
            ho_ten="Bob",
        )
        self.cust_bob.danh_sach_vai_tro.add(self.role_customer)

        # Core objects
        self.branch = ChiNhanh.objects.create(
            ten="Chi nhánh Edge Test",
            dia_chi="123 Duong Test",
            so_dien_thoai="0901111111",
            toa_do_gis="10.7769,106.7009",
            con_hoat_dong=True,
        )
        self.category = DanhMuc.objects.create(
            ten="Mon Bo",
            duong_dan="mon-bo-edge",
            con_hoat_dong=True,
        )
        self.dish = MonAn.objects.create(
            danh_muc=self.category,
            ten="Bo Luc Lac",
            duong_dan="bo-luc-lac-edge",
            don_gia=Decimal("150000"),
            diem_danh_gia=Decimal("0.0"),
            so_luot_danh_gia=0,
        )
        self.ingredient = NguyenLieu.objects.create(
            ten="Thit Bo Than",
            don_vi="kg",
            ton_kho_hien_tai=Decimal("25.000"),
            ton_kho_toi_thieu=Decimal("5.000"),
        )

    def test_stock_tx_insufficient_stock_rejection(self):
        """Staff attempting to export more than available stock receives HTTP 400."""
        self.client.force_authenticate(user=self.staff_user)
        res = self.client.post("/api/inventory-transactions/", {
            "nguyen_lieu": self.ingredient.id,
            "loai_giao_dich": "xuat",
            "so_luong": "30.000",
            "ghi_chu": "Xuat vuot ton",
        })
        self.assertEqual(res.status_code, 400)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.ton_kho_hien_tai, Decimal("25.000"))
        self.assertFalse(LichSuXuatNhapKho.objects.filter(ghi_chu="Xuat vuot ton").exists())

    def test_stock_tx_adjustment(self):
        """Staff performing stock adjustment sets exact balance."""
        self.client.force_authenticate(user=self.staff_user)
        res = self.client.post("/api/inventory-transactions/", {
            "nguyen_lieu": self.ingredient.id,
            "loai_giao_dich": "dieu_chinh",
            "so_luong": "18.500",
            "ghi_chu": "Kiem ke kho",
        })
        self.assertEqual(res.status_code, 201)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.ton_kho_hien_tai, Decimal("18.500"))
        tx = LichSuXuatNhapKho.objects.get(ghi_chu="Kiem ke kho")
        self.assertEqual(tx.ton_kho_truoc, Decimal("25.000"))
        self.assertEqual(tx.ton_kho_sau, Decimal("18.500"))

    def test_review_author_self_deletion_and_recalculation(self):
        """Author deleting own review succeeds with 204 and recalculates dish rating."""
        order = DonHang.objects.create(
            khach_hang=self.cust_alice,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.HOAN_TAT,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=self.dish.don_gia,
        )
        item = ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish,
            so_luong=1,
            don_gia_luc_dat=self.dish.don_gia,
            thanh_tien=self.dish.don_gia,
        )
        rev1 = DanhGia.objects.create(
            nguoi_dung=self.cust_alice,
            mon_an=self.dish,
            don_hang=order,
            chi_tiet_don_hang=item,
            diem_danh_gia=5,
            nhan_xet="Tuyet voi",
            hien_thi=True,
        )
        order2 = DonHang.objects.create(
            khach_hang=self.cust_bob,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.HOAN_TAT,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=self.dish.don_gia,
        )
        item2 = ChiTietDonHang.objects.create(
            don_hang=order2,
            mon_an=self.dish,
            so_luong=1,
            don_gia_luc_dat=self.dish.don_gia,
            thanh_tien=self.dish.don_gia,
        )
        rev2 = DanhGia.objects.create(
            nguoi_dung=self.cust_bob,
            mon_an=self.dish,
            don_hang=order2,
            chi_tiet_don_hang=item2,
            diem_danh_gia=3,
            nhan_xet="Binh thuong",
            hien_thi=True,
        )
        # Recalculate baseline
        from reviews.views import DanhGiaViewSet
        view = DanhGiaViewSet()
        view._cap_nhat_diem_mon(self.dish)
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.so_luot_danh_gia, 2)
        self.assertAlmostEqual(float(self.dish.diem_danh_gia), 4.0)

        # Alice deletes her own review (5 stars)
        self.client.force_authenticate(user=self.cust_alice)
        res = self.client.delete(f"/api/reviews/{rev1.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertFalse(DanhGia.objects.filter(id=rev1.id).exists())

        # Dish rating must now be 3.0 with count 1
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.so_luot_danh_gia, 1)
        self.assertAlmostEqual(float(self.dish.diem_danh_gia), 3.0)

    def test_review_cross_customer_deletion_forbidden(self):
        """Customer Bob attempting to delete Alice's review gets 403 Forbidden."""
        order = DonHang.objects.create(
            khach_hang=self.cust_alice,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.HOAN_TAT,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=self.dish.don_gia,
        )
        item = ChiTietDonHang.objects.create(
            don_hang=order,
            mon_an=self.dish,
            so_luong=1,
            don_gia_luc_dat=self.dish.don_gia,
            thanh_tien=self.dish.don_gia,
        )
        rev_alice = DanhGia.objects.create(
            nguoi_dung=self.cust_alice,
            mon_an=self.dish,
            don_hang=order,
            chi_tiet_don_hang=item,
            diem_danh_gia=5,
            nhan_xet="Review Alice",
            hien_thi=True,
        )

        self.client.force_authenticate(user=self.cust_bob)
        res = self.client.delete(f"/api/reviews/{rev_alice.id}/")
        self.assertEqual(res.status_code, 403)
        self.assertTrue(DanhGia.objects.filter(id=rev_alice.id).exists())

    def test_order_lookup_by_code_and_numeric_id(self):
        """Staff can transition order using both numeric ID and order code string."""
        order = DonHang.objects.create(
            ma_don_hang="DH-EDGE-9999",
            khach_hang=self.cust_alice,
            chi_nhanh=self.branch,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            tong_tien=self.dish.don_gia,
        )

        self.client.force_authenticate(user=self.staff_user)

        # Transition 1: via code string
        res1 = self.client.patch("/api/orders/DH-EDGE-9999/trang_thai/", {
            "trang_thai": "da_xac_nhan",
            "ghi_chu": "Xac nhan bang ma don",
        })
        self.assertEqual(res1.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # Transition 2: via numeric id
        res2 = self.client.patch(f"/api/orders/{order.id}/trang_thai/", {
            "trang_thai": "dang_che_bien",
            "ghi_chu": "Che bien bang id so",
        })
        self.assertEqual(res2.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DANG_CHE_BIEN)


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_edge_remediation_m5"])
    sys.exit(bool(failures))
