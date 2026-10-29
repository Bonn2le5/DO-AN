from rest_framework import serializers
from api.mixins import DualPayloadMixin
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai, Promotion, PromotionCode, PromotionUsage


class MaKhuyenMaiSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "code": "ma",
        "promotion": "khuyen_mai",
        "promotion_id": "khuyen_mai",
        "limit": "gioi_han",
        "is_active": "con_hoat_dong",
    }

    class Meta:
        model = MaKhuyenMai
        fields = "__all__"
        read_only_fields = ("da_dung",)


class KhuyenMaiSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "title": "ten",
        "name": "ten",
        "description": "mo_ta",
        "discount_type": "kieu_giam",
        "discount_value": "gia_tri_giam",
        "min_order_value": "don_hang_toi_thieu",
        "max_discount": "giam_toi_da",
        "start_date": "bat_dau_luc",
        "start_at": "bat_dau_luc",
        "end_date": "ket_thuc_luc",
        "end_at": "ket_thuc_luc",
        "is_active": "con_hoat_dong",
        "usage_limit": "gioi_han_su_dung",
    }
    danh_sach_ma = MaKhuyenMaiSerializer(many=True, read_only=True)
    codes = MaKhuyenMaiSerializer(source="danh_sach_ma", many=True, read_only=True)

    class Meta:
        model = KhuyenMai
        fields = "__all__"
        read_only_fields = ("so_lan_da_dung",)


class LichSuDungKhuyenMaiSerializer(serializers.ModelSerializer):
    class Meta:
        model = LichSuDungKhuyenMai
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "don_hang", "so_tien_giam")


PromotionSerializer = KhuyenMaiSerializer
PromotionCodeSerializer = MaKhuyenMaiSerializer
PromotionUsageSerializer = LichSuDungKhuyenMaiSerializer
