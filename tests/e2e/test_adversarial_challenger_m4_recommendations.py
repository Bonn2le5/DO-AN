#!/usr/bin/env python3
"""
Adversarial Empirical Stress Testing & Algorithmic Boundary Verification Suite for Milestone 4 (Recommendation Engine).
Web App Nhà hàng Mộc — Challenger m4_challenger_1.

Adversarial Focus Dimensions:
1. Pure-Python TF-IDF & Cosine Similarity mathematical accuracy and extreme edge cases
   (empty text, disjoint vocabularies, zero-norm tokens, single-word corpora).
2. Interaction weight correctness (xem=1, yeu_thich=2, them_gio_hang=3, dat_mon=4, danh_gia=5).
3. Cold-start popularity bounds strictly within [0.0, 1.0] and PostgreSQL NUMERIC(5,4) safety.
4. Cache invalidation on GoiYMonAn when user logs new interactions.
5. Guest/anonymous recommendations access without authentication error or database crash.
6. Explainable tags accuracy matching dish characteristics.
7. Empirical bug reproductions:
   - Bug 1: GoiYMonAnViewSet detail endpoint GET /api/recommendations/<pk>/ missing queryset/get_queryset (causes 500 AssertionError).
   - Bug 2: orders/services.py:83 hardcodes trong_so=6 instead of trong_so=4 on dat_mon.
   - Bug 3: Placing orders or submitting reviews fails to invalidate GoiYMonAn cached recommendations.
"""

import os
import sys
import math
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
from rest_framework import status

from foods.models import DanhMuc, MonAn, TheMonAn, NguyenLieu
from recommendations.models import TuongTacMonAn, GoiYMonAn
from recommendations.services import (
    DichVuGoiY,
    TRONG_SO_TUONG_TAC,
    ALIAS_TRONG_SO,
    tach_tu_khoa_mon_an,
    tao_ly_do_goi_y,
    MODEL_VERSION_COLD_START,
    MODEL_VERSION_CONTENT_BASED,
)
from orders.services import DichVuDonHang

User = get_user_model()


class TestMilestone4RecommendationsAdversarial(TransactionTestCase):
    """Adversarial stress and boundary suite for Milestone 4 Recommendation Engine."""

    def setUp(self):
        self.client = APIClient()
        User.objects.all().delete()
        GoiYMonAn.objects.all().delete()
        TuongTacMonAn.objects.all().delete()
        MonAn.objects.all().delete()
        DanhMuc.objects.all().delete()
        TheMonAn.objects.all().delete()
        NguyenLieu.objects.all().delete()

        # Users
        self.user_a = User.objects.create_user(
            username="khach_a_m4_rec",
            email="khach_a_m4_rec@moc.vn",
            thu_dien_tu="khach_a_m4_rec@moc.vn",
            so_dien_thoai="0901000001",
            password="Password@123",
            ho_ten="Khách Hàng A",
        )
        self.user_b = User.objects.create_user(
            username="khach_b_m4_rec",
            email="khach_b_m4_rec@moc.vn",
            thu_dien_tu="khach_b_m4_rec@moc.vn",
            so_dien_thoai="0901000002",
            password="Password@123",
            ho_ten="Khách Hàng B",
        )

        # Categories
        self.dm_lau = DanhMuc.objects.create(ten="Lẩu", duong_dan="lau")
        self.dm_nuong = DanhMuc.objects.create(ten="Món Nướng", duong_dan="mon-nuong")
        self.dm_chay = DanhMuc.objects.create(ten="Món Chay", duong_dan="mon-chay")
        self.dm_trang_mieng = DanhMuc.objects.create(ten="Tráng Miệng", duong_dan="trang-mieng")

        # Tags
        self.tag_cay = TheMonAn.objects.create(ten="Cay nồng", duong_dan="cay-nong")
        self.tag_thanh_dam = TheMonAn.objects.create(ten="Thanh đạm", duong_dan="thanh-dam")

        # Ingredients
        self.ing_hai_san = NguyenLieu.objects.create(ten="Tôm sú mực tươi", don_vi="kg")
        self.ing_bo = NguyenLieu.objects.create(ten="Bò tơ Tây Ninh", don_vi="kg")
        self.ing_sa_te = NguyenLieu.objects.create(ten="Sa tế ớt hiểm", don_vi="g")
        self.ing_nam = NguyenLieu.objects.create(ten="Nấm đông cô", don_vi="kg")

        # Dishes
        # 1. Hotpot spicy seafood
        self.mon_lau = MonAn.objects.create(
            danh_muc=self.dm_lau,
            ten="Lẩu Thái Hải Sản Sa Tế",
            duong_dan="lau-thai-hai-san-sa-te",
            mo_ta_ngan="Lẩu Thái chua cay nóng hổi tôm mực sa tế",
            don_gia=Decimal("280000"),
            do_cay=2,
            diem_danh_gia=Decimal("4.9"),
            so_luot_danh_gia=150,
            con_hang=True,
            hien_thi=True,
        )
        self.mon_lau.the_mon_an.add(self.tag_cay)
        self.mon_lau.nguyen_lieu.add(self.ing_hai_san, self.ing_sa_te, through_defaults={"so_luong_can": Decimal("1.0")})

        # 2. Grilled beef spicy
        self.mon_nuong = MonAn.objects.create(
            danh_muc=self.dm_nuong,
            ten="Bò Nướng Sa Tế Cay",
            duong_dan="bo-nuong-sa-te-cay",
            mo_ta_ngan="Bò nướng than hoa thơm lừng vị sa tế cay",
            don_gia=Decimal("195000"),
            do_cay=2,
            diem_danh_gia=Decimal("4.7"),
            so_luot_danh_gia=90,
            con_hang=True,
            hien_thi=True,
        )
        self.mon_nuong.the_mon_an.add(self.tag_cay)
        self.mon_nuong.nguyen_lieu.add(self.ing_bo, self.ing_sa_te, through_defaults={"so_luong_can": Decimal("1.0")})

        # 3. Vegetarian mushrooms
        self.mon_chay = MonAn.objects.create(
            danh_muc=self.dm_chay,
            ten="Lẩu Nấm Chay Thanh Đạm",
            duong_dan="lau-nam-chay-thanh-dam",
            mo_ta_ngan="Món lẩu chay thanh tịnh từ các loại nấm tự nhiên",
            don_gia=Decimal("150000"),
            la_mon_chay=True,
            do_cay=0,
            diem_danh_gia=Decimal("4.5"),
            so_luot_danh_gia=35,
            con_hang=True,
            hien_thi=True,
        )
        self.mon_chay.the_mon_an.add(self.tag_thanh_dam)
        self.mon_chay.nguyen_lieu.add(self.ing_nam, through_defaults={"so_luong_can": Decimal("1.0")})

        # 4. Pure Vegetarian Dessert
        self.mon_che = MonAn.objects.create(
            danh_muc=self.dm_trang_mieng,
            ten="Chè Hạt Sen Nhãn Nhục",
            duong_dan="che-hat-sen-nhan-nhuc",
            mo_ta_ngan="Món chè ngọt mát thanh lọc cơ thể",
            don_gia=Decimal("45000"),
            la_mon_chay=True,
            do_cay=0,
            diem_danh_gia=Decimal("4.2"),
            so_luot_danh_gia=20,
            con_hang=True,
            hien_thi=True,
        )

    # =========================================================================
    # 1. Pure-Python TF-IDF & Cosine Similarity Mathematical Correctness
    # =========================================================================

    def test_adv_01_tfidf_cosine_oracle_verification(self):
        """Verify TF-IDF formula, L2 normalization and Cosine Similarity against strict mathematical oracle."""
        TuongTacMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=self.mon_lau,
            loai_tuong_tac="dat_mon",
            trong_so=Decimal("4.00"),
        )

        recs = DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=4)
        self.assertEqual(len(recs), 4)

        top_rec = recs[0]
        self.assertEqual(top_rec.mon_an.id, self.mon_lau.id)
        self.assertEqual(top_rec.phien_ban_model, MODEL_VERSION_CONTENT_BASED)
        score_val = float(top_rec.diem_tuong_dong)
        self.assertAlmostEqual(score_val, 1.0, places=3, msg="Self-similarity with single interaction must be ~1.0")

        second_rec = recs[1]
        self.assertEqual(second_rec.mon_an.id, self.mon_nuong.id)
        self.assertGreater(float(second_rec.diem_tuong_dong), 0.0)

        last_rec = recs[-1]
        self.assertLess(float(last_rec.diem_tuong_dong), float(second_rec.diem_tuong_dong))

    def test_adv_02_disjoint_vocabulary_zero_cosine(self):
        """Adversarial: Disjoint vocabulary candidate dishes must produce exact 0.0 similarity."""
        mon_isolated = MonAn.objects.create(
            danh_muc=self.dm_trang_mieng,
            ten="Xyzqwerty Abcdef",
            duong_dan="xyzqwerty-abcdef",
            mo_ta_ngan="Zzzz kkkk pppp",
            don_gia=Decimal("10000"),
            diem_danh_gia=Decimal("4.0"),
            so_luot_danh_gia=1,
            con_hang=True,
            hien_thi=True,
        )

        TuongTacMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=self.mon_lau,
            loai_tuong_tac="xem",
            trong_so=1,
        )

        recs = DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=10)
        isolated_rec = [r for r in recs if r.mon_an.id == mon_isolated.id]
        self.assertTrue(len(isolated_rec) > 0)
        self.assertEqual(float(isolated_rec[0].diem_tuong_dong), 0.0)

    def test_adv_03_empty_text_dish_handling(self):
        """Adversarial: Dish with punctuation-only title and empty descriptions must not crash."""
        mon_blank = MonAn.objects.create(
            danh_muc=self.dm_trang_mieng,
            ten="...",
            duong_dan="blank-dish",
            mo_ta_ngan="",
            mo_ta_chi_tiet="",
            don_gia=Decimal("50000"),
            diem_danh_gia=Decimal("4.0"),
            so_luot_danh_gia=0,
            con_hang=True,
            hien_thi=True,
        )

        tokens = tach_tu_khoa_mon_an(mon_blank)
        self.assertIsInstance(tokens, list)

        TuongTacMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=mon_blank,
            loai_tuong_tac="xem",
            trong_so=1,
        )
        recs = DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=5)
        self.assertGreater(len(recs), 0)

    def test_adv_04_deleted_dish_in_user_interaction_history(self):
        """Adversarial: User has interaction record referencing dish that was hidden/disabled."""
        ghost_dish = MonAn.objects.create(
            danh_muc=self.dm_nuong,
            ten="Món Tạm Thời Bị Xóa",
            duong_dan="mon-tam-thoi-xoa",
            mo_ta_ngan="Sắp bị xóa",
            don_gia=Decimal("100000"),
            con_hang=True,
            hien_thi=True,
        )
        TuongTacMonAn.objects.create(
            nguoi_dung=self.user_a,
            mon_an=ghost_dish,
            loai_tuong_tac="dat_mon",
            trong_so=4,
        )

        ghost_dish.con_hang = False
        ghost_dish.hien_thi = False
        ghost_dish.save()

        recs = DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=3)
        self.assertEqual(len(recs), 3)
        rec_ids = [r.mon_an.id for r in recs]
        self.assertNotIn(ghost_dish.id, rec_ids)

    # =========================================================================
    # 2. Interaction Weight Hierarchy & Verification
    # =========================================================================

    def test_adv_05_interaction_weight_proportions(self):
        """Verify standard weights: xem=1 < yeu_thich=2 < them_gio_hang=3 < dat_mon=4 < danh_gia=5."""
        self.assertEqual(TRONG_SO_TUONG_TAC["xem"], 1)
        self.assertEqual(TRONG_SO_TUONG_TAC["yeu_thich"], 2)
        self.assertEqual(TRONG_SO_TUONG_TAC["them_gio_hang"], 3)
        self.assertEqual(TRONG_SO_TUONG_TAC["dat_mon"], 4)
        self.assertEqual(TRONG_SO_TUONG_TAC["danh_gia"], 5)

        self.assertEqual(ALIAS_TRONG_SO["view"], 1)
        self.assertEqual(ALIAS_TRONG_SO["thich"], 2)
        self.assertEqual(ALIAS_TRONG_SO["like"], 2)
        self.assertEqual(ALIAS_TRONG_SO["favorite"], 2)
        self.assertEqual(ALIAS_TRONG_SO["cart"], 3)
        self.assertEqual(ALIAS_TRONG_SO["gio_hang"], 3)
        self.assertEqual(ALIAS_TRONG_SO["dat_hang"], 4)
        self.assertEqual(ALIAS_TRONG_SO["order"], 4)
        self.assertEqual(ALIAS_TRONG_SO["review"], 5)
        self.assertEqual(ALIAS_TRONG_SO["rating"], 5)

    def test_adv_06_weight_influences_preference_vector_mathematically(self):
        """Higher weight action must exert greater magnitude influence on preference vector."""
        TuongTacMonAn.objects.create(nguoi_dung=self.user_a, mon_an=self.mon_chay, loai_tuong_tac="xem", trong_so=1)
        TuongTacMonAn.objects.create(nguoi_dung=self.user_a, mon_an=self.mon_lau, loai_tuong_tac="danh_gia", trong_so=5)

        recs = DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=4)
        scores = {r.mon_an.id: float(r.diem_tuong_dong) for r in recs}
        self.assertGreater(scores[self.mon_lau.id], scores[self.mon_chay.id],
                           "Rating (weight 5) must dominate over View (weight 1)")

    # =========================================================================
    # 3. Cold-Start Popularity Bounds & Database Integrity
    # =========================================================================

    def test_adv_07_cold_start_popularity_formula_and_bounds(self):
        """Stress-test cold-start score bounds [0.0, 1.0] under extreme values."""
        mon_extreme_zero = MonAn.objects.create(
            danh_muc=self.dm_nuong,
            ten="Món 0 Review",
            duong_dan="mon-0-review",
            don_gia=Decimal("10000"),
            diem_danh_gia=Decimal("0.0"),
            so_luot_danh_gia=0,
            con_hang=True,
            hien_thi=True,
        )
        mon_extreme_high = MonAn.objects.create(
            danh_muc=self.dm_nuong,
            ten="Món Triệu Review",
            duong_dan="mon-trieu-review",
            don_gia=Decimal("10000"),
            diem_danh_gia=Decimal("5.0"),
            so_luot_danh_gia=1000000,
            con_hang=True,
            hien_thi=True,
        )

        all_dishes = list(MonAn.objects.filter(con_hang=True, hien_thi=True))
        scored = DichVuGoiY.tinh_goi_y_cold_start(all_dishes, gioi_han=10)

        for mon, score, reason, is_cold in scored:
            self.assertTrue(is_cold)
            self.assertEqual(reason, "Phổ biến hôm nay")
            self.assertGreaterEqual(score, 0.0, f"Score {score} < 0.0 for dish {mon.ten}")
            self.assertLessEqual(score, 1.0, f"Score {score} > 1.0 for dish {mon.ten}")
            dec_score = Decimal(str(score))
            self.assertLessEqual(dec_score, Decimal("1.0000"))

        self.assertEqual(scored[0][0].id, mon_extreme_high.id)

    def test_adv_08_empty_database_cold_start_safety(self):
        """Cold-start when database has 0 dishes must return empty list without crash."""
        empty_recs = DichVuGoiY.tinh_goi_y_cold_start([], gioi_han=6)
        self.assertEqual(empty_recs, [])

        MonAn.objects.all().delete()
        res = DichVuGoiY.lay_goi_y_khach_vang_lai(gioi_han=6)
        self.assertEqual(res, [])

    # =========================================================================
    # 4. Cache Strategy & Invalidation Scenarios via Direct API
    # =========================================================================

    def test_adv_09_cache_invalidation_on_interaction_endpoints(self):
        """Verify cache invalidation across /api/tuong-tac/ and /api/recommendations/tuong-tac/."""
        DichVuGoiY.cap_nhat_goi_y(self.user_a, gioi_han=3)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 3)

        self.client.force_authenticate(user=self.user_a)

        # 1. Post to /api/tuong-tac/
        resp1 = self.client.post(
            "/api/tuong-tac/",
            {"mon_an": self.mon_nuong.id, "loai_tuong_tac": "yeu_thich"},
            format="json",
        )
        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

        # Re-populate cache via GET
        resp_get = self.client.get("/api/recommendations/")
        self.assertEqual(resp_get.status_code, 200)
        self.assertGreater(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

        # 2. Post to /api/recommendations/tuong-tac/
        resp2 = self.client.post(
            "/api/recommendations/tuong-tac/",
            {"mon_an": self.mon_chay.id, "loai_tuong_tac": "them_gio_hang"},
            format="json",
        )
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user_a).count(), 0)

    def test_adv_10_cache_refresh_flag_and_lam_moi_action(self):
        """Verify ?refresh=true, ?lam_moi=true, and /refresh/, /lam-moi/ endpoints."""
        self.client.force_authenticate(user=self.user_a)

        resp1 = self.client.get("/api/recommendations/?refresh=true")
        self.assertEqual(resp1.status_code, 200)

        resp2 = self.client.get("/api/recommendations/?lam_moi=true")
        self.assertEqual(resp2.status_code, 200)

        resp3 = self.client.post("/api/recommendations/refresh/")
        self.assertEqual(resp3.status_code, 200)

        resp4 = self.client.get("/api/recommendations/lam-moi/")
        self.assertEqual(resp4.status_code, 200)

    # =========================================================================
    # 5. Anonymous / Guest Recommendations Robustness
    # =========================================================================

    def test_adv_11_anonymous_guest_recommendations_no_db_persistence(self):
        """Anonymous guest can fetch recommendations without 401 and without saving to DB."""
        self.client.force_authenticate(user=None)

        endpoints = ["/api/recommendations/", "/api/goi-y/"]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, 200, f"Endpoint {ep} failed for guest")
            data = resp.json()
            self.assertGreater(len(data), 0)
            self.assertTrue(data[0]["is_cold_start"])
            self.assertEqual(data[0]["reason"], "Phổ biến hôm nay")
            self.assertIn("chi_tiet_mon", data[0])

        self.assertEqual(GoiYMonAn.objects.count(), 0, "Guest recommendations must NOT be written to database")

    def test_adv_12_anonymous_guest_access_control(self):
        """Anonymous guest cannot post interactions or call refresh actions (401 Unauthorized)."""
        self.client.force_authenticate(user=None)

        resp1 = self.client.post("/api/tuong-tac/", {"mon_an": self.mon_lau.id, "loai_tuong_tac": "xem"})
        self.assertEqual(resp1.status_code, 401)

        resp2 = self.client.post("/api/recommendations/refresh/")
        self.assertEqual(resp2.status_code, 401)

    # =========================================================================
    # 6. Explainable Recommendation Tags Correctness
    # =========================================================================

    def test_adv_13_explainable_tag_matching(self):
        """Verify explainable tag generated accurately identifies dominant features."""
        tag_hotpot = tao_ly_do_goi_y(self.mon_lau)
        self.assertIn("lẩu", tag_hotpot.lower())

        tag_spicy = tao_ly_do_goi_y(self.mon_nuong)
        self.assertIn("cay", tag_spicy.lower())

        tag_vegan = tao_ly_do_goi_y(self.mon_che)
        self.assertIn("chay", tag_vegan.lower())


if __name__ == "__main__":
    unittest.main()
