import re
from django.conf import settings
from django.db import models
try:
    from django.contrib.postgres.indexes import GistIndex
except ImportError:
    GistIndex = None
from foods.models import MoHinhThoiGian

try:
    if getattr(settings, "TESTING", False) or getattr(settings, "USE_SQLITE", False):
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
        indexes = (
            [GistIndex(fields=["toa_do_gis"], name="idx_chi_nhanh_toa_do")]
            if GistIndex and not getattr(settings, "TESTING", False) and not getattr(settings, "USE_SQLITE", False)
            else []
        )

    def __str__(self):
        return self.ten

    def _parse_coords(self):
        pt = self.toa_do_gis
        if pt is None:
            return None, None
        if hasattr(pt, "x") and hasattr(pt, "y"):
            return float(pt.x), float(pt.y)
        if isinstance(pt, (list, tuple)) and len(pt) >= 2:
            c1, c2 = float(pt[0]), float(pt[1])
            if c1 < 30.0 and c2 > 90.0:
                return c2, c1
            return c1, c2
        if isinstance(pt, str):
            m = re.search(r"POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)", pt, re.I)
            if m:
                c1, c2 = float(m.group(1)), float(m.group(2))
                if c1 < 30.0 and c2 > 90.0:
                    return c2, c1
                return c1, c2
            parts = pt.split(",")
            if len(parts) >= 2:
                try:
                    c1, c2 = float(parts[0].strip()), float(parts[1].strip())
                    if c1 < 30.0 and c2 > 90.0:
                        return c2, c1
                    return c1, c2
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


# Backward-compatible model aliases
Branch = ChiNhanh
