import re
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import VaiTro, QuyenHan, NguoiDungVaiTro

NguoiDung = get_user_model()


class VaiTroSerializer(serializers.ModelSerializer):

    class Meta:
        model = VaiTro
        fields = ("id", "ten", "mo_ta")


class QuyenHanSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuyenHan
        fields = "__all__"


class NguoiDungSerializer(serializers.ModelSerializer):
    danh_sach_vai_tro = serializers.SlugRelatedField(many=True, slug_field="ten", read_only=True)
    la_nhan_vien_nha_hang = serializers.ReadOnlyField()

    ho_ten = serializers.CharField(read_only=True)

    class Meta:
        model = NguoiDung
        fields = (
            "id", "thu_dien_tu", "username", "first_name", "last_name",
            "ho_ten", "so_dien_thoai", "anh_dai_dien", "ngay_sinh", "gioi_tinh",
            "chi_nhanh_quan_ly",
            "danh_sach_vai_tro", "is_active", "date_joined",
            "la_nhan_vien_nha_hang", "is_superuser",
        )
        read_only_fields = (
            "danh_sach_vai_tro", "is_active", "date_joined",
            "la_nhan_vien_nha_hang", "is_superuser",
        )

    def validate_chi_nhanh_quan_ly(self, value):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not (user.is_superuser or getattr(user, "la_quan_tri_vien", False)):
            raise serializers.ValidationError("Chỉ quản trị viên được gán chi nhánh quản lý.")
        return value


class DangKySerializer(serializers.ModelSerializer):
    mat_khau = serializers.CharField(write_only=True, min_length=6, error_messages={
        "required": "Vui lòng nhập mật khẩu.",
        "blank": "Vui lòng nhập mật khẩu.",
        "min_length": "Mật khẩu tối thiểu 6 ký tự.",
    })
    ho_ten = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = NguoiDung
        fields = ("thu_dien_tu", "username", "ho_ten", "mat_khau", "first_name", "last_name", "so_dien_thoai")
        extra_kwargs = {
            "username": {"required": False},
            # Kiểm tra trùng email tự làm trong validate() để không phân biệt hoa/thường
            "thu_dien_tu": {"validators": [], "error_messages": {
                "required": "Vui lòng nhập email.",
                "blank": "Vui lòng nhập email.",
                "invalid": "Email không hợp lệ.",
            }},
            "so_dien_thoai": {"required": True, "allow_blank": False, "error_messages": {
                "required": "Vui lòng nhập số điện thoại.",
                "blank": "Vui lòng nhập số điện thoại.",
            }},
        }

    @staticmethod
    def tai_khoan_cho_xac_thuc(thu_dien_tu):
        """Tài khoản đăng ký nhưng chưa nhập OTP (khác tài khoản bị admin khóa)."""
        return NguoiDung.objects.filter(
            thu_dien_tu__iexact=thu_dien_tu, is_active=False, xac_thuc_email__da_xac_thuc=False
        )

    def validate(self, attrs):
        thu_dien_tu = attrs["thu_dien_tu"].strip().lower()
        so_dien_thoai = re.sub(r"[\s.-]", "", attrs["so_dien_thoai"])
        cho_xac_thuc = self.tai_khoan_cho_xac_thuc(thu_dien_tu).values("pk")

        if NguoiDung.objects.filter(thu_dien_tu__iexact=thu_dien_tu).exclude(pk__in=cho_xac_thuc).exists():
            raise serializers.ValidationError({"thu_dien_tu": "Email này đã được đăng ký."})
        if not re.fullmatch(r"(0|\+84)\d{9,10}", so_dien_thoai):
            raise serializers.ValidationError({"so_dien_thoai": "Số điện thoại không hợp lệ."})
        if NguoiDung.objects.filter(so_dien_thoai=so_dien_thoai).exclude(pk__in=cho_xac_thuc).exists():
            raise serializers.ValidationError({"so_dien_thoai": "Số điện thoại này đã được sử dụng."})

        attrs["thu_dien_tu"] = thu_dien_tu
        attrs["so_dien_thoai"] = so_dien_thoai
        return attrs

    def create(self, du_lieu_da_xac_thuc):
        ho_ten = du_lieu_da_xac_thuc.pop("ho_ten", "").strip()
        mat_khau = du_lieu_da_xac_thuc.pop("mat_khau")

        # 0. Đăng ký lại khi chưa xác thực: xóa bản cũ để tạo lại và gửi mã mới
        self.tai_khoan_cho_xac_thuc(du_lieu_da_xac_thuc["thu_dien_tu"]).delete()

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


class DoiMatKhauSerializer(serializers.Serializer):
    mat_khau_cu = serializers.CharField()
    mat_khau_moi = serializers.CharField(min_length=6)

    def validate_mat_khau_cu(self, gia_tri):
        if not self.context["request"].user.check_password(gia_tri):
            raise serializers.ValidationError("Mật khẩu hiện tại không đúng.")
        return gia_tri


class DangNhapTokenSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Email hoặc mật khẩu không đúng, hoặc tài khoản chưa xác thực email "
                             "(đăng ký lại để nhận mã mới).",
    }

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
        elif isinstance(data, dict):
            data = dict(data)
        if isinstance(data.get("thu_dien_tu"), str):
            data["thu_dien_tu"] = data["thu_dien_tu"].strip().lower()
        return super().to_internal_value(data)


# Backward-compatible serializer aliases
UserSerializer = NguoiDungSerializer
RoleSerializer = VaiTroSerializer
PermissionSerializer = QuyenHanSerializer
LoginTokenSerializer = DangNhapTokenSerializer
