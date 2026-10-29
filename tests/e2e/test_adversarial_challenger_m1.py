#!/usr/bin/env python3
"""
Adversarial Test Harness reproducing and asserting all 18 Challenger 1 scenarios.
Milestone 1 Iteration 2 - Explorer 3 Proposal.

Usage:
    python tests/e2e/test_adversarial_challenger_m1.py
    # or via Django test runner:
    python manage.py test tests.e2e.test_adversarial_challenger_m1
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Ensure moc-backend is on python path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "moc-backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()


class AdversarialChallengerTestSuite(unittest.TestCase):
    """
    Test suite reproducing all 18 adversarial scenarios documented by Challenger 1.
    Before Worker fixes: 16 FAIL, 2 PASS.
    After Worker fixes: 18 PASS, 0 FAIL.
    """

    # --- Group 1: Food Model Properties & Kwargs ---

    def test_scenario_01_food_name_setter(self):
        """Scenario 1: Food.name setter updates underlying Vietnamese field ten."""
        from foods.models import Food
        f = Food(ten="Lẩu nấm")
        f.name = "Lẩu thái"
        self.assertEqual(f.ten, "Lẩu thái", "Food.name setter must update ten")
        self.assertEqual(f.name, "Lẩu thái", "Food.name getter must return updated name")

    def test_scenario_02_food_price_setter(self):
        """Scenario 2: Food.price setter updates underlying Vietnamese field don_gia."""
        from foods.models import Food
        f = Food(don_gia=100)
        f.price = 200
        self.assertEqual(f.don_gia, 200, "Food.price setter must update don_gia")
        self.assertEqual(f.price, 200, "Food.price getter must return updated price")

    def test_scenario_03_food_legacy_kwargs(self):
        """Scenario 3: Food(name='...', price=...) keyword arguments initialization."""
        from foods.models import Food
        f = Food(name="Lẩu cua đồng", price=250000)
        self.assertEqual(f.ten, "Lẩu cua đồng", "Legacy kwarg 'name' must populate ten")
        self.assertEqual(f.don_gia, 250000, "Legacy kwarg 'price' must populate don_gia")

    # --- Group 2: Table (BanAn) Properties, Kwargs & Enums ---

    def test_scenario_04_table_status_getter(self):
        """Scenario 4: Table.status getter returns underlying trang_thai."""
        from reservations.models import Table
        t = Table(trang_thai="trong")
        self.assertTrue(hasattr(t, "status"), "Table must expose 'status' property")
        self.assertEqual(t.status, "trong", "Table.status must equal trang_thai")

    def test_scenario_05_table_status_setter(self):
        """Scenario 5: Table.status setter mutates underlying field trang_thai."""
        from reservations.models import Table
        t = Table(trang_thai="trong")
        t.status = "dang_giu"
        self.assertEqual(t.trang_thai, "dang_giu", "Table.status setter must update trang_thai")
        self.assertEqual(t.status, "dang_giu")

    def test_scenario_06_table_legacy_kwargs(self):
        """Scenario 6: Table(status='trong') keyword arguments initialization."""
        from reservations.models import Table
        t = Table(status="trong")
        self.assertEqual(t.trang_thai, "trong", "Legacy kwarg 'status' must populate trang_thai")

    def test_scenario_07_table_status_enum_alias(self):
        """Scenario 7: Table.Status enum alias equals BanAn.TrangThai."""
        from reservations.models import BanAn, Table
        self.assertTrue(hasattr(Table, "Status"), "Table must expose 'Status' enum alias")
        self.assertEqual(Table.Status, BanAn.TrangThai, "Table.Status must alias BanAn.TrangThai")
        self.assertEqual(Table.Status.TRONG, BanAn.TrangThai.TRONG)

    # --- Group 3: Order (DonHang) Properties ---

    def test_scenario_08_order_total_getter(self):
        """Scenario 8: Order.total getter returns underlying field tong_tien."""
        from orders.models import Order
        o = Order(tong_tien=150000)
        self.assertTrue(hasattr(o, "total"), "Order must expose 'total' property")
        self.assertEqual(o.total, 150000, "Order.total must return tong_tien")

    def test_scenario_09_order_total_setter(self):
        """Scenario 9: Order.total setter updates underlying field tong_tien."""
        from orders.models import Order
        o = Order(tong_tien=100000)
        o.total = 200000
        self.assertEqual(o.tong_tien, 200000, "Order.total setter must update tong_tien")
        self.assertEqual(o.total, 200000)

    # --- Group 4: User (NguoiDung) Properties ---

    def test_scenario_10_user_name_getter(self):
        """Scenario 10: User.name getter returns full name or username."""
        from accounts.models import User
        u = User(username="moc_chef", first_name="Van", last_name="Nguyen")
        self.assertTrue(hasattr(u, "name"), "User must expose 'name' property")
        self.assertIn("Van", u.name, "User.name must reflect user full name")

    # --- Group 5: Branch (ChiNhanh) Properties & Kwargs ---

    def test_scenario_11_branch_name_setter(self):
        """Scenario 11: Branch.name setter updates underlying field ten."""
        from branches.models import Branch
        b = Branch(ten="Chi nhánh 1")
        b.name = "Chi nhánh Tân Bình"
        self.assertEqual(b.ten, "Chi nhánh Tân Bình", "Branch.name setter must update ten")
        self.assertEqual(b.name, "Chi nhánh Tân Bình")

    def test_scenario_12_branch_legacy_kwargs(self):
        """Scenario 12: Branch(name='CN1') keyword arguments initialization."""
        from branches.models import Branch
        b = Branch(name="Mộc Quận 1")
        self.assertEqual(b.ten, "Mộc Quận 1", "Legacy kwarg 'name' must populate ten")

    # --- Group 6: Payment (ThanhToan) Properties ---

    def test_scenario_13_payment_amount_getter(self):
        """Scenario 13: Payment.amount getter returns underlying field so_tien."""
        from payments.models import Payment
        p = Payment(so_tien=750000)
        self.assertTrue(hasattr(p, "amount"), "Payment must expose 'amount' property")
        self.assertEqual(p.amount, 750000, "Payment.amount must return so_tien")

    # --- Group 7: Serializers & Validation Compatibility ---

    def test_scenario_14_registration_preserves_email_and_thu_dien_tu(self):
        """Scenario 14: DangKySerializer preserves thu_dien_tu and synchronizes email."""
        from accounts.serializers import DangKySerializer
        from accounts.models import NguoiDung
        with patch.object(NguoiDung.objects, "create_user") as mock_create_user, \
             patch("accounts.serializers.VaiTro.objects.get_or_create") as mock_vt, \
             patch("accounts.serializers.NguoiDungVaiTro.objects.get_or_create") as mock_ndvt:
            mock_create_user.return_value = NguoiDung(
                id=1, username="customer1", email="customer@moc.vn", thu_dien_tu="customer@moc.vn"
            )
            mock_vt.return_value = (MagicMock(), False)
            mock_ndvt.return_value = (MagicMock(), False)

            serializer = DangKySerializer()
            payload = {
                "thu_dien_tu": "customer@moc.vn",
                "mat_khau": "SecurePass123!",
                "ho_ten": "Nguyen Van A",
            }
            serializer.create(payload)

            call_kwargs = mock_create_user.call_args[1]
            self.assertEqual(
                call_kwargs.get("thu_dien_tu"),
                "customer@moc.vn",
                "create_user must receive thu_dien_tu parameter",
            )
            self.assertEqual(
                call_kwargs.get("email"),
                "customer@moc.vn",
                "create_user must receive synchronized email parameter",
            )

    def test_scenario_15_food_serializer_english_payload(self):
        """Scenario 15: FoodSerializer transparently accepts English keys (name, price, category)."""
        from foods.serializers import FoodSerializer
        from foods.models import DanhMuc
        from rest_framework.relations import PrimaryKeyRelatedField

        data = {"name": "Phở Bò", "price": 65000, "category": 1}
        serializer = FoodSerializer()
        dummy_cat = DanhMuc(id=1, ten="Món nước")
        with patch.object(PrimaryKeyRelatedField, "to_internal_value", return_value=dummy_cat):
            internal = serializer.to_internal_value(data)
            self.assertEqual(internal.get("ten"), "Phở Bò", "name must map to ten")
            self.assertEqual(internal.get("don_gia"), 65000, "price must map to don_gia")
            self.assertEqual(internal.get("danh_muc"), dummy_cat, "category must map to danh_muc")

    def test_scenario_16_order_serializer_english_payload(self):
        """Scenario 16: OrderSerializer transparently accepts English keys (customer_name, phone, type)."""
        from orders.serializers import OrderSerializer

        data = {
            "customer_name": "Nguyen Van A",
            "phone": "0901234567",
            "type": "tu_den_lay",
        }
        serializer = OrderSerializer()
        internal = serializer.to_internal_value(data)
        self.assertEqual(internal.get("ten_khach"), "Nguyen Van A", "customer_name must map to ten_khach")
        self.assertEqual(internal.get("sdt_khach"), "0901234567", "phone must map to sdt_khach")
        self.assertEqual(internal.get("hinh_thuc"), "tu_den_lay", "type must map to hinh_thuc")

    # --- Group 8: QuerySet Filters & Relationships (Baseline Pass Verification) ---

    def test_scenario_17_food_queryset_vietnamese_filter(self):
        """Scenario 17: Food queryset filtering using Vietnamese column con_hang."""
        from foods.models import MonAn
        q = MonAn.objects.filter(con_hang=True)
        self.assertIn("con_hang", str(q.query), "QuerySet SQL must filter on con_hang column")

    def test_scenario_18_order_cross_model_relation_filter(self):
        """Scenario 18: Order cross-model relation JOIN with ChiTietDonHang and MonAn."""
        from orders.models import DonHang
        q = DonHang.objects.filter(trang_thai="cho_tiep_nhan", danh_sach_mon__mon_an__ten="Phở")
        sql = str(q.query)
        self.assertTrue(
            "chi_tiet_don_hang" in sql or "mon_an" in sql,
            "QuerySet SQL must execute JOIN with related tables",
        )


if __name__ == "__main__":
    unittest.main()
