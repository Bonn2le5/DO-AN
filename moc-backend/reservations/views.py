import uuid
import datetime
from datetime import timedelta
from zoneinfo import ZoneInfo
from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from api.permissions import LaNhanVienHoacChiDoc, LaNhanVienNhaHang
from .models import BanAn, DatBan, ChinhSachDatCoc, PhongRieng, PhienPhucVu
from .serializers import (
    BanAnSerializer, DatBanSerializer, ChinhSachCocSerializer, PhongRiengSerializer,
    PhienPhucVuSerializer, WalkInSerializer, XepBanSerializer,
    DanhSachMonPhienSerializer, CheckOutPhienSerializer,
)
from .services import DichVuDatBan, DichVuPhienPhucVu, tinh_suc_chua_con_lai


class BanAnViewSet(viewsets.ModelViewSet):
    serializer_class = BanAnSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_permissions(self):
        """
        Public customers may list/retrieve tables. Mutations remain restricted to staff.
        ModelViewSet modifications (create, update, destroy) remain restricted to staff.
        """
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        danh_sach = BanAn.objects.select_related("chi_nhanh", "phong_rieng")
        user = self.request.user
        is_staff = user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))
        if self.request.query_params.get("include_archived") != "true" or not is_staff:
            danh_sach = danh_sach.filter(da_luu_tru=False)
        if is_staff:
            if not (user.is_superuser or getattr(user, "la_quan_tri_vien", False)):
                branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
                if not branch_id:
                    return danh_sach.none()
                danh_sach = danh_sach.filter(chi_nhanh_id=branch_id)
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

    def perform_create(self, serializer):
        user = self.request.user
        if not (user.is_superuser or getattr(user, "la_quan_tri_vien", False)):
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            if not branch_id or serializer.validated_data.get("chi_nhanh").id != branch_id:
                raise PermissionDenied("Bạn chỉ được thêm bàn vào chi nhánh được phân công.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        table = self.get_object()
        requested_status = serializer.validated_data.get("trang_thai")
        if requested_status in {BanAn.TrangThai.DANG_PHUC_VU, BanAn.TrangThai.CHO_DON}:
            raise ValidationError({"trang_thai": "Trạng thái đang phục vụ và chờ dọn được cập nhật qua phiên phục vụ."})
        if table.trang_thai in {BanAn.TrangThai.DANG_PHUC_VU, BanAn.TrangThai.CHO_DON} and requested_status:
            raise ValidationError({"trang_thai": "Cần checkout hoặc xác nhận dọn bàn từ phiên phục vụ đang mở."})
        if not (user.is_superuser or getattr(user, "la_quan_tri_vien", False)):
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            requested_branch = serializer.validated_data.get("chi_nhanh", table.chi_nhanh)
            if not branch_id or table.chi_nhanh_id != branch_id or requested_branch.id != branch_id:
                raise PermissionDenied("Bạn chỉ được sửa bàn thuộc chi nhánh được phân công.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.danh_sach_phien_phuc_vu.filter(
            trang_thai__in=[PhienPhucVu.TrangThai.DANG_PHUC_VU, PhienPhucVu.TrangThai.CHO_DON]
        ).exists():
            raise ValidationError({"detail": "Không thể lưu trữ bàn đang phục vụ hoặc chờ dọn."})
        instance.da_luu_tru = True
        instance.save(update_fields=["da_luu_tru", "cap_nhat_luc"])


class PhongRiengViewSet(viewsets.ModelViewSet):
    serializer_class = PhongRiengSerializer
    permission_classes = [LaNhanVienHoacChiDoc]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        rooms = PhongRieng.objects.select_related("chi_nhanh")
        if self.request.query_params.get("include_inactive") != "true":
            rooms = rooms.filter(con_hoat_dong=True)
        user = self.request.user
        if user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)):
            if not (user.is_superuser or getattr(user, "la_quan_tri_vien", False)):
                branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
                return rooms.filter(chi_nhanh_id=branch_id) if branch_id else rooms.none()
        branch_id = self.request.query_params.get("chi_nhanh")
        if branch_id:
            rooms = rooms.filter(chi_nhanh_id=branch_id)
        return rooms

    def _enforce_branch(self, serializer, instance=None):
        user = self.request.user
        if user.is_superuser or getattr(user, "la_quan_tri_vien", False):
            return
        branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
        room = instance
        if not room:
            room = serializer.validated_data.get("chi_nhanh")
        requested_branch = serializer.validated_data.get("chi_nhanh", getattr(room, "chi_nhanh", None))
        if not branch_id or not requested_branch or requested_branch.id != branch_id:
            raise PermissionDenied("Bạn chỉ được quản lý phòng thuộc chi nhánh được phân công.")

    def perform_create(self, serializer):
        self._enforce_branch(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._enforce_branch(serializer, self.get_object())
        serializer.save()

    def perform_destroy(self, instance):
        instance.con_hoat_dong = False
        instance.save(update_fields=["con_hoat_dong", "cap_nhat_luc"])

class DatBanViewSet(viewsets.ModelViewSet):
    serializer_class = DatBanSerializer

    def get_queryset(self):
        danh_sach = DatBan.objects.select_related(
            "ban_an", "chi_nhanh", "nguoi_dung", "phien_phuc_vu__don_hang"
        ).prefetch_related("danh_sach_mon__mon_an").order_by("-tao_luc")
        user = self.request.user
        # ?mine=1: trang tài khoản — kể cả nhân viên chỉ thấy bàn mình đặt.
        if user.is_authenticated and self.request.query_params.get("mine"):
            return danh_sach.filter(nguoi_dung=user)
        # Match LaNhanVienNhaHang permissions: Django staff accounts may access
        # this endpoint even when they don't have an application role attached.
        if user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)):
            if user.is_superuser or getattr(user, "la_quan_tri_vien", False):
                return danh_sach
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            return danh_sach.filter(chi_nhanh_id=branch_id) if branch_id else danh_sach.none()
        return danh_sach.filter(nguoi_dung=user)

    def get_permissions(self):
        if self.action == "khung_gio_trong":
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
        payload = request.data.copy()
        user = request.user
        if getattr(user, "la_nhan_vien_nha_hang", False) and not (
            user.is_superuser or getattr(user, "la_quan_tri_vien", False)
        ):
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            if not branch_id:
                raise PermissionDenied("Tài khoản chưa được gán chi nhánh.")
            requested_branch = payload.get("chi_nhanh") or payload.get("branch") or payload.get("branch_id")
            if requested_branch and str(requested_branch) != str(branch_id):
                raise PermissionDenied("Bạn chỉ được tạo đặt bàn cho chi nhánh được phân công.")
            payload["chi_nhanh"] = branch_id
        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        du_lieu = serializer.validated_data
        dat_ban = DichVuDatBan.tao_dat_ban(nguoi_dung=request.user, du_lieu=du_lieu)
        return Response(self.get_serializer(dat_ban).data, status=201)

    def perform_update(self, serializer):
        user = self.request.user
        if getattr(user, "la_nhan_vien_nha_hang", False) and not (
            user.is_superuser or getattr(user, "la_quan_tri_vien", False)
        ):
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            reservation = self.get_object()
            requested_branch = serializer.validated_data.get("chi_nhanh", reservation.chi_nhanh)
            if not branch_id or reservation.chi_nhanh_id != branch_id or getattr(requested_branch, "id", None) != branch_id:
                raise PermissionDenied("Bạn chỉ được sửa đặt bàn thuộc chi nhánh được phân công.")
        if "ban_an" in serializer.validated_data and serializer.validated_data["ban_an"] != self.get_object().ban_an:
            raise ValidationError({"ban_an": "Dùng thao tác bắt đầu phục vụ sau check-in để xếp bàn và tạo hóa đơn."})
        serializer.save()

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
        requested_status = request.data.get("status")
        if requested_status in {DatBan.TrangThai.KHACH_DA_DEN, DatBan.TrangThai.HOAN_TAT}:
            raise ValidationError({"status": "Dùng thao tác check-in hoặc checkout của phiên phục vụ."})
        dat_ban = DichVuDatBan.doi_trang_thai(
            current,
            requested_status,
            request.user
        )
        if dat_ban.trang_thai == DatBan.TrangThai.DA_HUY:
            dat_ban.huy_luc = timezone.now()
            dat_ban.ly_do_huy = str(request.data.get("reason", request.data.get("ghi_chu", "")))
            dat_ban.save(update_fields=["huy_luc", "ly_do_huy", "cap_nhat_luc"])
        return Response(self.get_serializer(dat_ban).data)

    @action(detail=True, methods=["post"], url_path="check-in", permission_classes=[LaNhanVienNhaHang])
    def check_in(self, request, pk=None):
        dat_ban = self.get_object()
        sent_version = request.data.get("version")
        if sent_version is not None and int(sent_version) != dat_ban.phien_ban:
            conflict = APIException("Đặt bàn đã được cập nhật bởi người khác. Hãy tải lại.")
            conflict.status_code = 409
            raise conflict
        dat_ban = DichVuPhienPhucVu.check_in_dat_ban(dat_ban=dat_ban, nguoi_dung=request.user)
        return Response(self.get_serializer(dat_ban).data)

    @action(detail=True, methods=["post"], url_path="seat", permission_classes=[LaNhanVienNhaHang])
    def seat(self, request, pk=None):
        dat_ban = self.get_object()
        serializer = XepBanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phien = DichVuPhienPhucVu.xep_ban_va_bat_dau(
            nguoi_dung=request.user,
            dat_ban_id=dat_ban.id,
            ban_an_id=serializer.validated_data["ban_an"].id,
        )
        return Response(PhienPhucVuSerializer(phien, context={"request": request}).data, status=201)

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
        try:
            so_khach = int(request.query_params.get("so_khach", 1))
        except (TypeError, ValueError):
            return Response({"detail": "so_khach phải là số nguyên từ 1 đến 12."}, status=400)
        if so_khach < 1 or so_khach > 12:
            return Response({"detail": "so_khach phải nằm trong khoảng 1 đến 12."}, status=400)

        if not chi_nhanh_id or not ngay_str:
            return Response({"detail": "Cần cung cấp chi_nhanh_id và ngay."}, status=400)

        try:
            chi_nhanh = ChiNhanh.objects.get(id=chi_nhanh_id)
        except ChiNhanh.DoesNotExist:
            return Response({"detail": "Chi nhánh không tồn tại."}, status=404)

        ngay = parse_date(ngay_str)
        if not ngay:
            return Response({"detail": "Ngày không hợp lệ. Dùng định dạng YYYY-MM-DD."}, status=400)

        # Build slot grid 10:00-22:00 step 15 phút
        slots = []
        now_local = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        today_local = now_local.date()
        current = datetime.time(10, 0)
        end_time = datetime.time(22, 0)

        while current <= end_time:
            cho_con_lai, so_khach_trong_slot, suc_chua_chi_nhanh = tinh_suc_chua_con_lai(
                chi_nhanh, ngay, current
            )

            is_future_slot = ngay > today_local or (ngay == today_local and current > now_local.time())
            con_trong = is_future_slot and cho_con_lai >= so_khach

            slots.append({
                "khung_gio": current.strftime("%H:%M"),
                "con_trong": con_trong,
                "so_khach_hien_tai": so_khach_trong_slot,
                "suc_chua_toi_da": suc_chua_chi_nhanh,
                "so_cho_con_lai": cho_con_lai,
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


class PhienPhucVuViewSet(viewsets.ReadOnlyModelViewSet):
    """API vận hành bàn tại chỗ; tất cả thay đổi đi qua service có khóa giao dịch."""

    serializer_class = PhienPhucVuSerializer
    permission_classes = [LaNhanVienNhaHang]

    def get_queryset(self):
        danh_sach = PhienPhucVu.objects.select_related(
            "chi_nhanh", "ban_an", "dat_ban", "don_hang"
        ).order_by("-bat_dau_luc")
        user = self.request.user
        if not (user.is_superuser or getattr(user, "la_quan_tri_vien", False)):
            branch_id = getattr(user, "chi_nhanh_quan_ly_id", None)
            if not branch_id:
                return danh_sach.none()
            danh_sach = danh_sach.filter(chi_nhanh_id=branch_id)
        if self.request.query_params.get("chi_nhanh"):
            danh_sach = danh_sach.filter(chi_nhanh_id=self.request.query_params["chi_nhanh"])
        if self.request.query_params.get("ban_an") or self.request.query_params.get("table"):
            danh_sach = danh_sach.filter(ban_an_id=self.request.query_params.get("ban_an") or self.request.query_params.get("table"))
        if self.request.query_params.get("trang_thai") or self.request.query_params.get("status"):
            danh_sach = danh_sach.filter(trang_thai=self.request.query_params.get("trang_thai") or self.request.query_params.get("status"))
        return danh_sach

    def _assert_branch_access(self, branch_id):
        user = self.request.user
        if user.is_superuser or getattr(user, "la_quan_tri_vien", False):
            return
        if str(getattr(user, "chi_nhanh_quan_ly_id", "")) != str(branch_id):
            raise PermissionDenied("Bạn chỉ được thao tác phiên phục vụ thuộc chi nhánh được phân công.")

    @action(detail=False, methods=["post"], url_path="walk-in")
    def walk_in(self, request):
        serializer = WalkInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        self._assert_branch_access(data["ban_an"].chi_nhanh_id)
        phien = DichVuPhienPhucVu.tao_walk_in(
            nguoi_dung=request.user,
            ban_an_id=data["ban_an"].id,
            so_luong_khach=data["so_luong_khach"],
            ten_khach=data["ten_khach"],
            sdt_khach=data["sdt_khach"],
            ghi_chu=data["ghi_chu"],
        )
        return Response(self.get_serializer(phien).data, status=201)

    @action(detail=False, methods=["post"], url_path="from-reservation")
    def from_reservation(self, request):
        reservation_id = request.data.get("dat_ban") or request.data.get("reservation_id")
        if not reservation_id:
            raise ValidationError({"dat_ban": "Cần chọn đặt bàn đã check-in."})
        serializer = XepBanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dat_ban = DatBan.objects.select_related("chi_nhanh").filter(pk=reservation_id).first()
        if not dat_ban:
            raise ValidationError({"dat_ban": "Không tìm thấy đặt bàn."})
        self._assert_branch_access(dat_ban.chi_nhanh_id)
        phien = DichVuPhienPhucVu.xep_ban_va_bat_dau(
            nguoi_dung=request.user, dat_ban_id=dat_ban.id, ban_an_id=serializer.validated_data["ban_an"].id
        )
        return Response(self.get_serializer(phien).data, status=201)

    @action(detail=True, methods=["post", "put"], url_path="items")
    def items(self, request, pk=None):
        phien = self.get_object()
        serializer = DanhSachMonPhienSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.method == "PUT":
            phien = DichVuPhienPhucVu.cap_nhat_mon(
                nguoi_dung=request.user,
                phien_id=phien.id,
                danh_sach_item=serializer.validated_data["danh_sach_mon"],
            )
        else:
            phien = DichVuPhienPhucVu.them_mon(
                nguoi_dung=request.user,
                phien_id=phien.id,
                danh_sach_item=serializer.validated_data["danh_sach_mon"],
            )
        from foods.services import DichVuKho
        data = dict(self.get_serializer(phien).data)
        data["canh_bao_kho"] = DichVuKho.canh_bao_sap_het(
            phien.don_hang.danh_sach_mon.values_list("mon_an_id", flat=True)
        )
        return Response(data)

    @action(detail=True, methods=["post"], url_path="move-table")
    def move_table(self, request, pk=None):
        phien = self.get_object()
        serializer = XepBanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phien = DichVuPhienPhucVu.chuyen_ban(
            nguoi_dung=request.user, phien_id=phien.id, ban_an_moi_id=serializer.validated_data["ban_an"].id
        )
        return Response(self.get_serializer(phien).data)

    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        phien = self.get_object()
        serializer = CheckOutPhienSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phien = DichVuPhienPhucVu.check_out(
            nguoi_dung=request.user,
            phien_id=phien.id,
            phuong_thuc=serializer.validated_data["phuong_thuc"],
            ma_tham_chieu=serializer.validated_data["ma_tham_chieu"],
        )
        return Response(self.get_serializer(phien).data)

    @action(detail=True, methods=["post"], url_path="confirm-cleaned")
    def confirm_cleaned(self, request, pk=None):
        phien = self.get_object()
        phien = DichVuPhienPhucVu.xac_nhan_da_don(nguoi_dung=request.user, phien_id=phien.id)
        return Response(self.get_serializer(phien).data)


# Backward-compatible viewset aliases
TableViewSet = BanAnViewSet
ReservationViewSet = DatBanViewSet
DiningSessionViewSet = PhienPhucVuViewSet

