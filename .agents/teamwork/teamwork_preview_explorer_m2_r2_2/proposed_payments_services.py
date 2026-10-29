import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache, caches
from .models import ThanhToan, PhieuHoanTien
from reservations.models import DatBan
from orders.models import DonHang


def _safe_cache():
    try:
        cache.get("_probe_")
        return cache
    except Exception:
        try:
            return caches["locmem"]
        except Exception:
            return cache


class VNPayService:
    @staticmethod
    def get_client_ip(request) -> str:
        if not request:
            return "127.0.0.1"
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "127.0.0.1")

    @staticmethod
    def calculate_hmac_sha512(params: Dict[str, Any], hash_secret: str) -> str:
        clean_params = {}
        for k, v in params.items():
            if k in ("vnp_SecureHash", "vnp_SecureHashType"):
                continue
            if v is not None and str(v) != "":
                clean_params[k] = str(v)

        sorted_items = sorted(clean_params.items())
        hash_data = "&".join(
            f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items
        )
        return hmac.new(
            hash_secret.encode("utf-8"),
            hash_data.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()

    @staticmethod
    def verify_signature(params: Dict[str, Any], secure_hash: str, hash_secret: str) -> bool:
        if not secure_hash:
            return False
        expected_hash = VNPayService.calculate_hmac_sha512(params, hash_secret)
        return hmac.compare_digest(expected_hash.lower(), secure_hash.lower())

    @classmethod
    def create_payment_url(
        cls,
        *,
        thanh_toan: ThanhToan,
        ip_addr: str = "127.0.0.1",
        order_info: Optional[str] = None,
        locale: str = "vn",
        create_date: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        tmn_code = getattr(settings, "VNPAY_TMN_CODE", "MOCREST1")
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        base_url = getattr(settings, "VNPAY_URL", getattr(settings, "VNPAY_SANDBOX_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"))
        return_url = getattr(settings, "VNPAY_RETURN_URL", "http://localhost:5173/payment/vnpay-return")

        now = timezone.now()
        if not create_date:
            create_date = now.strftime("%Y%m%d%H%M%S")
        amount_vnd = int(Decimal(str(thanh_toan.so_tien)) * 100)

        if not thanh_toan.ma_giao_dich:
            thanh_toan.ma_giao_dich = f"TT{thanh_toan.id}_{int(now.timestamp())}"
            thanh_toan.save(update_fields=["ma_giao_dich", "cap_nhat_luc"])

        if not order_info:
            if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                order_info = f"Thanh toan dat coc ban {thanh_toan.dat_ban.ma_dat_ban}"
            elif thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.DON_HANG and thanh_toan.don_hang:
                order_info = f"Thanh toan don hang {thanh_toan.don_hang.ma_don_hang}"
            else:
                order_info = f"Thanh toan giao dich {thanh_toan.ma_giao_dich}"

        params: Dict[str, Any] = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": tmn_code,
            "vnp_Amount": str(amount_vnd),
            "vnp_CreateDate": create_date,
            "vnp_CurrCode": "VND",
            "vnp_IpAddr": ip_addr,
            "vnp_Locale": locale,
            "vnp_OrderInfo": order_info,
            "vnp_OrderType": "billpayment",
            "vnp_ReturnUrl": return_url,
            "vnp_TxnRef": thanh_toan.ma_giao_dich,
        }

        checksum = cls.calculate_hmac_sha512(params, hash_secret)
        params["vnp_SecureHash"] = checksum

        sorted_items = sorted(params.items())
        query_string = "&".join(
            f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_items
        )
        payment_url = f"{base_url}?{query_string}"
        return payment_url, params

    @classmethod
    def process_ipn(cls, query_params: Any) -> Tuple[str, str]:
        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        
        # Robust scalar parameter extraction from Django QueryDict or standard dict
        if hasattr(query_params, "dict"):
            raw_dict = query_params.dict()
        else:
            raw_dict = dict(query_params)
        params = {
            k: (v[0] if isinstance(v, list) and len(v) > 0 else v)
            for k, v in raw_dict.items()
        }

        vnp_secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        # 1. Verify Checksum (fail-fast without touching database)
        if not vnp_secure_hash or not cls.verify_signature(params, str(vnp_secure_hash), hash_secret):
            return "97", "Invalid Checksum"

        txn_ref = params.get("vnp_TxnRef")
        raw_amount = params.get("vnp_Amount", 0)
        try:
            amount = int(raw_amount)
        except (ValueError, TypeError):
            return "04", "Invalid amount"

        response_code = params.get("vnp_ResponseCode")

        # Stages 2 through 5 are enclosed within a single atomic transaction
        # to ensure select_for_update() pessimistic row lock persists across idempotency checks & mutations
        with transaction.atomic():
            # 2. Check Order Existence with pessimistic lock
            try:
                thanh_toan = ThanhToan.objects.select_for_update().select_related(
                    "dat_ban", "don_hang"
                ).get(ma_giao_dich=txn_ref)
            except ThanhToan.DoesNotExist:
                return "01", "Order not found"

            # 3. Check Amount (VNPay amount * 100)
            expected_amount = int(Decimal(str(thanh_toan.so_tien)) * 100)
            if amount != expected_amount:
                return "04", "Invalid amount"

            # 4. Idempotency Check
            if thanh_toan.trang_thai in (ThanhToan.TrangThai.THANH_CONG, ThanhToan.TrangThai.DA_HOAN_TIEN):
                return "02", "Order already confirmed"

            # 5. Process Confirmation or Failure
            now = timezone.now()
            c = _safe_cache()

            if response_code == "00":
                thanh_toan.trang_thai = ThanhToan.TrangThai.THANH_CONG
                thanh_toan.thanh_toan_luc = now
                thanh_toan.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])

                # Link DatBan
                if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                    db = thanh_toan.dat_ban
                    db.trang_thai = DatBan.TrangThai.DA_XAC_NHAN
                    db.trang_thai_coc = DatBan.TrangThaiCoc.THANH_CONG
                    db.thanh_toan_coc_luc = now
                    db.phien_ban += 1
                    db.save(update_fields=["trang_thai", "trang_thai_coc", "thanh_toan_coc_luc", "phien_ban", "cap_nhat_luc"])

                    # Release temporary hold keys
                    gio_str = str(db.gio_bat_dau)[:5]
                    try:
                        c.delete(f"table_hold:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{db.gio_bat_dau}")
                    except Exception:
                        pass

                # Link DonHang
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
                        ghi_chu="VNPay IPN confirmed payment"
                    )
                    try:
                        from foods.services import DichVuKho
                        DichVuKho.khau_tru_nguyen_lieu_bom(
                            danh_sach_mon=dh.danh_sach_mon.all(),
                            loai_tham_chieu="don_hang",
                            id_tham_chieu=dh.id,
                            nguoi_dung=thanh_toan.nguoi_dung,
                            ghi_chu=f"Xuất kho khi thanh toán thành công đơn hàng {dh.ma_don_hang}"
                        )
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).warning("BOM deduction in IPN warning: %s", e)

                return "00", "Confirm Success"
            else:
                thanh_toan.trang_thai = ThanhToan.TrangThai.THAT_BAI
                thanh_toan.save(update_fields=["trang_thai", "cap_nhat_luc"])

                if thanh_toan.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and thanh_toan.dat_ban:
                    db = thanh_toan.dat_ban
                    db.trang_thai = DatBan.TrangThai.DA_HUY
                    db.trang_thai_coc = DatBan.TrangThaiCoc.THAT_BAI
                    db.phien_ban += 1
                    db.save(update_fields=["trang_thai", "trang_thai_coc", "phien_ban", "cap_nhat_luc"])

                    # Release hold key so table is freed
                    gio_str = str(db.gio_bat_dau)[:5]
                    try:
                        c.delete(f"table_hold:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{gio_str}")
                        c.delete(f"giu-ban:{db.ban_an_id}:{db.ngay_dat}:{db.gio_bat_dau}")
                    except Exception:
                        pass

                return "00", "Confirm Failure"


class RefundService:
    POLICY_THRESHOLDS = {
        "TRUOC_24H": ("truoc_24h", 100.0, "da_hoan_tien"),
        "TU_6_DEN_24H": ("tu_6_den_24h", 50.0, "hoan_tien_mot_phan"),
        "TRONG_6H": ("trong_6h", 0.0, "that_bai"),
        "KHACH_KHONG_DEN": ("khach_khong_den", 0.0, "that_bai"),
    }

    @classmethod
    def calculate_refund(
        cls,
        thoi_gian_dat: datetime,
        thoi_gian_huy: datetime,
        so_tien_coc: float,
        is_no_show: bool = False,
    ) -> Tuple[str, float, float, float, str]:
        if is_no_show:
            moc, pct, status = cls.POLICY_THRESHOLDS["KHACH_KHONG_DEN"]
            return moc, pct, 0.0, float(so_tien_coc), status

        delta_seconds = (thoi_gian_dat - thoi_gian_huy).total_seconds()
        delta_hours = delta_seconds / 3600.0

        if delta_hours > 24.0:
            moc, pct, status = cls.POLICY_THRESHOLDS["TRUOC_24H"]
            so_tien_hoan = float(so_tien_coc)
            so_tien_phat = 0.0
        elif 6.0 <= delta_hours <= 24.0:
            moc, pct, status = cls.POLICY_THRESHOLDS["TU_6_DEN_24H"]
            so_tien_hoan = round(float(so_tien_coc) * 0.5, 2)
            so_tien_phat = round(float(so_tien_coc) - so_tien_hoan, 2)
        else:  # delta_hours < 6.0
            moc, pct, status = cls.POLICY_THRESHOLDS["TRONG_6H"]
            so_tien_hoan = 0.0
            so_tien_phat = float(so_tien_coc)

        return moc, pct, so_tien_hoan, so_tien_phat, status

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
    ) -> Dict[str, Any]:
        delta_seconds = (thoi_gian_dat - thoi_gian_huy).total_seconds()
        delta_hours = max(0.0, delta_seconds / 3600.0)

        moc, pct, so_tien_hoan, so_tien_phat, status = cls.calculate_refund(
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=thoi_gian_huy,
            so_tien_coc=so_tien_coc,
            is_no_show=is_no_show,
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
            "phuong_thuc_hoan": "vnpay_refund",
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
        now = timezone.now()
        naive_dt = datetime.combine(dat_ban.ngay_dat, dat_ban.gio_bat_dau)
        if timezone.is_aware(now):
            thoi_gian_dat = timezone.make_aware(naive_dt, timezone.get_current_timezone())
        else:
            thoi_gian_dat = naive_dt

        so_tien_coc = float(dat_ban.so_tien_coc)
        delta_seconds = (thoi_gian_dat - now).total_seconds()
        delta_hours = max(0.0, delta_seconds / 3600.0)

        moc, pct, so_tien_hoan, so_tien_phat, status_coc = cls.calculate_refund(
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=now,
            so_tien_coc=so_tien_coc,
            is_no_show=is_no_show,
        )

        dat_ban.trang_thai = DatBan.TrangThai.KHACH_KHONG_DEN if is_no_show else DatBan.TrangThai.DA_HUY
        dat_ban.trang_thai_coc = status_coc
        dat_ban.huy_luc = now
        dat_ban.ly_do_huy = ly_do
        dat_ban.phien_ban += 1
        dat_ban.save(update_fields=["trang_thai", "trang_thai_coc", "huy_luc", "ly_do_huy", "phien_ban", "cap_nhat_luc"])

        # Release table hold cache if any
        c = _safe_cache()
        gio_str = str(dat_ban.gio_bat_dau)[:5]
        try:
            c.delete(f"table_hold:{dat_ban.ban_an_id}:{dat_ban.ngay_dat}:{gio_str}")
            c.delete(f"giu-ban:{dat_ban.ban_an_id}:{dat_ban.ngay_dat}:{gio_str}")
            c.delete(f"giu-ban:{dat_ban.ban_an_id}:{dat_ban.ngay_dat}:{dat_ban.gio_bat_dau}")
        except Exception:
            pass

        # Update linked ThanhToan
        tt = dat_ban.danh_sach_thanh_toan.filter(loai_thanh_toan=ThanhToan.LoaiThanhToan.TIEN_COC).first()
        if tt:
            if so_tien_hoan > 0.0:
                tt.trang_thai = ThanhToan.TrangThai.DA_HOAN_TIEN
            tt.hoan_tien_luc = now
            tt.save(update_fields=["trang_thai", "hoan_tien_luc", "cap_nhat_luc"])

        khach_info = {
            "id": str(dat_ban.nguoi_dung_id or ""),
            "ho_ten": dat_ban.ten_khach or "",
            "so_dien_thoai": dat_ban.sdt_khach or "",
        }
        chi_nhanh_info = {
            "id": dat_ban.chi_nhanh_id,
            "ten": dat_ban.chi_nhanh.ten if dat_ban.chi_nhanh else "",
        }

        receipt_dict = cls.generate_refund_receipt(
            ma_dat_ban=dat_ban.ma_dat_ban,
            khach_hang_info=khach_info,
            chi_nhanh_info=chi_nhanh_info,
            thoi_gian_dat=thoi_gian_dat,
            thoi_gian_huy=now,
            so_tien_coc=so_tien_coc,
            ly_do_huy=ly_do,
            is_no_show=is_no_show,
        )

        pht = PhieuHoanTien.objects.create(
            ma_phieu_hoan=receipt_dict["ma_phieu_hoan"],
            dat_ban=dat_ban,
            thanh_toan=tt,
            so_tien_coc_goc=Decimal(str(so_tien_coc)),
            phan_tram_hoan=Decimal(str(pct)),
            so_tien_hoan=Decimal(str(so_tien_hoan)),
            so_tien_phat=Decimal(str(so_tien_phat)),
            moc_thoi_gian=moc,
            so_gio_truoc_gio_hen=Decimal(str(round(delta_hours, 2))),
            ly_do_huy=ly_do,
            trang_thai=status_coc,
            phuong_thuc_hoan="vnpay_refund",
            du_lieu_chi_tiet=receipt_dict,
        )

        return {
            "trang_thai": dat_ban.trang_thai,
            "phan_tram_hoan_tien": pct,
            "so_tien_hoan": so_tien_hoan,
            "so_tien_phat": so_tien_phat,
            "moc_thoi_gian": moc,
            "phieu_hoan_tien": receipt_dict,
            "phieu_hoan_tien_id": pht.id,
        }
