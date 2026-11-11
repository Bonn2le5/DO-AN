from rest_framework import serializers
from .models import ThanhToan, PhieuHoanTien


class ThanhToanSerializer(serializers.ModelSerializer):

    class Meta:
        model = ThanhToan
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "trang_thai", "thanh_toan_luc", "hoan_tien_luc")

    def validate(self, attrs):
        loai = attrs.get("loai_thanh_toan")
        don_hang = attrs.get("don_hang")
        dat_ban = attrs.get("dat_ban")

        if loai == ThanhToan.LoaiThanhToan.DON_HANG and (not don_hang or dat_ban):
            raise serializers.ValidationError("Thanh toán đơn hàng chỉ được gắn với đơn hàng.")
        if loai == ThanhToan.LoaiThanhToan.TIEN_COC and (not dat_ban or don_hang):
            raise serializers.ValidationError("Đặt cọc chỉ được gắn với đặt bàn.")
        return attrs


class PhieuHoanTienSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhieuHoanTien
        fields = "__all__"
        read_only_fields = ("ma_phieu_hoan", "tao_luc", "cap_nhat_luc")


class TaoPhienThanhToanSerializer(serializers.Serializer):
    loai_thanh_toan = serializers.ChoiceField(
        choices=[("tien_coc", "Tiền cọc"), ("don_hang", "Đơn hàng")],
        default="tien_coc",
        required=False
    )
    dat_ban_id = serializers.IntegerField(required=False, allow_null=True)
    don_hang_id = serializers.IntegerField(required=False, allow_null=True)
    ma_tham_chieu_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    so_tien = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)

    def validate(self, attrs):
        loai = attrs.get("loai_thanh_toan") or "tien_coc"
        attrs["loai_thanh_toan"] = loai

        dat_ban_id = attrs.get("dat_ban_id")
        don_hang_id = attrs.get("don_hang_id")
        ma_ref = attrs.get("ma_tham_chieu_id")

        if loai == "tien_coc":
            target_id = dat_ban_id or ma_ref
            if not target_id:
                raise serializers.ValidationError({"dat_ban_id": "Cần cung cấp dat_ban_id cho thanh toán tiền cọc."})
            attrs["dat_ban_id"] = target_id
        elif loai == "don_hang":
            target_id = don_hang_id or ma_ref
            if not target_id:
                raise serializers.ValidationError({"don_hang_id": "Cần cung cấp don_hang_id cho thanh toán đơn hàng."})
            attrs["don_hang_id"] = target_id

        return attrs
