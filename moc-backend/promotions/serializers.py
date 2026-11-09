from rest_framework import serializers
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai, Promotion, PromotionCode, PromotionUsage


class MaKhuyenMaiSerializer(serializers.ModelSerializer):

    class Meta:
        model = MaKhuyenMai
        fields = "__all__"
        read_only_fields = ("da_dung",)


class KhuyenMaiSerializer(serializers.ModelSerializer):
    danh_sach_ma = MaKhuyenMaiSerializer(many=True, read_only=True)

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
