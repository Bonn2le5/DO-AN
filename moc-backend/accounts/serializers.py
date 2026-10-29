from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.mixins import DualPayloadMixin
from .models import VaiTro, QuyenHan, NguoiDungVaiTro

NguoiDung = get_user_model()


class VaiTroSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "description": "mo_ta",
    }

    class Meta:
        model = VaiTro
        fields = ("id", "ten", "mo_ta")


class QuyenHanSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "name": "ten",
        "codename": "ma_quyen",
        "description": "mo_ta",
    }

    class Meta:
        model = QuyenHan
        fields = "__all__"


class NguoiDungSerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "email": "thu_dien_tu",
        "phone": "so_dien_thoai",
        "phone_number": "so_dien_thoai",
        "name": "ho_ten",
        "avatar": "anh_dai_dien",
        "birth_date": "ngay_sinh",
        "gender": "gioi_tinh",
    }
    danh_sach_vai_tro = serializers.SlugRelatedField(many=True, slug_field="ten", read_only=True)
    la_nhan_vien_nha_hang = serializers.ReadOnlyField()

    # Dual representation fields
    email = serializers.EmailField(source="thu_dien_tu", read_only=True)
    phone = serializers.CharField(source="so_dien_thoai", read_only=True)
    name = serializers.CharField(read_only=True)
    roles = serializers.SlugRelatedField(source="danh_sach_vai_tro", many=True, slug_field="ten", read_only=True)
    is_restaurant_staff = serializers.ReadOnlyField()

    class Meta:
        model = NguoiDung
        fields = (
            "id", "thu_dien_tu", "email", "username", "first_name", "last_name",
            "name", "so_dien_thoai", "phone", "anh_dai_dien", "ngay_sinh", "gioi_tinh",
            "danh_sach_vai_tro", "roles", "is_active", "date_joined",
            "la_nhan_vien_nha_hang", "is_restaurant_staff", "is_superuser",
        )
        read_only_fields = (
            "danh_sach_vai_tro", "roles", "is_active", "date_joined",
            "la_nhan_vien_nha_hang", "is_restaurant_staff", "is_superuser",
        )


class DangKySerializer(DualPayloadMixin, serializers.ModelSerializer):
    FIELD_ALIASES = {
        "email": "thu_dien_tu",
        "password": "mat_khau",
        "name": "ho_ten",
        "full_name": "ho_ten",
        "phone": "so_dien_thoai",
        "phone_number": "so_dien_thoai",
    }
    mat_khau = serializers.CharField(write_only=True, min_length=6)
    ho_ten = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = NguoiDung
        fields = ("thu_dien_tu", "username", "ho_ten", "mat_khau", "first_name", "last_name", "so_dien_thoai")
        extra_kwargs = {"username": {"required": False}}

    def create(self, du_lieu_da_xac_thuc):
        ho_ten = du_lieu_da_xac_thuc.pop("ho_ten", "").strip()
        mat_khau = du_lieu_da_xac_thuc.pop("mat_khau")

        # 1. Bảo toàn thu_dien_tu và đồng bộ email
        thu_dien_tu = du_lieu_da_xac_thuc.get("thu_dien_tu")
        if thu_dien_tu:
            du_lieu_da_xac_thuc["email"] = thu_dien_tu

        # 2. Tự động sinh username độc nhất nếu chưa được cấp
        if not du_lieu_da_xac_thuc.get("username"):
            base_username = (thu_dien_tu or "user").split("@", 1)[0]
            username = base_username
            try:
                counter = 1
                while NguoiDung.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
            except Exception:
                username = base_username
            du_lieu_da_xac_thuc["username"] = username

        # 3. Phân tách họ và tên
        if ho_ten and not du_lieu_da_xac_thuc.get("first_name"):
            parts = ho_ten.split(maxsplit=1)
            du_lieu_da_xac_thuc["first_name"] = parts[0]
            du_lieu_da_xac_thuc["last_name"] = parts[1] if len(parts) > 1 else ""

        # 4. Tạo user qua UserManager
        nguoi_dung = NguoiDung.objects.create_user(password=mat_khau, **du_lieu_da_xac_thuc)

        # 5. Gán vai trò mặc định khách hàng
        vai_tro_khach, _ = VaiTro.objects.get_or_create(ten="khach_hang", defaults={"mo_ta": "Khách hàng"})
        NguoiDungVaiTro.objects.get_or_create(nguoi_dung=nguoi_dung, vai_tro=vai_tro_khach)
        return nguoi_dung


class DoiMatKhauSerializer(DualPayloadMixin, serializers.Serializer):
    FIELD_ALIASES = {
        "old_password": "mat_khau_cu",
        "current_password": "mat_khau_cu",
        "new_password": "mat_khau_moi",
    }
    mat_khau_cu = serializers.CharField()
    mat_khau_moi = serializers.CharField(min_length=6)

    def validate_mat_khau_cu(self, gia_tri):
        if not self.context["request"].user.check_password(gia_tri):
            raise serializers.ValidationError("Mật khẩu hiện tại không đúng.")
        return gia_tri


class DangNhapTokenSerializer(TokenObtainPairSerializer):
    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)
        if "email" in data and "thu_dien_tu" not in data:
            data["thu_dien_tu"] = data["email"]
        if "username" in data and "thu_dien_tu" not in data:
            data["thu_dien_tu"] = data["username"]
        return super().to_internal_value(data)


# Backward-compatible serializer aliases
UserSerializer = NguoiDungSerializer
RoleSerializer = VaiTroSerializer
PermissionSerializer = QuyenHanSerializer
LoginTokenSerializer = DangNhapTokenSerializer
