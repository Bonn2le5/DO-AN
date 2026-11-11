from rest_framework import serializers, viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from api.throttling import ChoQuaKhiCacheLoi

from foods.models import MonAn
from .models import TuongTacMonAn, GoiYMonAn, SuKienGoiY
from .serializers import TuongTacMonAnSerializer, GoiYMonAnSerializer, SuKienGoiYSerializer
from .services import DichVuGoiY
from .tro_ly import GOI_Y_NHANH, TroLyKhongSanSang, goi_y_thuc_don


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
        d = serializer.validated_data
        if d["loai_tuong_tac"] == TuongTacMonAn.LoaiTuongTac.YEU_THICH:
            # Yêu thích là trạng thái bật/tắt: mỗi khách chỉ có 1 bản ghi cho 1 món
            cu = TuongTacMonAn.objects.filter(
                nguoi_dung=self.request.user, mon_an=d["mon_an"],
                loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.YEU_THICH,
            ).first()
            if cu is not None:
                serializer.instance = cu
                return
        serializer.save(nguoi_dung=self.request.user)
        # Xóa cache gợi ý cũ của người dùng này để lượt truy vấn kế tiếp tính toán theo khẩu vị mới
        GoiYMonAn.objects.filter(nguoi_dung=self.request.user).delete()

    @action(detail=False, methods=["post"], url_path="bo-yeu-thich")
    def bo_yeu_thich(self, request):
        """Bỏ yêu thích: xoá tín hiệu 'yeu_thich' của khách với món. Body: {"mon_an": id}"""
        try:
            mon_an_id = int(request.data.get("mon_an"))
        except (TypeError, ValueError):
            return Response({"detail": "Thiếu tham số mon_an."}, status=status.HTTP_400_BAD_REQUEST)
        # QuerySet.delete() vẫn bắn post_delete → signal tự xoá cache gợi ý
        so_xoa, _ = TuongTacMonAn.objects.filter(
            nguoi_dung=request.user, mon_an_id=mon_an_id,
            loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.YEU_THICH,
        ).delete()
        return Response({"da_xoa": so_xoa})


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
            limit = int(
                self.request.query_params.get("limit")
                or self.request.query_params.get("gioi_han")
                or 6
            )
        except (ValueError, TypeError):
            return 6
        return max(1, min(limit, 24))

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
            # Bỏ món đã hết hàng / bị ẩn sau lúc tính cache
            cached = list(
                GoiYMonAn.objects.filter(
                    nguoi_dung=user, mon_an__con_hang=True, mon_an__hien_thi=True
                )
                .select_related("mon_an", "mon_an__danh_muc")
                .prefetch_related("mon_an__the_mon_an")
                .order_by("thu_hang", "-diem_tuong_dong")[:limit]
            )
            # Cache đủ số món yêu cầu mới dùng; thiếu (món hết hàng, limit lớn hơn lúc tính) → tính lại
            if len(cached) >= limit:
                serializer = self.get_serializer(cached, many=True)
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


class TroLyGoiMonSerializer(serializers.Serializer):
    yeu_cau = serializers.CharField(max_length=500, trim_whitespace=True)
    dieu_chinh = serializers.ListField(
        child=serializers.CharField(max_length=300), required=False, default=list, max_length=10
    )
    so_nguoi = serializers.IntegerField(min_value=1, max_value=20, required=False)
    goi_y_nhanh = serializers.ChoiceField(choices=list(GOI_Y_NHANH), required=False)


class GioiHanTroLy(ChoQuaKhiCacheLoi, SimpleRateThrottle):
    """API mở cho khách chưa đăng nhập và mỗi câu hỏi tốn tiền gọi AI → chặn gọi dồn dập.
    Tính theo tài khoản nếu đã đăng nhập, còn lại theo IP."""
    scope = "tro_ly"
    rate = "20/min"

    def get_cache_key(self, request, view):
        nd = request.user
        dinh_danh = f"nd{nd.pk}" if nd and nd.is_authenticated else self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": dinh_danh}


class TroLyGoiMonView(APIView):
    """
    Trợ lý gọi món AI: POST {"yeu_cau": "...", "dieu_chinh": ["bớt cay"], "so_nguoi": 4}
    → JSON ý định + thực đơn chọn từ database theo nhóm món, số lượng, tổng tiền.
    "dieu_chinh": các lần điều chỉnh sau, ý nói sau ghi đè ý nói trước. AI lỗi/chưa cấu hình → 503.
    """
    permission_classes = [AllowAny]
    throttle_classes = [GioiHanTroLy]

    def post(self, request):
        ser = TroLyGoiMonSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        try:
            return Response(goi_y_thuc_don(
                d["yeu_cau"], d["dieu_chinh"], request.user, d.get("so_nguoi"), d.get("goi_y_nhanh")
            ))
        except TroLyKhongSanSang:
            return Response(
                {"detail": "Trợ lý AI đang bận, bạn thử lại sau ít phút nhé."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
