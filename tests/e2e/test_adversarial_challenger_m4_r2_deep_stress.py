#!/usr/bin/env python3
"""
Deep Adversarial Stress Testing Suite for Milestone 4 Round 2.
Web App Nhà hàng Mộc — Challenger m4_r2_challenger_1.

Focus Verification:
1. GET /api/recommendations/<pk>/ detail endpoint behavior:
   - 200 for user's own recommendation
   - 404 (IDOR prevention) when accessing another user's recommendation
   - 404 for non-existent recommendation ID (no HTTP 500)
   - 404 for guest user
   - 405 Method Not Allowed for PUT/PATCH/DELETE (ReadOnlyModelViewSet invariant)
2. Interaction weight correctness:
   - Order creation assigns trong_so=4.00 (single item, multi-item, multi-quantity)
   - Review creation assigns trong_so=5.00
3. Cache invalidation signals:
   - Order creation triggers post_save and clears user's GoiYMonAn cache
   - Multi-user isolation: User A's interaction does NOT invalidate User B's cache
   - Review creation clears user's GoiYMonAn cache
   - Interaction deletion triggers post_delete and clears user's cache
   - Rapid-fire interaction stress test (20 consecutive interactions)
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

# Daphne stub for testing in sandbox
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
from rest_framework import status

from foods.models import DanhMuc, MonAn
from recommendations.models import TuongTacMonAn, GoiYMonAn
from recommendations.services import DichVuGoiY
from orders.models import DonHang, ChiTietDonHang
from orders.services import DichVuDonHang
from reviews.models import DanhGia

User = get_user_model()


class TestM4R2DeepAdversarialStress(TransactionTestCase):
    """Deep Adversarial Stress and Verification Harness for M4 R2."""

    def setUp(self):
        self.client = APIClient()
        # Clean database in dependency order to prevent ProtectedError
        DanhGia.objects.all().delete()
        ChiTietDonHang.objects.all().delete()
        DonHang.objects.all().delete()
        GoiYMonAn.objects.all().delete()
        TuongTacMonAn.objects.all().delete()
        MonAn.objects.all().delete()
        DanhMuc.objects.all().delete()
        User.objects.all().delete()

        # Users
        self.user_a = User.objects.create_user(
            username="khach_a_stress",
            email="khach_a_stress@moc.vn",
            thu_dien_tu="khach_a_stress@moc.vn",
            so_dien_thoai="0901111111",
            password="Password@123",
            ho_ten="Khách Hàng A Stress",
        )
        self.user_b = User.objects.create_user(
            username="khach_b_stress",
            email="khach_b_stress@moc.vn",
            thu_dien_tu="khach_b_stress@moc.vn",
            so_dien_thoai="0902222222",
            password="Password@123",
            ho_ten="Khách Hàng B Stress",
        )

        # Categories
        self.dm_mon_chinh = DanhMuc.objects.create(ten="Món Chính", duong_dan="mon-chinh")
        self.dm_trang_mieng = DanhMuc.objects.create(ten="Tráng Miệng", duong_dan="trang-mieng")

        # Dishes
        self.mon_1 = MonAn.objects.create(
            danh_muc=self.dm_mon_chinh,
            ten="Bò Sốt Tiêu Đen",
            duong_dan="bo-sot-tieu-den",
            don_gia=Decimal("250000"),
            con_hang=True,
            hien_thi=True,
            so_luot_danh_gia=10,
            diem_danh_gia=Decimal("4.8"),
        )
        self.mon_2 = MonAn.objects.create(
            danh_muc=self.dm_mon_chinh,
            ten="Gà Hấp Lá Chanh",
            duong_dan="ga-hap-la-chanh",
            don_gia=Decimal("180000"),
            con_hang=True,
            hien_thi=True,
            so_luot_danh_gia=8,
            diem_danh_gia=Decimal("4.6"),
        )
        self.mon_3 = MonAn.objects.create(
            danh_muc=self.dm_trang_mieng,
            ten="Chè Bưởi An Giang",
            duong_dan="che-buoi-an-giang",
            don_gia=Decimal("35000"),
            con_hang=True,
            hien_thi=True,
            so_luot_danh_gia=5,
            diem_danh_gia=Decimal("4.5"),
        )

    # =========================================================================
    # Group 1: GET /api/recommendations/<pk>/ and HTTP Methods
    # =========================================================================

    def test_01_recommendations_detail_own_record_success(self):
        """User can successfully retrieve detail of their own recommendation record."""
        # Pre-seed recommendation
        rec = GoiYMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=self.mon_1,
            diem_tuong_dong=Decimal("0.8500"),
            ly_do_goi_y="Gợi ý vì bạn thích món bò",
            phien_ban_model="content_based_v1",
        )
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(f"/api/recommendations/{rec.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["id"], rec.id)
        self.assertEqual(data["mon_an"], self.mon_1.id)
        self.assertEqual(data["ly_do_goi_y"], "Gợi ý vì bạn thích món bò")
        self.assertAlmostEqual(float(data["diem_tuong_dong"]), 0.8500, places=4)

    def test_02_recommendations_detail_idor_prevention(self):
        """User A must NOT be able to access User B's recommendation detail (must return 404)."""
        rec_b = GoiYMonAn.objects.create(
            nguoi_dung=self.user_b,
            mon_an=self.mon_2,
            diem_tuong_dong=Decimal("0.9000"),
            ly_do_goi_y="Gợi ý riêng cho User B",
            phien_ban_model="content_based_v1",
        )
        # User A attempts to read User B's recommendation
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(f"/api/recommendations/{rec_b.id}/")
        self.assertEqual(
            resp.status_code,
            status.HTTP_404_NOT_FOUND,
            f"SECURITY VULNERABILITY: User A accessed User B's recommendation (got {resp.status_code})"
        )

    def test_03_recommendations_detail_nonexistent_and_invalid_pk(self):
        """Non-existent or malformed PK must cleanly return 404, never 500."""
        self.client.force_authenticate(user=self.user_a)
        for invalid_pk in ["999999", "abc", "-1"]:
            resp = self.client.get(f"/api/recommendations/{invalid_pk}/")
            self.assertEqual(
                resp.status_code,
                status.HTTP_404_NOT_FOUND,
                f"Expected 404 for PK '{invalid_pk}', got {resp.status_code}"
            )

    def test_04_recommendations_detail_unauthenticated_guest(self):
        """Guest (unauthenticated) accessing detail endpoint must get 404 without crashing."""
        rec = GoiYMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=self.mon_1,
            diem_tuong_dong=Decimal("0.7500"),
            ly_do_goi_y="Test",
        )
        self.client.force_authenticate(user=None)
        resp = self.client.get(f"/api/recommendations/{rec.id}/")
        # Anonymous get_queryset() returns .none(), so 404 Not Found is expected
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_05_recommendations_readonly_invariant(self):
        """GoiYMonAnViewSet is ReadOnly: PUT/PATCH/DELETE must return 405 Method Not Allowed."""
        rec = GoiYMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=self.mon_1,
            diem_tuong_dong=Decimal("0.7500"),
            ly_do_goi_y="Test",
        )
        self.client.force_authenticate(user=self.user_a)

        resp_put = self.client.put(f"/api/recommendations/{rec.id}/", {"diem_tuong_dong": "0.9999"})
        self.assertEqual(resp_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        resp_patch = self.client.patch(f"/api/recommendations/{rec.id}/", {"ly_do_goi_y": "Hacked"})
        self.assertEqual(resp_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        resp_delete = self.client.delete(f"/api/recommendations/{rec.id}/")
        self.assertEqual(resp_delete.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # =========================================================================
    # Group 2: Interaction Weights (Orders & Reviews)
    # =========================================================================

    def test_06_order_creation_interaction_weight_single_item(self):
        """Order creation assigns loai_tuong_tac=dat_mon and trong_so=4.00."""
        order = DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user_a,
            du_lieu={
                "items": [{"mon_an": self.mon_1, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )
        self.assertIsNotNone(order)
        tt = TuongTacMonAn.objects.filter(nguoi_dung=self.user_a, mon_an=self.mon_1).first()
        self.assertIsNotNone(tt)
        self.assertEqual(tt.loai_tuong_tac, TuongTacMonAn.LoaiTuongTac.DAT_MON)
        self.assertEqual(tt.trong_so, Decimal("4.00"))

    def test_07_order_creation_interaction_weight_multi_items_and_quantities(self):
        """Order creation with multiple distinct items and large quantities all get trong_so=4.00."""
        order = DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user_a,
            du_lieu={
                "items": [
                    {"mon_an": self.mon_1, "so_luong": 5},
                    {"mon_an": self.mon_2, "so_luong": 2},
                    {"mon_an": self.mon_3, "so_luong": 10},
                ],
                "hinh_thuc": "giao_hang",
                "dia_chi_giao": "123 Đường Mộc, Q1",
            }
        )
        self.assertIsNotNone(order)
        interactions = TuongTacMonAn.objects.filter(nguoi_dung=self.user_a)
        self.assertEqual(interactions.count(), 3)
        for tt in interactions:
            self.assertEqual(tt.loai_tuong_tac, TuongTacMonAn.LoaiTuongTac.DAT_MON)
            self.assertEqual(tt.trong_so, Decimal("4.00"))

    def test_08_review_creation_interaction_weight_is_5(self):
        """Submitting a review assigns loai_tuong_tac=danh_gia and trong_so=5.00."""
        # Create an order and mark as completed
        order = DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user_a,
            du_lieu={
                "items": [{"mon_an": self.mon_1, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )
        order.trang_thai = DonHang.TrangThai.HOAN_TAT
        order.save()
        item = ChiTietDonHang.objects.filter(don_hang=order).first()

        self.client.force_authenticate(user=self.user_a)
        resp = self.client.post(
            "/api/reviews/",
            {
                "mon_an": self.mon_1.id,
                "don_hang": order.id,
                "chi_tiet_don_hang": item.id,
                "diem_danh_gia": 5,
                "nhan_xet": "Món ăn quá ngon, phục vụ tuyệt vời!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        tt = TuongTacMonAn.objects.filter(
            nguoi_dung=self.user_a,
            mon_an=self.mon_1,
            loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DANH_GIA
        ).first()
        self.assertIsNotNone(tt)
        self.assertEqual(tt.trong_so, Decimal("5.00"))

    # =========================================================================
    # Group 3: Cache Invalidation Signals & Isolation
    # =========================================================================

    def test_09_order_creation_invalidates_cache_via_signal(self):
        """Placing an order triggers signal to delete cached GoiYMonAn records for user."""
        # 1. Seed recommendations for User A
        DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=3)
        self.assertGreater(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

        # 2. Place order
        DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user_a,
            du_lieu={
                "items": [{"mon_an": self.mon_2, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )

        # 3. Cache must be completely wiped
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

    def test_10_cache_invalidation_multi_user_isolation(self):
        """User A's order must NOT invalidate User B's cached recommendations."""
        # Seed cache for both User A and User B
        DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=2)
        DichVuGoiY.cap_nhat_goi_y(self.user_b, gioi_han=2)
        count_a_before = GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count()
        count_b_before = GoiYMonAn.objects.filter(nguoi_dung=self.user_b).count()
        self.assertGreater(count_a_before, 0)
        self.assertGreater(count_b_before, 0)

        # User A places order
        DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user_a,
            du_lieu={
                "items": [{"mon_an": self.mon_1, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )

        # User A's cache must be cleared
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)
        # User B's cache must remain UNTOUCHED
        self.assertEqual(
            GoiYMonAn.objects.filter(nguoi_dung=self.user_b).count(),
            count_b_before,
            "ISOLATION VIOLATION: User A's order cleared User B's cache!"
        )

    def test_11_review_creation_invalidates_cache_via_signal(self):
        """Submitting a review triggers signal to delete user's cached recommendations."""
        # 1. Create completed order
        order = DichVuDonHang.tao_don_hang(
            nguoi_dung=self.user_a,
            du_lieu={
                "items": [{"mon_an": self.mon_2, "so_luong": 1}],
                "hinh_thuc": "mang_ve",
            }
        )
        order.trang_thai = DonHang.TrangThai.HOAN_TAT
        order.save()
        item = ChiTietDonHang.objects.filter(don_hang=order).first()

        # 2. Seed cache for User A
        DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=3)
        self.assertGreater(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

        # 3. Post review
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.post(
            "/api/reviews/",
            {
                "mon_an": self.mon_2.id,
                "don_hang": order.id,
                "chi_tiet_don_hang": item.id,
                "diem_danh_gia": 4,
                "nhan_xet": "Ngon vừa miệng",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

    def test_12_interaction_deletion_triggers_post_delete_signal(self):
        """Deleting an interaction record also invalidates cached recommendations."""
        tt = TuongTacMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=self.mon_1,
            loai_tuong_tac="xem",
            trong_so=1,
        )
        DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=3)
        self.assertGreater(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

        # Delete the interaction
        tt.delete()

        # Cache must be invalidated
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

    def test_13_raw_signal_bypass_safety(self):
        """Raw model operations (fixtures / loaddata) bypass signal safely without errors."""
        from recommendations.signals import xoa_cache_goi_y_khi_co_tuong_tac

        # Call signal handler directly with raw=True
        tt = TuongTacMonAn(nguoi_dung=self.user_a, mon_an=self.mon_1, loai_tuong_tac="xem", trong_so=1)
        # Should return immediately without querying or failing
        xoa_cache_goi_y_khi_co_tuong_tac(sender=TuongTacMonAn, instance=tt, raw=True)

    def test_14_rapid_fire_interactions_stress(self):
        """20 consecutive rapid interactions execute cleanly without race conditions or orphaned cache."""
        for i in range(20):
            dish = self.mon_1 if i % 2 == 0 else self.mon_2
            TuongTacMonAn.objects.create(
                nguoi_dung=self.user_a,
                mon_an=dish,
                loai_tuong_tac="xem",
                trong_so=1,
            )
        # After 20 interactions, user's cache should be empty (invalidated on each create)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

        # Re-generating recommendations should succeed flawlessly
        new_recs = DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=3)
        self.assertEqual(len(new_recs), 3)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 3)


if __name__ == "__main__":
    os.environ["TESTING"] = "1"
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_adversarial_challenger_m4_r2_deep_stress"])
    sys.exit(bool(failures))
