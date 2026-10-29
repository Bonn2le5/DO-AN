#!/usr/bin/env python3
"""
Empirical Challenger Test Suite — Milestone 4 Round 2
Web App Nhà hàng Mộc — Challenger m4_r2_challenger_2.

Focus Areas:
1. Haversine antipodal stability (100k points + specific edge cases) directly via branches.services.
2. In-depth query param fuzzing for GET /api/branches/ (radius=abc, limit=abc, lat=999, lng=999, nan, inf).
3. In-depth query param fuzzing for GET /api/branches/nearest/ and aliases.
4. Vietnamese parameter aliases (vi_do, kinh_do, ban_kinh, so_luong).
5. SQL injection / boundary string fuzzing on query parameters.
"""

import os
import sys
import math
import random
from pathlib import Path

PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
BACKEND_DIR = PROJECT_ROOT / "moc-backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

import unittest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from branches.models import ChiNhanh
from branches.services import haversine_distance_km, find_nearest_branches


class TestMilestone4Round2AdversarialStress(TestCase):
    """Deep adversarial stress testing for GIS edge cases."""

    @classmethod
    def setUpTestData(cls):
        ChiNhanh.objects.all().delete()
        cls.b1 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh 1",
            dia_chi="123 Lê Lợi, Bến Nghé, Quận 1, TP.HCM",
            so_dien_thoai="02838111111",
            toa_do_gis="106.7000,10.7700",
            con_hoat_dong=True,
        )
        cls.b2 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh 2",
            dia_chi="456 Hoàng Văn Thụ, Phường 2, Tân Bình, TP.HCM",
            so_dien_thoai="02838222222",
            toa_do_gis="106.6600,10.8000",
            con_hoat_dong=True,
        )
        cls.b3_inactive = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Đóng Cửa",
            dia_chi="789 Nguyễn Thị Thập, Tân Phú, Quận 7, TP.HCM",
            so_dien_thoai="02838333333",
            toa_do_gis="106.7100,10.7300",
            con_hoat_dong=False,
        )

    def setUp(self):
        self.client = APIClient()

    # =========================================================================
    # SECTION 1: Haversine Antipodal Clamping & Mathematical Invariants
    # =========================================================================

    def test_haversine_exact_antipodal_pairs(self):
        """Verify haversine_distance_km never raises math domain error on antipodal points."""
        antipodal_targets = [
            (0.0, 0.0, 0.0, 180.0),
            (0.0, 0.0, 0.0, -180.0),
            (90.0, 0.0, -90.0, 0.0),
            (-90.0, 0.0, 90.0, 0.0),
            (45.0, 45.0, -45.0, -135.0),
            (-45.0, -45.0, 45.0, 135.0),
            (-5.902783176600167, -150.92817621645105, 5.902783176600167, 29.07182378354895),
            (10.7700, 106.7000, -10.7700, -73.3000),
        ]
        for lat1, lon1, lat2, lon2 in antipodal_targets:
            with self.subTest(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2):
                dist = haversine_distance_km(lat1, lon1, lat2, lon2)
                self.assertFalse(math.isnan(dist))
                self.assertFalse(math.isinf(dist))
                self.assertAlmostEqual(dist, 20015.11, delta=5.0)

    def test_haversine_100k_random_antipodal_stress(self):
        """Stress-test 100,000 randomized antipodal pairs to ensure zero math domain errors."""
        random.seed(12345)
        for i in range(100000):
            lat = random.uniform(-89.9999, 89.9999)
            lon = random.uniform(-179.9999, 179.9999)
            anti_lat = -lat
            anti_lon = lon + 180.0 if lon < 0 else lon - 180.0
            dist = haversine_distance_km(lat, lon, anti_lat, anti_lon)
            self.assertGreater(dist, 20000.0)
            self.assertLess(dist, 20030.0)

    def test_haversine_identical_and_near_zero(self):
        """Check near-zero micro distances."""
        d0 = haversine_distance_km(10.77, 106.70, 10.77, 106.70)
        self.assertEqual(d0, 0.0)

        # 1 millimeter offset (~1e-8 degrees)
        d_micro = haversine_distance_km(10.77, 106.70, 10.77000001, 106.70000001)
        self.assertGreaterEqual(d_micro, 0.0)
        self.assertLess(d_micro, 0.01)

    # =========================================================================
    # SECTION 2: List View Proximity & Malformed Query Parameters
    # =========================================================================

    def test_list_view_invalid_lat_lng(self):
        """Test GET /api/branches/ with out of bounds and non-numeric lat/lng."""
        cases = [
            ({"lat": "999", "lng": "999"}, 400),
            ({"lat": "-999", "lng": "-999"}, 400),
            ({"lat": "90.0001", "lng": "106.70"}, 400),
            ({"lat": "-90.0001", "lng": "106.70"}, 400),
            ({"lat": "10.77", "lng": "180.0001"}, 400),
            ({"lat": "10.77", "lng": "-180.0001"}, 400),
            ({"lat": "nan", "lng": "106.70"}, 400),
            ({"lat": "inf", "lng": "106.70"}, 400),
            ({"lat": "-inf", "lng": "106.70"}, 400),
            ({"lat": "10.77", "lng": "nan"}, 400),
            ({"lat": "10.77", "lng": "inf"}, 400),
            ({"lat": "abc", "lng": "106.70"}, 400),
            ({"lat": "10.77", "lng": "xyz"}, 400),
            ({"lat": "10.77"}, 400),  # Missing lng
            ({"lng": "106.70"}, 400),  # Missing lat
        ]
        for params, expected_status in cases:
            with self.subTest(endpoint="/api/branches/", params=params):
                resp = self.client.get("/api/branches/", params)
                self.assertEqual(resp.status_code, expected_status, f"Params {params} got {resp.status_code}")

    def test_list_view_invalid_radius_limit(self):
        """Test GET /api/branches/ with malformed radius and limit."""
        base = {"lat": "10.77", "lng": "106.70"}
        cases = [
            ({"radius": "abc"}, 400),
            ({"radius": "-5"}, 400),
            ({"radius": "0"}, 400),
            ({"radius": "nan"}, 400),
            ({"radius": "inf"}, 400),
            ({"radius": "-inf"}, 400),
            ({"limit": "abc"}, 400),
            ({"limit": "-1"}, 400),
            ({"limit": "0"}, 400),
            ({"limit": "1.5"}, 400),
            ({"limit": "nan"}, 400),
            ({"limit": "inf"}, 400),
            ({"radius": "1; DROP TABLE chi_nhanh;--"}, 400),
            ({"limit": "1 OR 1=1"}, 400),
        ]
        for extra, expected_status in cases:
            params = {**base, **extra}
            with self.subTest(params=params):
                resp = self.client.get("/api/branches/", params)
                self.assertEqual(resp.status_code, expected_status, f"Params {params} got {resp.status_code}")

    def test_list_view_valid_requests(self):
        """Test GET /api/branches/ with valid queries."""
        # 1. Standard list without proximity
        resp = self.client.get("/api/branches/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(results), 2)  # Inactive excluded for anonymous

        # 2. Proximity ordering
        resp = self.client.get("/api/branches/", {"lat": 10.7701, "lng": 106.7001})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], self.b1.id)  # b1 is closer

        # 3. Proximity with radius and limit
        resp = self.client.get("/api/branches/", {"lat": 10.7701, "lng": 106.7001, "radius": 2.0, "limit": 1})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.b1.id)

    # =========================================================================
    # SECTION 3: Nearest View Malformed Parameters & Aliases
    # =========================================================================

    def test_nearest_view_invalid_parameters_all_endpoints(self):
        """Test nearest endpoints reject invalid lat, lng, radius, limit with HTTP 400."""
        endpoints = [
            "/api/branches/nearest/",
            "/api/branches/tim-gan-nhat/",
            "/api/chi-nhanh/nearest/",
            "/api/chi-nhanh/tim-gan-nhat/",
        ]
        invalid_param_sets = [
            {},  # Empty
            {"lat": "10.77"},  # Missing lng
            {"lng": "106.70"},  # Missing lat
            {"lat": "999", "lng": "999"},
            {"lat": "-999", "lng": "-999"},
            {"lat": "nan", "lng": "106.70"},
            {"lat": "inf", "lng": "106.70"},
            {"lat": "10.77", "lng": "nan"},
            {"lat": "10.77", "lng": "inf"},
            {"lat": "abc", "lng": "106.70"},
            {"lat": "10.77", "lng": "xyz"},
            {"lat": "10.77", "lng": "106.70", "radius": "abc"},
            {"lat": "10.77", "lng": "106.70", "radius": "-5"},
            {"lat": "10.77", "lng": "106.70", "radius": "0"},
            {"lat": "10.77", "lng": "106.70", "radius": "nan"},
            {"lat": "10.77", "lng": "106.70", "radius": "inf"},
            {"lat": "10.77", "lng": "106.70", "limit": "abc"},
            {"lat": "10.77", "lng": "106.70", "limit": "-1"},
            {"lat": "10.77", "lng": "106.70", "limit": "0"},
            {"lat": "10.77", "lng": "106.70", "limit": "3.5"},
        ]
        for ep in endpoints:
            for params in invalid_param_sets:
                with self.subTest(endpoint=ep, params=params):
                    resp = self.client.get(ep, params)
                    self.assertEqual(
                        resp.status_code,
                        status.HTTP_400_BAD_REQUEST,
                        f"Endpoint {ep} with {params} returned {resp.status_code}, expected 400"
                    )

    def test_nearest_view_vietnamese_aliases_invalid(self):
        """Vietnamese aliases (vi_do, kinh_do, ban_kinh, so_luong) must also reject invalid inputs with HTTP 400."""
        cases = [
            ({"vi_do": "999", "kinh_do": "999"}, 400),
            ({"vi_do": "10.77", "kinh_do": "106.70", "ban_kinh": "abc"}, 400),
            ({"vi_do": "10.77", "kinh_do": "106.70", "ban_kinh": "-1"}, 400),
            ({"vi_do": "10.77", "kinh_do": "106.70", "so_luong": "abc"}, 400),
            ({"vi_do": "10.77", "kinh_do": "106.70", "so_luong": "-1"}, 400),
            ({"vi_do": "10.77", "kinh_do": "106.70", "so_luong": "0"}, 400),
        ]
        for params, expected in cases:
            with self.subTest(params=params):
                resp = self.client.get("/api/chi-nhanh/tim-gan-nhat/", params)
                self.assertEqual(resp.status_code, expected)

    def test_nearest_view_valid_aliases(self):
        """Valid queries with Vietnamese aliases work correctly."""
        resp = self.client.get("/api/chi-nhanh/tim-gan-nhat/", {
            "vi_do": 10.7701,
            "kinh_do": 106.7001,
            "ban_kinh": 5.0,
            "so_luong": 1,
            "all": "true",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.b1.id)


if __name__ == "__main__":
    unittest.main()
