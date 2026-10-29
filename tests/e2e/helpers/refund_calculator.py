"""
Authoritative Deposit Refund & Cancellation Policy Engine.
Implements the business logic defined in moc_schema_tieng_viet.sql (lines 281-287)
and Master Thesis Section 2.3 for table reservation deposit refunds.
"""

from datetime import datetime
from typing import Dict, Any, Tuple, Optional


POLICY_THRESHOLDS = {
    "TRUOC_24H": ("truoc_24h", 100.0, "da_hoan_tien"),
    "TU_6_DEN_24H": ("tu_6_den_24h", 50.0, "hoan_tien_mot_phan"),
    "TRONG_6H": ("trong_6h", 0.0, "that_bai"),
    "KHACH_KHONG_DEN": ("khach_khong_den", 0.0, "that_bai"),
}


def calculate_refund(
    thoi_gian_dat: datetime,
    thoi_gian_huy: datetime,
    so_tien_coc: float,
    is_no_show: bool = False,
) -> Tuple[str, float, float, float, str]:
    """
    Calculate the cancellation refund based on time delta in hours.
    Returns:
    (moc_thoi_gian, phan_tram_hoan, so_tien_hoan, so_tien_phat, trang_thai_coc)
    """
    if is_no_show:
        moc, pct, status = POLICY_THRESHOLDS["KHACH_KHONG_DEN"]
        return moc, pct, 0.0, so_tien_coc, status

    delta_seconds = (thoi_gian_dat - thoi_gian_huy).total_seconds()
    delta_hours = delta_seconds / 3600.0

    if delta_hours > 24.0:
        moc, pct, status = POLICY_THRESHOLDS["TRUOC_24H"]
        so_tien_hoan = float(so_tien_coc)
        so_tien_phat = 0.0
    elif 6.0 <= delta_hours <= 24.0:
        moc, pct, status = POLICY_THRESHOLDS["TU_6_DEN_24H"]
        so_tien_hoan = round(float(so_tien_coc) * 0.5, 2)
        so_tien_phat = round(float(so_tien_coc) - so_tien_hoan, 2)
    else:  # delta_hours < 6.0
        moc, pct, status = POLICY_THRESHOLDS["TRONG_6H"]
        so_tien_hoan = 0.0
        so_tien_phat = float(so_tien_coc)

    return moc, pct, so_tien_hoan, so_tien_phat, status


def generate_refund_receipt(
    ma_dat_ban: str,
    khach_hang_info: Dict[str, str],
    chi_nhanh_info: Dict[str, Any],
    thoi_gian_dat: datetime,
    thoi_gian_huy: datetime,
    so_tien_coc: float,
    ly_do_huy: str = "Khách hàng yêu cầu hủy",
    is_no_show: bool = False,
) -> Dict[str, Any]:
    """
    Generate an authoritative PhieuHoanTien audit record.
    """
    delta_seconds = (thoi_gian_dat - thoi_gian_huy).total_seconds()
    delta_hours = max(0.0, delta_seconds / 3600.0)

    moc, pct, so_tien_hoan, so_tien_phat, status = calculate_refund(
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
