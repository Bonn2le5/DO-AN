from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon
from promotions.models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai


class DichVuDonHang:
    @staticmethod
    @transaction.atomic
    def tao_don_hang(*, nguoi_dung, du_lieu):
        danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("items", [])
        ma_km = du_lieu.pop("ma_khuyen_mai", "") or du_lieu.pop("promo_code", "")

        if not danh_sach_item:
            raise ValidationError({"items": "Đơn hàng phải có ít nhất một món ăn."})

        tien_hang = Decimal("0")
        danh_sach_chuan_hoa = []

        for item in danh_sach_item:
            mon_an = item["mon_an"]
            so_luong = item.get("so_luong") if "so_luong" in item else item.get("quantity", 1)
            if so_luong < 1 or not mon_an.hien_thi or not mon_an.con_hang:
                raise ValidationError({"items": f"Món {mon_an.ten} hiện không khả dụng."})
            if mon_an.ton_kho_cache is not None and not mon_an.quan_ly_kho and mon_an.ton_kho_cache < so_luong:
                raise ValidationError({"items": f"Món {mon_an.ten} không đủ số lượng trong kho."})

            don_gia = mon_an.don_gia_hien_tai
            tien_hang += don_gia * so_luong
            danh_sach_chuan_hoa.append((mon_an, so_luong, don_gia))

        khuyen_mai = ma_khuyen_mai_obj = None
        tien_giam = Decimal("0")

        if ma_km:
            khuyen_mai = KhuyenMai.objects.select_for_update().filter(ma_giam_gia__iexact=ma_km).first()
            ma_khuyen_mai_obj = MaKhuyenMai.objects.select_for_update().filter(
                ma__iexact=ma_km, con_hoat_dong=True
            ).select_related("khuyen_mai").first()

            if ma_khuyen_mai_obj:
                khuyen_mai = ma_khuyen_mai_obj.khuyen_mai

            if not khuyen_mai or (khuyen_mai.gioi_han_su_dung is not None and khuyen_mai.so_lan_da_dung >= khuyen_mai.gioi_han_su_dung):
                raise ValidationError({"promo_code": "Mã khuyến mãi không hợp lệ hoặc đã hết lượt."})

            tien_giam = khuyen_mai.tinh_tien_giam(tien_hang)
            if not tien_giam:
                raise ValidationError({"promo_code": "Đơn hàng chưa đạt giá trị tối thiểu để áp dụng mã này."})

            if ma_khuyen_mai_obj and ma_khuyen_mai_obj.gioi_han is not None and ma_khuyen_mai_obj.da_dung >= ma_khuyen_mai_obj.gioi_han:
                raise ValidationError({"promo_code": "Mã giảm giá cá nhân đã hết lượt sử dụng."})

        if du_lieu["hinh_thuc"] == DonHang.HinhThuc.GIAO_HANG and not du_lieu.get("dia_chi_giao"):
            raise ValidationError({"dia_chi_giao": "Địa chỉ giao hàng là bắt buộc đối với đơn giao tận nơi."})

        don_hang = DonHang.objects.create(
            khach_hang=nguoi_dung,
            tien_hang=tien_hang,
            tien_giam=tien_giam,
            tong_tien=tien_hang - tien_giam,
            khuyen_mai=khuyen_mai,
            **du_lieu
        )

        for mon_an, so_luong, don_gia in danh_sach_chuan_hoa:
            if mon_an.ton_kho_cache is not None and not mon_an.quan_ly_kho:
                mon_an.ton_kho_cache -= so_luong
                mon_an.save(update_fields=["ton_kho_cache", "cap_nhat_luc"])

            ChiTietDonHang.objects.create(
                don_hang=don_hang,
                mon_an=mon_an,
                so_luong=so_luong,
                don_gia_luc_dat=don_gia,
                thanh_tien=don_gia * so_luong
            )

            from recommendations.models import TuongTacMonAn
            TuongTacMonAn.objects.create(
                nguoi_dung=nguoi_dung, mon_an=mon_an,
                loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON, trong_so=4
            )

        if khuyen_mai:
            khuyen_mai.so_lan_da_dung += 1
            khuyen_mai.save(update_fields=["so_lan_da_dung", "cap_nhat_luc"])
            if ma_khuyen_mai_obj:
                ma_khuyen_mai_obj.da_dung += 1
                ma_khuyen_mai_obj.save(update_fields=["da_dung", "cap_nhat_luc"])
            LichSuDungKhuyenMai.objects.create(
                khuyen_mai=khuyen_mai, ma_khuyen_mai=ma_khuyen_mai_obj,
                nguoi_dung=nguoi_dung, don_hang=don_hang, so_tien_giam=tien_giam
            )

        LichSuTrangThaiDon.objects.create(
            don_hang=don_hang, tu_trang_thai=None,
            sang_trang_thai=don_hang.trang_thai, doi_boi=nguoi_dung
        )
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
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=dh.danh_sach_mon.all(),
                loai_tham_chieu="don_hang",
                id_tham_chieu=dh.id,
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
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                from django.utils import timezone

                channel_layer = get_channel_layer()
                if not channel_layer:
                    return

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

                for group in [f"order_{dh.id}", f"order_{dh.ma_don_hang}", "staff_orders"]:
                    async_to_sync(channel_layer.group_send)(group, broadcast_msg)
            except Exception:
                pass

        transaction.on_commit(_broadcast)
        return dh

