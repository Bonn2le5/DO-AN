from rest_framework import serializers
from api.mixins import DualPayloadMixin
from orders.models import DonHang, ChiTietDonHang, Order, OrderItem
from .models import DanhGia, Review


class DanhGiaSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "order": "don_hang",
        "order_id": "don_hang",
        "order_item": "chi_tiet_don_hang",
        "order_item_id": "chi_tiet_don_hang",
        "food": "mon_an",
        "food_id": "mon_an",
        "rating": "diem_danh_gia",
        "score": "diem_danh_gia",
        "comment": "nhan_xet",
        "review": "nhan_xet",
        "visible": "hien_thi",
        "is_visible": "hien_thi",
    }
    ten_nguoi_dung = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    food_name = serializers.CharField(source="mon_an.ten", read_only=True)
    rating = serializers.IntegerField(source="diem_danh_gia", required=False)
    comment = serializers.CharField(source="nhan_xet", required=False, allow_blank=True)

    class Meta:
        model = DanhGia
        fields = "__all__"
        read_only_fields = ("nguoi_dung",)

    def get_ten_nguoi_dung(self, obj):
        return obj.nguoi_dung.get_full_name() or obj.nguoi_dung.username

    get_user_name = get_ten_nguoi_dung

    def validate_diem_danh_gia(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Điểm đánh giá phải từ 1 đến 5.")
        return value

    def validate(self, attrs):
        if self.instance:
            return attrs
        request = self.context.get("request")
        if not request:
            return attrs
        don_hang = attrs.get("don_hang") or attrs.get("order")
        item = attrs.get("chi_tiet_don_hang") or attrs.get("order_item")
        mon_an = attrs.get("mon_an") or attrs.get("food")

        if don_hang and don_hang.khach_hang_id != request.user.id:
            raise serializers.ValidationError({"don_hang": "Chỉ được đánh giá đơn hàng của bạn."})
        if don_hang and don_hang.trang_thai != DonHang.TrangThai.HOAN_TAT:
            raise serializers.ValidationError({"don_hang": "Chỉ được đánh giá đơn hàng đã hoàn tất."})
        if item and don_hang and item.don_hang_id != don_hang.id:
            raise serializers.ValidationError({"chi_tiet_don_hang": "Món ăn không thuộc đơn hàng đã chọn."})
        if item and mon_an and item.mon_an_id != mon_an.id:
            raise serializers.ValidationError({"chi_tiet_don_hang": "Chi tiết đơn không khớp với món ăn."})
        return attrs


ReviewSerializer = DanhGiaSerializer
