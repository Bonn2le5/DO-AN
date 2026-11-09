from rest_framework import serializers
from orders.models import DonHang, ChiTietDonHang, Order, OrderItem
from .models import DanhGia, Review


class DanhGiaSerializer(serializers.ModelSerializer):
    ten_nguoi_dung = serializers.SerializerMethodField()
    food_name = serializers.CharField(source="mon_an.ten", read_only=True)

    class Meta:
        model = DanhGia
        fields = "__all__"
        read_only_fields = ("nguoi_dung",)
        # Bỏ trống thì validate() tự tìm món khách đã dùng trong đơn hoàn tất.
        extra_kwargs = {"don_hang": {"required": False}, "chi_tiet_don_hang": {"required": False}}

    def get_ten_nguoi_dung(self, obj):
        return obj.nguoi_dung.get_full_name() or obj.nguoi_dung.username

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
        don_hang = attrs.get("don_hang")
        item = attrs.get("chi_tiet_don_hang")
        mon_an = attrs.get("mon_an")

        if don_hang and don_hang.khach_hang_id != request.user.id:
            raise serializers.ValidationError({"don_hang": "Chỉ được đánh giá đơn hàng của bạn."})
        if don_hang and don_hang.trang_thai != DonHang.TrangThai.HOAN_TAT:
            raise serializers.ValidationError({"don_hang": "Chỉ được đánh giá đơn hàng đã hoàn tất."})
        if item and don_hang and item.don_hang_id != don_hang.id:
            raise serializers.ValidationError({"chi_tiet_don_hang": "Món ăn không thuộc đơn hàng đã chọn."})
        if item and mon_an and item.mon_an_id != mon_an.id:
            raise serializers.ValidationError({"chi_tiet_don_hang": "Chi tiết đơn không khớp với món ăn."})
        if not item:
            if not mon_an:
                raise serializers.ValidationError({"mon_an": "Cần chọn món để đánh giá."})
            item = (
                ChiTietDonHang.objects.filter(
                    don_hang__khach_hang=request.user,
                    don_hang__trang_thai=DonHang.TrangThai.HOAN_TAT,
                    mon_an=mon_an,
                    danh_gia__isnull=True,
                    **({"don_hang": don_hang} if don_hang else {}),
                ).select_related("don_hang").order_by("-don_hang__tao_luc").first()
            )
            if not item:
                raise serializers.ValidationError(
                    {"mon_an": "Bạn chỉ đánh giá được món đã dùng tại nhà hàng (đơn đã hoàn tất) và chưa đánh giá."}
                )
            attrs["chi_tiet_don_hang"] = item
            attrs["don_hang"] = item.don_hang
        return attrs


ReviewSerializer = DanhGiaSerializer
