from rest_framework import serializers
from api.mixins import DualPayloadMixin
from foods.models import MonAn
from foods.serializers import MonAnSerializer
from .models import BanAn, DatBan, MonAnTrongDatBan, ChinhSachDatCoc, QuyTacHuyDatCoc


class BanAnSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "table_number": "so_ban",
        "number": "so_ban",
        "capacity": "suc_chua",
        "area": "khu_vuc",
        "status": "trang_thai",
    }

    class Meta:
        model = BanAn
        fields = "__all__"


class QuyTacHuyCocSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "policy": "chinh_sach",
        "policy_id": "chinh_sach",
        "time_milestone": "moc_thoi_gian",
        "refund_percentage": "phan_tram_hoan_tien",
    }

    class Meta:
        model = QuyTacHuyDatCoc
        fields = "__all__"


class ChinhSachCocSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "deposit_percentage": "phan_tram_coc",
        "hold_time_minutes": "thoi_gian_giu_cho_phut",
        "payment_limit_minutes": "han_thanh_toan_phut",
        "hotline": "so_dien_thoai_lien_he",
        "guide_text": "noi_dung_huong_dan",
        "guideText": "noi_dung_huong_dan",
        "is_active": "con_ap_dung",
    }
    quy_tac_huy = QuyTacHuyCocSerializer(many=True, read_only=True)

    class Meta:
        model = ChinhSachDatCoc
        fields = "__all__"


class MonAnDatBanSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "food_id": "mon_an_id",
        "quantity": "so_luong",
    }
    mon_an_id = serializers.PrimaryKeyRelatedField(
        queryset=MonAn.objects.filter(con_hang=True), source="mon_an", write_only=True
    )
    mon_an = MonAnSerializer(read_only=True)

    class Meta:
        model = MonAnTrongDatBan
        fields = ("id", "mon_an_id", "mon_an", "so_luong", "don_gia_luc_dat")
        read_only_fields = ("id", "mon_an", "don_gia_luc_dat")


class DatBanSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "chi_nhanh_id": "chi_nhanh",
        "table": "ban_an",
        "table_id": "ban_an",
        "ban_an_id": "ban_an",
        "idBan": "ban_an",
        "customer_name": "ten_khach",
        "name": "ten_khach",
        "customer_phone": "sdt_khach",
        "phone": "sdt_khach",
        "customer_email": "email_khach",
        "email": "email_khach",
        "guest_count": "so_luong_khach",
        "number_of_guests": "so_luong_khach",
        "party_size": "so_luong_khach",
        "date": "ngay_dat",
        "reservation_date": "ngay_dat",
        "start_time": "gio_bat_dau",
        "time": "gio_bat_dau",
        "end_time": "gio_ket_thuc",
        "note": "ghi_chu",
        "notes": "ghi_chu",
        "hold_token": "id_giu_ban",
        "items": "danh_sach_mon",
        "food_items": "danh_sach_mon",
        "type": "hinh_thuc",
        "reservation_type": "hinh_thuc",
    }
    danh_sach_mon = MonAnDatBanSerializer(many=True, required=False)
    food_items = MonAnDatBanSerializer(many=True, source="danh_sach_mon", read_only=True)
    so_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    ten_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    ban_an_id = serializers.IntegerField(source="ban_an.id", read_only=True)
    refund_record = serializers.SerializerMethodField()
    id_giu_ban = serializers.CharField(write_only=True, required=False)
    ban_an = serializers.PrimaryKeyRelatedField(
        queryset=BanAn.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = DatBan
        fields = "__all__"
        read_only_fields = (
            "nguoi_dung", "ma_dat_ban", "trang_thai",
            "yeu_cau_dat_coc", "so_tien_coc", "trang_thai_coc",
            "thanh_toan_coc_luc", "huy_luc", "phien_ban"
        )

    def get_refund_record(self, obj):
        refund = obj.phieu_hoan_tien.order_by("-tao_luc").first()
        if not refund:
            return None
        detail = refund.du_lieu_chi_tiet or {}
        return {
            "percent": float(refund.phan_tram_hoan), "amount": float(refund.so_tien_hoan),
            "reference": detail.get("reference", ""), "note": detail.get("note", ""),
            "at": refund.tao_luc, "by": detail.get("verified_by", "Nhân viên"),
        }

    def validate(self, attrs):
        ban = attrs.get("ban_an")
        chi_nhanh = attrs.get("chi_nhanh")
        if ban and not chi_nhanh:
            attrs["chi_nhanh"] = ban.chi_nhanh
        elif ban and chi_nhanh and ban.chi_nhanh_id != chi_nhanh.id:
            raise serializers.ValidationError({"ban_an": "Bàn không thuộc chi nhánh đã chọn."})
        if not ban and not chi_nhanh:
            raise serializers.ValidationError({"chi_nhanh": "Cần cung cấp chi_nhanh hoặc ban_an."})
        return attrs



# Backward-compatible serializer aliases
TableSerializer = BanAnSerializer
ReservationSerializer = DatBanSerializer
ReservationItemSerializer = MonAnDatBanSerializer
DepositPolicySerializer = ChinhSachCocSerializer
DepositRefundRuleSerializer = QuyTacHuyCocSerializer
