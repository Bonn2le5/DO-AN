from django.utils import timezone
from django.db.models import Count, F, OuterRef, Q, Subquery
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from api.permissions import LaNhanVienNhaHang
from rest_framework.response import Response
from .models import HoiThoai, TinNhan, ChatRoom, ChatMessage
from .serializers import (
    HoiThoaiSerializer,
    HoiThoaiListSerializer,
    TinNhanSerializer,
    ChatRoomSerializer,
    ChatMessageSerializer,
)
from .services import (
    broadcast_message, broadcast_read, save_message, serialize_message, is_staff_user,
)


class HoiThoaiViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return HoiThoaiListSerializer if self.action == "list" else HoiThoaiSerializer

    def get_permissions(self):
        if self.request.user.is_authenticated and getattr(self.request.user, "la_nhan_vien_nha_hang", False):
            return [LaNhanVienNhaHang()]
        return super().get_permissions()

    def get_queryset(self):
        q = HoiThoai.objects.select_related("khach_hang")
        user = self.request.user
        if not is_staff_user(user):
            return q.filter(khach_hang=user)
        if self.action == "list":
            last = TinNhan.objects.filter(hoi_thoai=OuterRef("pk")).order_by("-id")
            q = q.annotate(
                unread_count=Count("danh_sach_tin_nhan", filter=Q(
                    danh_sach_tin_nhan__da_doc=False,
                    danh_sach_tin_nhan__nguoi_gui_id=F("khach_hang_id"),
                )),
                last_message=Subquery(last.values("noi_dung")[:1]),
            ).order_by(F("tin_nhan_cuoi_luc").desc(nulls_last=True))
        return q

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
        return self.messages(request, pk=pk)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        room = self.get_object()
        if request.method == "POST":
            ser = TinNhanSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            data = ser.validated_data
            text = (data.get("noi_dung") or "").strip()
            if not text:
                return Response({"noi_dung": ["Nội dung trống."]}, status=400)
            room, payload = save_message(
                room_id=room.id, user=request.user, text=text[:5000],
                msg_type=data.get("loai_tin_nhan") or "van_ban",
                client_id=request.data.get("client_id"),
            )
            broadcast_message(room, payload)
            return Response(payload, status=201)

        qs = room.danh_sach_tin_nhan.select_related("nguoi_gui")
        if request.query_params.get("after_id"):
            qs = qs.filter(id__gt=request.query_params["after_id"]).order_by("id")[:200]
            return Response([serialize_message(m) for m in qs])
        if request.query_params.get("before_id"):
            qs = qs.filter(id__lt=request.query_params["before_id"])
        items = list(qs.order_by("-id")[:50])[::-1]
        return Response([serialize_message(m) for m in items])

    @action(detail=True, methods=["post"], url_path="mark_read")
    def mark_read(self, request, pk=None):
        room = self.get_object()
        room.danh_sach_tin_nhan.filter(da_doc=False).exclude(nguoi_gui=request.user).update(da_doc=True, doc_luc=timezone.now())
        broadcast_read(room, request.user)
        return Response({"ok": True})


ChatRoomViewSet = HoiThoaiViewSet
