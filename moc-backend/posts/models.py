from django.conf import settings
from django.db import models
from django.utils.text import slugify
from foods.models import MoHinhThoiGian


class DanhMucBaiViet(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    duong_dan = models.SlugField(max_length=120, unique=True, blank=True)
    mo_ta = models.TextField(blank=True)

    _LEGACY_MAP = {
        "name": "ten",
        "slug": "duong_dan",
        "description": "mo_ta",
    }

    class Meta:
        db_table = "danh_muc_bai_viet"
        verbose_name = "Danh mục bài viết"

    def save(self, *a, **kw):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*a, **kw)

    @property
    def name(self):
        return self.ten

    @name.setter
    def name(self, val):
        self.ten = val

    @property
    def slug(self):
        return self.duong_dan

    @slug.setter
    def slug(self, val):
        self.duong_dan = val

    @property
    def description(self):
        return self.mo_ta

    @description.setter
    def description(self, val):
        self.mo_ta = val


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

    _LEGACY_MAP = {
        "category": "danh_muc",
        "category_id": "danh_muc_id",
        "author": "tac_gia",
        "author_id": "tac_gia_id",
        "title": "tieu_de",
        "slug": "duong_dan",
        "thumbnail": "anh_dai_dien",
        "thumbnail_url": "anh_dai_dien",
        "content": "noi_dung",
        "status": "trang_thai",
        "published_at": "dang_luc",
    }

    class Meta:
        db_table = "bai_viet"
        verbose_name = "Bài viết"
        indexes = [models.Index(fields=["trang_thai", "-dang_luc"])]

    def save(self, *a, **kw):
        if not self.duong_dan:
            self.duong_dan = slugify(self.tieu_de)
        super().save(*a, **kw)

    @property
    def category(self):
        return self.danh_muc

    @category.setter
    def category(self, val):
        self.danh_muc = val

    @property
    def category_id(self):
        return self.danh_muc_id

    @category_id.setter
    def category_id(self, val):
        self.danh_muc_id = val

    @property
    def author(self):
        return self.tac_gia

    @author.setter
    def author(self, val):
        self.tac_gia = val

    @property
    def author_id(self):
        return self.tac_gia_id

    @author_id.setter
    def author_id(self, val):
        self.tac_gia_id = val

    @property
    def title(self):
        return self.tieu_de

    @title.setter
    def title(self, val):
        self.tieu_de = val

    @property
    def slug(self):
        return self.duong_dan

    @slug.setter
    def slug(self, val):
        self.duong_dan = val

    @property
    def content(self):
        return self.noi_dung

    @content.setter
    def content(self, val):
        self.noi_dung = val

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def thumbnail_url(self):
        return self.anh_dai_dien

    @thumbnail_url.setter
    def thumbnail_url(self, val):
        self.anh_dai_dien = val

    @property
    def published_at(self):
        return self.dang_luc

    @published_at.setter
    def published_at(self, val):
        self.dang_luc = val


# Backward-compatible model aliases
PostCategory = DanhMucBaiViet
Post = BaiViet
BaiViet.Status = BaiViet.TrangThai
Post.Status = BaiViet.TrangThai
