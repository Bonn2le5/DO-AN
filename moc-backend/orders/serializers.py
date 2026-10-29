from rest_framework import serializers
from api.mixins import DualPayloadMixin
from foods.models import MonAn
from foods.serializers import MonAnSerializer
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon


class ChiTietDonHangSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "food_id": "mon_an_id",
        "dish_id": "mon_an_id",
        "quantity": "so_luong",
        "note": "ghi_chu",
        "notes": "ghi_chu",
    }
    mon_an_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True), source="mon_an", write_only=True
    )
    mon_an = MonAnSerializer(read_only=True)

    class Meta:
        model = ChiTietDonHang
        fields = ("id", "mon_an_id", "mon_an", "don_gia_luc_dat", "so_luong", "thanh_tien")
        read_only_fields = ("id", "mon_an", "don_gia_luc_dat", "thanh_tien")


class LichSuTrangThaiDonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LichSuTrangThaiDon
        fields = ("tu_trang_thai", "sang_trang_thai", "ghi_chu", "tao_luc")


class DonHangSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "order_type": "hinh_thuc",
        "type": "hinh_thuc",
        "customer_name": "ten_khach",
        "name": "ten_khach",
        "customer_phone": "sdt_khach",
        "phone": "sdt_khach",
        "delivery_address": "dia_chi_giao",
        "address": "dia_chi_giao",
        "note": "ghi_chu",
        "notes": "ghi_chu",
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "table": "dat_ban",
        "table_id": "dat_ban",
        "coupon_code": "ma_khuyen_mai",
        "promotion_code": "ma_khuyen_mai",
        "items": "danh_sach_mon",
        "order_items": "danh_sach_mon",
    }
    danh_sach_mon = ChiTietDonHangSerializer(many=True, required=False)
    items = ChiTietDonHangSerializer(source="danh_sach_mon", many=True, read_only=True)
    lich_su_trang_thai = LichSuTrangThaiDonSerializer(many=True, read_only=True)
    ma_khuyen_mai = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = DonHang
        fields = "__all__"
        read_only_fields = (
            "khach_hang", "ma_don_hang", "trang_thai",
            "tien_hang", "tien_giam", "tong_tien", "khuyen_mai"
        )


# Backward-compatible serializer aliases
OrderSerializer = DonHangSerializer
OrderItemSerializer = ChiTietDonHangSerializer
OrderStatusHistorySerializer = LichSuTrangThaiDonSerializer
