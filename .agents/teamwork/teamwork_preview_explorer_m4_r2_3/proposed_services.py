"""
GIS Spatial Service for ChiNhanh (Branches).
Provides hybrid execution:
1. High-performance PostGIS native query using ST_Distance & GiST spatial index.
2. In-memory Haversine geodesic fallback when running on SQLite (testing) or non-spatial backends.
"""
import math
from typing import List, Optional, Tuple
from django.conf import settings
from django.db import connection
from .models import ChiNhanh

EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate geodesic distance between two points on Earth using the Haversine formula.
    Matches PostGIS ST_Distance(geography).
    Clamps 'a' in [0.0, 1.0] to eliminate floating-point domain errors on antipodal coordinates.
    """
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


def is_spatial_database() -> bool:
    """Check if the active database backend supports spatial GeoDjango queries."""
    if getattr(settings, "TESTING", False) or getattr(settings, "USE_SQLITE", False):
        return False
    return getattr(connection.features, "has_spatial_db", False)


def find_nearest_branches(
    user_lat: float,
    user_lng: float,
    radius_km: Optional[float] = None,
    limit: Optional[int] = None,
    only_active: bool = True,
) -> List[ChiNhanh]:
    """
    Find branches nearest to (user_lat, user_lng) ordered by distance ascending.
    Uses PostGIS ST_Distance & GiST index when running on PostgreSQL,
    automatically falls back to Haversine geodesic calculation on SQLite/testing.
    """
    user_lat = float(user_lat)
    user_lng = float(user_lng)

    # 1. Native PostGIS Execution
    if is_spatial_database():
        try:
            from django.contrib.gis.geos import Point
            from django.contrib.gis.db.models.functions import Distance
            from django.contrib.gis.measure import D

            # Point(x=lng, y=lat, srid=4326)
            user_point = Point(user_lng, user_lat, srid=4326)
            qs = ChiNhanh.objects.all()
            if only_active:
                qs = qs.filter(con_hoat_dong=True)

            if radius_km is not None and float(radius_km) > 0:
                qs = qs.filter(toa_do_gis__dwithin=(user_point, D(km=float(radius_km))))

            qs = qs.annotate(distance=Distance("toa_do_gis", user_point)).order_by("distance")

            if limit:
                qs = qs[:limit]

            results = []
            for b in qs:
                dist_m = getattr(b.distance, "m", float(b.distance))
                dist_km = getattr(b.distance, "km", dist_m / 1000.0)
                b.distance_km = round(dist_km, 2)
                b.distance_m = round(dist_m, 1)
                b.khoang_cach_km = b.distance_km
                b.khoang_cach_m = b.distance_m
                results.append(b)
            return results
        except Exception:
            # Fall back gracefully to Haversine if PostGIS query fails
            pass

    # 2. SQLite / Non-spatial Fallback Execution (Haversine)
    qs = ChiNhanh.objects.all()
    if only_active:
        qs = qs.filter(con_hoat_dong=True)

    scored_branches = []
    for branch in qs:
        b_lat = branch.vi_do
        b_lng = branch.kinh_do
        if b_lat is None or b_lng is None:
            continue
        dist_km = haversine_distance_km(user_lat, user_lng, b_lat, b_lng)
        if radius_km is not None and float(radius_km) > 0 and dist_km > float(radius_km):
            continue
        branch.distance_km = dist_km
        branch.distance_m = round(dist_km * 1000, 1)
        branch.khoang_cach_km = dist_km
        branch.khoang_cach_m = branch.distance_m
        scored_branches.append((dist_km, branch))

    scored_branches.sort(key=lambda item: item[0])

    if limit:
        scored_branches = scored_branches[:limit]

    return [b for _, b in scored_branches]
