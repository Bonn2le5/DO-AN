from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian




class ThanhToan(MoHinhThoiGian):
    class LoaiThanhToan(models.TextChoices):
        DON_HANG = "don_hang", "Đơn hàng"
        TIEN_COC = "tien_coc", "Tiền cọc"

    class TrangThai(models.TextChoices):
        CHO_XU_LY = "cho_xu_ly", "Chờ xử lý"
        THANH_CONG = "thanh_cong", "Thành công"
        THAT_BAI = "that_bai", "Thất bại"
        DA_HOAN_TIEN = "da_hoan_tien", "Đã hoàn tiền"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_thanh_toan", on_delete=models.PROTECT
    )
    don_hang = models.ForeignKey(
        "orders.DonHang", related_name="danh_sach_thanh_toan",
        null=True, blank=True, on_delete=models.CASCADE
    )
    dat_ban = models.ForeignKey(
        "reservations.DatBan", related_name="danh_sach_thanh_toan",
        null=True, blank=True, on_delete=models.CASCADE
    )
    loai_thanh_toan = models.CharField(max_length=15, choices=LoaiThanhToan.choices)
    phuong_thuc = models.CharField(max_length=30)   # 'tien_mat','chuyen_khoan','vnpay',...
    so_tien = models.DecimalField(max_digits=12, decimal_places=2)
    ma_giao_dich = models.CharField(max_length=100, blank=True)   # vnp_TxnRef hoặc mã ngân hàng
    trang_thai = models.CharField(max_length=15, choices=TrangThai.choices, default=TrangThai.CHO_XU_LY)
    thanh_toan_luc = models.DateTimeField(null=True, blank=True)
    hoan_tien_luc = models.DateTimeField(null=True, blank=True)

    _LEGACY_MAP = {
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "order": "don_hang",
        "order_id": "don_hang_id",
        "reservation": "dat_ban",
        "reservation_id": "dat_ban_id",
        "payment_type": "loai_thanh_toan",
        "method": "phuong_thuc",
        "payment_method": "phuong_thuc",
        "amount": "so_tien",
        "transaction_id": "ma_giao_dich",
        "status": "trang_thai",
        "paid_at": "thanh_toan_luc",
        "refunded_at": "hoan_tien_luc",
    }

    class Meta:
        db_table = "thanh_toan"
        verbose_name = "Thanh toán"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(loai_thanh_toan="don_hang", don_hang__isnull=False, dat_ban__isnull=True)
                    | models.Q(loai_thanh_toan="tien_coc", dat_ban__isnull=False, don_hang__isnull=True)
                ),
                name="kiem_tra_muc_tieu_thanh_toan",
            )
        ]

    @property
    def amount(self):
        return self.so_tien

    @amount.setter
    def amount(self, val):
        self.so_tien = val

    @property
    def method(self):
        return self.phuong_thuc

    @method.setter
    def method(self, val):
        self.phuong_thuc = val

    @property
    def payment_method(self):
        return self.phuong_thuc

    @payment_method.setter
    def payment_method(self, val):
        self.phuong_thuc = val

    @property
    def transaction_id(self):
        return self.ma_giao_dich

    @transaction_id.setter
    def transaction_id(self, val):
        self.ma_giao_dich = val

    @property
    def user(self):
        return self.nguoi_dung

    @user.setter
    def user(self, val):
        self.nguoi_dung = val

    @property
    def user_id(self):
        return self.nguoi_dung_id

    @user_id.setter
    def user_id(self, val):
        self.nguoi_dung_id = val

    @property
    def order(self):
        return self.don_hang

    @order.setter
    def order(self, val):
        self.don_hang = val

    @property
    def order_id(self):
        return self.don_hang_id

    @order_id.setter
    def order_id(self, val):
        self.don_hang_id = val

    @property
    def reservation(self):
        return self.dat_ban

    @reservation.setter
    def reservation(self, val):
        self.dat_ban = val

    @property
    def reservation_id(self):
        return self.dat_ban_id

    @reservation_id.setter
    def reservation_id(self, val):
        self.dat_ban_id = val

    @property
    def payment_type(self):
        return self.loai_thanh_toan

    @payment_type.setter
    def payment_type(self, val):
        self.loai_thanh_toan = val

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def paid_at(self):
        return self.thanh_toan_luc

    @paid_at.setter
    def paid_at(self, val):
        self.thanh_toan_luc = val

    @property
    def refunded_at(self):
        return self.hoan_tien_luc

    @refunded_at.setter
    def refunded_at(self, val):
        self.hoan_tien_luc = val

    @property
    def created_at(self):
        return self.tao_luc

    @created_at.setter
    def created_at(self, val):
        self.tao_luc = val

    @property
    def updated_at(self):
        return self.cap_nhat_luc

    @updated_at.setter
    def updated_at(self, val):
        self.cap_nhat_luc = val


# Backward-compatible model aliases
Payment = ThanhToan
PaymentType = ThanhToan.LoaiThanhToan
PaymentStatus = ThanhToan.TrangThai
ThanhToan.PaymentType = ThanhToan.LoaiThanhToan
ThanhToan.Status = ThanhToan.TrangThai
Payment.PaymentType = ThanhToan.LoaiThanhToan
Payment.Status = ThanhToan.TrangThai


class PhieuHoanTien(MoHinhThoiGian):
    class MocThoiGian(models.TextChoices):
        TRUOC_24H = "truoc_24h", "Trước 24h"
        TU_6_DEN_24H = "tu_6_den_24h", "6–24h"
        TRONG_6H = "trong_6h", "Trong 6h"
        KHACH_KHONG_DEN = "khach_khong_den", "Khách không đến"

    class TrangThai(models.TextChoices):
        DA_HOAN_TIEN = "da_hoan_tien", "Đã hoàn tiền"
        HOAN_TIEN_MOT_PHAN = "hoan_tien_mot_phan", "Hoàn tiền một phần"
        THAT_BAI = "that_bai", "Thất bại"

    ma_phieu_hoan = models.CharField(max_length=50, unique=True, editable=False)
    dat_ban = models.ForeignKey(
        "reservations.DatBan", related_name="phieu_hoan_tien", on_delete=models.CASCADE
    )
    thanh_toan = models.ForeignKey(
        ThanhToan, related_name="phieu_hoan_tien", null=True, blank=True, on_delete=models.SET_NULL
    )
    so_tien_coc_goc = models.DecimalField(max_digits=12, decimal_places=2)
    phan_tram_hoan = models.DecimalField(max_digits=5, decimal_places=2)
    so_tien_hoan = models.DecimalField(max_digits=12, decimal_places=2)
    so_tien_phat = models.DecimalField(max_digits=12, decimal_places=2)
    moc_thoi_gian = models.CharField(max_length=20, choices=MocThoiGian.choices)
    so_gio_truoc_gio_hen = models.DecimalField(max_digits=7, decimal_places=2)
    ly_do_huy = models.TextField(blank=True)
    trang_thai = models.CharField(max_length=20, choices=TrangThai.choices)
    phuong_thuc_hoan = models.CharField(max_length=30, default="vnpay_refund")
    du_lieu_chi_tiet = models.JSONField(default=dict, blank=True)

    _LEGACY_MAP = {
        "refund_code": "ma_phieu_hoan",
        "code": "ma_phieu_hoan",
        "reservation": "dat_ban",
        "reservation_id": "dat_ban_id",
        "payment": "thanh_toan",
        "payment_id": "thanh_toan_id",
        "original_deposit": "so_tien_coc_goc",
        "original_amount": "so_tien_coc_goc",
        "refund_percentage": "phan_tram_hoan",
        "refund_percent": "phan_tram_hoan",
        "refund_amount": "so_tien_hoan",
        "penalty_amount": "so_tien_phat",
        "time_milestone": "moc_thoi_gian",
        "milestone": "moc_thoi_gian",
        "hours_before_booking": "so_gio_truoc_gio_hen",
        "cancel_reason": "ly_do_huy",
        "reason": "ly_do_huy",
        "status": "trang_thai",
        "refund_method": "phuong_thuc_hoan",
        "method": "phuong_thuc_hoan",
        "detail_data": "du_lieu_chi_tiet",
        "details": "du_lieu_chi_tiet",
    }

    class Meta:
        db_table = "phieu_hoan_tien"
        verbose_name = "Phiếu hoàn tiền"

    def __str__(self):
        return f"{self.ma_phieu_hoan} ({self.dat_ban.ma_dat_ban if self.dat_ban else ''})"

    @property
    def refund_code(self):
        return self.ma_phieu_hoan

    @refund_code.setter
    def refund_code(self, val):
        self.ma_phieu_hoan = val

    @property
    def reservation(self):
        return self.dat_ban

    @reservation.setter
    def reservation(self, val):
        self.dat_ban = val

    @property
    def payment(self):
        return self.thanh_toan

    @payment.setter
    def payment(self, val):
        self.thanh_toan = val

    @property
    def refund_amount(self):
        return self.so_tien_hoan

    @refund_amount.setter
    def refund_amount(self, val):
        self.so_tien_hoan = val

    @property
    def penalty_amount(self):
        return self.so_tien_phat

    @penalty_amount.setter
    def penalty_amount(self, val):
        self.so_tien_phat = val

    @property
    def refund_percentage(self):
        return self.phan_tram_hoan

    @refund_percentage.setter
    def refund_percentage(self, val):
        self.phan_tram_hoan = val

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val


# Backward-compatible model aliases for refund receipts
RefundReceipt = PhieuHoanTien
PhieuHoanTien.Status = PhieuHoanTien.TrangThai
PhieuHoanTien.Milestone = PhieuHoanTien.MocThoiGian
RefundReceipt.Status = PhieuHoanTien.TrangThai
RefundReceipt.Milestone = PhieuHoanTien.MocThoiGian

