from django.conf import settings
from django.db import models
from django.utils.text import slugify
import inspect

# Ensure CheckConstraint compatibility across Django 4.x, 5.x, and 6.x
if not getattr(models.CheckConstraint, "_is_compat_patched", False):
    _orig_cc_init = models.CheckConstraint.__init__
    def _compat_cc_init(self, *args, **kwargs):
        sig = inspect.signature(_orig_cc_init)
        if "condition" in sig.parameters and "check" in kwargs:
            kwargs["condition"] = kwargs.pop("check")
        elif "check" in sig.parameters and "condition" in kwargs:
            kwargs["check"] = kwargs.pop("condition")
        return _orig_cc_init(self, *args, **kwargs)
    models.CheckConstraint.__init__ = _compat_cc_init
    models.CheckConstraint._is_compat_patched = True


class MoHinhThoiGian(models.Model):
    tao_luc = models.DateTimeField(auto_now_add=True)
    cap_nhat_luc = models.DateTimeField(auto_now=True)


    class Meta:
        abstract = True


class DanhMuc(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    duong_dan = models.SlugField(unique=True, blank=True)
    mo_ta = models.TextField(blank=True)
    anh_dai_dien = models.ImageField(upload_to="danh_muc/", blank=True, null=True)
    con_hoat_dong = models.BooleanField(default=True)


    class Meta:
        db_table = "danh_muc"
        verbose_name = "Danh mục"

    def save(self, *args, **kwargs):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.ten


class TheMonAn(MoHinhThoiGian):
    ten = models.CharField(max_length=50)
    duong_dan = models.SlugField(unique=True, blank=True)


    class Meta:
        db_table = "the_mon_an"
        verbose_name = "Thẻ món ăn"

    def save(self, *args, **kwargs):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.ten


class NguyenLieu(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    don_vi = models.CharField(max_length=30, blank=True)
    ton_kho_hien_tai = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    ton_kho_toi_thieu = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    con_hoat_dong = models.BooleanField(default=True)


    class Meta:
        db_table = "nguyen_lieu"
        verbose_name = "Nguyên liệu"


    def __str__(self):
        return self.ten


class MonAn(MoHinhThoiGian):
    danh_muc = models.ForeignKey(DanhMuc, related_name="danh_sach_mon", on_delete=models.PROTECT)
    ten = models.CharField(max_length=180, db_index=True)
    duong_dan = models.SlugField(unique=True, blank=True)
    mo_ta_ngan = models.TextField(blank=True)
    mo_ta_chi_tiet = models.TextField(blank=True)
    don_gia = models.DecimalField(max_digits=12, decimal_places=2)
    ton_kho_cache = models.PositiveIntegerField(null=True, blank=True)   # cache; dùng khi quan_ly_kho=False
    con_hang = models.BooleanField(default=True, db_index=True)
    hien_thi = models.BooleanField(default=True)
    noi_bat = models.BooleanField(default=False)
    la_mon_chay = models.BooleanField(default=False)
    do_cay = models.PositiveSmallIntegerField(default=0)
    quan_ly_kho = models.BooleanField(default=False)
    the_mon_an = models.ManyToManyField(TheMonAn, through="MonAnThe", related_name="danh_sach_mon", blank=True)
    diem_danh_gia = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    so_luot_danh_gia = models.PositiveIntegerField(default=0)
    nguyen_lieu = models.ManyToManyField(NguyenLieu, through="DinhMucNguyenLieu", blank=True)


    class Meta:
        db_table = "mon_an"
        verbose_name = "Món ăn"
        ordering = ["-tao_luc"]
        indexes = [
            models.Index(fields=["danh_muc", "con_hang"]),
            models.Index(fields=["ten"]),
        ]

    def save(self, *args, **kwargs):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*args, **kwargs)

    @property
    def don_gia_hien_tai(self):
        return self.don_gia

    @don_gia_hien_tai.setter
    def don_gia_hien_tai(self, val):
        self.don_gia = val


    def __str__(self):
        return self.ten


class MonAnThe(models.Model):
    mon_an = models.ForeignKey(MonAn, on_delete=models.CASCADE)
    the = models.ForeignKey(TheMonAn, on_delete=models.CASCADE)

    class Meta:
        db_table = "mon_an_the"
        unique_together = ("mon_an", "the")


class DinhMucNguyenLieu(models.Model):
    mon_an = models.ForeignKey(MonAn, on_delete=models.CASCADE)
    nguyen_lieu = models.ForeignKey(NguyenLieu, on_delete=models.PROTECT)
    so_luong_can = models.DecimalField(max_digits=14, decimal_places=3)

    class Meta:
        db_table = "dinh_muc_nguyen_lieu"
        unique_together = ("mon_an", "nguyen_lieu")


class HinhAnhMonAn(MoHinhThoiGian):
    mon_an = models.ForeignKey(MonAn, related_name="hinh_anh", on_delete=models.CASCADE)
    anh = models.ImageField(upload_to="mon_an/")
    van_ban_mo_ta = models.CharField(max_length=200, blank=True)
    la_anh_chinh = models.BooleanField(default=False)
    thu_tu = models.PositiveIntegerField(default=0)


    class Meta:
        db_table = "hinh_anh_mon_an"


class LichSuXuatNhapKho(MoHinhThoiGian):
    class LoaiGiaoDich(models.TextChoices):
        NHAP = "nhap", "Nhập kho"
        XUAT = "xuat", "Xuất kho"
        DIEU_CHINH = "dieu_chinh", "Điều chỉnh"

    nguyen_lieu = models.ForeignKey(NguyenLieu, related_name="lich_su_giao_dich", on_delete=models.PROTECT)
    loai_giao_dich = models.CharField(max_length=15, choices=LoaiGiaoDich.choices)
    so_luong = models.DecimalField(max_digits=14, decimal_places=3)
    ton_kho_truoc = models.DecimalField(max_digits=14, decimal_places=3)
    ton_kho_sau = models.DecimalField(max_digits=14, decimal_places=3)
    loai_tham_chieu = models.CharField(max_length=30, blank=True)
    id_tham_chieu = models.BigIntegerField(null=True, blank=True)
    ghi_chu = models.TextField(blank=True)
    tao_boi = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        db_table = "lich_su_xuat_nhap_kho"
