from django.http import Http404
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.permissions import LaNhanVienNhaHang
from .models import DonHang
from .serializers import DonHangSerializer
from .services import DichVuDonHang


class DonHangViewSet(viewsets.ModelViewSet):
    serializer_class = DonHangSerializer
    # Đã bỏ đặt món trực tuyến: đơn chỉ sinh ra từ phiên phục vụ tại bàn.
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.user.is_authenticated and getattr(self.request.user, "la_nhan_vien_nha_hang", False):
            return [LaNhanVienNhaHang()]
        return super().get_permissions()

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_val = self.kwargs.get(lookup_url_kwarg)
        if lookup_val is None:
            return super().get_object()
        if str(lookup_val).isdigit():
            obj = queryset.filter(pk=lookup_val).first()
            if not obj:
                obj = queryset.filter(ma_don_hang__iexact=str(lookup_val)).first()
        else:
            obj = queryset.filter(ma_don_hang__iexact=str(lookup_val)).first()
        if not obj:
            raise Http404("Không tìm thấy đơn hàng.")
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        danh_sach = (
            DonHang.objects.select_related("khach_hang", "chi_nhanh", "dat_ban", "khuyen_mai")
            .prefetch_related("danh_sach_mon__mon_an", "lich_su_trang_thai")
            .order_by("-tao_luc")
        )
        is_staff = (
            getattr(self.request.user, "la_nhan_vien_nha_hang", False)
            or getattr(self.request.user, "is_staff", False)
        )
        if is_staff:
            if self.request.user.is_superuser or getattr(self.request.user, "la_quan_tri_vien", False):
                return danh_sach
            branch_id = getattr(self.request.user, "chi_nhanh_quan_ly_id", None)
            return danh_sach.filter(chi_nhanh_id=branch_id) if branch_id else danh_sach.none()
        return danh_sach.filter(khach_hang=self.request.user)


    def perform_update(self, serializer):
        user = self.request.user
        if getattr(user, "la_nhan_vien_nha_hang", False) and not (
            user.is_superuser or getattr(user, "la_quan_tri_vien", False)
        ):
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            order = self.get_object()
            requested_branch = serializer.validated_data.get("chi_nhanh", order.chi_nhanh)
            if not branch_id or order.chi_nhanh_id != branch_id or getattr(requested_branch, "id", None) != branch_id:
                raise PermissionDenied("Bạn chỉ được sửa đơn hàng thuộc chi nhánh được phân công.")
        serializer.save()

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def trang_thai(self, request, pk=None):
        status_val = (
            request.data.get("status")
            or request.data.get("trang_thai")
            or request.data.get("to_status")
        )
        note_val = (
            request.data.get("note")
            or request.data.get("ghi_chu")
            or ""
        )
        don_hang = DichVuDonHang.doi_trang_thai(
            self.get_object(),
            status_val,
            request.user,
            note_val,
        )
        from foods.services import DichVuKho
        data = dict(self.get_serializer(don_hang).data)
        data["canh_bao_kho"] = DichVuKho.canh_bao_sap_het(
            don_hang.danh_sach_mon.values_list("mon_an_id", flat=True)
        )
        return Response(data)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def chuyen_trang_thai(self, request, pk=None):
        return self.trang_thai(request, pk=pk)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def cap_nhat_trang_thai(self, request, pk=None):
        return self.trang_thai(request, pk=pk)

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
    def status(self, request, pk=None):
        return self.trang_thai(request, pk=pk)


# Backward-compatible viewset aliases
OrderViewSet = DonHangViewSet
