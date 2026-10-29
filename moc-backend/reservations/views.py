import uuid
import datetime
from datetime import timedelta
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from api.permissions import LaNhanVienHoacChiDoc, LaNhanVienNhaHang
from .models import BanAn, DatBan, ChinhSachDatCoc
from .serializers import BanAnSerializer, DatBanSerializer, ChinhSachCocSerializer
from .services import DichVuDatBan


class BanAnViewSet(viewsets.ModelViewSet):
    serializer_class = BanAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_permissions(self):
        """
        Public customers (guest or authenticated) must be allowed to temporarily hold a table,
        and list/retrieve tables.
        ModelViewSet modifications (create, update, destroy) remain restricted to staff.
        """
        if self.action in {"giu_ban", "giu_ban_hyphen", "list", "retrieve"}:
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
                    DatBan.TrangThai.CHO_XAC_NHAN,
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
        if self.action == "giu_ban_frontend":
            return [AllowAny()]
        if self.action == "chinh_sach_coc" and self.request.method == "GET":
            return [AllowAny()]
        if self.action == "chinh_sach_coc":
            return [LaNhanVienNhaHang()]
        if self.action in {"create", "huy_dat_ban", "cancel"}:
            return [IsAuthenticated()]
        if self.action == "trang_thai":
            return [LaNhanVienNhaHang()]
        if self.request.user.is_authenticated and getattr(self.request.user, "la_nhan_vien_nha_hang", False):
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

    @action(detail=False, methods=["get", "put"], permission_classes=[AllowAny])
    def chinh_sach_coc(self, request):
        chinh_sach = ChinhSachDatCoc.objects.prefetch_related("quy_tac_huy").filter(con_ap_dung=True)
        if request.query_params.get("branch"):
            chinh_sach = chinh_sach.filter(chi_nhanh_id=request.query_params["branch"])
        policy = chinh_sach.first()
        if request.method == "GET":
            if not policy:
                policy = ChinhSachDatCoc.objects.create(phan_tram_coc=20)
                from .models import QuyTacHuyDatCoc
                QuyTacHuyDatCoc.objects.bulk_create([
                    QuyTacHuyDatCoc(chinh_sach=policy, moc_thoi_gian="truoc_24h", phan_tram_hoan_tien=100),
                    QuyTacHuyDatCoc(chinh_sach=policy, moc_thoi_gian="tu_6_den_24h", phan_tram_hoan_tien=50),
                    QuyTacHuyDatCoc(chinh_sach=policy, moc_thoi_gian="trong_6h", phan_tram_hoan_tien=0),
                    QuyTacHuyDatCoc(chinh_sach=policy, moc_thoi_gian="khach_khong_den", phan_tram_hoan_tien=0),
                ])
            return Response(ChinhSachCocSerializer(policy).data)
        if not request.user.is_authenticated or not getattr(request.user, "la_nhan_vien_nha_hang", False):
            raise PermissionDenied()
        if not policy:
            policy = ChinhSachDatCoc.objects.create(phan_tram_coc=20)
        serializer = ChinhSachCocSerializer(policy, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        policy = serializer.save()
        if "rules" in request.data or "quy_tac_huy" in request.data:
            from .models import QuyTacHuyDatCoc
            rules = request.data.get("rules", request.data.get("quy_tac_huy", []))
            QuyTacHuyDatCoc.objects.filter(chinh_sach=policy).delete()
            for rule in rules:
                bucket = rule.get("time_milestone", rule.get("moc_thoi_gian"))
                pct = rule.get("refund_percentage", rule.get("phan_tram_hoan_tien", 0))
                QuyTacHuyDatCoc.objects.create(chinh_sach=policy, moc_thoi_gian=bucket, phan_tram_hoan_tien=pct)
        return Response(ChinhSachCocSerializer(policy).data)

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
        current = self.get_object()
        sent_version = request.data.get("version")
        if sent_version is not None and int(sent_version) != current.phien_ban:
            conflict = APIException("Đặt bàn đã được cập nhật bởi người khác. Hãy tải lại.")
            conflict.status_code = 409
            raise conflict
        dat_ban = DichVuDatBan.doi_trang_thai(
            current,
            request.data.get("status"),
            request.user
        )
        if dat_ban.trang_thai == DatBan.TrangThai.DA_HUY:
            dat_ban.huy_luc = timezone.now()
            dat_ban.ly_do_huy = str(request.data.get("reason", request.data.get("ghi_chu", "")))
            dat_ban.save(update_fields=["huy_luc", "ly_do_huy", "cap_nhat_luc"])
        return Response(self.get_serializer(dat_ban).data)

    @action(detail=True, methods=["post"], url_path="record-refund", permission_classes=[LaNhanVienNhaHang])
    def record_refund(self, request, pk=None):
        dat_ban = self.get_object()
        if dat_ban.trang_thai not in {DatBan.TrangThai.DA_HUY, DatBan.TrangThai.KHACH_KHONG_DEN}:
            raise ValidationError({"detail": "Chỉ ghi nhận hoàn cọc cho đặt bàn đã huỷ hoặc khách không đến."})
        if dat_ban.trang_thai_coc != DatBan.TrangThaiCoc.THANH_CONG or dat_ban.phieu_hoan_tien.exists():
            raise ValidationError({"detail": "Khoản cọc chưa thanh toán hoặc đã được xử lý."})
        percent = int(request.data.get("percent", 0))
        if not 0 <= percent <= 100:
            raise ValidationError({"percent": "Tỉ lệ hoàn phải từ 0 đến 100."})
        reference = str(request.data.get("reference", "")).strip()
        if percent > 0 and not reference:
            raise ValidationError({"reference": "Cần mã tham chiếu giao dịch chuyển khoản."})
        from payments.models import PhieuHoanTien, ThanhToan
        payment = dat_ban.danh_sach_thanh_toan.filter(loai_thanh_toan="tien_coc").order_by("-tao_luc").first()
        amount = round(float(dat_ban.so_tien_coc) * percent / 100, 2)
        bucket = request.data.get("bucket")
        bucket = {">24h": "truoc_24h", "6-24h": "tu_6_den_24h", "<6h": "trong_6h", "no_show": "khach_khong_den"}.get(bucket)
        if not bucket:
            if dat_ban.trang_thai == DatBan.TrangThai.KHACH_KHONG_DEN:
                bucket = "khach_khong_den"
            else:
                canceled_at = dat_ban.huy_luc or timezone.now()
                hours = (timezone.make_aware(datetime.datetime.combine(dat_ban.ngay_dat, dat_ban.gio_bat_dau)) - canceled_at).total_seconds() / 3600
                bucket = "truoc_24h" if hours > 24 else "tu_6_den_24h" if hours >= 6 else "trong_6h"
        hours_before = max(0, (timezone.make_aware(datetime.datetime.combine(dat_ban.ngay_dat, dat_ban.gio_bat_dau)) - (dat_ban.huy_luc or timezone.now())).total_seconds() / 3600)
        PhieuHoanTien.objects.create(dat_ban=dat_ban, thanh_toan=payment, so_tien_coc_goc=dat_ban.so_tien_coc,
            phan_tram_hoan=percent, so_tien_hoan=amount, so_tien_phat=float(dat_ban.so_tien_coc)-amount,
            moc_thoi_gian=bucket, so_gio_truoc_gio_hen=hours_before, ly_do_huy=dat_ban.ly_do_huy,
            trang_thai="da_hoan_tien" if percent == 100 else "hoan_tien_mot_phan" if percent else "that_bai",
            phuong_thuc_hoan="chuyen_khoan", du_lieu_chi_tiet={"reference": reference, "note": request.data.get("note", ""), "verified_by": request.user.get_full_name() or request.user.username})
        dat_ban.trang_thai_coc = "da_hoan_tien" if percent == 100 else "hoan_tien_mot_phan" if percent else dat_ban.trang_thai_coc
        dat_ban.phien_ban += 1
        dat_ban.save(update_fields=["trang_thai_coc", "phien_ban", "cap_nhat_luc"])
        return Response(self.get_serializer(dat_ban).data)

    @action(detail=False, methods=["get"], url_path="khung-gio-trong", permission_classes=[AllowAny])
    def khung_gio_trong(self, request):
        """
        Trả về danh sách khung giờ theo lưới 15 phút trong khoảng 10:00-22:00.
        Mỗi slot có trạng thái: con_trong (True/False) dựa vào sức chứa chi nhánh.
        Query params: chi_nhanh_id, ngay (YYYY-MM-DD), so_khach
        """
        from branches.models import ChiNhanh

        chi_nhanh_id = request.query_params.get("chi_nhanh_id") or request.query_params.get("chi_nhanh")
        ngay_str = request.query_params.get("ngay") or request.query_params.get("date")
        so_khach = int(request.query_params.get("so_khach", 1))

        if not chi_nhanh_id or not ngay_str:
            return Response({"detail": "Cần cung cấp chi_nhanh_id và ngay."}, status=400)

        try:
            chi_nhanh = ChiNhanh.objects.get(id=chi_nhanh_id)
        except ChiNhanh.DoesNotExist:
            return Response({"detail": "Chi nhánh không tồn tại."}, status=404)

        ngay = parse_date(ngay_str)
        if not ngay:
            return Response({"detail": "Ngày không hợp lệ. Dùng định dạng YYYY-MM-DD."}, status=400)

        # Tính sức chứa chi nhánh dựa trên danh sách bàn
        suc_chua_chi_nhanh = (
            chi_nhanh.danh_sach_ban.aggregate(tong=models.Sum("suc_chua"))["tong"] or 100
        )
        if chi_nhanh.danh_sach_ban.count() == 0:
            suc_chua_chi_nhanh = 0

        # Lấy danh sách đặt bàn đã xác nhận trong ngày
        dat_ban_trong_ngay = list(DatBan.objects.filter(
            chi_nhanh=chi_nhanh,
            ngay_dat=ngay,
            trang_thai__in=["cho_xac_nhan", "da_xac_nhan", "da_xep_ban", "dang_phuc_vu",
                            DatBan.TrangThai.CHO_XAC_NHAN, DatBan.TrangThai.CHO_THANH_TOAN, DatBan.TrangThai.DA_XAC_NHAN,
                            DatBan.TrangThai.KHACH_DA_DEN],
        ))

        thoi_gian_phuc_vu = datetime.timedelta(hours=2)

        # Build slot grid 10:00-22:00 step 15 phút
        slots = []
        now_local = timezone.localtime().replace(tzinfo=None)
        current = datetime.time(10, 0)
        end_time = datetime.time(22, 0)

        while current <= end_time:
            current_dt = datetime.datetime.combine(ngay, current)
            end_dt = current_dt + thoi_gian_phuc_vu

            # Tính số khách đang dùng bữa tại slot này
            so_khach_trong_slot = 0
            for db in dat_ban_trong_ngay:
                try:
                    gio = db.gio_bat_dau
                    if hasattr(gio, "hour"):
                        start = datetime.datetime.combine(ngay, gio)
                    else:
                        parts = str(gio)[:5].split(":")
                        start = datetime.datetime.combine(ngay, datetime.time(int(parts[0]), int(parts[1])))
                    end_s = start + thoi_gian_phuc_vu
                    if start < end_dt and end_s > current_dt:
                        so_khach_trong_slot += db.so_luong_khach
                except Exception:
                    pass

            con_trong = current_dt > now_local and (suc_chua_chi_nhanh - so_khach_trong_slot) >= so_khach

            slots.append({
                "khung_gio": current.strftime("%H:%M"),
                "con_trong": con_trong,
                "so_khach_hien_tai": so_khach_trong_slot,
                "suc_chua_toi_da": suc_chua_chi_nhanh,
            })

            # Next slot +15 min
            dt = datetime.datetime.combine(ngay, current) + datetime.timedelta(minutes=15)
            current = dt.time()

        return Response({
            "chi_nhanh_id": chi_nhanh.id,
            "ten_chi_nhanh": chi_nhanh.ten,
            "ngay": ngay_str,
            "slots": slots,
        })


# Backward-compatible viewset aliases
TableViewSet = BanAnViewSet
ReservationViewSet = DatBanViewSet

