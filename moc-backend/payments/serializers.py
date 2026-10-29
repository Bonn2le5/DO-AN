from rest_framework import serializers
from api.mixins import DualPayloadMixin
from .models import ThanhToan, Payment, PhieuHoanTien, RefundReceipt


class ThanhToanSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "payment_type": "loai_thanh_toan",
        "type": "loai_thanh_toan",
        "payment_method": "phuong_thuc",
        "method": "phuong_thuc",
        "amount": "so_tien",
        "order": "don_hang",
        "order_id": "don_hang",
        "reservation": "dat_ban",
        "reservation_id": "dat_ban",
        "transaction_id": "ma_giao_dich",
    }

    class Meta:
        model = ThanhToan
        fields = "__all__"
        read_only_fields = ("nguoi_dung", "trang_thai", "thanh_toan_luc", "hoan_tien_luc")

    def validate(self, attrs):
        loai = attrs.get("loai_thanh_toan") or attrs.get("payment_type")
        don_hang = attrs.get("don_hang") or attrs.get("order")
        dat_ban = attrs.get("dat_ban") or attrs.get("reservation")

        if loai == ThanhToan.LoaiThanhToan.DON_HANG and (not don_hang or dat_ban):
            raise serializers.ValidationError("Thanh toán đơn hàng chỉ được gắn với đơn hàng.")
        if loai == ThanhToan.LoaiThanhToan.TIEN_COC and (not dat_ban or don_hang):
            raise serializers.ValidationError("Đặt cọc chỉ được gắn với đặt bàn.")
        return attrs


PaymentSerializer = ThanhToanSerializer


class PhieuHoanTienSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "refund_code": "ma_phieu_hoan",
        "code": "ma_phieu_hoan",
        "reservation": "dat_ban",
        "reservation_id": "dat_ban",
        "payment": "thanh_toan",
        "payment_id": "thanh_toan",
        "original_deposit": "so_tien_coc_goc",
        "original_amount": "so_tien_coc_goc",
        "refund_percentage": "phan_tram_hoan",
        "refund_percent": "phan_tram_hoan",
        "refund_amount": "so_tien_hoan",
        "penalty_amount": "so_tien_phat",
        "time_milestone": "moc_thoi_gian",
        "milestone": "moc_thoi_gian",
        "hours_before_booking": "so_gio_truoc_gio_hen",
        "cancel_reason": "ly_do_huy",
        "reason": "ly_do_huy",
        "status": "trang_thai",
        "refund_method": "phuong_thuc_hoan",
        "method": "phuong_thuc_hoan",
    }

    class Meta:
        model = PhieuHoanTien
        fields = "__all__"
        read_only_fields = ("ma_phieu_hoan", "tao_luc", "cap_nhat_luc")


RefundReceiptSerializer = PhieuHoanTienSerializer


class VNPayCreatePaymentSerializer(serializers.Serializer):
    loai_thanh_toan = serializers.ChoiceField(
        choices=[("tien_coc", "Tiền cọc"), ("don_hang", "Đơn hàng")],
        default="tien_coc",
        required=False
    )
    payment_type = serializers.CharField(required=False, write_only=True)
    dat_ban_id = serializers.IntegerField(required=False, allow_null=True)
    reservation_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    don_hang_id = serializers.IntegerField(required=False, allow_null=True)
    order_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    ma_tham_chieu_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    so_tien = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, write_only=True)
    order_info = serializers.CharField(max_length=255, required=False, default="", allow_blank=True)
    ip_addr = serializers.CharField(max_length=50, required=False, default="")

    def validate(self, attrs):
        loai = attrs.get("payment_type") or attrs.get("loai_thanh_toan") or "tien_coc"
        attrs["loai_thanh_toan"] = loai

        dat_ban_id = attrs.get("dat_ban_id") or attrs.get("reservation_id")
        don_hang_id = attrs.get("don_hang_id") or attrs.get("order_id")
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

        so_tien = attrs.get("amount") or attrs.get("so_tien")
        if so_tien:
            attrs["so_tien"] = so_tien

        return attrs

