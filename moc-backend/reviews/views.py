from django.db.models import Avg, Count
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.permissions import LaNhanVienNhaHang
from rest_framework.exceptions import PermissionDenied
from .models import DanhGia, Review
from .serializers import DanhGiaSerializer, ReviewSerializer
from recommendations.models import TuongTacMonAn, FoodInteraction


class DanhGiaViewSet(viewsets.ModelViewSet):
    serializer_class = DanhGiaSerializer

    def get_permissions(self):
        if self.request.user.is_authenticated and getattr(self.request.user, "la_nhan_vien_nha_hang", False):
            return [LaNhanVienNhaHang()]
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        q = DanhGia.objects.select_related(
            "nguoi_dung", "mon_an", "don_hang", "chi_tiet_don_hang"
        )
        user = self.request.user
        is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
        if not is_staff:
            q = q.filter(hien_thi=True)
        food_id = self.request.query_params.get("food") or self.request.query_params.get("mon_an")
        if food_id:
            q = q.filter(mon_an_id=food_id)
        return q

    def _cap_nhat_diem_mon(self, mon_an):
        ket_qua = mon_an.danh_sach_danh_gia.filter(hien_thi=True).aggregate(
            rating=Avg("diem_danh_gia"), count=Count("id")
        )
        mon_an.diem_danh_gia = ket_qua["rating"] or 0
        mon_an.so_luot_danh_gia = ket_qua["count"] or 0
        mon_an.save(update_fields=["diem_danh_gia", "so_luot_danh_gia", "cap_nhat_luc"])

    def perform_create(self, serializer):
        danh_gia = serializer.save(nguoi_dung=self.request.user)
        self._cap_nhat_diem_mon(danh_gia.mon_an)
        TuongTacMonAn.objects.create(
            nguoi_dung=self.request.user,
            mon_an=danh_gia.mon_an,
            loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DANH_GIA,
            trong_so=5
        )

    def perform_update(self, serializer):
        user = self.request.user
        is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
        if serializer.instance.nguoi_dung_id != user.id and not is_staff:
            raise PermissionDenied("Bạn chỉ có thể sửa đánh giá của mình.")
        danh_gia = serializer.save()
        self._cap_nhat_diem_mon(danh_gia.mon_an)

    def perform_destroy(self, instance):
        user = self.request.user
        is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
        if instance.nguoi_dung_id != user.id and not is_staff:
            raise PermissionDenied("Bạn không có quyền xóa đánh giá này.")
        mon_an = instance.mon_an
        instance.delete()
        self._cap_nhat_diem_mon(mon_an)


ReviewViewSet = DanhGiaViewSet

