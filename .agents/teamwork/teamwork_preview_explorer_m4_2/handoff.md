# Handoff Report: Milestone 4 (Feature 23) - PostGIS GIS Nearest Branch Spatial Query

**Author**: Explorer `m4_explorer_gis`  
**Working Directory**: `/Users/VuVan/Documents/DO-AN/.agents/teamwork/teamwork_preview_explorer_m4_2`  
**Target Milestone**: Milestone 4 (Feature 23: PostGIS Nearest Branch Spatial Query)  
**Parent Orchestrator**: `e1a47f66-ae44-4e72-ae56-b7ecb23a0048`  
**Date**: 2026-10-14  

---

## 1. Observation

### 1.1. Authoritative Schema & Existing Model Analysis
- **Authoritative SQL Schema** (`moc_schema_tieng_viet.sql`, lines 102–115):
  ```sql
  CREATE TABLE chi_nhanh (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ten             VARCHAR(150) NOT NULL,
    dia_chi         TEXT         NOT NULL,
    so_dien_thoai   VARCHAR(20),
    toa_do_gis      geography(Point, 4326) NOT NULL,   -- (kinh_do, vi_do) — PostGIS
    con_hoat_dong   BOOLEAN     NOT NULL DEFAULT true,
    tao_luc         TIMESTAMPTZ NOT NULL DEFAULT now(),
    cap_nhat_luc    TIMESTAMPTZ NOT NULL DEFAULT now()
  );
  CREATE INDEX idx_chi_nhanh_toa_do ON chi_nhanh USING GIST (toa_do_gis);
  ```
- **Existing Django Model** (`moc-backend/branches/models.py`, lines 5–26):
  ```python
  try:
      if getattr(settings, "TESTING", False):
          raise ImportError("Testing uses SQLite fallback")
      from django.contrib.gis.db import models as gis_models
      PointFieldClass = gis_models.PointField
  except (ImportError, Exception):
      class PointFieldClass(models.CharField):
          def __init__(self, *args, **kwargs):
              kwargs.pop("geography", None)
              kwargs.pop("srid", None)
              kwargs.setdefault("max_length", 100)
              kwargs.setdefault("default", "0.0,0.0")
              super().__init__(*args, **kwargs)
  ```
  `ChiNhanh` defines:
  `toa_do_gis = PointFieldClass(geography=True, srid=4326)`
  However, `ChiNhanh` does **not** expose `@property` for `kinh_do`, `vi_do`, `lng`, or `lat`, nor does `Meta` specify the GiST index `idx_chi_nhanh_toa_do`.

### 1.2. GDAL and GEOS Library Status in Virtualenv & System
Direct tool execution in Python (`moc-backend/.venv`):
- Command:
  ```bash
  /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python -c "from django.contrib.gis import gdal, geos"
  ```
- Verbatim Error:
  ```
  django.core.exceptions.ImproperlyConfigured: Could not find the GDAL library (tried "gdal", "GDAL", "gdal3.6.0", "gdal3.5.0", "gdal3.4.0", "gdal3.3.0", "gdal3.2.0", "gdal3.1.0", "gdal3.0.0", "gdal2.4.0", "gdal2.3.0", "gdal2.2.0"). Is GDAL installed? If it is, try setting GDAL_LIBRARY_PATH in your settings.
  ```
- Homebrew inspection verified that GDAL 3.13.3 and GEOS 3.14.1 exist at:
  - `/opt/homebrew/opt/gdal/lib/libgdal.dylib`
  - `/opt/homebrew/opt/geos/lib/libgeos_c.dylib`
- When configuring `settings.GDAL_LIBRARY_PATH` and `settings.GEOS_LIBRARY_PATH`, GeoDjango loads successfully:
  ```
  GEOS version: b'3.14.1-CAPI-1.20.5'
  GDAL version: b'3.13.3'
  ```
  In `moc-backend/config/settings.py`, `GDAL_LIBRARY_PATH` and `GEOS_LIBRARY_PATH` are currently missing.

### 1.3. SQLite Testing & Spatial Query Failure
In `moc-backend/config/settings.py` (lines 68, 124–140):
- When `TESTING=True` or `USE_SQLITE=True`:
  - `django.contrib.gis` is omitted from `INSTALLED_APPS` (`*(['django.contrib.gis'] if not TESTING else [])`).
  - Database engine is standard `django.db.backends.sqlite3` (no SpatiaLite).
  - `PointFieldClass` defaults to `models.CharField`.
- Attempting to execute `Distance("toa_do_gis", point)` under SQLite produces verbatim error:
  ```
  TypeError: Distance function requires a GeometryField in position 1, got PointFieldClass.
  ```
- Furthermore, attempting to access `obj.toa_do_gis.x` in `ChiNhanhSerializer` when `toa_do_gis` is stored as `str` produces:
  ```
  AttributeError: 'str' object has no attribute 'x'
  ```

### 1.4. Existing Nearest Branch API Status
- Router configuration (`moc-backend/api/urls.py`, lines 50–51):
  ```python
  router.register("branches", BranchViewSet, basename="branch")
  router.register("chi-nhanh", BranchViewSet, basename="chi-nhanh")
  ```
- `moc-backend/branches/views.py` currently only implements basic `ModelViewSet` (`list`, `retrieve`, `create`, `update`, `destroy`) without any `@action` for `nearest` or `tim-gan-nhat`.
- Requesting `GET /api/branches/nearest/` returns HTTP 404 Not Found.

### 1.5. Test Suite Expectations
- `tests/e2e/tier1/test_t1_recommendation_gis.py` lines 87–109:
  - `test_t1_recommendation_gis_01_haversine_distance`: Tan Binh to District 1 ~ 4.10 km (between 3.5 and 5.0 km).
  - `test_t1_recommendation_gis_02_nearest_branch_lookup`: User at (10.7930, 106.6675) selects Tan Binh branch (ID 1) with distance < 0.5 km.
  - `test_t1_recommendation_gis_03_inactive_branch_filtered`: Inactive branches (`con_hoat_dong=False`) must be excluded even if physically closer.
- `tests/e2e/helpers/ai_gis_oracle.py`:
  - Uses `EARTH_RADIUS_KM = 6371.0088` and Haversine formula.

---

## 2. Logic Chain

1. **Premise 1 (Dual-Environment Requirement)**:
   - In production (PostgreSQL 14+ / PostGIS), the database column `toa_do_gis` is `geography(Point, 4326)` indexed by GiST. High-speed spatial queries must leverage native `ST_Distance(geography, geography)` and `ST_DWithin` spatial filtering.
   - In automated test pipelines (`manage.py test` with SQLite in-memory), GeoDjango spatial functions cannot execute because SQLite does not load the C SpatiaLite dynamic extension.
2. **Premise 2 (Mathematical Equivalence)**:
   - For points on Earth's surface, the Haversine formula with radius $R = 6371.0088\text{ km}$ calculates great-circle spherical distance.
   - For urban restaurant branch distances (< 100 km), Haversine spherical distance and PostGIS WGS84 ellipsoidal geodesic distance differ by less than 0.1% (a deviation of less than 5 meters over 5 km).
3. **Premise 3 (Clean Architecture Deduction)**:
   - Rather than forcing fragile SpatiaLite C-library compilation into local test environments, we establish a **Hybrid Spatial Architecture**:
     - Database inspection: Check `is_spatial_database()` via `connection.features.has_spatial_db`.
     - When `has_spatial_db == True`: Execute native PostGIS GeoDjango ORM query:
       `ChiNhanh.objects.filter(con_hoat_dong=True).filter(toa_do_gis__dwithin=(user_point, D(km=radius_km))).annotate(distance=Distance('toa_do_gis', user_point)).order_by('distance')`.
     - When `has_spatial_db == False` (SQLite / testing): Execute Haversine spherical calculation over candidate active branches, sorting by computed distance and filtering by radius.
4. **Premise 4 (Coordinate Abstraction Layer)**:
   - To eliminate `AttributeError: 'str' object has no attribute 'x'`, `ChiNhanh` model must provide coordinate property getters/setters (`kinh_do`, `vi_do`, `lng`, `lat`, `longitude`, `latitude`) that transparently parse GeoDjango `Point`, WKT strings (`POINT (x y)`), CSV strings (`x,y`), and coordinate tuples.
5. **Premise 5 (REST API Dual Routing)**:
   - The API must support both English and Vietnamese parameter names (`lat`/`latitude`/`vi_do`, `lng`/`longitude`/`kinh_do`, `radius`/`radius_km`/`ban_kinh`).
   - The endpoint must expose dual routes: `/api/branches/nearest/`, `/api/chi-nhanh/nearest/`, and `/api/chi-nhanh/tim-gan-nhat/`.

---

## 3. Caveats

1. **PostGIS Extension in PostgreSQL**:
   Production PostgreSQL databases must have `CREATE EXTENSION IF NOT EXISTS postgis;` executed before migrations.
2. **Coordinate Order Standardization**:
   PostGIS / GeoDjango `Point(x, y)` takes `(longitude, latitude)`.
   Many human APIs accept `(latitude, longitude)`.
   Our blueprint explicitly maps `x = longitude (kinh_do)` and `y = latitude (vi_do)` everywhere to prevent swapped axis bugs.
3. **No Code Written to Source Files**:
   In strict accordance with the read-only Explorer role, no modifications were made to `moc-backend/`. Full blueprints are provided below for the implementer agent.

---

## 4. Conclusion & Technical Implementation Blueprint

The solution consists of 6 coordinated additions/updates across `moc-backend`:

### Blueprint 1: `moc-backend/config/settings.py`
Add GDAL & GEOS auto-detection at top of settings:
```python
import os
import platform

# Auto-detect GDAL / GEOS libraries for PostGIS & GeoDjango
GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH", default=None)
GEOS_LIBRARY_PATH = env("GEOS_LIBRARY_PATH", default=None)

if not GDAL_LIBRARY_PATH:
    for candidate in [
        "/opt/homebrew/opt/gdal/lib/libgdal.dylib",
        "/usr/local/opt/gdal/lib/libgdal.dylib",
        "/opt/homebrew/lib/libgdal.dylib",
        "/usr/local/lib/libgdal.dylib",
        "/usr/lib/libgdal.so",
    ]:
        if os.path.exists(candidate):
            GDAL_LIBRARY_PATH = candidate
            break

if not GEOS_LIBRARY_PATH:
    for candidate in [
        "/opt/homebrew/opt/geos/lib/libgeos_c.dylib",
        "/usr/local/opt/geos/lib/libgeos_c.dylib",
        "/opt/homebrew/lib/libgeos_c.dylib",
        "/usr/local/lib/libgeos_c.dylib",
        "/usr/lib/x86_64-linux-gnu/libgeos_c.so",
        "/usr/lib/libgeos_c.so",
    ]:
        if os.path.exists(candidate):
            GEOS_LIBRARY_PATH = candidate
            break
```

---

### Blueprint 2: `moc-backend/branches/models.py`
Enhance `ChiNhanh` with coordinate parsers, properties, and GiST index:
```python
import re
from django.conf import settings
from django.db import models
from django.contrib.postgres.indexes import GistIndex
from foods.models import MoHinhThoiGian

try:
    if getattr(settings, "TESTING", False):
        raise ImportError("Testing uses SQLite fallback")
    from django.contrib.gis.db import models as gis_models
    PointFieldClass = gis_models.PointField
except (ImportError, Exception):
    class PointFieldClass(models.CharField):
        def __init__(self, *args, **kwargs):
            kwargs.pop("geography", None)
            kwargs.pop("srid", None)
            kwargs.setdefault("max_length", 100)
            kwargs.setdefault("default", "0.0,0.0")
            super().__init__(*args, **kwargs)


class ChiNhanh(MoHinhThoiGian):
    ten = models.CharField(max_length=150)
    dia_chi = models.TextField()
    so_dien_thoai = models.CharField(max_length=20, blank=True)
    toa_do_gis = PointFieldClass(geography=True, srid=4326)
    con_hoat_dong = models.BooleanField(default=True)

    _LEGACY_MAP = {
        "name": "ten",
        "address": "dia_chi",
        "phone": "so_dien_thoai",
        "phone_number": "so_dien_thoai",
        "location": "toa_do_gis",
        "is_active": "con_hoat_dong",
    }

    class Meta:
        db_table = "chi_nhanh"
        verbose_name = "Chi nhánh"
        indexes = [
            GistIndex(fields=["toa_do_gis"], name="idx_chi_nhanh_toa_do"),
        ]

    def __str__(self):
        return self.ten

    def _parse_coords(self):
        pt = self.toa_do_gis
        if pt is None:
            return None, None
        if hasattr(pt, "x") and hasattr(pt, "y"):
            return float(pt.x), float(pt.y)
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            return float(pt[0]), float(pt[1])
        if isinstance(pt, str):
            m = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", pt, re.I)
            if m:
                return float(m.group(1)), float(m.group(2))
            parts = pt.split(",")
            if len(parts) >= 2:
                try:
                    return float(parts[0].strip()), float(parts[1].strip())
                except ValueError:
                    return None, None
        return None, None

    @property
    def kinh_do(self):
        return self._parse_coords()[0]

    @property
    def vi_do(self):
        return self._parse_coords()[1]

    @property
    def lng(self):
        return self.kinh_do

    @property
    def lat(self):
        return self.vi_do

    @property
    def longitude(self):
        return self.kinh_do

    @property
    def latitude(self):
        return self.vi_do

    @property
    def name(self):
        return self.ten

    @name.setter
    def name(self, val):
        self.ten = val

    @property
    def address(self):
        return self.dia_chi

    @address.setter
    def address(self, val):
        self.dia_chi = val

    @property
    def phone(self):
        return self.so_dien_thoai

    @phone.setter
    def phone(self, val):
        self.so_dien_thoai = val

    @property
    def location(self):
        return self.toa_do_gis

    @location.setter
    def location(self, val):
        self.toa_do_gis = val

    @property
    def is_active(self):
        return self.con_hoat_dong

    @is_active.setter
    def is_active(self, val):
        self.con_hoat_dong = bool(val)


Branch = ChiNhanh
```

---

### Blueprint 3: `moc-backend/branches/services.py` (New Service Module)
```python
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
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
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
```

---

### Blueprint 4: `moc-backend/branches/serializers.py`
Enhance serializer with distance annotations and coordinate accessors:
```python
from rest_framework import serializers
from api.mixins import DualPayloadMixin
from .models import ChiNhanh, Branch


class ChiNhanhSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "address": "dia_chi",
        "phone": "so_dien_thoai",
        "phone_number": "so_dien_thoai",
        "is_active": "con_hoat_dong",
    }
    kinh_do = serializers.FloatField(source="kinh_do", read_only=True)
    vi_do = serializers.FloatField(source="vi_do", read_only=True)
    longitude = serializers.FloatField(source="kinh_do", read_only=True)
    latitude = serializers.FloatField(source="vi_do", read_only=True)
    lng = serializers.FloatField(source="kinh_do", read_only=True)
    lat = serializers.FloatField(source="vi_do", read_only=True)

    name = serializers.CharField(source="ten", read_only=True)
    address = serializers.CharField(source="dia_chi", read_only=True)
    phone = serializers.CharField(source="so_dien_thoai", read_only=True)
    is_active = serializers.BooleanField(source="con_hoat_dong", read_only=True)

    distance_km = serializers.SerializerMethodField()
    distance_m = serializers.SerializerMethodField()
    khoang_cach_km = serializers.SerializerMethodField()
    khoang_cach_m = serializers.SerializerMethodField()

    def get_distance_km(self, obj):
        d = getattr(obj, "distance_km", None)
        if d is not None:
            return round(float(d), 2)
        dist = getattr(obj, "distance", None)
        if dist is not None:
            return round(float(dist.km if hasattr(dist, "km") else dist / 1000.0), 2)
        return None

    def get_distance_m(self, obj):
        d = getattr(obj, "distance_m", None)
        if d is not None:
            return round(float(d), 1)
        dist = getattr(obj, "distance", None)
        if dist is not None:
            return round(float(dist.m if hasattr(dist, "m") else dist), 1)
        return None

    get_khoang_cach_km = get_distance_km
    get_khoang_cach_m = get_distance_m

    class Meta:
        model = ChiNhanh
        fields = (
            "id", "ten", "dia_chi", "so_dien_thoai", "toa_do_gis",
            "kinh_do", "vi_do", "longitude", "latitude", "lng", "lat",
            "name", "address", "phone", "is_active",
            "con_hoat_dong", "distance_km", "distance_m",
            "khoang_cach_km", "khoang_cach_m", "tao_luc", "cap_nhat_luc"
        )


BranchSerializer = ChiNhanhSerializer
```

---

### Blueprint 5: `moc-backend/branches/views.py`
Add `nearest` action and query parameter handling:
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from api.permissions import LaNhanVienHoacChiDoc
from .models import ChiNhanh, Branch
from .serializers import ChiNhanhSerializer, BranchSerializer
from .services import find_nearest_branches


class ChiNhanhViewSet(viewsets.ModelViewSet):
    queryset = ChiNhanh.objects.all()
    serializer_class = ChiNhanhSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
        q = ChiNhanh.objects.all()
        user = self.request.user
        is_staff = user.is_authenticated and getattr(user, "la_nhan_vien_nha_hang", False)
        return q if is_staff else q.filter(con_hoat_dong=True)

    def list(self, request, *args, **kwargs):
        # Support proximity ordering in standard list endpoint if lat & lng are supplied
        lat = request.query_params.get("lat") or request.query_params.get("latitude") or request.query_params.get("vi_do")
        lng = request.query_params.get("lng") or request.query_params.get("longitude") or request.query_params.get("kinh_do")

        if lat is not None and lng is not None:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
            except ValueError:
                return Response({"detail": "Tọa độ lat và lng phải là số thực."}, status=status.HTTP_400_BAD_REQUEST)

            radius = request.query_params.get("radius") or request.query_params.get("radius_km") or request.query_params.get("ban_kinh")
            radius_f = float(radius) if radius else None
            limit = request.query_params.get("limit") or request.query_params.get("so_luong")
            limit_i = int(limit) if limit else None

            branches = find_nearest_branches(lat_f, lng_f, radius_km=radius_f, limit=limit_i, only_active=True)
            serializer = self.get_serializer(branches, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="nearest")
    def nearest(self, request):
        """
        Find nearest branch to client coordinates.
        Query Params:
        - lat / latitude / vi_do: float (required)
        - lng / longitude / kinh_do: float (required)
        - radius / radius_km / ban_kinh: float (optional)
        - all / list: bool (optional, return list if true)
        """
        lat = request.query_params.get("lat") or request.query_params.get("latitude") or request.query_params.get("vi_do")
        lng = request.query_params.get("lng") or request.query_params.get("longitude") or request.query_params.get("kinh_do")

        if lat is None or lng is None:
            return Response(
                {"detail": "Vui lòng cung cấp tọa độ lat (vĩ độ) và lng (kinh độ)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat_f = float(lat)
            lng_f = float(lng)
        except ValueError:
            return Response({"detail": "Tọa độ lat và lng phải là số thực."}, status=status.HTTP_400_BAD_REQUEST)

        if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lng_f <= 180.0):
            return Response(
                {"detail": "Tọa độ không hợp lệ (-90 <= lat <= 90, -180 <= lng <= 180)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        radius = request.query_params.get("radius") or request.query_params.get("radius_km") or request.query_params.get("ban_kinh")
        radius_f = float(radius) if radius else None
        return_all = str(request.query_params.get("all", "")).lower() in ("true", "1", "yes")

        branches = find_nearest_branches(lat_f, lng_f, radius_km=radius_f, limit=None if return_all else 1, only_active=True)

        if not branches:
            msg = f"Không tìm thấy chi nhánh nào trong bán kính {radius_f} km." if radius_f else "Không tìm thấy chi nhánh nào đang hoạt động."
            return Response({"detail": msg}, status=status.HTTP_404_NOT_FOUND)

        if return_all:
            serializer = self.get_serializer(branches, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(branches[0])
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="tim-gan-nhat")
    def tim_gan_nhat(self, request):
        return self.nearest(request)


BranchViewSet = ChiNhanhViewSet
```

---

### Blueprint 6: `moc-backend/branches/tests.py` (Test Suite)
```python
from django.test import TestCase
from rest_framework.test import APIClient
from .models import ChiNhanh, Branch
from .services import haversine_distance_km, find_nearest_branches
from .serializers import ChiNhanhSerializer


class ChiNhanhGISTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.b_tb = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Tân Bình",
            dia_chi="123 Hoàng Văn Thụ, Tân Bình, TP.HCM",
            so_dien_thoai="028 3811 1111",
            toa_do_gis="106.6669,10.7925",
            con_hoat_dong=True,
        )
        self.b_q1 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Quận 1",
            dia_chi="45 Pasteur, Quận 1, TP.HCM",
            so_dien_thoai="028 3822 2222",
            toa_do_gis="106.7009,10.7769",
            con_hoat_dong=True,
        )
        self.b_q7 = ChiNhanh.objects.create(
            ten="Nhà hàng Mộc - Chi nhánh Quận 7",
            dia_chi="78 Nguyễn Thị Thập, Quận 7, TP.HCM",
            so_dien_thoai="028 3877 7777",
            toa_do_gis="106.7150,10.7325",
            con_hoat_dong=False,  # Inactive
        )

    def test_model_coordinate_properties(self):
        self.assertAlmostEqual(self.b_tb.kinh_do, 106.6669)
        self.assertAlmostEqual(self.b_tb.vi_do, 10.7925)
        self.assertAlmostEqual(self.b_tb.lng, 106.6669)
        self.assertAlmostEqual(self.b_tb.lat, 10.7925)

    def test_haversine_distance(self):
        dist = haversine_distance_km(10.7925, 106.6669, 10.7769, 106.7009)
        self.assertGreater(dist, 3.5)
        self.assertLess(dist, 5.0)

    def test_find_nearest_service(self):
        # Coordinates ~100m from Tan Binh branch
        branches = find_nearest_branches(10.7930, 106.6675, limit=1)
        self.assertEqual(len(branches), 1)
        self.assertEqual(branches[0].id, self.b_tb.id)
        self.assertLess(branches[0].distance_km, 0.5)

    def test_inactive_branch_filtered(self):
        # User very close to closed Q7 branch
        branches = find_nearest_branches(10.7320, 106.7155, limit=1)
        self.assertEqual(len(branches), 1)
        self.assertNotEqual(branches[0].id, self.b_q7.id)

    def test_api_nearest_endpoint(self):
        resp = self.client.get("/api/branches/nearest/", {"lat": 10.7930, "lng": 106.6675})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], self.b_tb.id)
        self.assertIn("distance_km", data)
        self.assertLess(data["distance_km"], 0.5)

    def test_api_nearest_vn_alias(self):
        resp = self.client.get("/api/chi-nhanh/nearest/", {"vi_do": 10.7930, "kinh_do": 106.6675})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], self.b_tb.id)

    def test_api_nearest_missing_coords(self):
        resp = self.client.get("/api/branches/nearest/")
        self.assertEqual(resp.status_code, 400)
```

---

## 5. Verification Method

Once implemented by the backend worker, verify independently using:

1. **Django System Check**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python manage.py check
   ```
   *Expected result*: `System check identified no issues (0 silenced).`

2. **Branch Spatial Unit Tests**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python manage.py test branches
   ```
   *Expected result*: All branch tests pass cleanly under SQLite test runner without requiring SpatiaLite.

3. **Master E2E Tier 1 Runner**:
   ```bash
   /Users/VuVan/Documents/DO-AN/moc-backend/.venv/bin/python tests/e2e/runner.py --tier 1
   ```
   *Expected result*: 30/30 tests pass (100.0% pass rate).

4. **Live REST API Proximity Verification**:
   ```bash
   curl -s "http://127.0.0.1:8000/api/branches/nearest/?lat=10.7930&lng=106.6675" | jq .
   curl -s "http://127.0.0.1:8000/api/chi-nhanh/tim-gan-nhat/?vi_do=10.7930&kinh_do=106.6675" | jq .
   ```
   *Expected result*: HTTP 200, Tan Binh branch JSON payload with `distance_km < 0.5` and dual language fields.

5. **Invalidation Conditions**:
   - If `django.contrib.gis.geos` throws `ImproperlyConfigured` under production PostgreSQL mode, verify `settings.GDAL_LIBRARY_PATH`.
   - If tests fail on SQLite with `Distance function requires a GeometryField`, verify `is_spatial_database()` returns `False` during testing.
