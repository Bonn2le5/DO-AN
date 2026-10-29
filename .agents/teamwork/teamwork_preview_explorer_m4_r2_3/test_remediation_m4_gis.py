"""
Remediation Verification Tests for GIS Spatial Edge Cases (Milestone 4 R2).
Web App Nhà hàng Mộc — Explorer m4_r2_explorer_3.

Covers:
1. Antipodal coordinate pairs in Haversine (IEEE 754 precision clamping)
2. Coordinate boundary validation in ChiNhanhViewSet.list (-90 <= lat <= 90, -180 <= lng <= 180, NaN, Inf)
3. Parameter sanitization for radius in both list and nearest (HTTP 400 for non-numeric, <= 0)
4. Parameter sanitization for limit in both list and nearest (HTTP 400 for non-numeric, <= 0)
"""

import math
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from branches.models import ChiNhanh
from branches.services import haversine_distance_km


class TestGISRemediationM4R2(TestCase):
    def setUp(self):
        self.client = APIClient()
        ChiNhanh.objects.all().delete()
        self.branch = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Tân Bình",
            dia_chi="123 Hoàng Văn Thụ, Tân Bình, TP.HCM",
            so_dien_thoai="028 3811 1111",
            toa_do_gis="106.6669,10.7925",
            con_hoat_dong=True,
        )

    def test_haversine_antipodal_pairs_clamping(self):
        """Verify antipodal coordinate pairs do not raise math domain error."""
        known_failing_pair = (
            -5.902783176600167, -150.92817621645105,
            5.902783176600167, 29.07182378354895
        )
        dist = haversine_distance_km(*known_failing_pair)
        self.assertAlmostEqual(dist, 20015.11, places=1)

    def test_nearest_invalid_radius_returns_400(self):
        """Malformed or non-positive radius in nearest view must return HTTP 400."""
        invalid_radii = ["abc", "nan", "inf", "-5", "0"]
        for r in invalid_radii:
            with self.subTest(radius=r):
                resp = self.client.get("/api/branches/nearest/", {"lat": 10.7925, "lng": 106.6669, "radius": r})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nearest_invalid_limit_returns_400(self):
        """Malformed or non-positive limit in nearest view must return HTTP 400."""
        invalid_limits = ["abc", "3.14", "-1", "0"]
        for lim in invalid_limits:
            with self.subTest(limit=lim):
                resp = self.client.get("/api/branches/nearest/", {"lat": 10.7925, "lng": 106.6669, "limit": lim})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_coordinate_boundary_validation(self):
        """Invalid coordinate boundaries in list view must return HTTP 400."""
        invalid_coords = [
            (999.0, 999.0),
            (-999.0, -999.0),
            (95.0, 106.6669),
            (10.7925, 200.0),
            ("nan", 106.6669),
            ("inf", 106.6669),
        ]
        for lat, lng in invalid_coords:
            with self.subTest(lat=lat, lng=lng):
                resp = self.client.get("/api/branches/", {"lat": lat, "lng": lng})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_single_coordinate_returns_400(self):
        """Providing only lat or only lng in list view must return HTTP 400."""
        resp1 = self.client.get("/api/branches/", {"lat": 10.7925})
        self.assertEqual(resp1.status_code, status.HTTP_400_BAD_REQUEST)
        resp2 = self.client.get("/api/branches/", {"lng": 106.6669})
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_invalid_radius_and_limit_returns_400(self):
        """Malformed or non-positive radius and limit in list view must return HTTP 400."""
        base_coords = {"lat": 10.7925, "lng": 106.6669}
        for r in ["abc", "-1", "0"]:
            with self.subTest(radius=r):
                resp = self.client.get("/api/branches/", {**base_coords, "radius": r})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        for lim in ["abc", "-1", "0"]:
            with self.subTest(limit=lim):
                resp = self.client.get("/api/branches/", {**base_coords, "limit": lim})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
