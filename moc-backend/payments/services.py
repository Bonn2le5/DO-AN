import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import APIException, ValidationError
from .models import ThanhToan, PhieuHoanTien
from reservations.models import DatBan
from orders.models import DonHang


class DichVuPayOS:
    """Cổng thanh toán PayOS (QR chuyển khoản). Tài liệu: https://payos.vn/docs/api/"""

    class ChuaCauHinh(APIException):
        status_code = 503
        default_detail = "PayOS chưa được cấu hình: cần PAYOS_CLIENT_ID, PAYOS_API_KEY và PAYOS_CHECKSUM_KEY."
        default_code = "payos_not_configured"

    class LoiCong(APIException):
        status_code = 502
        default_detail = "Không kết nối được PayOS, vui lòng thử lại."
        default_code = "payos_error"

    @staticmethod
    def _khoa_checksum() -> str:
        khoa = getattr(settings, "PAYOS_CHECKSUM_KEY", "")
        if not khoa:
            raise DichVuPayOS.ChuaCauHinh()
        return khoa

    @staticmethod
    def ky(du_lieu: Dict[str, Any], khoa: str) -> str:
        """HMAC-SHA256 trên chuỗi key=value nối bằng & theo thứ tự key a→z."""
        def gia_tri(v):
            if v is None or v in ("null", "undefined"):
                return ""
            if isinstance(v, bool):
                return "true" if v else "false"
            if isinstance(v, (list, dict)):
                return json.dumps(v, separators=(",", ":"), ensure_ascii=False, sort_keys=True)
            return str(v)

        chuoi = "&".join(f"{k}={gia_tri(v)}" for k, v in sorted(du_lieu.items()))
        return hmac.new(khoa.encode("utf-8"), chuoi.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def _goi_api(cls, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        client_id = getattr(settings, "PAYOS_CLIENT_ID", "")
        api_key = getattr(settings, "PAYOS_API_KEY", "")
        if not client_id or not api_key:
            raise cls.ChuaCauHinh()
        req = urllib.request.Request(
            f"{settings.PAYOS_API_URL.rstrip('/')}{path}",
            method=method,
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers={
                "x-client-id": client_id,
                "x-api-key": api_key,
                "Content-Type": "application/json",
                # PayOS sits behind Cloudflare, which rejects the default "Python-urllib" agent (error 1010).
                "User-Agent": "moc-backend/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                ket_qua = json.loads(res.read().decode("utf-8"))
        except (urllib.error.URLError, ValueError) as exc:
            raise cls.LoiCong() from exc
        if ket_qua.get("code") != "00":
            raise cls.LoiCong(f"PayOS: {ket_qua.get('desc') or 'lỗi không xác định'}")
        return ket_qua.get("data") or {}

    @classmethod
    def tao_link(cls, *, thanh_toan: ThanhToan, het_han_luc: datetime) -> str:
        """Tạo link thanh toán mới, trả về checkoutUrl. Link cũ đang chờ (nếu có) bị huỷ để khách không trả nhầm."""
        khoa = cls._khoa_checksum()
        if thanh_toan.ma_giao_dich:
            trang_thai = cls.doi_soat(thanh_toan.ma_giao_dich)
            if trang_thai == "PAID":
                raise ValidationError({"detail": "Giao dịch này đã được thanh toán."})
            if trang_thai == "PENDING":
                try:
                    cls._goi_api("POST", f"/v2/payment-requests/{thanh_toan.ma_giao_dich}/cancel",
                                 {"cancellationReason": "Tạo link thanh toán mới"})
                except cls.LoiCong:
                    pass

        if thanh_toan.dat_ban:
            mo_ta = thanh_toan.dat_ban.ma_dat_ban
        elif thanh_toan.don_hang:
            mo_ta = thanh_toan.don_hang.ma_don_hang
        else:
            mo_ta = f"TT{thanh_toan.id}"

        # orderCode phải là số nguyên duy nhất và không được dùng lại sau khi huỷ.
        ma_don = int(time.time() * 1000)
        du_lieu = {
            "orderCode": ma_don,
            "amount": int(Decimal(str(thanh_toan.so_tien))),
            "description": mo_ta[:25],
            "returnUrl": settings.PAYOS_RETURN_URL,
            "cancelUrl": settings.PAYOS_CANCEL_URL,
        }
        du_lieu["signature"] = cls.ky(du_lieu, khoa)
        du_lieu["expiredAt"] = int(het_han_luc.timestamp())

        ket_qua = cls._goi_api("POST", "/v2/payment-requests", du_lieu)
        thanh_toan.ma_giao_dich = str(ma_don)
        thanh_toan.save(update_fields=["ma_giao_dich", "cap_nhat_luc"])
        return ket_qua["checkoutUrl"]

    @classmethod
    def xu_ly_webhook(cls, body: Dict[str, Any]) -> bool:
        """PayOS chỉ gửi webhook khi tiền đã vào tài khoản. Trả False nếu chữ ký sai."""
        du_lieu = body.get("data") or {}
        chu_ky = str(body.get("signature") or "")
        if not chu_ky or not hmac.compare_digest(cls.ky(du_lieu, cls._khoa_checksum()), chu_ky.lower()):
            return False
        if du_lieu.get("code") == "00":
            cls.xac_nhan(str(du_lieu.get("orderCode")), int(du_lieu.get("amount") or 0), thanh_cong=True)
        return True

    @classmethod
    def doi_soat(cls, ma_giao_dich: str) -> Optional[str]:
        """Hỏi PayOS trạng thái thật của giao dịch (returnUrl/cancelUrl không có chữ ký nên không tin được)."""
        try:
            info = cls._goi_api("GET", f"/v2/payment-requests/{ma_giao_dich}")
        except cls.LoiCong:
            return None
        trang_thai = info.get("status")
        if trang_thai == "PAID":
            cls.xac_nhan(ma_giao_dich, int(info.get("amount") or 0), thanh_cong=True)
        elif trang_thai in {"CANCELLED", "EXPIRED"}:
            cls.xac_nhan(ma_giao_dich, int(info.get("amount") or 0), thanh_cong=False)
        return trang_thai

    @classmethod
    def xac_nhan(cls, ma_giao_dich: str, so_tien: int, *, thanh_cong: bool) -> str:
        """Cập nhật thanh toán và đặt bàn/đơn hàng liên quan. Gọi lặp lại nhiều lần vẫn an toàn."""
        with transaction.atomic():
            # Chỉ khoá dòng thanh toán: FOR UPDATE qua join nullable dat_ban/don_hang bị PostgreSQL từ chối.
            thanh_toan = ThanhToan.objects.select_for_update().filter(ma_giao_dich=ma_giao_dich).first()
            if not thanh_toan:
                return "khong_tim_thay"
            if so_tien != int(Decimal(str(thanh_toan.so_tien))):
                return "sai_so_tien"
            if thanh_toan.trang_thai != ThanhToan.TrangThai.CHO_XU_LY:
                return "da_xu_ly"

            now = timezone.now()
            if thanh_cong:
                thanh_toan.trang_thai = ThanhToan.TrangThai.THANH_CONG
                thanh_toan.thanh_toan_luc = now
                thanh_toan.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])

                if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                    db = thanh_toan.dat_ban
                    db.trang_thai_coc = DatBan.TrangThaiCoc.THANH_CONG
                    db.thanh_toan_coc_luc = now
                    # Phiếu đã bị huỷ vì quá hạn thì giữ nguyên "Đã huỷ" để nhân viên hoàn cọc.
                    if db.trang_thai == DatBan.TrangThai.CHO_THANH_TOAN:
                        db.trang_thai = DatBan.TrangThai.CHO_XAC_NHAN
                    db.phien_ban += 1
                    db.save(update_fields=["trang_thai", "trang_thai_coc", "thanh_toan_coc_luc", "phien_ban", "cap_nhat_luc"])

                elif thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.DON_HANG and thanh_toan.don_hang:
                    dh = thanh_toan.don_hang
                    dh.trang_thai = DonHang.TrangThai.DA_XAC_NHAN
                    dh.save(update_fields=["trang_thai", "cap_nhat_luc"])
                    from orders.models import LichSuTrangThaiDon
                    LichSuTrangThaiDon.objects.create(
                        don_hang=dh,
                        tu_trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
                        sang_trang_thai=DonHang.TrangThai.DA_XAC_NHAN,
                        doi_boi=thanh_toan.nguoi_dung,
                        ghi_chu="PayOS xác nhận thanh toán"
                    )
                    try:
                        from foods.services import DichVuKho
                        DichVuKho.dong_bo_nguyen_lieu_don(
                            don_hang=dh,
                            nguoi_dung=thanh_toan.nguoi_dung,
                            ghi_chu=f"Xuất kho khi thanh toán thành công đơn hàng {dh.ma_don_hang}"
                        )
                    except Exception:
                        pass
                return "thanh_cong"

            thanh_toan.trang_thai = ThanhToan.TrangThai.THAT_BAI
            thanh_toan.save(update_fields=["trang_thai", "cap_nhat_luc"])
            if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                db = thanh_toan.dat_ban
                if db.trang_thai == DatBan.TrangThai.CHO_THANH_TOAN:
                    db.trang_thai = DatBan.TrangThai.DA_HUY
                db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
                db.phien_ban += 1
                db.save(update_fields=["trang_thai", "trang_thai_coc", "phien_ban", "cap_nhat_luc"])
            return "that_bai"


class DichVuHoanTien:
    POLICY_THRESHOLDS = {
        "TRUOC_24H": ("truoc_24h", 100.0, "da_hoan_tien"),
        "TU_6_DEN_24H": ("tu_6_den_24h", 50.0, "hoan_tien_mot_phan"),
        "TRONG_6H": ("trong_6h", 0.0, "that_bai"),
        "KHACH_KHONG_DEN": ("khach_khong_den", 0.0, "that_bai"),
    }

    @classmethod
    def ty_le_theo_chinh_sach(cls, chi_nhanh_id) -> Dict[str, float]:
        """Tỉ lệ hoàn theo từng mốc, đọc từ quy tắc huỷ của chính sách cọc (riêng chi nhánh, không có thì chung).
        Mốc nào chưa cấu hình dùng mặc định 100 / 50 / 0 / 0."""
        from reservations.services import lay_chinh_sach_coc
        ty_le = {moc: pct for moc, pct, _ in cls.POLICY_THRESHOLDS.values()}
        chinh_sach = lay_chinh_sach_coc(chi_nhanh_id)
        if chinh_sach:
            for quy_tac in chinh_sach.quy_tac_huy.all():
                ty_le[quy_tac.moc_thoi_gian] = min(100.0, max(0.0, float(quy_tac.phan_tram_hoan_tien)))
        return ty_le

    @staticmethod
    def trang_thai_theo_ty_le(pct: float) -> str:
        return "da_hoan_tien" if pct >= 100 else "hoan_tien_mot_phan" if pct > 0 else "that_bai"

    @classmethod
    def calculate_refund(
        cls,
        thoi_gian_dat: datetime,
        thoi_gian_huy: datetime,
        so_tien_coc: float,
        is_no_show: bool = False,
        ty_le: Optional[Dict[str, float]] = None,
    ) -> Tuple[str, float, float, float, str]:
        """Mốc huỷ và số tiền hoàn / bị giữ. ty_le: tỉ lệ hoàn theo mốc (mặc định 100 / 50 / 0 / 0)."""
        ty_le = ty_le or {moc: pct for moc, pct, _ in cls.POLICY_THRESHOLDS.values()}
        if is_no_show:
            moc = "khach_khong_den"
        else:
            so_gio = (thoi_gian_dat - thoi_gian_huy).total_seconds() / 3600.0
            moc = "truoc_24h" if so_gio > 24.0 else "tu_6_den_24h" if so_gio >= 6.0 else "trong_6h"
        pct = float(ty_le.get(moc, 0.0))
        # Tiền Việt không có phần lẻ: làm tròn tới đồng.
        so_tien_hoan = float(round(Decimal(str(so_tien_coc)) * Decimal(str(pct)) / 100))
        so_tien_phat = float(Decimal(str(so_tien_coc)) - Decimal(str(so_tien_hoan)))
        return moc, pct, so_tien_hoan, so_tien_phat, cls.trang_thai_theo_ty_le(pct)

    @classmethod
    def generate_refund_receipt(
        cls,
        ma_dat_ban: str,
        khach_hang_info: Dict[str, str],
        chi_nhanh_info: Dict[str, Any],
        thoi_gian_dat: datetime,
        thoi_gian_huy: datetime,
        so_tien_coc: float,
        ly_do_huy: str = "Khách hàng yêu cầu hủy",
        is_no_show: bool = False,
        ty_le: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        delta_seconds = (thoi_gian_dat - thoi_gian_huy).total_seconds()
        delta_hours = max(0.0, delta_seconds / 3600.0)

        moc, pct, so_tien_hoan, so_tien_phat, status = cls.calculate_refund(
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=thoi_gian_huy,
            so_tien_coc=so_tien_coc,
            is_no_show=is_no_show,
            ty_le=ty_le,
        )

        date_str = thoi_gian_huy.strftime("%Y%m%d")
        receipt_code = f"RF-{ma_dat_ban}-{date_str}"

        return {
            "ma_phieu_hoan": receipt_code,
            "ma_dat_ban": ma_dat_ban,
            "khach_hang": khach_hang_info,
            "chi_nhanh": chi_nhanh_info,
            "thoi_gian_dat_ban": thoi_gian_dat.isoformat(),
            "thoi_gian_yeu_cau_huy": thoi_gian_huy.isoformat(),
            "so_gio_truoc_gio_hen": round(delta_hours, 2),
            "chinh_sach_ap_dung": {
                "moc": moc,
                "ty_le_hoan_phan_tram": pct,
            },
            "tai_chinh": {
                "so_tien_coc_goc": float(so_tien_coc),
                "so_tien_hoan_tra": float(so_tien_hoan),
                "so_tien_khau_tru_phat": float(so_tien_phat),
            },
            "ly_do_huy": ly_do_huy,
            "phuong_thuc_hoan": "chuyen_khoan",
            "trang_thai": status,
            "tao_luc": thoi_gian_huy.isoformat(),
        }

    @classmethod
    @transaction.atomic
    def process_cancellation_and_refund(
        cls,
        dat_ban: DatBan,
        user=None,
        ly_do: str = "Khách hàng yêu cầu hủy",
        is_no_show: bool = False,
    ) -> Dict[str, Any]:
        from reservations.services import (
            TRANG_THAI_DUOC_BAO_KHONG_DEN, TRANG_THAI_DUOC_HUY, thoi_diem_hen,
        )

        # Khoá phiếu: IPN VNPay có thể đổi trạng thái cọc cùng lúc.
        dat_ban = DatBan.objects.select_for_update().select_related("chi_nhanh").get(pk=dat_ban.pk)
        duoc_phep = TRANG_THAI_DUOC_BAO_KHONG_DEN if is_no_show else TRANG_THAI_DUOC_HUY
        if dat_ban.trang_thai not in duoc_phep:
            hanh_dong = "báo khách không đến" if is_no_show else "huỷ"
            raise ValidationError({"chi_tiet": (
                f"Không thể {hanh_dong} đặt bàn đang ở trạng thái {dat_ban.get_trang_thai_display()}."
            )})

        now = timezone.now()
        thoi_gian_dat = thoi_diem_hen(dat_ban)

        if dat_ban.trang_thai_coc != DatBan.TrangThaiCoc.THANH_CONG:
            # Chưa thu cọc thì không có gì để hoàn: chỉ huỷ, không lập phiếu hoàn.
            # Nếu IPN thành công đến sau, phiếu giữ "Đã huỷ" và nhân viên ghi nhận hoàn cọc thủ công.
            dat_ban.trang_thai = DatBan.TrangThai.KHACH_KHONG_DEN if is_no_show else DatBan.TrangThai.DA_HUY
            dat_ban.huy_luc = now
            dat_ban.ly_do_huy = ly_do
            dat_ban.phien_ban += 1
            dat_ban.save(update_fields=["trang_thai", "huy_luc", "ly_do_huy", "phien_ban", "cap_nhat_luc"])
            return {
                "trang_thai": dat_ban.trang_thai,
                "phan_tram_hoan_tien": 0.0,
                "so_tien_hoan": 0.0,
                "so_tien_phat": 0.0,
                "moc_thoi_gian": None,
                "phieu_hoan_tien": None,
                "phieu_hoan_tien_id": None,
            }

        so_tien_coc = float(dat_ban.so_tien_coc)
        delta_seconds = (thoi_gian_dat - now).total_seconds()
        delta_hours = max(0.0, delta_seconds / 3600.0)

        ty_le = cls.ty_le_theo_chinh_sach(dat_ban.chi_nhanh_id)
        moc, pct, so_tien_hoan, so_tien_phat, status_coc = cls.calculate_refund(
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=now,
            so_tien_coc=so_tien_coc,
            is_no_show=is_no_show,
            ty_le=ty_le,
        )

        dat_ban.trang_thai = DatBan.TrangThai.KHACH_KHONG_DEN if is_no_show else DatBan.TrangThai.DA_HUY
        dat_ban.huy_luc = now
        dat_ban.ly_do_huy = ly_do
        dat_ban.phien_ban += 1
        dat_ban.save(update_fields=["trang_thai", "huy_luc", "ly_do_huy", "phien_ban", "cap_nhat_luc"])

        tt = dat_ban.danh_sach_thanh_toan.filter(
            loai_thanh_toan=ThanhToan.LoaiThanhToan.TIEN_COC, trang_thai=ThanhToan.TrangThai.THANH_CONG
        ).order_by("-tao_luc").first()
        ket_qua = {
            "trang_thai": dat_ban.trang_thai,
            "phan_tram_hoan_tien": pct,
            "so_tien_hoan": so_tien_hoan,
            "so_tien_phat": so_tien_phat,
            "moc_thoi_gian": moc,
            "phieu_hoan_tien": None,
            "phieu_hoan_tien_id": None,
        }

        if so_tien_hoan > 0:
            # Có tiền phải trả lại: hệ thống KHÔNG tự đánh dấu "đã hoàn". Cọc giữ "thành công" để phiếu
            # hiện trong danh sách cần hoàn cọc; nhân viên chuyển khoản xong mới ghi nhận (ghi-nhan-hoan-tien).
            ket_qua["trang_thai_hoan"] = "cho_hoan"
            return ket_qua

        # Không được hoàn (trong 6h / khách không đến): lập phiếu mất cọc ngay, không còn việc gì phải làm.
        receipt_dict = cls.generate_refund_receipt(
            ma_dat_ban=dat_ban.ma_dat_ban,
            khach_hang_info={"id": str(dat_ban.nguoi_dung_id or ""), "ho_ten": dat_ban.ten_khach or "",
                             "so_dien_thoai": dat_ban.sdt_khach or ""},
            chi_nhanh_info={"id": dat_ban.chi_nhanh_id, "ten": dat_ban.chi_nhanh.ten if dat_ban.chi_nhanh else ""},
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=now,
            so_tien_coc=so_tien_coc,
            ly_do_huy=ly_do,
            is_no_show=is_no_show,
            ty_le=ty_le,
        )
        receipt_dict["phuong_thuc_hoan"] = "khong_hoan"
        pht = PhieuHoanTien.objects.create(
            dat_ban=dat_ban,
            thanh_toan=tt,
            so_tien_coc_goc=Decimal(str(so_tien_coc)),
            phan_tram_hoan=Decimal(str(pct)),
            so_tien_hoan=Decimal("0"),
            so_tien_phat=Decimal(str(so_tien_phat)),
            moc_thoi_gian=moc,
            so_gio_truoc_gio_hen=Decimal(str(round(delta_hours, 2))),
            ly_do_huy=ly_do,
            trang_thai=PhieuHoanTien.TrangThai.THAT_BAI,
            phuong_thuc_hoan="khong_hoan",
            du_lieu_chi_tiet=receipt_dict,
        )
        ket_qua.update(trang_thai_hoan="khong_hoan", phieu_hoan_tien=receipt_dict, phieu_hoan_tien_id=pht.id)
        return ket_qua
