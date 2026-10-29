from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from api.permissions import LaNhanVienNhaHang
from .models import VaiTro, QuyenHan, NguoiDungVaiTro
from .serializers import (
    NguoiDungSerializer,
    DangKySerializer,
    DoiMatKhauSerializer,
    VaiTroSerializer,
    QuyenHanSerializer,
    DangNhapTokenSerializer,
)


class DangNhapTokenView(TokenObtainPairView):
    serializer_class = DangNhapTokenSerializer

NguoiDung = get_user_model()


class XacThucViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def dang_ky(self, request):
        s = DangKySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        # Tạo user với is_active=False để chờ xác thực email
        nguoi_dung = s.save(is_active=False)

        # Tạo bản ghi XacThucEmail và gửi OTP
        from .models import XacThucEmail
        xac_thuc, _ = XacThucEmail.objects.get_or_create(nguoi_dung=nguoi_dung)
        ma_otp = xac_thuc.tao_ma()

        # Gửi email (console backend in ra terminal trong môi trường dev)
        send_mail(
            subject="Mã xác thực tài khoản Nhà hàng Mộc",
            message=(
                f"Chào {nguoi_dung.first_name or nguoi_dung.username},\n\n"
                f"Mã xác thực của bạn là: {ma_otp}\n\n"
                f"Mã có hiệu lực trong 15 phút.\n\n"
                f"Nhà hàng Mộc"
            ),
            from_email=None,  # dùng DEFAULT_FROM_EMAIL
            recipient_list=[nguoi_dung.thu_dien_tu],
            fail_silently=True,
        )

        return Response({
            "message": "Vui lòng kiểm tra email để xác thực tài khoản.",
            "email": nguoi_dung.thu_dien_tu,
        }, status=201)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        return self.dang_ky(request)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="dang-ky")
    def dang_ky_kebab(self, request):
        return self.dang_ky(request)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="gui-ma-xac-thuc")
    def gui_ma_xac_thuc(self, request):
        """Gửi lại mã OTP xác thực email."""
        from .models import XacThucEmail
        email = request.data.get("email", "").strip()
        if not email:
            return Response({"detail": "Cần cung cấp email."}, status=400)

        try:
            nguoi_dung = NguoiDung.objects.get(thu_dien_tu=email)
        except NguoiDung.DoesNotExist:
            return Response({"detail": "Email không tồn tại."}, status=404)

        if nguoi_dung.is_active:
            return Response({"detail": "Tài khoản đã được xác thực."}, status=400)

        xac_thuc, _ = XacThucEmail.objects.get_or_create(nguoi_dung=nguoi_dung)
        ma_otp = xac_thuc.tao_ma()

        send_mail(
            subject="Mã xác thực tài khoản Nhà hàng Mộc",
            message=(
                f"Mã xác thực mới của bạn là: {ma_otp}\n\n"
                f"Mã có hiệu lực trong 15 phút.\n\nNhà hàng Mộc"
            ),
            from_email=None,
            recipient_list=[email],
            fail_silently=True,
        )
        return Response({"message": "Đã gửi lại mã xác thực."})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="xac-thuc-email")
    def xac_thuc_email(self, request):
        """Xác thực OTP. Trả về tokens nếu thành công."""
        from .models import XacThucEmail
        email = request.data.get("email", "").strip()
        ma_otp = request.data.get("ma_xac_thuc", "").strip()

        if not email or not ma_otp:
            return Response({"detail": "Cần cung cấp email và mã xác thực."}, status=400)

        try:
            nguoi_dung = NguoiDung.objects.get(thu_dien_tu=email)
        except NguoiDung.DoesNotExist:
            return Response({"detail": "Email không tồn tại."}, status=404)

        try:
            xac_thuc = nguoi_dung.xac_thuc_email
        except XacThucEmail.DoesNotExist:
            return Response({"detail": "Chưa có yêu cầu xác thực. Vui lòng đăng ký lại."}, status=400)

        if xac_thuc.da_xac_thuc:
            return Response({"detail": "Email đã được xác thực."}, status=400)

        if not xac_thuc.con_hieu_luc:
            return Response({"detail": "Mã xác thực đã hết hạn. Vui lòng yêu cầu gửi lại."}, status=400)

        if xac_thuc.ma_xac_thuc != ma_otp:
            return Response({"detail": "Mã xác thực không chính xác."}, status=400)

        # Kích hoạt tài khoản
        nguoi_dung.is_active = True
        nguoi_dung.save(update_fields=["is_active"])
        xac_thuc.da_xac_thuc = True
        xac_thuc.save(update_fields=["da_xac_thuc"])

        # Trả về tokens để auto-login
        token = RefreshToken.for_user(nguoi_dung)
        user_data = NguoiDungSerializer(nguoi_dung).data
        return Response({
            "message": "Xác thực email thành công!",
            "user": user_data,
            "nguoi_dung": user_data,
            "access": str(token.access_token),
            "refresh": str(token),
        })

    @action(detail=False, methods=["get", "patch", "put"], permission_classes=[IsAuthenticated])
    def ho_so(self, request):
        if request.method in ["PATCH", "PUT"]:
            s = NguoiDungSerializer(request.user, data=request.data, partial=True)
            s.is_valid(raise_exception=True)
            s.save()
            return Response(s.data)
        return Response(NguoiDungSerializer(request.user).data)

    @action(detail=False, methods=["get", "patch", "put"], permission_classes=[IsAuthenticated])
    def profile(self, request):
        return self.ho_so(request)

    @action(detail=False, methods=["get", "patch", "put"], permission_classes=[IsAuthenticated], url_path="ho-so")
    def ho_so_kebab(self, request):
        return self.ho_so(request)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def doi_mat_khau(self, request):
        s = DoiMatKhauSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        request.user.set_password(s.validated_data["mat_khau_moi"])
        request.user.save()
        return Response({"thong_bao": "Đã đổi mật khẩu thành công.", "message": "Password changed successfully."})

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="change_password")
    def change_password(self, request):
        return self.doi_mat_khau(request)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="change-password")
    def change_password_kebab(self, request):
        return self.doi_mat_khau(request)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="doi-mat-khau")
    def doi_mat_khau_kebab(self, request):
        return self.doi_mat_khau(request)


class NguoiDungViewSet(viewsets.ModelViewSet):
    queryset = NguoiDung.objects.all().order_by("-date_joined")
    serializer_class = NguoiDungSerializer
    permission_classes = [LaNhanVienNhaHang]

    def _require_admin(self):
        if not (self.request.user.is_superuser or getattr(self.request.user, "la_quan_tri_vien", False)):
            raise PermissionDenied("Chỉ quản trị viên mới được quản lý tài khoản.")

    @action(detail=False, methods=["post"], url_path="admin_create")
    def admin_create(self, request):
        self._require_admin()
        email = str(request.data.get("email", "")).strip().lower()
        password = str(request.data.get("password", ""))
        name = str(request.data.get("name", "")).strip()
        if not email or not password or len(password) < 8:
            raise ValidationError({"password": "Email bắt buộc; mật khẩu khởi tạo tối thiểu 8 ký tự."})
        if NguoiDung.objects.filter(thu_dien_tu=email).exists():
            raise ValidationError({"email": "Email này đã được sử dụng."})
        username = email.split("@", 1)[0]
        base, suffix = username, 1
        while NguoiDung.objects.filter(username=username).exists():
            username = f"{base}_{suffix}"; suffix += 1
        user = NguoiDung.objects.create_user(username=username, thu_dien_tu=email, email=email, password=password, so_dien_thoai=request.data.get("phone", ""))
        user.name = name
        user.is_active = bool(request.data.get("active", True))
        user.save()
        self._set_admin_role(user, request.data.get("role", "customer"))
        return Response(self.get_serializer(user).data, status=201)

    @action(detail=True, methods=["patch"], url_path="admin_update")
    def admin_update(self, request, pk=None):
        self._require_admin()
        user = self.get_object()
        if "email" in request.data:
            email = str(request.data["email"]).strip().lower()
            if NguoiDung.objects.exclude(pk=user.pk).filter(thu_dien_tu=email).exists():
                raise ValidationError({"email": "Email này đã được sử dụng."})
            user.thu_dien_tu = user.email = email
        if "name" in request.data: user.name = str(request.data["name"]).strip()
        if "phone" in request.data: user.so_dien_thoai = str(request.data["phone"] or "")
        if "active" in request.data: user.is_active = bool(request.data["active"])
        if request.data.get("password"):
            if len(str(request.data["password"])) < 8: raise ValidationError({"password": "Mật khẩu tối thiểu 8 ký tự."})
            user.set_password(str(request.data["password"]))
        user.save()
        if "role" in request.data: self._set_admin_role(user, request.data["role"])
        return Response(self.get_serializer(user).data)

    @staticmethod
    def _set_admin_role(user, role_key):
        role_name = {"admin": "quan_tri_vien", "staff": "nhan_vien", "customer": "khach_hang"}.get(str(role_key), str(role_key))
        role, _ = VaiTro.objects.get_or_create(ten=role_name, defaults={"mo_ta": role_name})
        user.danh_sach_vai_tro.set([role])


class VaiTroViewSet(viewsets.ModelViewSet):
    queryset = VaiTro.objects.prefetch_related("danh_sach_quyen__quyen_han")
    serializer_class = VaiTroSerializer
    permission_classes = [LaNhanVienNhaHang]

    @action(detail=True, methods=["get", "put"], url_path="permissions")
    def permissions(self, request, pk=None):
        if not (request.user.is_superuser or getattr(request.user, "la_quan_tri_vien", False)):
            raise PermissionDenied("Chỉ quản trị viên mới được thay đổi phân quyền.")
        role = self.get_object()
        if role.ten in {"quan_tri_vien", "admin"} and request.method == "PUT":
            raise ValidationError({"detail": "Vai trò quản trị viên luôn có toàn quyền."})
        from .models import QuyenHan, VaiTroQuyenHan
        if request.method == "PUT":
            matrix = request.data.get("permissions", {})
            wanted = []
            for module, actions in matrix.items():
                for action_name in actions:
                    codename = f"{module}.{action_name}"
                    permission, _ = QuyenHan.objects.get_or_create(ma_quyen=codename, defaults={"ten": codename, "mo_ta": "Quyền quản trị giao diện"})
                    wanted.append(permission)
            modules = list(matrix)
            old = role.danh_sach_quyen.all()
            if modules:
                scoped = Q()
                for module in modules:
                    scoped |= Q(quyen_han__ma_quyen__startswith=f"{module}.")
                old.filter(scoped).delete()
            VaiTroQuyenHan.objects.bulk_create([VaiTroQuyenHan(vai_tro=role, quyen_han=permission) for permission in wanted], ignore_conflicts=True)
        matrix = {}
        for relation in role.danh_sach_quyen.select_related("quyen_han").all():
            codename = relation.quyen_han.ma_quyen
            if "." in codename:
                module, action_name = codename.rsplit(".", 1)
                matrix.setdefault(module, []).append(action_name)
        return Response({"id": role.id, "name": role.ten, "permissions": matrix})


class QuyenHanViewSet(viewsets.ModelViewSet):
    queryset = QuyenHan.objects.all()
    serializer_class = QuyenHanSerializer
    permission_classes = [LaNhanVienNhaHang]


# Backward-compatible viewset aliases
UserViewSet = NguoiDungViewSet
RoleViewSet = VaiTroViewSet
PermissionViewSet = QuyenHanViewSet
AuthViewSet = XacThucViewSet
