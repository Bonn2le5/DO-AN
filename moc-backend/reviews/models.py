from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn


class DanhGia(MoHinhThoiGian):
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_danh_gia", on_delete=models.CASCADE
    )
    mon_an = models.ForeignKey(
        "foods.MonAn", related_name="danh_sach_danh_gia", on_delete=models.CASCADE
    )
    don_hang = models.ForeignKey(
        "orders.DonHang", related_name="danh_sach_danh_gia", on_delete=models.CASCADE
    )
    chi_tiet_don_hang = models.OneToOneField(
        "orders.ChiTietDonHang", related_name="danh_gia", on_delete=models.CASCADE
    )
    diem_danh_gia = models.PositiveSmallIntegerField()
    nhan_xet = models.TextField(blank=True)
    hien_thi = models.BooleanField(default=True)


    class Meta:
        db_table = "danh_gia"
        verbose_name = "Đánh giá"
        indexes = [models.Index(fields=["mon_an"])]


class DanhGiaBuaAn(MoHinhThoiGian):
    """Đánh giá chung cho cả bữa ăn (một đơn tại bàn): phục vụ và không gian."""

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_danh_gia_bua_an", on_delete=models.CASCADE
    )
    don_hang = models.OneToOneField(
        "orders.DonHang", related_name="danh_gia_bua_an", on_delete=models.CASCADE
    )
    diem_phuc_vu = models.PositiveSmallIntegerField()
    diem_khong_gian = models.PositiveSmallIntegerField()
    nhan_xet = models.TextField(blank=True)
    hien_thi = models.BooleanField(default=True)

    class Meta:
        db_table = "danh_gia_bua_an"
        verbose_name = "Đánh giá bữa ăn"
