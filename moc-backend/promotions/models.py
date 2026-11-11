from django.conf import settings
from django.db import models
from django.utils import timezone
from foods.models import MoHinhThoiGian


class KhuyenMai(MoHinhThoiGian):
    class KieuGiam(models.TextChoices):
        PHAN_TRAM = "phan_tram", "Phần trăm"
        SO_TIEN = "so_tien_co_dinh", "Số tiền cố định"

    ma_giam_gia = models.CharField(max_length=50, unique=True)
    ten = models.CharField(max_length=150)
    mo_ta = models.TextField(blank=True)
    kieu_giam = models.CharField(max_length=20, choices=KieuGiam.choices)
    gia_tri_giam = models.DecimalField(max_digits=12, decimal_places=2)
    don_hang_toi_thieu = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    giam_toi_da = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bat_dau_luc = models.DateTimeField()
    ket_thuc_luc = models.DateTimeField()
    gioi_han_su_dung = models.PositiveIntegerField(null=True, blank=True)
    so_lan_da_dung = models.PositiveIntegerField(default=0)
    con_hoat_dong = models.BooleanField(default=True)


    class Meta:
        db_table = "khuyen_mai"
        verbose_name = "Khuyến mãi"

    def con_hieu_luc(self):
        thoi_gian_hien_tai = timezone.now()
        return self.con_hoat_dong and self.bat_dau_luc <= thoi_gian_hien_tai <= self.ket_thuc_luc

    def tinh_tien_giam(self, tien_hang):
        if not self.con_hieu_luc() or tien_hang < self.don_hang_toi_thieu:
            return 0
        if self.kieu_giam == self.KieuGiam.PHAN_TRAM:
            so_tien_giam = tien_hang * self.gia_tri_giam / 100
        else:
            so_tien_giam = self.gia_tri_giam
        return min(so_tien_giam, self.giam_toi_da) if self.giam_toi_da else so_tien_giam

    def __str__(self):
        return f"{self.ma_giam_gia} - {self.ten}"


class MaKhuyenMai(MoHinhThoiGian):
    """Mã phụ/cá nhân hoá phát sinh dưới 1 KhuyenMai."""
    khuyen_mai = models.ForeignKey(KhuyenMai, related_name="danh_sach_ma", on_delete=models.CASCADE)
    ma = models.CharField(max_length=50, unique=True)
    gioi_han = models.PositiveIntegerField(null=True, blank=True)
    da_dung = models.PositiveIntegerField(default=0)
    con_hoat_dong = models.BooleanField(default=True)


    class Meta:
        db_table = "ma_khuyen_mai"


class LichSuDungKhuyenMai(MoHinhThoiGian):
    khuyen_mai = models.ForeignKey(KhuyenMai, related_name="lich_su_su_dung", on_delete=models.CASCADE)
    ma_khuyen_mai = models.ForeignKey(MaKhuyenMai, null=True, blank=True, on_delete=models.SET_NULL)
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="lich_su_khuyen_mai", on_delete=models.CASCADE
    )
    don_hang = models.ForeignKey(
        "orders.DonHang", related_name="lich_su_khuyen_mai", on_delete=models.CASCADE
    )
    so_tien_giam = models.DecimalField(max_digits=12, decimal_places=2)


    class Meta:
        db_table = "lich_su_dung_khuyen_mai"
        unique_together = ("don_hang", "khuyen_mai")
