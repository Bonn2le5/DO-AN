from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
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
        with transaction.atomic():
            nguoi_dung = s.save(is_active=False)

        # Tạo bản ghi XacThucEmail và gửi OTP qua Resend
        from .models import XacThucEmail
        from .services_email import gui_email_xac_thuc
        xac_thuc, _ = XacThucEmail.objects.get_or_create(nguoi_dung=nguoi_dung)
        ma_otp = xac_thuc.tao_ma()

        gui_email_xac_thuc(
            thu_dien_tu=nguoi_dung.thu_dien_tu,
            ten_nguoi_nhan=nguoi_dung.first_name or nguoi_dung.username,
            ma_otp=ma_otp,
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
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response({"detail": "Cần cung cấp email."}, status=400)

        try:
            nguoi_dung = NguoiDung.objects.get(thu_dien_tu=email)
        except NguoiDung.DoesNotExist:
            return Response({"detail": "Email không tồn tại."}, status=404)

        if nguoi_dung.is_active:
            return Response({"detail": "Tài khoản đã được xác thực."}, status=400)

        from .services_email import gui_email_xac_thuc
        xac_thuc, _ = XacThucEmail.objects.get_or_create(nguoi_dung=nguoi_dung)
        ma_otp = xac_thuc.tao_ma()

        gui_email_xac_thuc(
            thu_dien_tu=email,
            ten_nguoi_nhan=nguoi_dung.first_name or nguoi_dung.username,
            ma_otp=ma_otp,
        )
        return Response({"message": "Đã gửi lại mã xác thực."})

    @action(detail=False, methods=["post"], permission_classes=[AllowAny], url_path="xac-thuc-email")
    def xac_thuc_email(self, request):
        """Xác thực OTP. Trả về tokens nếu thành công."""
        from .models import XacThucEmail
        email = request.data.get("email", "").strip().lower()
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
            "nguoi_dung": user_data,
            "access": str(token.access_token),
            "refresh": str(token),
        })

    @action(detail=False, methods=["get", "patch", "put"], permission_classes=[IsAuthenticated])
    def ho_so(self, request):
        if request.method in ["PATCH", "PUT"]:
            email_moi = request.data.get("thu_dien_tu")
            if email_moi and email_moi.strip().lower() != request.user.thu_dien_tu.lower():
                # Đổi email = đổi thông tin đăng nhập, nên phải nhập lại mật khẩu.
                if not request.user.check_password(request.data.get("mat_khau_hien_tai") or ""):
                    return Response({"mat_khau_hien_tai": ["Mật khẩu hiện tại không đúng."]}, status=400)
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
        return Response({"thong_bao": "Đã đổi mật khẩu thành công."})

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

    def _is_admin(self):
        return bool(self.request.user.is_superuser or getattr(self.request.user, "la_quan_tri_vien", False))

    def _managed_branch_id(self):
        """Chi nhánh mà quản lý được quản lý nhân viên; None nếu không phải quản lý chi nhánh."""
        user = self.request.user
        if self._is_admin() or not getattr(user, "la_quan_ly_chi_nhanh", False):
            return None
        return user.chi_nhanh_quan_ly_id

    def _require_admin(self):
        if not self._is_admin():
            raise PermissionDenied("Chỉ quản trị viên mới được quản lý tài khoản.")

    def _require_admin_or_manager(self):
        if not (self._is_admin() or self._managed_branch_id()):
            raise PermissionDenied("Chỉ quản trị viên hoặc quản lý chi nhánh mới được quản lý nhân viên.")

    def get_queryset(self):
        qs = super().get_queryset()
        if self._is_admin():
            return qs
        branch_id = self._managed_branch_id()
        if not branch_id:
            return qs.none()
        # Quản lý chỉ thấy nhân viên bán hàng của chi nhánh mình.
        return qs.filter(chi_nhanh_quan_ly_id=branch_id, danh_sach_vai_tro__ten="nhan_vien_ban_hang").distinct()

    # CRUD mặc định chỉ dành cho admin; quản lý dùng admin_create / admin_update.
    def create(self, request, *args, **kwargs):
        self._require_admin(); return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self._require_admin(); return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        self._require_admin(); return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["post"], url_path="admin_create")
    def admin_create(self, request):
        self._require_admin_or_manager()
        email = str(request.data.get("email", "")).strip().lower()
        password = str(request.data.get("password", ""))
        name = str(request.data.get("name", "")).strip()
        role_key = request.data.get("role", "customer")
        manager_branch = self._managed_branch_id()
        if manager_branch:
            # Quản lý chỉ tạo được nhân viên bán hàng cho chi nhánh mình.
            role_key = "staff"
        if not email:
            raise ValidationError({"email": "Email là bắt buộc."})
        try:
            validate_email(email)
        except DjangoValidationError:
            raise ValidationError({"email": "Email chưa đúng định dạng."})
        if not password or len(password) < 8:
            raise ValidationError({"password": "Mật khẩu khởi tạo phải có ít nhất 8 ký tự."})
        if not name:
            raise ValidationError({"name": "Họ và tên là bắt buộc."})
        role_aliases = {
            "admin": "admin", "quan_tri_vien": "admin",
            "branch_manager": "branch_manager", "quan_ly_chi_nhanh": "branch_manager",
            "staff": "staff", "employee": "staff", "nhan_vien_ban_hang": "staff", "nhan_vien": "branch_manager",
            "customer": "customer", "khach_hang": "customer",
        }
        normalized_role = role_aliases.get(str(role_key))
        if normalized_role is None:
            raise ValidationError({"role": "Vai trò không hợp lệ."})
        branch_id = manager_branch or request.data.get("branch_id")
        if normalized_role in {"staff", "branch_manager"} and not branch_id:
            raise ValidationError({"branch_id": "Nhân viên và quản lý chi nhánh phải được gán một chi nhánh."})
        if NguoiDung.objects.filter(thu_dien_tu__iexact=email).exists():
            raise ValidationError({"email": "Email này đã được sử dụng."})
        managed_branch = None
        if branch_id not in (None, ""):
            from branches.models import ChiNhanh
            try:
                managed_branch = ChiNhanh.objects.get(pk=branch_id)
            except (ChiNhanh.DoesNotExist, ValueError, TypeError):
                raise ValidationError({"branch_id": "Chi nhánh không tồn tại hoặc không hợp lệ."})
        username = email.split("@", 1)[0]
        base, suffix = username, 1
        while NguoiDung.objects.filter(username=username).exists():
            username = f"{base}_{suffix}"; suffix += 1
        with transaction.atomic():
            user = NguoiDung.objects.create_user(username=username, thu_dien_tu=email, email=email, password=password, so_dien_thoai=request.data.get("phone", ""))
            user.ho_ten = name
            user.is_active = request.data.get("active", True)
            user.chi_nhanh_quan_ly = managed_branch
            user.save()
            self._set_admin_role(user, normalized_role)
        return Response(self.get_serializer(user).data, status=201)

    @action(detail=True, methods=["patch"], url_path="admin_update")
    def admin_update(self, request, pk=None):
        self._require_admin_or_manager()
        user = self.get_object()
        manager_branch = self._managed_branch_id()
        if manager_branch:
            # Form gửi kèm vai trò/chi nhánh hiện tại: chấp nhận, nhưng không cho đổi sang giá trị khác.
            role = request.data.get("role")
            branch = request.data.get("branch_id")
            if role not in (None, "", "staff", "nhan_vien_ban_hang") or (branch not in (None, "") and str(branch) != str(manager_branch)):
                raise PermissionDenied("Quản lý chi nhánh không đổi được vai trò hay chi nhánh của nhân viên.")
        requested_role = request.data.get("role")
        if requested_role in {"staff", "employee", "nhan_vien_ban_hang", "branch_manager", "quan_ly_chi_nhanh", "nhan_vien"} and not (
            request.data.get("branch_id") or user.chi_nhanh_quan_ly_id
        ):
            raise ValidationError({"branch_id": "Quản lý chi nhánh phải được gán một chi nhánh."})
        if "email" in request.data:
            email = str(request.data["email"]).strip().lower()
            if NguoiDung.objects.exclude(pk=user.pk).filter(thu_dien_tu=email).exists():
                raise ValidationError({"email": "Email này đã được sử dụng."})
            user.thu_dien_tu = user.email = email
        if "name" in request.data: user.ho_ten = str(request.data["name"]).strip()
        if "phone" in request.data: user.so_dien_thoai = str(request.data["phone"] or "")
        if "active" in request.data: user.is_active = bool(request.data["active"])
        if "branch_id" in request.data and not manager_branch:
            self._set_managed_branch(user, request.data.get("branch_id"))
        if request.data.get("password"):
            if len(str(request.data["password"])) < 8: raise ValidationError({"password": "Mật khẩu tối thiểu 8 ký tự."})
            user.set_password(str(request.data["password"]))
        user.save()
        if "role" in request.data and not manager_branch: self._set_admin_role(user, request.data["role"])
        return Response(self.get_serializer(user).data)

    @staticmethod
    def _set_admin_role(user, role_key):
        role_name = {
            "admin": "quan_tri_vien",
            "branch_manager": "quan_ly_chi_nhanh",
            "staff": "nhan_vien_ban_hang",
            "customer": "khach_hang",
        }.get(str(role_key), str(role_key))
        role, _ = VaiTro.objects.get_or_create(ten=role_name, defaults={"mo_ta": role_name})
        user.danh_sach_vai_tro.set([role])

    @staticmethod
    def _set_managed_branch(user, branch_id):
        if branch_id in (None, ""):
            user.chi_nhanh_quan_ly = None
        else:
            from branches.models import ChiNhanh
            try:
                user.chi_nhanh_quan_ly = ChiNhanh.objects.get(pk=branch_id)
            except ChiNhanh.DoesNotExist:
                raise ValidationError({"branch_id": "Chi nhánh không tồn tại."})
        user.save(update_fields=["chi_nhanh_quan_ly"])


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
