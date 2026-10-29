from django.utils import timezone
from rest_framework import viewsets
from api.permissions import LaNhanVienHoacChiDoc, LaNhanVienNhaHang, IsStaffOrReadOnly, IsRestaurantStaff
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai, Promotion, PromotionCode, PromotionUsage
from .serializers import (
    KhuyenMaiSerializer, MaKhuyenMaiSerializer, LichSuDungKhuyenMaiSerializer,
    PromotionSerializer, PromotionCodeSerializer, PromotionUsageSerializer
)


class KhuyenMaiViewSet(viewsets.ModelViewSet):
    serializer_class = KhuyenMaiSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_queryset(self):
        q = KhuyenMai.objects.prefetch_related("danh_sach_ma")
        if self.request.query_params.get("active") or self.request.query_params.get("con_han"):
            now = timezone.now()
            q = q.filter(con_hoat_dong=True, bat_dau_luc__lte=now, ket_thuc_luc__gte=now)
        return q


class MaKhuyenMaiViewSet(viewsets.ModelViewSet):
    queryset = MaKhuyenMai.objects.select_related("khuyen_mai")
    serializer_class = MaKhuyenMaiSerializer
    permission_classes = [LaNhanVienHoacChiDoc]


class LichSuDungKhuyenMaiViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LichSuDungKhuyenMaiSerializer
    permission_classes = [LaNhanVienNhaHang]
    queryset = LichSuDungKhuyenMai.objects.select_related("khuyen_mai", "nguoi_dung", "don_hang")


PromotionViewSet = KhuyenMaiViewSet
PromotionCodeViewSet = MaKhuyenMaiViewSet
PromotionUsageViewSet = LichSuDungKhuyenMaiViewSet
