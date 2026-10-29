#!/usr/bin/env python3
"""
Adversarial Empirical Stress Testing & GIS Geolocation Verification Suite for Milestone 4.
Web App Nhà hàng Mộc — Challenger m4_challenger_2.

Adversarial Focus Dimensions:
1. Haversine distance accuracy vs Geodesic standards (WGS-84 reference, antipodal floating point stability)
2. Inactive branch exclusion (con_hoat_dong=False strictly excluded across all endpoints)
3. Coordinate boundary validation (-90 <= lat <= 90, -180 <= lng <= 180, NaN, Inf, non-numeric strings)
4. Radius filtering and limit parameters (multi-branch ordering, boundary distances, 404 threshold)
5. REST API dual endpoint compatibility (/api/branches/nearest/, /api/chi-nhanh/nearest/, /api/chi-nhanh/tim-gan-nhat/)
6. Coordinate parsing fuzzing (WKT, CSV, inverted lat/lng, corrupted strings)
7. High-density geospatial stress test (200 branches, rapid query load)
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
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from branches.models import ChiNhanh
from branches.services import haversine_distance_km, find_nearest_branches
from branches.serializers import ChiNhanhSerializer


def wgs84_vincenty_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """WGS-84 ellipsoid reference formula for geodesic accuracy baseline."""
    a = 6378.137  # semi-major axis (km)
    f = 1 / 298.257223563  # flattening
    b = a * (1 - f)

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    L = math.radians(lon2 - lon1)
    U1 = math.atan((1 - f) * math.tan(phi1))
    U2 = math.atan((1 - f) * math.tan(phi2))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sinU2, cosU2 = math.sin(U2), math.cos(U2)

    lamb = L
    for _ in range(100):
        sinLambda, cosLambda = math.sin(lamb), math.cos(lamb)
        sinSigma = math.sqrt((cosU2 * sinLambda) ** 2 + (cosU1 * sinU2 - sinU1 * cosU2 * cosLambda) ** 2)
        if sinSigma == 0:
            return 0.0
        cosSigma = sinU1 * sinU2 + cosU1 * cosU2 * cosLambda
        sigma = math.atan2(sinSigma, cosSigma)
        sinAlpha = cosU1 * cosU2 * sinLambda / sinSigma
        cos2Alpha = 1 - sinAlpha ** 2
        cos2SigmaM = cosSigma - 2 * sinU1 * sinU2 / cos2Alpha if cos2Alpha != 0 else 0
        C = f / 16 * cos2Alpha * (4 + f * (4 - 3 * cos2Alpha))
        lambPrev = lamb
        lamb = L + (1 - C) * f * sinAlpha * (sigma + C * sinSigma * (cos2SigmaM + C * cosSigma * (-1 + 2 * cos2SigmaM ** 2)))
        if abs(lamb - lambPrev) < 1e-12:
            break
    uSq = cos2Alpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + uSq / 16384 * (4096 + uSq * (-768 + uSq * (320 - 175 * uSq)))
    B = uSq / 1024 * (256 + uSq * (-128 + uSq * (74 - 47 * uSq)))
    deltaSigma = B * sinSigma * (cos2SigmaM + B / 4 * (cosSigma * (-1 + 2 * cos2SigmaM ** 2) - B / 6 * cos2SigmaM * (-3 + 4 * sinSigma ** 2) * (-3 + 4 * cos2SigmaM ** 2)))
    s = b * A * (sigma - deltaSigma)
    return round(s, 2)


class TestMilestone4GISAdversarial(TransactionTestCase):
    """Adversarial stress and edge-case verification for Milestone 4 GIS."""

    def setUp(self):
        self.client = APIClient()
        ChiNhanh.objects.all().delete()

        # Seed realistic branches in Ho Chi Minh City
        self.b_tan_binh = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Tân Bình",
            dia_chi="123 Hoàng Văn Thụ, Phường 2, Tân Bình, TP.HCM",
            so_dien_thoai="028 3811 1111",
            toa_do_gis="106.6669,10.7925",
            con_hoat_dong=True,
        )
        self.b_district1 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Quận 1",
            dia_chi="45 Pasteur, Bến Nghé, Quận 1, TP.HCM",
            so_dien_thoai="028 3822 2222",
            toa_do_gis="106.7009,10.7769",
            con_hoat_dong=True,
        )
        self.b_district7 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Quận 7 (Tạm đóng)",
            dia_chi="78 Nguyễn Thị Thập, Tân Phú, Quận 7, TP.HCM",
            so_dien_thoai="028 3877 7777",
            toa_do_gis="106.7150,10.7325",
            con_hoat_dong=False,  # INACTIVE
        )

    # =========================================================================
    # DIMENSION 1: Haversine Accuracy vs Geodesic Standards & Float Stability
    # =========================================================================

    def test_haversine_identical_point_zero_distance(self):
        """Identical coordinates must return exactly 0.0 distance."""
        dist = haversine_distance_km(10.7925, 106.6669, 10.7925, 106.6669)
        self.assertEqual(dist, 0.0)

    def test_haversine_accuracy_vs_wgs84_vincenty(self):
        """Verify Haversine deviation against WGS-84 geodesic reference is < 0.5%."""
        # 1. Local city distance (Tan Binh to District 1, ~4.1 km)
        d_hav = haversine_distance_km(10.7925, 106.6669, 10.7769, 106.7009)
        d_wgs = wgs84_vincenty_km(10.7925, 106.6669, 10.7769, 106.7009)
        diff_local = abs(d_hav - d_wgs)
        rel_err_local = diff_local / d_wgs
        self.assertLess(rel_err_local, 0.01)  # < 1%
        self.assertLess(diff_local, 0.05)     # < 50 meters diff

        # 2. Regional distance (Hanoi to HCMC, ~1130 km)
        d_hav_long = haversine_distance_km(21.0285, 105.8542, 10.8231, 106.6297)
        d_wgs_long = wgs84_vincenty_km(21.0285, 105.8542, 10.8231, 106.6297)
        rel_err_long = abs(d_hav_long - d_wgs_long) / d_wgs_long
        self.assertLess(rel_err_long, 0.005)  # < 0.5% standard threshold

    def test_haversine_pole_to_pole(self):
        """Poles distance should equal half Earth's circumference (~20015 km)."""
        dist = haversine_distance_km(90.0, 0.0, -90.0, 0.0)
        self.assertAlmostEqual(dist, 20015.11, delta=1.0)

    # =========================================================================
    # DIMENSION 2: Inactive Branch Exclusion
    # =========================================================================

    def test_inactive_branch_excluded_service(self):
        """Inactive branch right at user location must NOT be returned by service."""
        # User coordinate right at District 7 inactive branch (10.7325, 106.7150)
        results = find_nearest_branches(10.7325, 106.7150, limit=1, only_active=True)
        self.assertEqual(len(results), 1)
        self.assertNotEqual(results[0].id, self.b_district7.id)
        # Should return closest ACTIVE branch (District 1, ~6km away)
        self.assertEqual(results[0].id, self.b_district1.id)

    def test_inactive_branch_excluded_api_endpoints(self):
        """Inactive branch must be excluded across all API endpoints."""
        endpoints = [
            "/api/branches/nearest/",
            "/api/chi-nhanh/nearest/",
            "/api/chi-nhanh/tim-gan-nhat/",
            "/api/branches/tim-gan-nhat/",
        ]
        user_coords = {"lat": 10.7325, "lng": 106.7150}
        for ep in endpoints:
            with self.subTest(endpoint=ep):
                resp = self.client.get(ep, user_coords)
                self.assertEqual(resp.status_code, status.HTTP_200_OK)
                data = resp.json()
                self.assertNotEqual(data["id"], self.b_district7.id)
                self.assertEqual(data["id"], self.b_district1.id)
                self.assertTrue(data["is_active"])
                self.assertTrue(data["con_hoat_dong"])

    def test_inactive_branch_excluded_all_true_flag(self):
        """When ?all=true is specified, only active branches are returned."""
        resp = self.client.get("/api/branches/nearest/", {"lat": 10.7930, "lng": 106.6675, "all": "true"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # Only 2 active branches, inactive excluded
        returned_ids = [b["id"] for b in data]
        self.assertNotIn(self.b_district7.id, returned_ids)

    def test_all_branches_inactive_returns_404(self):
        """If all branches in database are inactive, nearest API returns 404 cleanly."""
        ChiNhanh.objects.all().update(con_hoat_dong=False)
        resp = self.client.get("/api/branches/nearest/", {"lat": 10.7930, "lng": 106.6675})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("đang hoạt động", resp.json()["detail"])

    # =========================================================================
    # DIMENSION 3: Coordinate Boundary Validation (-90..90, -180..180, malformed)
    # =========================================================================

    def test_boundary_valid_limits(self):
        """Valid boundary coordinates (-90, 90, -180, 180) must be accepted without 400."""
        valid_pairs = [
            (90.0, 180.0),
            (-90.0, -180.0),
            (0.0, 0.0),
            (90.0, -180.0),
            (-90.0, 180.0),
        ]
        for lat, lng in valid_pairs:
            with self.subTest(lat=lat, lng=lng):
                resp = self.client.get("/api/branches/nearest/", {"lat": lat, "lng": lng})
                self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
                self.assertNotEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_boundary_out_of_bounds_rejected(self):
        """Out-of-bounds coordinates must return HTTP 400 Bad Request."""
        invalid_pairs = [
            (90.0001, 106.66),
            (-90.0001, 106.66),
            (10.79, 180.0001),
            (10.79, -180.0001),
            (999.0, 999.0),
            (-999.0, -999.0),
        ]
        for lat, lng in invalid_pairs:
            with self.subTest(lat=lat, lng=lng):
                resp = self.client.get("/api/branches/nearest/", {"lat": lat, "lng": lng})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("không hợp lệ", resp.json()["detail"])

    def test_boundary_special_floats_nan_inf_rejected(self):
        """NaN and Infinity strings must return HTTP 400 Bad Request."""
        special_values = ["nan", "NaN", "inf", "-inf", "Infinity", "-Infinity"]
        for val in special_values:
            with self.subTest(val=val):
                resp = self.client.get("/api/branches/nearest/", {"lat": val, "lng": 106.66})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_boundary_non_numeric_strings_rejected(self):
        """Non-numeric strings must return HTTP 400 Bad Request."""
        resp = self.client.get("/api/branches/nearest/", {"lat": "invalid_lat", "lng": "106.66"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phải là số thực", resp.json()["detail"])

    def test_missing_coordinates_rejected(self):
        """Missing lat or lng must return HTTP 400 Bad Request."""
        resp1 = self.client.get("/api/branches/nearest/", {"lat": 10.79})
        self.assertEqual(resp1.status_code, status.HTTP_400_BAD_REQUEST)
        resp2 = self.client.get("/api/branches/nearest/", {"lng": 106.66})
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        resp3 = self.client.get("/api/branches/nearest/")
        self.assertEqual(resp3.status_code, status.HTTP_400_BAD_REQUEST)

    # =========================================================================
    # DIMENSION 4: Radius Filtering & Limit Parameters
    # =========================================================================

    def test_radius_filtering_within_and_exceeded(self):
        """Verify strict distance radius filtering."""
        user_coords = {"lat": 10.7930, "lng": 106.6675}  # ~100m from Tan Binh, ~4.1km from Q1

        # Radius 1.0 km: Only Tan Binh should match
        resp_1km = self.client.get("/api/branches/nearest/", {**user_coords, "radius": 1.0, "all": "true"})
        self.assertEqual(resp_1km.status_code, status.HTTP_200_OK)
        data_1km = resp_1km.json()
        self.assertEqual(len(data_1km), 1)
        self.assertEqual(data_1km[0]["id"], self.b_tan_binh.id)

        # Radius 5.0 km: Both Tan Binh and District 1 should match
        resp_5km = self.client.get("/api/branches/nearest/", {**user_coords, "radius": 5.0, "all": "true"})
        self.assertEqual(resp_5km.status_code, status.HTTP_200_OK)
        data_5km = resp_5km.json()
        self.assertEqual(len(data_5km), 2)
        self.assertEqual(data_5km[0]["id"], self.b_tan_binh.id)
        self.assertEqual(data_5km[1]["id"], self.b_district1.id)

        # Radius 0.05 km (50 meters): No branch matches -> HTTP 404
        resp_50m = self.client.get("/api/branches/nearest/", {**user_coords, "radius": 0.05})
        self.assertEqual(resp_50m.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("0.05 km", resp_50m.json()["detail"])

    def test_limit_parameter_in_proximity_list(self):
        """Verify limit parameter restricts number of returned branches."""
        user_coords = {"lat": 10.7930, "lng": 106.6675}
        resp = self.client.get("/api/branches/", {**user_coords, "limit": 1})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        results = data["results"] if isinstance(data, dict) and "results" in data else data
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.b_tan_binh.id)

    # =========================================================================
    # DIMENSION 5: REST API Dual Endpoints & Field Parity
    # =========================================================================

    def test_vietnamese_query_param_aliases(self):
        """API must support Vietnamese query parameter aliases (vi_do, kinh_do, ban_kinh)."""
        resp = self.client.get("/api/chi-nhanh/tim-gan-nhat/", {
            "vi_do": 10.7930,
            "kinh_do": 106.6675,
            "ban_kinh": 5.0,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data["id"], self.b_tan_binh.id)

    def test_response_payload_dual_fields(self):
        """Serializer output must contain both Vietnamese and English fields."""
        resp = self.client.get("/api/branches/nearest/", {"lat": 10.7930, "lng": 106.6675})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        expected_fields = [
            "id", "ten", "dia_chi", "so_dien_thoai", "toa_do_gis",
            "kinh_do", "vi_do", "longitude", "latitude", "lng", "lat",
            "name", "address", "phone", "is_active", "con_hoat_dong",
            "distance_km", "distance_m", "khoang_cach_km", "khoang_cach_m",
        ]
        for f in expected_fields:
            self.assertIn(f, data, f"Required field '{f}' missing from nearest API payload")

        # Metric synchronization checks
        self.assertEqual(data["distance_km"], data["khoang_cach_km"])
        self.assertEqual(data["distance_m"], data["khoang_cach_m"])
        self.assertAlmostEqual(data["distance_km"] * 1000, data["distance_m"], delta=1.0)
        self.assertEqual(data["name"], data["ten"])
        self.assertEqual(data["address"], data["dia_chi"])
        self.assertEqual(data["is_active"], data["con_hoat_dong"])

    # =========================================================================
    # DIMENSION 6: Coordinate Parser Fuzzing & Auto-Swap
    # =========================================================================

    def test_coordinate_parser_robustness(self):
        """ChiNhanh._parse_coords must parse WKT, CSV, lists, and auto-detect lat/lng order in Vietnam."""
        test_cases = [
            ("106.6669,10.7925", (106.6669, 10.7925)),           # CSV: lng, lat
            ("10.7925, 106.6669", (106.6669, 10.7925)),          # CSV: lat, lng (auto-swapped)
            ("POINT (106.6669 10.7925)", (106.6669, 10.7925)),   # WKT: lng lat
            ("POINT (10.7925 106.6669)", (106.6669, 10.7925)),   # WKT: lat lng (auto-swapped)
            ((106.6669, 10.7925), (106.6669, 10.7925)),          # Tuple
            ([10.7925, 106.6669], (106.6669, 10.7925)),          # List (auto-swapped)
            (None, (None, None)),                                 # None
            ("", (None, None)),                                   # Empty
            ("corrupted_string", (None, None)),                   # Corrupt string
            ("invalid,coords", (None, None)),                     # Bad CSV
            ("106.6669", (None, None)),                           # Single coord
        ]
        for raw_val, expected in test_cases:
            with self.subTest(raw=raw_val):
                b = ChiNhanh(ten="Temp", dia_chi="Temp", toa_do_gis=raw_val)
                parsed = b._parse_coords()
                self.assertEqual(parsed, expected)

    # =========================================================================
    # DIMENSION 7: High-Density Geospatial Query Stress Test
    # =========================================================================

    def test_high_density_geospatial_stress(self):
        """Stress-test 200 branches with 100 rapid random nearest queries."""
        ChiNhanh.objects.all().delete()
        branches = []
        for i in range(200):
            lat = round(random.uniform(8.5, 22.5), 4)
            lng = round(random.uniform(102.5, 109.5), 4)
            active = (i % 10 != 0)  # 10% inactive
            branches.append(ChiNhanh(
                ten=f"Chi nhánh Mộc #{i+1}",
                dia_chi=f"Địa chỉ số #{i+1}",
                toa_do_gis=f"{lng},{lat}",
                con_hoat_dong=active
            ))
        ChiNhanh.objects.bulk_create(branches)

        # 100 queries
        for _ in range(100):
            q_lat = round(random.uniform(10.0, 11.5), 4)
            q_lng = round(random.uniform(106.0, 107.0), 4)
            resp = self.client.get("/api/branches/nearest/", {"lat": q_lat, "lng": q_lng})
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            data = resp.json()
            self.assertTrue(data["is_active"])
            self.assertTrue(data["con_hoat_dong"])
            self.assertGreaterEqual(data["distance_km"], 0.0)


if __name__ == "__main__":
    unittest.main()
