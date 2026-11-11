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
    phuong_thuc = models.CharField(max_length=30)   # 'tien_mat','chuyen_khoan','payos',...
    so_tien = models.DecimalField(max_digits=12, decimal_places=2)
    ma_giao_dich = models.CharField(max_length=100, blank=True)   # orderCode PayOS hoặc mã ngân hàng
    trang_thai = models.CharField(max_length=15, choices=TrangThai.choices, default=TrangThai.CHO_XU_LY)
    thanh_toan_luc = models.DateTimeField(null=True, blank=True)
    hoan_tien_luc = models.DateTimeField(null=True, blank=True)


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
    phuong_thuc_hoan = models.CharField(max_length=30, default="chuyen_khoan")
    du_lieu_chi_tiet = models.JSONField(default=dict, blank=True)


    class Meta:
        db_table = "phieu_hoan_tien"
        verbose_name = "Phiếu hoàn tiền"

    def __str__(self):
        return f"{self.ma_phieu_hoan} ({self.dat_ban.ma_dat_ban if self.dat_ban else ''})"
