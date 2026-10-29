from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from api.permissions import LaNhanVienNhaHang
from rest_framework.response import Response
from .models import HoiThoai, TinNhan, ChatRoom, ChatMessage
from .serializers import (
    HoiThoaiSerializer,
    TinNhanSerializer,
    ChatRoomSerializer,
    ChatMessageSerializer,
)


class HoiThoaiViewSet(viewsets.ModelViewSet):
    serializer_class = HoiThoaiSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.user.is_authenticated and getattr(self.request.user, "la_nhan_vien_nha_hang", False):
            return [LaNhanVienNhaHang()]
        return super().get_permissions()

    def get_queryset(self):
        q = HoiThoai.objects.prefetch_related("danh_sach_tin_nhan")
        user = self.request.user
        is_staff = user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)
        return q if is_staff else q.filter(khach_hang=user)

    def perform_create(self, serializer):
        serializer.save(khach_hang=self.request.user)

    @action(detail=False, methods=["get"])
    def active(self, request):
        """
        Retrieves the active open conversation for the requesting customer,
        or creates a new open conversation if none exists.
        """
        user = request.user
        room = (
            HoiThoai.objects.filter(khach_hang=user, trang_thai=HoiThoai.TrangThai.MO)
            .order_by("-cap_nhat_luc")
            .first()
        )
        if not room:
            room = HoiThoai.objects.create(khach_hang=user, trang_thai=HoiThoai.TrangThai.MO)
        return Response(self.get_serializer(room).data)

    @action(detail=True, methods=["post"])
    def gui_tin_nhan(self, request, pk=None):
        room = self.get_object()
        serializer = TinNhanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(hoi_thoai=room, nguoi_gui=request.user)
        room.tin_nhan_cuoi_luc = timezone.now()
        room.save(update_fields=["tin_nhan_cuoi_luc", "cap_nhat_luc"])
        return Response(TinNhanSerializer(message).data, status=201)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        if request.method.lower() == "post":
            return self.gui_tin_nhan(request, pk=pk)
        room = self.get_object()
        tin_nhan_list = room.danh_sach_tin_nhan.order_by("tao_luc")
        return Response(TinNhanSerializer(tin_nhan_list, many=True).data)

    @action(detail=True, methods=["post"], url_path="mark_read")
    def mark_read(self, request, pk=None):
        room = self.get_object()
        room.danh_sach_tin_nhan.filter(da_doc=False).exclude(nguoi_gui=request.user).update(da_doc=True, doc_luc=timezone.now())
        return Response(self.get_serializer(room).data)


ChatRoomViewSet = HoiThoaiViewSet
