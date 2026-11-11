from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.permissions import LaNhanVienNhaHang
from rest_framework.exceptions import PermissionDenied
from .models import DanhGia
from .serializers import DanhGiaSerializer, GuiDanhGiaBuaAnSerializer
from .services import cap_nhat_diem_mon, co_the_danh_gia_mon, don_cho_danh_gia, gui_danh_gia_bua_an
from recommendations.services import dong_bo_tuong_tac_danh_gia


class DanhGiaViewSet(viewsets.ModelViewSet):
    serializer_class = DanhGiaSerializer

    def get_permissions(self):
        if self.request.user.is_authenticated and getattr(self.request.user, "la_nhan_vien_nha_hang", False):
            return [LaNhanVienNhaHang()]
        if self.action in {"create", "update", "partial_update", "destroy", "cho_danh_gia", "bua_an", "co_the"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        q = DanhGia.objects.select_related(
            "nguoi_dung", "mon_an", "don_hang", "chi_tiet_don_hang"
        )
        user = self.request.user
        if self.request.query_params.get("mine"):
            # Chủ đánh giá thấy cả đánh giá đang bị ẩn của mình.
            return q.filter(nguoi_dung=user).order_by("-tao_luc") if user.is_authenticated else q.none()
        is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
        if not is_staff:
            q = q.filter(hien_thi=True)
        food_id = self.request.query_params.get("mon_an")
        if food_id:
            q = q.filter(mon_an_id=food_id)
        return q

    def _cap_nhat_diem_mon(self, mon_an):
        cap_nhat_diem_mon(mon_an)

    @action(detail=False, methods=["get"], url_path="cho-danh-gia")
    def cho_danh_gia(self, request):
        """Các bữa ăn đã hoàn tất còn món / phần chung chưa đánh giá."""
        return Response(don_cho_danh_gia(request.user))

    @action(detail=False, methods=["post"], url_path="bua-an")
    def bua_an(self, request):
        """Gửi đánh giá cả bữa: {don_hang, mon: [{chi_tiet_don_hang, diem_danh_gia, nhan_xet}], diem_phuc_vu, diem_khong_gian, nhan_xet}"""
        ser = GuiDanhGiaBuaAnSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return Response(gui_danh_gia_bua_an(request.user, ser.validated_data), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="co-the")
    def co_the(self, request):
        """Khách đã dùng món này (đơn hoàn tất) và còn lượt đánh giá chưa? GET ?mon_an=<id>"""
        try:
            mon_an_id = int(request.query_params.get("mon_an"))
        except (TypeError, ValueError):
            return Response({"detail": "Thiếu tham số mon_an."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"co_the": co_the_danh_gia_mon(request.user, mon_an_id)})

    def perform_create(self, serializer):
        danh_gia = serializer.save(nguoi_dung=self.request.user)
        self._cap_nhat_diem_mon(danh_gia.mon_an)
        dong_bo_tuong_tac_danh_gia(danh_gia.nguoi_dung_id, danh_gia.mon_an_id)

    def perform_update(self, serializer):
        user = self.request.user
        is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
        if serializer.instance.nguoi_dung_id != user.id and not is_staff:
            raise PermissionDenied("Bạn chỉ có thể sửa đánh giá của mình.")
        danh_gia = serializer.save()
        self._cap_nhat_diem_mon(danh_gia.mon_an)
        dong_bo_tuong_tac_danh_gia(danh_gia.nguoi_dung_id, danh_gia.mon_an_id)

    def perform_destroy(self, instance):
        user = self.request.user
        is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
        if instance.nguoi_dung_id != user.id and not is_staff:
            raise PermissionDenied("Bạn không có quyền xóa đánh giá này.")
        mon_an, chu_id = instance.mon_an, instance.nguoi_dung_id
        instance.delete()
        self._cap_nhat_diem_mon(mon_an)
        dong_bo_tuong_tac_danh_gia(chu_id, mon_an.id)
