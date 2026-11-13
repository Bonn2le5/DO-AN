import base64
import binascii
import re
from django.core.files.base import ContentFile
from rest_framework import serializers
from decimal import Decimal
from .models import DanhMuc, NguyenLieu, MonAn, HinhAnhMonAn, TheMonAn, LichSuXuatNhapKho, DinhMucNguyenLieu, TonKhoChiNhanh


class DanhMucSerializer(serializers.ModelSerializer):

    class Meta:
        model = DanhMuc
        fields = "__all__"


class TheMonAnSerializer(serializers.ModelSerializer):

    class Meta:
        model = TheMonAn
        fields = "__all__"


class TonKhoChiNhanhSerializer(serializers.ModelSerializer):
    ten_chi_nhanh = serializers.CharField(source="chi_nhanh.ten", read_only=True)
    ten_nguyen_lieu = serializers.CharField(source="nguyen_lieu.ten", read_only=True)
    don_vi = serializers.CharField(source="nguyen_lieu.don_vi", read_only=True)
    sap_het = serializers.BooleanField(read_only=True)

    class Meta:
        model = TonKhoChiNhanh
        fields = (
            "id", "nguyen_lieu", "chi_nhanh", "ten_chi_nhanh", "ten_nguyen_lieu", "don_vi",
            "ton_kho_hien_tai", "ton_kho_toi_thieu", "sap_het", "cap_nhat_luc",
        )
        # Tồn hiện tại chỉ đổi qua phiếu kho; ở đây chỉ sửa được mức tối thiểu.
        read_only_fields = ("nguyen_lieu", "chi_nhanh", "ton_kho_hien_tai")

    def validate_ton_kho_toi_thieu(self, value):
        if value < 0:
            raise serializers.ValidationError("Tồn tối thiểu không được âm.")
        return value


class NguyenLieuSerializer(serializers.ModelSerializer):
    """
    Danh mục nguyên liệu dùng chung. Tồn kho trả theo các chi nhánh trong context["chi_nhanh_ids"]:
    - ton_kho: từng chi nhánh;
    - ton_kho_hien_tai / ton_kho_toi_thieu / sap_het: tổng (hoặc của chi nhánh đang chọn nếu chỉ một).
    """
    so_mon_dinh_muc = serializers.IntegerField(read_only=True, default=0)
    ton_kho = serializers.SerializerMethodField()
    ton_kho_hien_tai = serializers.SerializerMethodField()
    sap_het = serializers.SerializerMethodField()
    # Ghi: mức tối thiểu mặc định cho mọi chi nhánh khi tạo nguyên liệu. Đọc: tổng tối thiểu.
    ton_kho_toi_thieu = serializers.DecimalField(max_digits=14, decimal_places=3, required=False, min_value=0)

    class Meta:
        model = NguyenLieu
        fields = (
            "id", "ten", "don_vi", "con_hoat_dong", "tao_luc", "cap_nhat_luc", "so_mon_dinh_muc",
            "ton_kho", "ton_kho_hien_tai", "ton_kho_toi_thieu", "sap_het",
        )

    def _rows(self, obj):
        ids = self.context.get("chi_nhanh_ids")
        rows = list(obj.ton_kho_chi_nhanh.all())
        if ids is not None:
            rows = [r for r in rows if r.chi_nhanh_id in ids]
        return sorted(rows, key=lambda r: r.chi_nhanh_id)

    def get_ton_kho(self, obj):
        rows = self._rows(obj)
        data = list(TonKhoChiNhanhSerializer(rows, many=True).data)
        # Chi nhánh trong phạm vi nhưng chưa có dòng tồn (vd. chi nhánh mới mở): hiện tồn 0.
        co = {r.chi_nhanh_id for r in rows}
        for cn_id, ten in sorted(self.context.get("chi_nhanh_ten", {}).items()):
            if cn_id not in co:
                data.append({
                    "id": None, "nguyen_lieu": obj.id, "chi_nhanh": cn_id, "ten_chi_nhanh": ten,
                    "ten_nguyen_lieu": obj.ten, "don_vi": obj.don_vi, "ton_kho_hien_tai": "0.000",
                    "ton_kho_toi_thieu": "0.000", "sap_het": True, "cap_nhat_luc": None,
                })
        return sorted(data, key=lambda d: d["chi_nhanh"])

    def get_ton_kho_hien_tai(self, obj):
        return str(sum((r.ton_kho_hien_tai for r in self._rows(obj)), Decimal("0")))

    def get_sap_het(self, obj):
        return any(r.sap_het for r in self._rows(obj))

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data["ton_kho_toi_thieu"] = str(sum((r.ton_kho_toi_thieu for r in self._rows(obj)), Decimal("0")))
        return data

    def validate_ten(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Tên nguyên liệu không được để trống.")
        return value

    def create(self, validated_data):
        toi_thieu = validated_data.pop("ton_kho_toi_thieu", None)
        nl = super().create(validated_data)
        from branches.models import ChiNhanh
        from .services import DichVuKho
        DichVuKho.dam_bao_ton_kho([nl.id], ChiNhanh.objects.values_list("id", flat=True), toi_thieu)
        return nl

    def update(self, instance, validated_data):
        # Mức tối thiểu sửa theo từng chi nhánh qua /api/ton-kho/.
        validated_data.pop("ton_kho_toi_thieu", None)
        return super().update(instance, validated_data)


class HinhAnhMonAnSerializer(serializers.ModelSerializer):

    class Meta:
        model = HinhAnhMonAn
        fields = ("id", "anh", "van_ban_mo_ta", "la_anh_chinh", "thu_tu")


class MonAnSerializer(serializers.ModelSerializer):
    chi_tiet_danh_muc = DanhMucSerializer(source="danh_muc", read_only=True)
    the_mon_an = serializers.SlugRelatedField(
        many=True, slug_field="ten",
        queryset=TheMonAn.objects.all(), required=False
    )
    hinh_anh = HinhAnhMonAnSerializer(many=True, read_only=True)
    don_gia_hien_tai = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    # Tên nguyên liệu chính lấy từ định mức (DinhMucNguyenLieu); sửa ở trang Nguyên liệu & kho.
    nguyen_lieu = serializers.SlugRelatedField(many=True, read_only=True, slug_field="ten")

    def _save_primary_image(self, instance, image_data):
        if not image_data or not image_data.startswith("data:image/"):
            return
        match = re.fullmatch(r"data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)", image_data)
        if not match:
            raise serializers.ValidationError({"image": "Ảnh phải ở định dạng JPG, PNG hoặc WebP hợp lệ."})
        try:
            content = base64.b64decode(match.group(2), validate=True)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError({"image": "Dữ liệu ảnh không hợp lệ."})
        if len(content) > 5 * 1024 * 1024:
            raise serializers.ValidationError({"image": "Ảnh không được lớn hơn 5 MB."})
        extension = "jpg" if match.group(1) == "jpeg" else match.group(1)
        image = instance.hinh_anh.filter(la_anh_chinh=True).first()
        if image is None:
            image = HinhAnhMonAn(mon_an=instance, la_anh_chinh=True)
        image.anh.save(f"mon-an-{instance.pk}.{extension}", ContentFile(content), save=True)

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        self._image_data = data.pop("image", None)
        category = data.get("danh_muc")
        if category not in (None, "") and not str(category).isdigit():
            found = DanhMuc.objects.filter(ten__iexact=str(category)).first() or DanhMuc.objects.filter(duong_dan=str(category)).first()
            if not found:
                raise serializers.ValidationError({"category": "Danh mục món ăn không tồn tại."})
            data["danh_muc"] = found.pk
        return super().to_internal_value(data)

    def create(self, validated_data):
        instance = super().create(validated_data)
        self._save_primary_image(instance, getattr(self, "_image_data", None))
        return instance

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        self._save_primary_image(instance, getattr(self, "_image_data", None))
        return instance

    class Meta:
        model = MonAn
        fields = "__all__"
        read_only_fields = ("duong_dan", "diem_danh_gia", "so_luot_danh_gia")


class LichSuKhoSerializer(serializers.ModelSerializer):
    ten_chi_nhanh = serializers.CharField(source="chi_nhanh.ten", read_only=True, default="")
    ten_nguyen_lieu = serializers.CharField(source="nguyen_lieu.ten", read_only=True)
    don_vi = serializers.CharField(source="nguyen_lieu.don_vi", read_only=True)
    ten_nguoi_tao = serializers.SerializerMethodField()

    class Meta:
        model = LichSuXuatNhapKho
        fields = "__all__"
        read_only_fields = ("tao_boi", "ton_kho_truoc", "ton_kho_sau", "loai_tham_chieu", "id_tham_chieu")

    def get_ten_nguoi_tao(self, obj):
        u = obj.tao_boi
        if not u:
            return ""
        return getattr(u, "ho_ten", "") or u.get_full_name() or u.username

    def validate(self, attrs):
        so_luong = attrs.get("so_luong")
        if attrs.get("loai_giao_dich") == LichSuXuatNhapKho.LoaiGiaoDich.DIEU_CHINH:
            if so_luong is None or so_luong < 0:
                raise serializers.ValidationError({"so_luong": "Tồn kho thực tế không được âm."})
        elif so_luong is None or so_luong <= 0:
            raise serializers.ValidationError({"so_luong": "Số lượng phải lớn hơn 0."})
        return attrs


class DinhMucNguyenLieuSerializer(serializers.ModelSerializer):
    ten_mon = serializers.CharField(source="mon_an.ten", read_only=True)
    ten_nguyen_lieu = serializers.CharField(source="nguyen_lieu.ten", read_only=True)
    don_vi = serializers.CharField(source="nguyen_lieu.don_vi", read_only=True)

    class Meta:
        model = DinhMucNguyenLieu
        fields = ("id", "mon_an", "nguyen_lieu", "so_luong_can", "ten_mon", "ten_nguyen_lieu", "don_vi")
        validators = []

    def validate(self, attrs):
        mon_an = attrs.get("mon_an", getattr(self.instance, "mon_an", None))
        nguyen_lieu = attrs.get("nguyen_lieu", getattr(self.instance, "nguyen_lieu", None))
        trung = DinhMucNguyenLieu.objects.filter(mon_an=mon_an, nguyen_lieu=nguyen_lieu)
        if self.instance:
            trung = trung.exclude(pk=self.instance.pk)
        if trung.exists():
            raise serializers.ValidationError({"mon_an": f"Món '{mon_an.ten}' đã có định mức cho nguyên liệu này."})
        return attrs

    def validate_so_luong_can(self, value):
        if value <= 0:
            raise serializers.ValidationError("Định mức phải lớn hơn 0.")
        return value
