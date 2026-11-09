from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from foods.models import MonAn
from .models import TuongTacMonAn, GoiYMonAn, SuKienGoiY, FoodInteraction, Recommendation
from .serializers import (
    TuongTacMonAnSerializer,
    GoiYMonAnSerializer,
    SuKienGoiYSerializer,
    InteractionSerializer,
    RecommendationSerializer,
)
from .services import DichVuGoiY, RecommendationService


class TuongTacMonAnViewSet(viewsets.ModelViewSet):
    """
    ViewSet xử lý ghi nhận tương tác món ăn của người dùng (xem, yêu thích, thêm giỏ, đặt món, đánh giá).
    Tự động vô hiệu hóa cache gợi ý cũ để tái tính toán khẩu vị mới.
    """
    serializer_class = TuongTacMonAnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TuongTacMonAn.objects.filter(nguoi_dung=self.request.user).order_by("-tao_luc")

    def perform_create(self, serializer):
        serializer.save(nguoi_dung=self.request.user)
        # Xóa cache gợi ý cũ của người dùng này để lượt truy vấn kế tiếp tính toán theo khẩu vị mới
        GoiYMonAn.objects.filter(nguoi_dung=self.request.user).delete()


class GoiYMonAnViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet cung cấp danh sách gợi ý món ăn (AI Recommender).
    Hỗ trợ cả khách vãng lai (AllowAny) qua Cold-Start Popularity
    và người dùng đăng nhập qua Content-Based Filtering (TF-IDF + Cosine).
    """
    queryset = GoiYMonAn.objects.all()
    serializer_class = GoiYMonAnSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user and user.is_authenticated:
            return (
                GoiYMonAn.objects.filter(nguoi_dung=user)
                .select_related("mon_an", "mon_an__danh_muc")
                .prefetch_related("mon_an__the_mon_an")
                .order_by("thu_hang", "-diem_tuong_dong")
            )
        return GoiYMonAn.objects.none()

    def get_limit(self):
        try:
            return int(
                self.request.query_params.get("limit")
                or self.request.query_params.get("gioi_han")
                or 6
            )
        except (ValueError, TypeError):
            return 6

    def list(self, request, *args, **kwargs):
        user = request.user
        limit = self.get_limit()
        is_refresh = (
            request.query_params.get("refresh", "").lower() in ("true", "1")
            or request.query_params.get("lam_moi", "").lower() in ("true", "1")
        )

        # Trường hợp 1: Khách vãng lai chưa đăng nhập
        if not user or not user.is_authenticated:
            items = DichVuGoiY.lay_goi_y_khach_vang_lai(gioi_han=limit)
            serializer = self.get_serializer(items, many=True)
            return Response(serializer.data)

        # Trường hợp 2: Người dùng đã đăng nhập -> Kiểm tra cache DB trước
        if not is_refresh:
            cached_qs = (
                GoiYMonAn.objects.filter(nguoi_dung=user)
                .select_related("mon_an", "mon_an__danh_muc")
                .prefetch_related("mon_an__the_mon_an")
                .order_by("thu_hang", "-diem_tuong_dong")
            )
            if cached_qs.exists():
                serializer = self.get_serializer(cached_qs[:limit], many=True)
                return Response(serializer.data)

        # Trường hợp 3: Chưa có cache hoặc yêu cầu làm mới (?refresh=true)
        items = DichVuGoiY.cap_nhat_goi_y(user, gioi_han=limit)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post", "get"], permission_classes=[IsAuthenticated])
    def refresh(self, request):
        """Bắt buộc tính toán lại gợi ý mới và cập nhật cache cho user."""
        limit = self.get_limit()
        items = DichVuGoiY.cap_nhat_goi_y(request.user, gioi_han=limit)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post", "get"], url_path="lam-moi", permission_classes=[IsAuthenticated])
    def lam_moi(self, request):
        """Alias tiếng Việt cho refresh action."""
        return self.refresh(request)

    @action(detail=False, methods=["get"], url_path="tuong-tu", permission_classes=[AllowAny])
    def tuong_tu(self, request):
        """Món tương tự (Item-to-Item TF-IDF): GET ?mon_an=<id>&limit=3"""
        try:
            mon_an_id = int(request.query_params.get("mon_an"))
        except (TypeError, ValueError):
            return Response({"detail": "Thiếu tham số mon_an."}, status=status.HTTP_400_BAD_REQUEST)
        items = DichVuGoiY.mon_tuong_tu(mon_an_id, gioi_han=min(self.get_limit(), 12))
        return Response(self.get_serializer(items, many=True).data)

    @action(detail=False, methods=["post"], url_path="su-kien", permission_classes=[AllowAny])
    def su_kien(self, request):
        """
        Ghi nhận hiển thị / nhấp món được gợi ý để đo CTR & Conversion.
        Body: {"loai_su_kien": "hien_thi"|"nhap", "vi_tri": "...", "mon_an_ids": [..], "phien_ban_model": ".."}
        """
        serializer = SuKienGoiYSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user and request.user.is_authenticated else None
        d = serializer.validated_data
        ids = list(MonAn.objects.filter(id__in=set(d["mon_an_ids"])).values_list("id", flat=True))
        SuKienGoiY.objects.bulk_create([
            SuKienGoiY(
                nguoi_dung=user,
                mon_an_id=mid,
                loai_su_kien=d["loai_su_kien"],
                vi_tri=d["vi_tri"],
                phien_ban_model=d.get("phien_ban_model", ""),
            )
            for mid in ids
        ])
        return Response({"da_ghi": len(ids)}, status=status.HTTP_201_CREATED)


InteractionViewSet = TuongTacMonAnViewSet
RecommendationViewSet = GoiYMonAnViewSet
