from rest_framework import viewsets
from api.permissions import LaNhanVienHoacChiDoc, IsStaffOrReadOnly
from .models import DanhMucBaiViet, BaiViet, PostCategory, Post
from .serializers import DanhMucBaiVietSerializer, BaiVietSerializer, PostCategorySerializer, PostSerializer


class DanhMucBaiVietViewSet(viewsets.ModelViewSet):
    queryset = DanhMucBaiViet.objects.all()
    serializer_class = DanhMucBaiVietSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"


class BaiVietViewSet(viewsets.ModelViewSet):
    serializer_class = BaiVietSerializer
    permission_classes = [LaNhanVienHoacChiDoc]
    lookup_field = "duong_dan"

    def get_queryset(self):
        q = BaiViet.objects.select_related("danh_muc", "tac_gia").order_by("-dang_luc", "-tao_luc")
        user = self.request.user
        if not user.is_authenticated or not getattr(user, "la_nhan_vien_nha_hang", False):
            q = q.filter(trang_thai=BaiViet.TrangThai.DA_DANG)
        tim_kiem = self.request.query_params.get("tim_kiem") or self.request.query_params.get("search")
        if tim_kiem:
            q = q.filter(tieu_de__icontains=tim_kiem)
        return q

    def perform_create(self, serializer):
        serializer.save(tac_gia=self.request.user)


PostCategoryViewSet = DanhMucBaiVietViewSet
PostViewSet = BaiVietViewSet
