from django.conf import settings
from django.db import models
from django.utils.text import slugify
from foods.models import MoHinhThoiGian


class DanhMucBaiViet(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    duong_dan = models.SlugField(max_length=120, unique=True, blank=True)
    mo_ta = models.TextField(blank=True)


    class Meta:
        db_table = "danh_muc_bai_viet"
        verbose_name = "Danh mục bài viết"

    def save(self, *a, **kw):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*a, **kw)


class BaiViet(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        NHAP = "nhap", "Bản nháp"
        DA_DANG = "da_dang", "Đã đăng"
        LUU_TRU = "luu_tru", "Lưu trữ"

    danh_muc = models.ForeignKey(
        DanhMucBaiViet, null=True, blank=True,
        related_name="danh_sach_bai_viet", on_delete=models.SET_NULL
    )
    tac_gia = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_bai_viet", on_delete=models.PROTECT
    )
    tieu_de = models.CharField(max_length=200)
    duong_dan = models.SlugField(max_length=220, unique=True, blank=True)
    anh_dai_dien = models.TextField(blank=True)
    noi_dung = models.TextField()
    trang_thai = models.CharField(max_length=10, choices=TrangThai.choices, default=TrangThai.NHAP)
    dang_luc = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = "bai_viet"
        verbose_name = "Bài viết"
        indexes = [models.Index(fields=["trang_thai", "-dang_luc"])]

    def save(self, *a, **kw):
        if not self.duong_dan:
            self.duong_dan = slugify(self.tieu_de)
        super().save(*a, **kw)
