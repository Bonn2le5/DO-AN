#!/usr/bin/env python3
"""
Bug Reproduction Harness for Milestone 4 (Recommendation Engine).
Web App Nhà hàng Mộc — Challenger m4_challenger_1.

This suite empirically documents three concrete bugs in Milestone 4 implementation:
1. Bug 1: GoiYMonAnViewSet detail endpoint (GET /api/recommendations/<pk>/) crashes with
   AssertionError (HTTP 500) because queryset / get_queryset() is not defined on the viewset.
2. Bug 2: Placing orders via DichVuDonHang.tao_don_hang (orders/services.py:83) hardcodes
   trong_so=6 instead of trong_so=4 on dat_mon, violating Feature 20 specification.
3. Bug 3: Placing an order (or submitting a review) fails to invalidate GoiYMonAn cached
   recommendations because cache invalidation was only implemented in TuongTacMonAnViewSet.perform_create.
"""

import os
import sys
import types
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
BACKEND_DIR = PROJECT_ROOT / "moc-backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Daphne mock stub for Channels testing in offline sandbox
if "daphne" not in sys.modules:
    daphne_mod = types.ModuleType("daphne")
    daphne_mod.testing = types.SimpleNamespace(DaphneProcess=object)
    sys.modules["daphne"] = daphne_mod
    sys.modules["daphne.testing"] = daphne_mod.testing

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

import unittest
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from foods.models import DanhMuc, MonAn
from recommendations.models import TuongTacMonAn, GoiYMonAn
from recommendations.services import DichVuGoiY
from orders.models import DonHang, ChiTietDonHang
from orders.services import DichVuDonHang

User = get_user_model()


class TestMilestone4BugReproduction(TransactionTestCase):
    """Empirical Bug Reproduction Tests for Milestone 4."""

    def setUp(self):
        self.client = APIClient()
        ChiTietDonHang.objects.all().delete()
        DonHang.objects.all().delete()
        User.objects.all().delete()
        GoiYMonAn.objects.all().delete()
        TuongTacMonAn.objects.all().delete()
        MonAn.objects.all().delete()
        DanhMuc.objects.all().delete()

        self.user = User.objects.create_user(
            username="khach_bug_test",
            email="khach_bug_test@moc.vn",
            thu_dien_tu="khach_bug_test@moc.vn",
            so_dien_thoai="0909999999",
            password="Password@123",
            ho_ten="Khách Test Bug",
        )

        self.dm = DanhMuc.objects.create(ten="Lẩu", duong_dan="lau")
        self.mon = MonAn.objects.create(
            danh_muc=self.dm,
            ten="Lẩu Bò Sa Tế",
            duong_dan="lau-bo-sa-te",
            don_gia=Decimal("200000"),
            con_hang=True,
            hien_thi=True,
        )

    def test_reproduce_bug_1_detail_endpoint_assertion_error(self):
        """
        Bug 1: Calling GET /api/recommendations/<pk>/ should return 404 (or 200),
        NOT crash with HTTP 500 AssertionError from DRF GenericAPIView.get_queryset().
        """
        self.client.force_authenticate(user=self.user)
        try:
            resp = self.client.get("/api/recommendations/1/")
            self.assertNotEqual(
                resp.status_code,
                500,
                "CRITICAL BUG: GET /api/recommendations/<pk>/ raised AssertionError 500 because queryset/get_queryset() is missing!"
            )
        except AssertionError as e:
            if "should either include a `queryset` attribute" in str(e):
                self.fail(f"CRITICAL BUG REPRODUCED: {e}")
            raise

    def test_reproduce_bug_2_order_service_interaction_weight_is_6_not_4(self):
        """
        Bug 2: Placing order via DichVuDonHang.tao_don_hang logs TuongTacMonAn with weight 6.00 instead of 4.00.
        Feature 20 strictly requires: xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5.
        """
        order = DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user,
            du_lieu={
                "items": [{"mon_an": self.mon, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )
        tt = TuongTacMonAn.objects.filter(nguoi_dung=self.user, mon_an=self.mon).first()
        self.assertIsNotNone(tt, "TuongTacMonAn must be created upon order creation")
        self.assertEqual(
            tt.trong_so,
            Decimal("4.00"),
            f"HIGH BUG REPRODUCED: orders/services.py:83 created TuongTacMonAn with trong_so={tt.trong_so}, expected 4.00 per Feature 20"
        )

    def test_reproduce_bug_3_order_creation_fails_to_invalidate_cache(self):
        """
        Bug 3: Placing an order does not invalidate existing GoiYMonAn recommendation cache.
        User's recommendation cache remains stale until manual refresh.
        """
        # 1. User has cached recommendations
        DichVuGoiY.cap_nhat_goi_y(self.user, gioi_han=1)
        cache_before = GoiYMonAn.objects.filter(nguoi_dung=self.user).count()
        self.assertGreater(cache_before, 0)

        # 2. User places order
        DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user,
            du_lieu={
                "items": [{"mon_an": self.mon, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )

        # 3. Cache should be cleared/invalidated
        cache_after = GoiYMonAn.objects.filter(nguoi_dung=self.user).count()
        self.assertEqual(
            cache_after,
            0,
            f"MEDIUM BUG REPRODUCED: Cache was not invalidated after placing order (still has {cache_after} cached items)"
        )


if __name__ == "__main__":
    unittest.main()
