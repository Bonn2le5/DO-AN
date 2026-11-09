from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn


class TuongTacMonAn(MoHinhThoiGian):
    class LoaiTuongTac(models.TextChoices):
        XEM = "xem", "Xem"
        YEU_THICH = "yeu_thich", "Yêu thích"
        DAT_MON = "dat_mon", "Đặt món"
        DANH_GIA = "danh_gia", "Đánh giá"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="tuong_tac_mon_an", on_delete=models.CASCADE
    )
    mon_an = models.ForeignKey(MonAn, related_name="danh_sach_tuong_tac", on_delete=models.CASCADE)
    loai_tuong_tac = models.CharField(max_length=20, choices=LoaiTuongTac.choices)
    trong_so = models.DecimalField(max_digits=5, decimal_places=2, default=1)


    class Meta:
        db_table = "tuong_tac_mon_an"
        indexes = [models.Index(fields=["nguoi_dung", "tao_luc"])]
        verbose_name = "Tương tác món ăn"


class GoiYMonAn(MoHinhThoiGian):
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_goi_y", on_delete=models.CASCADE
    )
    mon_an = models.ForeignKey(MonAn, on_delete=models.CASCADE)
    diem_tuong_dong = models.DecimalField(max_digits=5, decimal_places=4)  # cosine similarity
    ly_do_goi_y = models.TextField(blank=True)
    phien_ban_model = models.CharField(max_length=30, blank=True)
    thu_hang = models.PositiveSmallIntegerField(default=0)  # vị trí trong Top-N (0 = đầu)


    class Meta:
        db_table = "goi_y_mon_an"
        unique_together = ("nguoi_dung", "mon_an", "phien_ban_model")
        verbose_name = "Gợi ý món ăn"


class SuKienGoiY(MoHinhThoiGian):
    """
    Nhật ký hiển thị / nhấp vào món được gợi ý — nguồn dữ liệu để đo CTR và Conversion.
    nguoi_dung để trống với khách chưa đăng nhập (chỉ tính vào CTR).
    """

    class LoaiSuKien(models.TextChoices):
        HIEN_THI = "hien_thi", "Hiển thị"
        NHAP = "nhap", "Nhấp / chọn món"

    class ViTri(models.TextChoices):
        TRANG_CHU = "trang_chu", "Trang chủ"
        CHI_TIET_MON = "chi_tiet_mon", "Món tương tự (chi tiết món)"
        GOI_MON = "goi_mon", "Bước gọi món khi đặt bàn"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="su_kien_goi_y",
        null=True, blank=True, on_delete=models.CASCADE,
    )
    mon_an = models.ForeignKey(MonAn, related_name="su_kien_goi_y", on_delete=models.CASCADE)
    loai_su_kien = models.CharField(max_length=20, choices=LoaiSuKien.choices)
    vi_tri = models.CharField(max_length=20, choices=ViTri.choices, default=ViTri.TRANG_CHU)
    phien_ban_model = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = "su_kien_goi_y"
        indexes = [models.Index(fields=["loai_su_kien", "tao_luc"])]
        verbose_name = "Sự kiện gợi ý"


# Backward-compatible model aliases
FoodInteraction = TuongTacMonAn
Recommendation = GoiYMonAn
TuongTacMonAn.Type = TuongTacMonAn.LoaiTuongTac
FoodInteraction.Type = TuongTacMonAn.LoaiTuongTac
