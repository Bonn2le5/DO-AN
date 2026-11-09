from rest_framework import serializers
from foods.models import MonAn
from foods.serializers import MonAnSerializer
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon


class ChiTietDonHangSerializer(serializers.ModelSerializer):
    mon_an_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True), source="mon_an", write_only=True
    )
    mon_an = MonAnSerializer(read_only=True)

    class Meta:
        model = ChiTietDonHang
        fields = ("id", "mon_an_id", "mon_an", "don_gia_luc_dat", "so_luong", "thanh_tien", "ghi_chu")
        read_only_fields = ("id", "mon_an", "don_gia_luc_dat", "thanh_tien")


class LichSuTrangThaiDonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LichSuTrangThaiDon
        fields = ("tu_trang_thai", "sang_trang_thai", "ghi_chu", "tao_luc")


class DonHangSerializer(serializers.ModelSerializer):
    danh_sach_mon = ChiTietDonHangSerializer(many=True, required=False)
    lich_su_trang_thai = LichSuTrangThaiDonSerializer(many=True, read_only=True)
    ma_khuyen_mai = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = DonHang
        fields = "__all__"
        read_only_fields = (
            "khach_hang", "ma_don_hang", "trang_thai", "phien_phuc_vu",
            "tien_hang", "tien_giam", "tong_tien", "khuyen_mai"
        )


# Backward-compatible serializer aliases
OrderSerializer = DonHangSerializer
OrderItemSerializer = ChiTietDonHangSerializer
OrderStatusHistorySerializer = LichSuTrangThaiDonSerializer
