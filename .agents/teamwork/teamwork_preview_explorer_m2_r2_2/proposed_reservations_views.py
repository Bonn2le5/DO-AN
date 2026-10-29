import uuid
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from api.permissions import LaNhanVienHoacChiDoc, LaNhanVienNhaHang
from .models import BanAn, DatBan, ChinhSachDatCoc
from .serializers import BanAnSerializer, DatBanSerializer, ChinhSachCocSerializer
from .services import DichVuDatBan


class BanAnViewSet(viewsets.ModelViewSet):
    serializer_class = BanAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_permissions(self):
        """
        Public customers (guest or authenticated) must be allowed to temporarily hold a table.
        ModelViewSet standard modifications remain restricted to staff.
        """
        if self.action in {"giu_ban", "giu_ban_hyphen"}:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        danh_sach = BanAn.objects.select_related("chi_nhanh")
        tham_so = self.request.query_params
        if tham_so.get("chi_nhanh"):
            danh_sach = danh_sach.filter(chi_nhanh_id=tham_so["chi_nhanh"])
        if tham_so.get("guest_count"):
            danh_sach = danh_sach.filter(suc_chua__gte=int(tham_so["guest_count"]))
        if tham_so.get("reservation_date") and tham_so.get("start_time"):
            ban_da_dat = DatBan.objects.filter(
                ngay_dat=tham_so["reservation_date"],
                gio_bat_dau=tham_so["start_time"],
                trang_thai__in=[
                    DatBan.TrangThai.CHO_THANH_TOAN,
                    DatBan.TrangThai.DA_XAC_NHAN,
                    DatBan.TrangThai.KHACH_DA_DEN
                ]
            ).values_list("ban_an_id", flat=True)
            danh_sach = danh_sach.exclude(id__in=ban_da_dat)
        return danh_sach

    @action(detail=True, methods=["post"], url_path="giu_ban", permission_classes=[AllowAny])
    def giu_ban(self, request, pk=None):
        return self._xu_ly_giu_ban(request, ban_id=pk)

    @action(detail=True, methods=["post"], url_path="giu-ban", permission_classes=[AllowAny])
    def giu_ban_hyphen(self, request, pk=None):
        return self._xu_ly_giu_ban(request, ban_id=pk)

    def _xu_ly_giu_ban(self, request, ban_id):
        ngay = request.data.get("ngay") or request.data.get("ngay_dat") or request.data.get("date")
        gio = request.data.get("gio") or request.data.get("gio_bat_dau") or request.data.get("time")
        so_khach = request.data.get("so_luong_khach") or request.data.get("guest_count") or request.data.get("guests")

        if not ngay or not gio or not so_khach:
            return Response(
                {"detail": "Thiếu thông tin ngày, giờ hoặc số lượng khách.", "code": "THIEU_THONG_TIN"},
                status=400
            )

        thanh_cong, ket_qua = DichVuDatBan.giu_ban_tam_thoi(
            ban_id=ban_id, ngay=ngay, gio=gio, so_khach=so_khach
        )
        if not thanh_cong:
            return Response(ket_qua, status=409)

        return Response(ket_qua, status=200)


class DatBanViewSet(viewsets.ModelViewSet):
    serializer_class = DatBanSerializer

    def get_queryset(self):
        danh_sach = DatBan.objects.select_related("ban_an", "chi_nhanh", "nguoi_dung").prefetch_related("danh_sach_mon__mon_an").order_by("-tao_luc")
        return danh_sach if self.request.user.is_authenticated and self.request.user.la_nhan_vien_nha_hang else danh_sach.filter(nguoi_dung=self.request.user)

    def get_permissions(self):
        if self.action in {"giu_ban_frontend", "chinh_sach_coc"}:
            return [AllowAny()]
        if self.action in {"create", "huy_dat_ban", "cancel"}:
            return [IsAuthenticated()]
        if self.action == "trang_thai":
            return [LaNhanVienNhaHang()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dat_ban = DichVuDatBan.tao_dat_ban(nguoi_dung=request.user, du_lieu=serializer.validated_data)
        return Response(self.get_serializer(dat_ban).data, status=201)

    @action(detail=False, methods=["post"], url_path="giu-ban", permission_classes=[AllowAny])
    def giu_ban_frontend(self, request):
        """Hỗ trợ trực tiếp cho fetch('/api/dat-ban/giu-ban/') từ frontend"""
        ban_id = request.data.get("ban_an_id") or request.data.get("idBan") or request.data.get("table_id")
        ngay = request.data.get("ngay") or request.data.get("ngay_dat") or request.data.get("date")
        gio = request.data.get("gio") or request.data.get("gio_bat_dau") or request.data.get("time")
        so_khach = request.data.get("so_luong_khach") or request.data.get("guest_count") or request.data.get("guests")

        if not ban_id or not ngay or not gio or not so_khach:
            return Response(
                {"detail": "Thiếu thông tin bàn, ngày, giờ hoặc số lượng khách.", "code": "THIEU_THONG_TIN"},
                status=400
            )

        thanh_cong, ket_qua = DichVuDatBan.giu_ban_tam_thoi(
            ban_id=ban_id, ngay=ngay, gio=gio, so_khach=so_khach
        )
        if not thanh_cong:
            return Response(ket_qua, status=409)
        return Response(ket_qua, status=200)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def chinh_sach_coc(self, request):
        chinh_sach = ChinhSachDatCoc.objects.prefetch_related("quy_tac_huy").filter(con_ap_dung=True)
        if request.query_params.get("branch"):
            chinh_sach = chinh_sach.filter(chi_nhanh_id=request.query_params["branch"])
        return Response(ChinhSachCocSerializer(chinh_sach.first()).data if chinh_sach.first() else None)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def huy_dat_ban(self, request, pk=None):
        dat_ban = self.get_object()
        if dat_ban.nguoi_dung_id != request.user.id and not getattr(request.user, "la_nhan_vien_nha_hang", False):
            return Response({"chi_tiet": "Không có quyền hủy đặt bàn này."}, status=403)

        if dat_ban.trang_thai in [DatBan.TrangThai.DA_HUY, DatBan.TrangThai.HOAN_TAT]:
            return Response(
                {"chi_tiet": f"Đặt bàn này đã ở trạng thái {dat_ban.get_trang_thai_display()}."},
                status=400
            )

        from payments.services import RefundService
        ly_do = request.data.get("ly_do") or request.data.get("reason", "Khách hàng yêu cầu hủy")
        is_staff = getattr(request.user, "la_nhan_vien_nha_hang", False) or getattr(request.user, "is_staff", False)
        is_no_show = bool(request.data.get("is_no_show", False)) and is_staff

        result = RefundService.process_cancellation_and_refund(
            dat_ban=dat_ban,
            user=request.user,
            ly_do=ly_do,
            is_no_show=is_no_show,
        )
        result["dat_ban"] = self.get_serializer(dat_ban).data
        return Response(result)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        return self.huy_dat_ban(request, pk=pk)

    @action(detail=True, methods=["patch"], permission_classes=[LaNhanVienNhaHang])
    def trang_thai(self, request, pk=None):
        dat_ban = DichVuDatBan.doi_trang_thai(
            self.get_object(),
            request.data.get("status"),
            request.user
        )
        return Response(self.get_serializer(dat_ban).data)


# Backward-compatible viewset aliases
TableViewSet = BanAnViewSet
ReservationViewSet = DatBanViewSet
