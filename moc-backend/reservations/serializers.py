from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rest_framework import serializers
from api.mixins import DualPayloadMixin
from foods.models import MonAn
from foods.serializers import MonAnSerializer
from .models import BanAn, DatBan, MonAnTrongDatBan, ChinhSachDatCoc, QuyTacHuyDatCoc, PhongRieng, PhienPhucVu


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
    phien_phuc_vu_hien_tai = serializers.SerializerMethodField()

    def get_phien_phuc_vu_hien_tai(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not getattr(user, "la_nhan_vien_nha_hang", False):
            return None
        phien = PhienPhucVu.objects.filter(
            ban_an=obj,
            trang_thai__in=[PhienPhucVu.TrangThai.DANG_PHUC_VU, PhienPhucVu.TrangThai.CHO_DON],
        ).select_related("dat_ban").first()
        if not phien:
            return None
        try:
            don_hang = phien.don_hang
            don_hang_id = don_hang.id
            ma_don_hang = don_hang.ma_don_hang
            tong_tien = don_hang.tong_tien
        except Exception:
            don_hang_id = None
            ma_don_hang = ""
            tong_tien = 0
        return {
            "id": phien.id,
            "code": phien.ma_phien,
            "status": phien.trang_thai,
            "guest_count": phien.so_luong_khach,
            "customer_name": phien.ten_khach,
            "started_at": phien.bat_dau_luc,
            "reservation_id": phien.dat_ban_id,
            "order_id": don_hang_id,
            "order_code": ma_don_hang,
            "order_total": tong_tien,
        }

    class Meta:
        model = BanAn
        fields = "__all__"

    def validate_suc_chua(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Sức chứa bàn phải từ 1 đến 12 ghế.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        room = attrs.get("phong_rieng", getattr(self.instance, "phong_rieng", None))
        branch = attrs.get("chi_nhanh", getattr(self.instance, "chi_nhanh", None))
        if room and branch and room.chi_nhanh_id != branch.id:
            raise serializers.ValidationError({"phong_rieng": "Phòng riêng phải thuộc cùng chi nhánh với bàn."})
        if room and "phong_rieng" in attrs and not room.con_hoat_dong and room.pk != getattr(self.instance, "phong_rieng_id", None):
            raise serializers.ValidationError({"phong_rieng": "Phòng riêng đã ngừng sử dụng."})
        return attrs


class PhongRiengSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "name": "ten_phong",
        "floor": "tang",
        "capacity": "suc_chua",
        "active": "con_hoat_dong",
    }

    class Meta:
        model = PhongRieng
        fields = "__all__"

    def validate_suc_chua(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError("Sức chứa phòng phải từ 1 đến 12 ghế.")
        return value


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
    phien_phuc_vu_id = serializers.SerializerMethodField()
    don_hang_id = serializers.SerializerMethodField()
    ma_don_hang = serializers.SerializerMethodField()
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

    def get_phien_phuc_vu_id(self, obj):
        try:
            return obj.phien_phuc_vu.id
        except PhienPhucVu.DoesNotExist:
            return None

    def get_don_hang_id(self, obj):
        try:
            return obj.phien_phuc_vu.don_hang.id
        except (PhienPhucVu.DoesNotExist, AttributeError):
            return None

    def get_ma_don_hang(self, obj):
        try:
            return obj.phien_phuc_vu.don_hang.ma_don_hang
        except (PhienPhucVu.DoesNotExist, AttributeError):
            return ""

    def validate(self, attrs):
        ban = attrs.get("ban_an")
        if ban and self.instance is None:
            raise serializers.ValidationError({"ban_an": "Khách đặt chỗ theo chi nhánh; nhân viên sẽ xếp bàn khi khách đến."})
        chi_nhanh = attrs.get("chi_nhanh", getattr(self.instance, "chi_nhanh", None))
        ngay_dat = attrs.get("ngay_dat", getattr(self.instance, "ngay_dat", None))
        gio_bat_dau = attrs.get("gio_bat_dau", getattr(self.instance, "gio_bat_dau", None))
        so_khach = attrs.get("so_luong_khach", getattr(self.instance, "so_luong_khach", 0))
        if so_khach < 1 or so_khach > 12:
            raise serializers.ValidationError({"so_luong_khach": "Mỗi lượt đặt bàn tối đa 12 khách."})
        if ngay_dat and gio_bat_dau and self.instance is None:
            now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
            if ngay_dat < now_vn.date() or (
                ngay_dat == now_vn.date() and gio_bat_dau <= now_vn.time().replace(tzinfo=None)
            ):
                raise serializers.ValidationError({"gio_bat_dau": "Khung giờ này đã qua. Vui lòng chọn giờ khác."})
        if ban and not chi_nhanh:
            attrs["chi_nhanh"] = ban.chi_nhanh
        elif ban and chi_nhanh and ban.chi_nhanh_id != chi_nhanh.id:
            raise serializers.ValidationError({"ban_an": "Bàn không thuộc chi nhánh đã chọn."})
        if ban and self.instance and ban.chi_nhanh_id != self.instance.chi_nhanh_id:
            raise serializers.ValidationError({"ban_an": "Bàn phải thuộc chi nhánh của đặt chỗ."})
        if ban and ban.suc_chua < so_khach:
            raise serializers.ValidationError({"ban_an": "Bàn không đủ chỗ cho số khách này."})
        if ban and ban.trang_thai == BanAn.TrangThai.BAO_TRI:
            raise serializers.ValidationError({"ban_an": "Bàn đang được bảo trì."})
        if ban and ngay_dat and gio_bat_dau:
            conflicts = DatBan.objects.filter(
                ban_an=ban,
                ngay_dat=ngay_dat,
                trang_thai__in=[
                    DatBan.TrangThai.CHO_XAC_NHAN,
                    DatBan.TrangThai.CHO_THANH_TOAN,
                    DatBan.TrangThai.DA_XAC_NHAN,
                    DatBan.TrangThai.KHACH_DA_DEN,
                ],
            )
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            start = datetime.combine(ngay_dat, gio_bat_dau)
            end = start + timedelta(hours=2)
            for reservation in conflicts:
                other_start = datetime.combine(reservation.ngay_dat, reservation.gio_bat_dau)
                other_end = datetime.combine(reservation.ngay_dat, reservation.gio_ket_thuc) if reservation.gio_ket_thuc else other_start + timedelta(hours=2)
                if start < other_end and end > other_start:
                    raise serializers.ValidationError({"ban_an": "Bàn đã có đặt chỗ trong khoảng thời gian này."})
        if not ban and not chi_nhanh:
            raise serializers.ValidationError({"chi_nhanh": "Cần cung cấp chi_nhanh hoặc ban_an."})
        return attrs


class PhienPhucVuSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh",
        "table": "ban_an",
        "table_id": "ban_an",
        "reservation": "dat_ban",
        "reservation_id": "dat_ban",
        "guest_count": "so_luong_khach",
        "customer_name": "ten_khach",
        "customer_phone": "sdt_khach",
        "note": "ghi_chu",
        "status": "trang_thai",
    }
    so_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    ten_ban = serializers.CharField(source="ban_an.so_ban", read_only=True)
    don_hang_id = serializers.SerializerMethodField()
    ma_don_hang = serializers.SerializerMethodField()
    tien_coc_da_tra = serializers.SerializerMethodField()

    class Meta:
        model = PhienPhucVu
        fields = "__all__"
        read_only_fields = (
            "ma_phien", "chi_nhanh", "ban_an", "dat_ban", "trang_thai", "bat_dau_luc",
            "check_out_luc", "da_don_luc", "nguoi_bat_dau", "nguoi_check_out", "nguoi_xac_nhan_don",
        )

    def get_don_hang_id(self, obj):
        try:
            return obj.don_hang.id
        except AttributeError:
            return None

    def get_ma_don_hang(self, obj):
        try:
            return obj.don_hang.ma_don_hang
        except AttributeError:
            return ""

    def get_tien_coc_da_tra(self, obj):
        from .services import DichVuPhienPhucVu
        return DichVuPhienPhucVu.tien_coc_da_tra(obj)


class WalkInSerializer(DualPayloadMixin, serializers.Serializer):
    FIELD_ALIASES = {
        "table": "ban_an",
        "table_id": "ban_an",
        "guest_count": "so_luong_khach",
        "customer_name": "ten_khach",
        "customer_phone": "sdt_khach",
        "note": "ghi_chu",
    }
    ban_an = serializers.PrimaryKeyRelatedField(queryset=BanAn.objects.all())
    so_luong_khach = serializers.IntegerField(min_value=1, max_value=12)
    ten_khach = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    sdt_khach = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    ghi_chu = serializers.CharField(required=False, allow_blank=True, default="")


class XepBanSerializer(DualPayloadMixin, serializers.Serializer):
    FIELD_ALIASES = {"table": "ban_an", "table_id": "ban_an"}
    ban_an = serializers.PrimaryKeyRelatedField(queryset=BanAn.objects.all())


class ThemMonPhienSerializer(DualPayloadMixin, serializers.Serializer):
    FIELD_ALIASES = {"food_id": "mon_an_id", "quantity": "so_luong", "note": "ghi_chu"}
    mon_an_id = serializers.PrimaryKeyRelatedField(queryset=MonAn.objects.filter(con_hang=True), source="mon_an")
    so_luong = serializers.IntegerField(min_value=1)
    ghi_chu = serializers.CharField(required=False, allow_blank=True, default="")


class DanhSachMonPhienSerializer(DualPayloadMixin, serializers.Serializer):
    FIELD_ALIASES = {"items": "danh_sach_mon"}
    danh_sach_mon = ThemMonPhienSerializer(many=True)


class CheckOutPhienSerializer(DualPayloadMixin, serializers.Serializer):
    FIELD_ALIASES = {"payment_method": "phuong_thuc", "reference": "ma_tham_chieu"}
    phuong_thuc = serializers.ChoiceField(
        choices=["tien_mat", "chuyen_khoan", "vnpay"], required=False, default="tien_mat"
    )
    ma_tham_chieu = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")



# Backward-compatible serializer aliases
TableSerializer = BanAnSerializer
ReservationSerializer = DatBanSerializer
ReservationItemSerializer = MonAnDatBanSerializer
DepositPolicySerializer = ChinhSachCocSerializer
DepositRefundRuleSerializer = QuyTacHuyCocSerializer
DiningSessionSerializer = PhienPhucVuSerializer
