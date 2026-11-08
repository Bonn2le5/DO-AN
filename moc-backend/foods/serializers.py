import base64
import binascii
import re
from django.core.files.base import ContentFile
from rest_framework import serializers
from api.mixins import DualPayloadMixin
from decimal import Decimal
from .models import DanhMuc, NguyenLieu, MonAn, HinhAnhMonAn, TheMonAn, LichSuXuatNhapKho, DinhMucNguyenLieu


class DanhMucSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "slug": "duong_dan",
        "description": "mo_ta",
        "image": "anh_dai_dien",
        "is_active": "con_hoat_dong",
    }

    class Meta:
        model = DanhMuc
        fields = "__all__"


class TheMonAnSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "slug": "duong_dan",
    }

    class Meta:
        model = TheMonAn
        fields = "__all__"


class NguyenLieuSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "unit": "don_vi",
        "current_stock": "ton_kho_hien_tai",
        "min_stock": "ton_kho_toi_thieu",
        "is_active": "con_hoat_dong",
    }

    so_mon_dinh_muc = serializers.IntegerField(read_only=True, default=0)
    sap_het = serializers.SerializerMethodField()

    class Meta:
        model = NguyenLieu
        fields = "__all__"

    def get_sap_het(self, obj):
        return obj.ton_kho_hien_tai <= 0 or obj.ton_kho_hien_tai <= obj.ton_kho_toi_thieu

    def validate_ten(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Tên nguyên liệu không được để trống.")
        return value

    def validate_ton_kho_hien_tai(self, value):
        if value < 0:
            raise serializers.ValidationError("Tồn kho không được âm.")
        return value

    def validate_ton_kho_toi_thieu(self, value):
        if value < 0:
            raise serializers.ValidationError("Tồn tối thiểu không được âm.")
        return value

    def create(self, validated_data):
        """Tồn đầu kỳ được ghi thành một phiếu nhập để lịch sử kho khớp với tồn hiện tại."""
        ton_dau = validated_data.pop("ton_kho_hien_tai", Decimal("0")) or Decimal("0")
        nl = super().create({**validated_data, "ton_kho_hien_tai": ton_dau})
        if ton_dau > 0:
            request = self.context.get("request")
            user = request.user if request and request.user.is_authenticated else None
            LichSuXuatNhapKho.objects.create(
                nguyen_lieu=nl, loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
                so_luong=ton_dau, ton_kho_truoc=0, ton_kho_sau=ton_dau,
                loai_tham_chieu="ton_dau_ky", ghi_chu="Tồn đầu kỳ khi tạo nguyên liệu", tao_boi=user,
            )
        return nl

    def update(self, instance, validated_data):
        # Tồn kho chỉ thay đổi qua phiếu nhập / xuất / điều chỉnh để luôn có lịch sử.
        validated_data.pop("ton_kho_hien_tai", None)
        return super().update(instance, validated_data)


class HinhAnhMonAnSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "image": "anh",
        "description": "van_ban_mo_ta",
        "is_primary": "la_anh_chinh",
        "order": "thu_tu",
    }

    class Meta:
        model = HinhAnhMonAn
        fields = ("id", "anh", "van_ban_mo_ta", "la_anh_chinh", "thu_tu")


class MonAnSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "price": "don_gia",
        "current_price": "don_gia",
        "description": "mo_ta_chi_tiet",
        "short_description": "mo_ta_ngan",
        "category": "danh_muc",
        "category_id": "danh_muc",
        "is_available": "con_hang",
        "is_active": "con_hang",
        "is_featured": "noi_bat",
        "is_vegetarian": "la_mon_chay",
        "spicy_level": "do_cay",
        "spiciness": "do_cay",
        "slug": "duong_dan",
        "tags": "the_mon_an",
    }
    chi_tiet_danh_muc = DanhMucSerializer(source="danh_muc", read_only=True)
    the_mon_an = serializers.SlugRelatedField(
        many=True, slug_field="ten",
        queryset=TheMonAn.objects.all(), required=False
    )
    hinh_anh = HinhAnhMonAnSerializer(many=True, read_only=True)
    don_gia_hien_tai = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

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
        category = data.get("category", data.get("danh_muc"))
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


# Backward-compatible serializer aliases
CategorySerializer = DanhMucSerializer
TagSerializer = TheMonAnSerializer
IngredientSerializer = NguyenLieuSerializer
FoodSerializer = MonAnSerializer
FoodImageSerializer = HinhAnhMonAnSerializer
InventoryHistorySerializer = LichSuKhoSerializer
