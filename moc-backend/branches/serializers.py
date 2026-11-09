from rest_framework import serializers
from .models import ChiNhanh, Branch


class ChiNhanhSerializer(serializers.ModelSerializer):
    kinh_do = serializers.FloatField(read_only=True)
    vi_do = serializers.FloatField(read_only=True)
    khoang_cach_km = serializers.SerializerMethodField()
    khoang_cach_m = serializers.SerializerMethodField()

    def get_khoang_cach_km(self, obj):
        d = getattr(obj, "distance_km", None)
        if d is not None:
            return round(float(d), 2)
        dist = getattr(obj, "distance", None)
        if dist is not None:
            return round(float(dist.km if hasattr(dist, "km") else dist / 1000.0), 2)
        return None

    def get_khoang_cach_m(self, obj):
        d = getattr(obj, "distance_m", None)
        if d is not None:
            return round(float(d), 1)
        dist = getattr(obj, "distance", None)
        if dist is not None:
            return round(float(dist.m if hasattr(dist, "m") else dist), 1)
        return None

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        lat = data.get("vi_do")
        lng = data.get("kinh_do")
        if lat is not None and lng is not None:
            # WKT dùng được cho cả PointField (Postgres) lẫn CharField dự phòng (SQLite khi test).
            data["toa_do_gis"] = f"SRID=4326;POINT({float(lng)} {float(lat)})"
        return super().to_internal_value(data)

    class Meta:
        model = ChiNhanh
        fields = (
            "id", "ten", "dia_chi", "so_dien_thoai", "toa_do_gis",
            "kinh_do", "vi_do", "con_hoat_dong",
            "khoang_cach_km", "khoang_cach_m", "tao_luc", "cap_nhat_luc"
        )


BranchSerializer = ChiNhanhSerializer
