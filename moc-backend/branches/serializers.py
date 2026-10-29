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
    kinh_do = serializers.FloatField(read_only=True)
    vi_do = serializers.FloatField(read_only=True)
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

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        lat = data.get("lat", data.get("latitude", data.get("vi_do")))
        lng = data.get("lng", data.get("longitude", data.get("kinh_do")))
        if lat is not None and lng is not None:
            data["toa_do_gis"] = {"type": "Point", "coordinates": [float(lng), float(lat)]}
        return super().to_internal_value(data)

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
