from rest_framework import serializers
from api.mixins import DualPayloadMixin
from foods.models import MonAn, Food
from foods.serializers import MonAnSerializer, FoodSerializer
from .models import GioHang, ChiTietGioHang, Cart, CartItem


class ChiTietGioHangSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "food_id": "mon_an_id",
        "food": "mon_an_id",
        "quantity": "so_luong",
        "note": "ghi_chu",
        "notes": "ghi_chu",
    }
    mon_an_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True, hien_thi=True),
        source="mon_an", write_only=True, required=False
    )
    food_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True, hien_thi=True),
        source="mon_an", write_only=True, required=False
    )
    mon_an = MonAnSerializer(read_only=True)
    food = MonAnSerializer(source="mon_an", read_only=True)
    quantity = serializers.IntegerField(source="so_luong", required=False)
    unit_price = serializers.DecimalField(source="don_gia_luc_dat", max_digits=12, decimal_places=2, read_only=True)
    note = serializers.CharField(source="ghi_chu", required=False, allow_blank=True)

    class Meta:
        model = ChiTietGioHang
        fields = (
            "id", "gio_hang", "mon_an", "mon_an_id", "food_id", "food",
            "so_luong", "quantity", "don_gia_luc_dat", "unit_price",
            "ghi_chu", "note", "tao_luc", "cap_nhat_luc"
        )
        read_only_fields = ("gio_hang", "don_gia_luc_dat", "unit_price")


class GioHangSerializer(serializers.ModelSerializer):
    danh_sach_mon = ChiTietGioHangSerializer(many=True, read_only=True)
    items = ChiTietGioHangSerializer(source="danh_sach_mon", many=True, read_only=True)

    class Meta:
        model = GioHang
        fields = "__all__"
        read_only_fields = ("nguoi_dung",)


CartItemSerializer = ChiTietGioHangSerializer
CartSerializer = GioHangSerializer
