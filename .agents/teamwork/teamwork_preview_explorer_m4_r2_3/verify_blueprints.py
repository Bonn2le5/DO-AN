#!/usr/bin/env python3
"""
Verification script for GIS edge case fixes.
Tests:
1. Antipodal pairs float precision clamping in Haversine.
2. Coordinate boundary validation in list view.
3. Radius parameter sanitization in list and nearest views.
4. Limit parameter sanitization in list and nearest views.
"""
import os
import sys
import math
import random

PROJECT_ROOT = "/Users/VuVan/Documents/DO-AN"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "moc-backend"))
os.environ["TESTING"] = "1"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory
from branches.models import ChiNhanh

# Import proposed implementations
# 1. Haversine with clamp
EARTH_RADIUS_KM = 6371.0088

def haversine_clamped(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(EARTH_RADIUS_KM * c, 2)


def test_antipodal_pairs():
    print("--- 1. Testing 100,000 Antipodal Pairs with Clamping ---")
    random.seed(42)
    failures = 0
    known_failing_pair = (-5.902783176600167, -150.92817621645105, 5.902783176600167, 29.07182378354895)
    d = haversine_clamped(*known_failing_pair)
    assert d == 20015.11, f"Expected 20015.11, got {d}"
    print(f"Known failure pair (-5.90, -150.93) to (5.90, 29.07): PASSED, dist = {d} km")

    for _ in range(100000):
        lat = random.uniform(-89.9, 89.9)
        lon = random.uniform(-179.9, 179.9)
        # Antipodal point: -lat, lon + 180 (wrapped)
        anti_lat = -lat
        anti_lon = lon + 180.0 if lon < 0 else lon - 180.0
        try:
            dist = haversine_clamped(lat, lon, anti_lat, anti_lon)
            assert 20000.0 < dist < 20030.0
        except Exception as e:
            failures += 1

    assert failures == 0, f"Encountered {failures} antipodal failures!"
    print(f"100,000 random antipodal pairs: 100% PASSED (0 failures)")


def test_proposed_views():
    print("\n--- 2. Testing Proposed Views Edge Cases ---")
    # Dynamically load the proposed viewset class
    with open("/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_r2_3/proposed_views.py") as f:
        code = f.read()

    namespace = {"__name__": "branches.views", "__file__": "proposed_views.py"}
    exec(code, namespace)
    ProposedChiNhanhViewSet = namespace["ChiNhanhViewSet"]

    factory = APIRequestFactory()
    list_view = ProposedChiNhanhViewSet.as_view({"get": "list"})
    nearest_view = ProposedChiNhanhViewSet.as_view({"get": "nearest"})

    # Seed test branch
    ChiNhanh.objects.all().delete()
    ChiNhanh.objects.create(
        ten="Chi nhánh Trung Tâm", dia_chi="123 Lê Lợi, Q1", toa_do_gis="106.7000,10.7700", con_hoat_dong=True
    )

    test_matrix = [
        # (view, query_url, expected_status, description)
        (nearest_view, "/?lat=10.77&lng=106.70", 200, "Nearest valid params"),
        (nearest_view, "/?lat=10.77", 400, "Nearest missing lng"),
        (nearest_view, "/?lng=106.70", 400, "Nearest missing lat"),
        (nearest_view, "/", 400, "Nearest missing both"),
        (nearest_view, "/?lat=95.0&lng=106.70", 400, "Nearest lat > 90"),
        (nearest_view, "/?lat=-95.0&lng=106.70", 400, "Nearest lat < -90"),
        (nearest_view, "/?lat=10.77&lng=185.0", 400, "Nearest lng > 180"),
        (nearest_view, "/?lat=nan&lng=106.70", 400, "Nearest lat NaN"),
        (nearest_view, "/?lat=inf&lng=106.70", 400, "Nearest lat Inf"),
        (nearest_view, "/?lat=10.77&lng=106.70&radius=abc", 400, "Nearest malformed radius string"),
        (nearest_view, "/?lat=10.77&lng=106.70&radius=-5", 400, "Nearest negative radius"),
        (nearest_view, "/?lat=10.77&lng=106.70&radius=0", 400, "Nearest zero radius"),
        (nearest_view, "/?lat=10.77&lng=106.70&radius=nan", 400, "Nearest radius NaN"),
        (nearest_view, "/?lat=10.77&lng=106.70&limit=abc", 400, "Nearest malformed limit string"),
        (nearest_view, "/?lat=10.77&lng=106.70&limit=-1", 400, "Nearest negative limit"),
        (nearest_view, "/?lat=10.77&lng=106.70&limit=0", 400, "Nearest zero limit"),
        (nearest_view, "/?lat=10.77&lng=106.70&radius=10.0&all=true", 200, "Nearest all=true within radius"),
        (nearest_view, "/?lat=10.85&lng=106.70&radius=0.001", 404, "Nearest radius 1m threshold exceeded"),

        # List view tests
        (list_view, "/", 200, "List standard no params"),
        (list_view, "/?lat=10.77&lng=106.70", 200, "List proximity valid coordinates"),
        (list_view, "/?lat=10.77", 400, "List lat provided without lng"),
        (list_view, "/?lng=106.70", 400, "List lng provided without lat"),
        (list_view, "/?lat=999&lng=999", 400, "List out-of-bounds coordinates"),
        (list_view, "/?lat=nan&lng=106.70", 400, "List lat NaN"),
        (list_view, "/?lat=inf&lng=106.70", 400, "List lat Inf"),
        (list_view, "/?lat=10.77&lng=106.70&radius=abc", 400, "List malformed radius string"),
        (list_view, "/?lat=10.77&lng=106.70&radius=-1", 400, "List negative radius"),
        (list_view, "/?lat=10.77&lng=106.70&radius=0", 400, "List zero radius"),
        (list_view, "/?lat=10.77&lng=106.70&limit=abc", 400, "List malformed limit string"),
        (list_view, "/?lat=10.77&lng=106.70&limit=-10", 400, "List negative limit"),
        (list_view, "/?lat=10.77&lng=106.70&limit=0", 400, "List zero limit"),
        (list_view, "/?lat=10.77&lng=106.70&radius=5.0&limit=1", 200, "List valid proximity radius and limit"),
    ]

    for v, url, exp_status, desc in test_matrix:
        req = factory.get(url)
        resp = v(req)
        assert resp.status_code == exp_status, f"FAILED [{desc}]: url={url}, expected={exp_status}, got={resp.status_code}, data={getattr(resp, 'data', None)}"
        print(f"  PASS: [{desc}] {url} -> {resp.status_code}")

    print("\nProposed views passed all 32 edge-case matrix scenarios!")

if __name__ == "__main__":
    test_antipodal_pairs()
    test_proposed_views()
