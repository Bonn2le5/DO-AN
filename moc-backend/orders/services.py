import logging
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon

logger = logging.getLogger(__name__)


def gui_su_kien_don_hang(dh, message):
    """Gửi sự kiện WS cho người theo dõi đơn và luồng đơn của nhân viên.

    Mỗi nhóm chỉ gửi một lần: người theo dõi đơn chỉ ở nhóm order_<id>.
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    groups = [f"order_{dh.id}", "staff_orders"]
    if dh.chi_nhanh_id:
        groups.append(f"staff_orders_branch_{dh.chi_nhanh_id}")
    for group in groups:
        try:
            async_to_sync(channel_layer.group_send)(group, message)
        except Exception:
            logger.exception("Không gửi được sự kiện WS %s tới nhóm %s", message.get("type"), group)


class DichVuDonHang:
    @staticmethod
    def tao_don_tai_cho(*, nguoi_dung, phien_phuc_vu, ten_khach="", sdt_khach="", ghi_chu=""):
        """Tạo hóa đơn rỗng khi bắt đầu phục vụ tại bàn.

        Món được thêm sau qua phiên phục vụ, vì khách walk-in thường gọi món
        sau khi đã ổn định chỗ ngồi.
        """
        don_hang = DonHang.objects.create(
            # Gắn khách đã đặt bàn (nếu có tài khoản) để họ đánh giá món sau khi dùng.
            khach_hang=getattr(phien_phuc_vu.dat_ban, "nguoi_dung", None),
            chi_nhanh=phien_phuc_vu.chi_nhanh,
            dat_ban=phien_phuc_vu.dat_ban,
            phien_phuc_vu=phien_phuc_vu,
            hinh_thuc=DonHang.HinhThuc.TAI_CHO,
            ten_khach=ten_khach or "Khách tại bàn",
            sdt_khach=sdt_khach or "",
            ghi_chu=ghi_chu or "",
            tien_hang=Decimal("0"),
            tien_giam=Decimal("0"),
            tong_tien=Decimal("0"),
        )
        LichSuTrangThaiDon.objects.create(
            don_hang=don_hang,
            tu_trang_thai=None,
            sang_trang_thai=don_hang.trang_thai,
            doi_boi=nguoi_dung,
            ghi_chu=f"Mở phiên phục vụ {phien_phuc_vu.ma_phien}",
        )

        order_payload = {
            "id": don_hang.id,
            "order_number": don_hang.ma_don_hang,
            "ma_don_hang": don_hang.ma_don_hang,
            "status": don_hang.trang_thai,
            "status_display": don_hang.get_trang_thai_display(),
            "order_type": don_hang.hinh_thuc,
            "chi_nhanh_id": don_hang.chi_nhanh_id,
            "customer_name": don_hang.ten_khach,
            "total_amount": str(don_hang.tong_tien),
            "created_at": don_hang.tao_luc.isoformat(),
        }
        transaction.on_commit(lambda: gui_su_kien_don_hang(don_hang, {
            "type": "order_created", "order": order_payload, "data": order_payload,
        }))
        return don_hang

    @staticmethod
    @transaction.atomic
    def them_mon_tai_cho(*, don_hang, danh_sach_item, nguoi_dung):
        """Thêm món vào hóa đơn của phiên đang phục vụ và tính lại tổng tiền."""
        don_hang = DonHang.objects.select_for_update(of=("self",)).select_related("phien_phuc_vu").get(pk=don_hang.pk)
        if don_hang.hinh_thuc != DonHang.HinhThuc.TAI_CHO or not don_hang.phien_phuc_vu_id:
            raise ValidationError({"order": "Chỉ hóa đơn dùng tại bàn mới được thêm món từ phiên phục vụ."})
        if don_hang.phien_phuc_vu.trang_thai != "dang_phuc_vu":
            raise ValidationError({"session": "Phiên phục vụ này đã checkout hoặc đang chờ dọn."})
        if don_hang.trang_thai in DichVuDonHang.TERMINAL_STATES:
            raise ValidationError({"order": "Hóa đơn đã kết thúc, không thể thêm món."})

        for item in danh_sach_item:
            mon_an = item["mon_an"]
            so_luong = item["so_luong"]
            if so_luong < 1 or not mon_an.hien_thi or not mon_an.con_hang:
                raise ValidationError({"items": f"Món {mon_an.ten} hiện không khả dụng."})
            if mon_an.ton_kho_cache is not None and not mon_an.quan_ly_kho and mon_an.ton_kho_cache < so_luong:
                raise ValidationError({"items": f"Món {mon_an.ten} không đủ số lượng trong kho."})

            # Món khách đặt trước giữ đơn giá đã chốt lúc đặt (tiền cọc tính theo giá đó).
            don_gia = item["don_gia"] if item.get("don_gia") is not None else mon_an.don_gia_hien_tai
            ChiTietDonHang.objects.create(
                don_hang=don_hang,
                mon_an=mon_an,
                so_luong=so_luong,
                don_gia_luc_dat=don_gia,
                thanh_tien=don_gia * so_luong,
                ghi_chu=item.get("ghi_chu", ""),
            )
            if mon_an.ton_kho_cache is not None and not mon_an.quan_ly_kho:
                mon_an.ton_kho_cache -= so_luong
                mon_an.save(update_fields=["ton_kho_cache", "cap_nhat_luc"])

        tien_hang = sum((item.thanh_tien for item in don_hang.danh_sach_mon.all()), Decimal("0"))
        don_hang.tien_hang = tien_hang
        don_hang.tong_tien = max(Decimal("0"), tien_hang - don_hang.tien_giam)
        don_hang.save(update_fields=["tien_hang", "tong_tien", "cap_nhat_luc"])
        return don_hang

    STATUS_ALIASES = {
        "pending": DonHang.TrangThai.CHO_TIEP_NHAN,
        "confirmed": DonHang.TrangThai.DA_XAC_NHAN,
        "cooking": DonHang.TrangThai.DANG_CHE_BIEN,
        "processing": DonHang.TrangThai.DANG_CHE_BIEN,
        "ready": DonHang.TrangThai.SAN_SANG,
        "completed": DonHang.TrangThai.HOAN_TAT,
        "cancelled": DonHang.TrangThai.DA_HUY,
        "canceled": DonHang.TrangThai.DA_HUY,
    }

    VALID_STATES = {
        DonHang.TrangThai.CHO_TIEP_NHAN,
        DonHang.TrangThai.DA_XAC_NHAN,
        DonHang.TrangThai.DANG_CHE_BIEN,
        DonHang.TrangThai.SAN_SANG,
        DonHang.TrangThai.HOAN_TAT,
        DonHang.TrangThai.DA_HUY,
    }

    TERMINAL_STATES = {
        DonHang.TrangThai.HOAN_TAT,
        DonHang.TrangThai.DA_HUY,
    }

    ALLOWED_TRANSITIONS = {
        DonHang.TrangThai.CHO_TIEP_NHAN: {
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.DA_XAC_NHAN: {
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.DANG_CHE_BIEN: {
            DonHang.TrangThai.SAN_SANG,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.SAN_SANG: {
            DonHang.TrangThai.HOAN_TAT,
            DonHang.TrangThai.DA_HUY,
        },
        DonHang.TrangThai.HOAN_TAT: set(),
        DonHang.TrangThai.DA_HUY: set(),
    }

    @classmethod
    def chuan_hoa_trang_thai(cls, status_str):
        if not status_str:
            return None
        s = str(status_str).lower().strip()
        return cls.STATUS_ALIASES.get(s, s)

    @classmethod
    @transaction.atomic
    def doi_trang_thai(
        cls,
        don_hang,
        trang_thai_moi=None,
        nguoi_dung=None,
        ghi_chu="",
        **kwargs
    ):
        trang_thai_raw = (
            trang_thai_moi
            if trang_thai_moi is not None
            else kwargs.get("trang_thai_moi_raw", kwargs.get("status"))
        )
        trang_thai_moi_canonical = cls.chuan_hoa_trang_thai(trang_thai_raw)

        if not trang_thai_moi_canonical or trang_thai_moi_canonical not in cls.VALID_STATES:
            raise ValidationError({"status": f"Trạng thái '{trang_thai_raw}' không hợp lệ."})

        # Pessimistic row locking
        dh = DonHang.objects.select_for_update().get(id=don_hang.id)
        trang_thai_cu = dh.trang_thai

        # Terminal state immutability
        if trang_thai_cu in cls.TERMINAL_STATES:
            raise ValidationError({
                "status": f"Không thể thay đổi trạng thái của đơn hàng đã kết thúc ('{trang_thai_cu}')."
            })

        # Self-transition rejection
        if trang_thai_cu == trang_thai_moi_canonical:
            raise ValidationError({
                "status": f"Đơn hàng đã ở trạng thái '{trang_thai_cu}'."
            })

        # FSM state transition validation
        allowed = cls.ALLOWED_TRANSITIONS.get(trang_thai_cu, set())
        if trang_thai_moi_canonical not in allowed:
            raise ValidationError({
                "status": f"Không thể chuyển trạng thái đơn hàng từ '{trang_thai_cu}' sang '{trang_thai_moi_canonical}'."
            })

        # Role & authorization check:
        # Customer can only cancel pending orders (cho_tiep_nhan); other transitions require restaurant staff.
        is_staff = (
            nguoi_dung is None
            or getattr(nguoi_dung, "is_staff", False)
            or getattr(nguoi_dung, "la_nhan_vien_nha_hang", False)
        )
        if not is_staff:
            if dh.khach_hang_id != getattr(nguoi_dung, "id", None):
                raise PermissionDenied("Bạn không có quyền thay đổi trạng thái đơn hàng này.")
            if trang_thai_cu != DonHang.TrangThai.CHO_TIEP_NHAN or trang_thai_moi_canonical != DonHang.TrangThai.DA_HUY:
                raise PermissionDenied(
                    "Khách hàng chỉ có thể hủy đơn khi đơn hàng đang ở trạng thái chờ tiếp nhận."
                )

        # Hook BOM Material Deduction when order is confirmed
        if trang_thai_moi_canonical == DonHang.TrangThai.DA_XAC_NHAN:
            from foods.services import DichVuKho
            DichVuKho.dong_bo_nguyen_lieu_don(
                don_hang=dh,
                nguoi_dung=nguoi_dung,
                ghi_chu=ghi_chu or f"Xuất kho khi xác nhận đơn hàng {dh.ma_don_hang}"
            )
        elif trang_thai_moi_canonical == DonHang.TrangThai.DA_HUY and trang_thai_cu in [
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
        ]:
            from foods.services import DichVuKho
            DichVuKho.hoan_tra_nguyen_lieu_bom(
                loai_tham_chieu="don_hang",
                id_tham_chieu=dh.id,
                nguoi_dung=nguoi_dung,
                ghi_chu=ghi_chu or f"Hoàn kho do hủy đơn hàng {dh.ma_don_hang}"
            )

        dh.trang_thai = trang_thai_moi_canonical
        dh.save(update_fields=["trang_thai", "cap_nhat_luc"])

        # Ghi tương tác "đặt món" cho mô hình gợi ý AI khi đơn hoàn tất.
        # Món đã gọi trước lúc đặt bàn đã được ghi khi tạo đặt bàn → bỏ qua để không tính 2 lần.
        if trang_thai_moi_canonical == DonHang.TrangThai.HOAN_TAT and dh.khach_hang_id:
            from recommendations.services import ghi_nhan_dat_mon
            mon_ids = set(dh.danh_sach_mon.values_list("mon_an_id", flat=True))
            if dh.dat_ban_id and dh.dat_ban.nguoi_dung_id == dh.khach_hang_id:
                mon_ids -= set(dh.dat_ban.danh_sach_mon.values_list("mon_an_id", flat=True))
            ghi_nhan_dat_mon(dh.khach_hang, mon_ids)

        # Audit log in LichSuTrangThaiDon (safe note truncation <= 255 chars)
        clean_note = (ghi_chu or "")[:255]
        LichSuTrangThaiDon.objects.create(
            don_hang=dh,
            tu_trang_thai=trang_thai_cu,
            sang_trang_thai=trang_thai_moi_canonical,
            doi_boi=nguoi_dung,
            ghi_chu=clean_note,
        )

        # Post-commit broadcast (transaction.on_commit)
        def _broadcast():
            try:
                from django.utils import timezone

                actor_name = (
                    getattr(nguoi_dung, "ho_ten", None)
                    or getattr(nguoi_dung, "get_full_name", lambda: "")()
                    or getattr(nguoi_dung, "username", "Hệ thống")
                    if nguoi_dung else "Hệ thống"
                )
                actor_id = getattr(nguoi_dung, "id", None)
                now_iso = timezone.now().isoformat()

                event_payload = {
                    "type": "order_status_update",
                    "order_id": dh.id,
                    "order_number": dh.ma_don_hang,
                    "ma_don_hang": dh.ma_don_hang,
                    "order_code": dh.ma_don_hang,
                    "from_status": trang_thai_cu,
                    "trang_thai_cu": trang_thai_cu,
                    "to_status": trang_thai_moi_canonical,
                    "trang_thai_moi": trang_thai_moi_canonical,
                    "status": trang_thai_moi_canonical,
                    "status_display": dh.get_trang_thai_display(),
                    "note": clean_note,
                    "ghi_chu": clean_note,
                    "changed_by": actor_name,
                    "changed_by_id": actor_id,
                    "timestamp": now_iso,
                    "thoi_gian": now_iso,
                }
                broadcast_msg = {
                    "type": "order_status_update",
                    "data": event_payload,
                    **event_payload,
                }

                gui_su_kien_don_hang(dh, broadcast_msg)
            except Exception:
                logger.exception("Lỗi khi tạo sự kiện cập nhật trạng thái đơn %s", dh.id)

        transaction.on_commit(_broadcast)
        return dh

