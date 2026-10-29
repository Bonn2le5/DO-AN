from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import GioHang, ChiTietGioHang, Cart, CartItem
from .serializers import GioHangSerializer, ChiTietGioHangSerializer, CartSerializer, CartItemSerializer


class GioHangViewSet(viewsets.GenericViewSet):
    serializer_class = GioHangSerializer
    permission_classes = [IsAuthenticated]

    def _cart(self):
        gio_hang, _ = GioHang.objects.prefetch_related("danh_sach_mon__mon_an").get_or_create(
            nguoi_dung=self.request.user,
            trang_thai=GioHang.TrangThai.DANG_SU_DUNG
        )
        return gio_hang

    def list(self, request):
        return Response(self.get_serializer(self._cart()).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        serializer = ChiTietGioHangSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = self._cart()
        mon_an = serializer.validated_data["mon_an"]
        so_luong = serializer.validated_data.get("so_luong", 1)
        ghi_chu = serializer.validated_data.get("ghi_chu", "")

        item, created = ChiTietGioHang.objects.get_or_create(
            gio_hang=cart,
            mon_an=mon_an,
            defaults={
                "so_luong": so_luong,
                "don_gia_luc_dat": mon_an.don_gia,
                "ghi_chu": ghi_chu,
            }
        )
        if not created:
            item.so_luong += so_luong
            item.save(update_fields=["so_luong", "cap_nhat_luc"])

        return Response(ChiTietGioHangSerializer(item).data, status=201 if created else 200)

    @action(detail=False, methods=["patch", "delete"], url_path=r"items/(?P<item_id>[^/.]+)")
    def item(self, request, item_id=None):
        cart = self._cart()
        item = cart.danh_sach_mon.get(pk=item_id)
        if request.method == "DELETE":
            item.delete()
            return Response(status=204)
        serializer = ChiTietGioHangSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


CartViewSet = GioHangViewSet
