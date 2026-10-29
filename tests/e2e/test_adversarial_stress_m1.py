#!/usr/bin/env python3
"""
Adversarial Stress Test Suite for Milestone 1 Iteration 2.
Evaluates:
- Property setters (boundary types, None, empty strings, numbers, booleans)
- Legacy kwargs instantiation vs unrecognized parameters (TypeError assertion)
- Multi-user registration (uniqueness, username disambiguation, dual payload parity)
- Authentication credentials compatibility (email, username, thu_dien_tu)
"""

import sys
import unittest
from pathlib import Path
from decimal import Decimal

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "moc-backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.conf import settings
# Use SQLite in-memory database for isolated empirical testing without external service dependency
settings.DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}

import django
django.setup()

from django.core.management import call_command
# Setup schemas for auth and accounts
call_command("migrate", "contenttypes", verbosity=0)
call_command("migrate", "auth", verbosity=0)
call_command("migrate", "accounts", verbosity=0)

from foods.models import Food, MonAn, DanhMuc, NguyenLieu
from reservations.models import Table, BanAn
from orders.models import Order, DonHang
from payments.models import Payment, ThanhToan
from branches.models import Branch, ChiNhanh
from accounts.models import User, NguoiDung, VaiTro
from accounts.serializers import DangKySerializer, DangNhapTokenSerializer
from rest_framework.exceptions import AuthenticationFailed


class AdversarialPropertySetterStressTest(unittest.TestCase):
    """Stress tests property getters and setters across models with edge cases and unexpected types."""

    def test_food_name_setter_types(self):
        f = Food(ten="Gà nướng")
        # Unicode string
        f.name = "Gà nướng mật ong ớt hiểm"
        self.assertEqual(f.ten, "Gà nướng mật ong ớt hiểm")
        self.assertEqual(f.name, "Gà nướng mật ong ớt hiểm")

        # Empty string
        f.name = ""
        self.assertEqual(f.ten, "")

        # None value
        f.name = None
        self.assertIsNone(f.ten)

        # Non-string type
        f.name = 12345
        self.assertEqual(f.ten, 12345)

    def test_food_price_setter_types(self):
        f = Food(don_gia=50000)
        # Decimal
        f.price = Decimal("85000.50")
        self.assertEqual(f.don_gia, Decimal("85000.50"))

        # Integer
        f.price = 90000
        self.assertEqual(f.don_gia, 90000)

        # String representation
        f.price = "120000"
        self.assertEqual(f.don_gia, "120000")

        # Zero
        f.price = 0
        self.assertEqual(f.don_gia, 0)

    def test_food_is_active_setter_truthiness(self):
        f = Food(con_hang=True, hien_thi=True)
        self.assertTrue(f.is_active)

        # Setting False
        f.is_active = False
        self.assertFalse(f.con_hang)
        self.assertFalse(f.hien_thi)
        self.assertFalse(f.is_active)

        # Setting integer 1
        f.is_active = 1
        self.assertTrue(f.con_hang)
        self.assertTrue(f.hien_thi)
        self.assertTrue(f.is_active)

        # Setting None (falsy)
        f.is_active = None
        self.assertFalse(f.con_hang)
        self.assertFalse(f.hien_thi)
        self.assertFalse(f.is_active)

    def test_table_properties_boundary(self):
        t = Table(so_ban="T01", suc_chua=4, trang_thai="trong")
        # Status via enum
        t.status = BanAn.TrangThai.DA_DAT
        self.assertEqual(t.trang_thai, "da_dat")
        self.assertEqual(t.status, "da_dat")

        # Capacity setter
        t.capacity = 10
        self.assertEqual(t.suc_chua, 10)
        self.assertEqual(t.capacity, 10)

        # Table number setter
        t.table_number = "VIP_99"
        self.assertEqual(t.so_ban, "VIP_99")
        self.assertEqual(t.table_number, "VIP_99")

    def test_order_properties_boundary(self):
        o = Order(tong_tien=Decimal("200000.00"), trang_thai="cho_tiep_nhan")
        # Total setters
        o.total = Decimal("350000.00")
        self.assertEqual(o.tong_tien, Decimal("350000.00"))
        self.assertEqual(o.total, Decimal("350000.00"))

        o.total_amount = 400000
        self.assertEqual(o.tong_tien, 400000)

        # Status setter
        o.status = "da_xac_nhan"
        self.assertEqual(o.trang_thai, "da_xac_nhan")
        self.assertEqual(o.status, "da_xac_nhan")

    def test_payment_properties_boundary(self):
        p = Payment(so_tien=Decimal("500000.00"), phuong_thuc="vnpay")
        p.amount = Decimal("750000.00")
        self.assertEqual(p.so_tien, Decimal("750000.00"))
        self.assertEqual(p.amount, Decimal("750000.00"))

        p.payment_method = "tien_mat"
        self.assertEqual(p.phuong_thuc, "tien_mat")
        self.assertEqual(p.payment_method, "tien_mat")

    def test_user_name_and_phone_setter_edge_cases(self):
        u = User(username="user_edge")
        # Single name
        u.name = "Nguyen"
        self.assertEqual(u.first_name, "Nguyen")
        self.assertEqual(u.last_name, "")
        self.assertEqual(u.name, "Nguyen")

        # Two-word name
        u.name = "Nguyen Van"
        self.assertEqual(u.first_name, "Nguyen")
        self.assertEqual(u.last_name, "Van")
        self.assertEqual(u.name, "Nguyen Van")

        # Multi-word name
        u.name = "Nguyen Van An Binh"
        self.assertEqual(u.first_name, "Nguyen")
        self.assertEqual(u.last_name, "Van An Binh")
        self.assertEqual(u.name, "Nguyen Van An Binh")

        # Empty string (falls back to username)
        u.name = ""
        self.assertEqual(u.first_name, "")
        self.assertEqual(u.last_name, "")
        self.assertEqual(u.name, "user_edge")

        # None (falls back to username)
        u.name = None
        self.assertEqual(u.first_name, "")
        self.assertEqual(u.last_name, "")
        self.assertEqual(u.name, "user_edge")

        # Phone None handling
        u.phone = None
        self.assertEqual(u.so_dien_thoai, "")
        self.assertEqual(u.phone, "")

        u.phone = "0987654321"
        self.assertEqual(u.so_dien_thoai, "0987654321")
        self.assertEqual(u.phone, "0987654321")


class AdversarialKwargsInstantiationStressTest(unittest.TestCase):
    """Stress tests legacy kwargs remapping and verifies TypeError on unrecognized parameters."""

    def test_unrecognized_kwargs_raise_type_error(self):
        """Verifies that unknown parameters cause TypeError across all models."""
        with self.assertRaises(TypeError):
            Food(invalid_food_arg="bad_data")

        with self.assertRaises(TypeError):
            Table(unknown_table_property=999)

        with self.assertRaises(TypeError):
            Order(bogus_order_kwarg=[1, 2, 3])

        with self.assertRaises(TypeError):
            Payment(phantom_field=True)

        with self.assertRaises(TypeError):
            User(nonexistent_user_attribute="fail")

    def test_canonical_precedence_over_legacy_kwargs(self):
        """When both legacy and canonical kwargs are passed, canonical must take precedence."""
        f = Food(name="Legacy Name", ten="Canonical Name")
        self.assertEqual(f.ten, "Canonical Name")
        self.assertEqual(f.name, "Canonical Name")

    def test_multiple_simultaneous_legacy_kwargs(self):
        """Instantiating with multiple legacy kwargs in a single call."""
        f = Food(name="Bò né", price=79000, description="Nóng hổi", is_active=True)
        self.assertEqual(f.ten, "Bò né")
        self.assertEqual(f.don_gia, 79000)
        self.assertEqual(f.mo_ta_chi_tiet, "Nóng hổi")
        self.assertTrue(f.con_hang)
        self.assertTrue(f.hien_thi)

    def test_inherited_legacy_kwargs_from_mohinhthoigian(self):
        """Verifies MoHinhThoiGian legacy kwargs (created_at, updated_at)."""
        import datetime
        dt = datetime.datetime(2026, 1, 1, 12, 0, 0)
        f = Food(name="Gỏi cuốn", created_at=dt, updated_at=dt)
        self.assertEqual(f.tao_luc, dt)
        self.assertEqual(f.cap_nhat_luc, dt)


class AdversarialMultiUserRegistrationStressTest(unittest.TestCase):
    """Stress tests DangKySerializer for multi-user registrations and validation boundaries."""

    def test_multi_user_registration_distinct_emails(self):
        """Registers multiple users with distinct emails and verifies independent creation."""
        import uuid
        run_id = uuid.uuid4().hex[:6]
        for i in range(1, 6):
            payload = {
                "email": f"customer_{run_id}_{i}@moc.vn",
                "password": f"Password@{i}Secure",
                "name": f"Khách Hàng {i}",
                "phone": f"090000000{i}",
            }
            serializer = DangKySerializer(data=payload)
            self.assertTrue(serializer.is_valid(), f"User {i} must be valid: {serializer.errors}")
            user = serializer.save()
            self.assertEqual(user.email, f"customer_{run_id}_{i}@moc.vn")
            self.assertEqual(user.thu_dien_tu, f"customer_{run_id}_{i}@moc.vn")
            self.assertEqual(user.name, f"Khách Hàng {i}")
            self.assertTrue(user.check_password(f"Password@{i}Secure"))

    def test_multi_user_auto_disambiguate_usernames(self):
        """When username is not provided, users with same email prefix receive distinct usernames."""
        import uuid
        tag = uuid.uuid4().hex[:6]
        p1 = {"email": f"alex_{tag}@company-a.com", "password": "Password123!"}
        s1 = DangKySerializer(data=p1)
        self.assertTrue(s1.is_valid())
        u1 = s1.save()
        self.assertEqual(u1.username, f"alex_{tag}")

        p2 = {"email": f"alex_{tag}@company-b.com", "password": "Password123!"}
        s2 = DangKySerializer(data=p2)
        self.assertTrue(s2.is_valid())
        u2 = s2.save()
        self.assertEqual(u2.username, f"alex_{tag}_1")

        p3 = {"email": f"alex_{tag}@company-c.com", "password": "Password123!"}
        s3 = DangKySerializer(data=p3)
        self.assertTrue(s3.is_valid())
        u3 = s3.save()
        self.assertEqual(u3.username, f"alex_{tag}_2")

    def test_duplicate_email_registration_rejected(self):
        """Registering with an already existing email must be rejected by serializer validation."""
        import uuid
        email = f"dup_{uuid.uuid4().hex[:6]}@moc.vn"
        payload1 = {"email": email, "password": "Password123!", "name": "First"}
        s1 = DangKySerializer(data=payload1)
        self.assertTrue(s1.is_valid())
        s1.save()

        # Attempt duplicate via English 'email'
        payload2 = {"email": email, "password": "DifferentPassword123!", "name": "Second"}
        s2 = DangKySerializer(data=payload2)
        self.assertFalse(s2.is_valid(), "Duplicate email must fail validation")
        self.assertIn("thu_dien_tu", s2.errors)

        # Attempt duplicate via Vietnamese 'thu_dien_tu'
        payload3 = {"thu_dien_tu": email, "mat_khau": "DifferentPassword123!", "ho_ten": "Third"}
        s3 = DangKySerializer(data=payload3)
        self.assertFalse(s3.is_valid(), "Duplicate thu_dien_tu must fail validation")
        self.assertIn("thu_dien_tu", s3.errors)

    def test_registration_validation_rules(self):
        """Verifies validation on invalid emails, short passwords, and missing fields."""
        # Invalid email format
        s_bad_email = DangKySerializer(data={"email": "invalid-format", "password": "ValidPassword123"})
        self.assertFalse(s_bad_email.is_valid())
        self.assertIn("thu_dien_tu", s_bad_email.errors)

        # Short password (< 6 chars)
        s_short_pwd = DangKySerializer(data={"email": "valid@moc.vn", "password": "123"})
        self.assertFalse(s_short_pwd.is_valid())
        self.assertIn("mat_khau", s_short_pwd.errors)

        # Missing password
        s_no_pwd = DangKySerializer(data={"email": "valid@moc.vn"})
        self.assertFalse(s_no_pwd.is_valid())
        self.assertIn("mat_khau", s_no_pwd.errors)

        # Missing email
        s_no_email = DangKySerializer(data={"password": "ValidPassword123"})
        self.assertFalse(s_no_email.is_valid())
        self.assertIn("thu_dien_tu", s_no_email.errors)

    def test_authentication_credentials_interoperability(self):
        """Verifies DangNhapTokenSerializer accepts email, thu_dien_tu, or username."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        u = NguoiDung.objects.create_user(
            username=f"tester_{uid}",
            email=f"tester_{uid}@moc.vn",
            thu_dien_tu=f"tester_{uid}@moc.vn",
            password="StrongPassword123!",
        )

        # Login with email
        s1 = DangNhapTokenSerializer(data={"email": f"tester_{uid}@moc.vn", "password": "StrongPassword123!"})
        self.assertTrue(s1.is_valid(), f"Login with email failed: {s1.errors}")
        self.assertIn("access", s1.validated_data)
        self.assertIn("refresh", s1.validated_data)

        # Login with thu_dien_tu
        s2 = DangNhapTokenSerializer(data={"thu_dien_tu": f"tester_{uid}@moc.vn", "password": "StrongPassword123!"})
        self.assertTrue(s2.is_valid(), f"Login with thu_dien_tu failed: {s2.errors}")

        # Login with username
        s3 = DangNhapTokenSerializer(data={"username": f"tester_{uid}@moc.vn", "password": "StrongPassword123!"})
        self.assertTrue(s3.is_valid(), f"Login with username failed: {s3.errors}")

        # Login with wrong password raises AuthenticationFailed
        s_bad = DangNhapTokenSerializer(data={"email": f"tester_{uid}@moc.vn", "password": "WrongPassword"})
        with self.assertRaises(AuthenticationFailed):
            s_bad.is_valid(raise_exception=True)


if __name__ == "__main__":
    unittest.main()
