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


class LegacyKwargsMixin:
    """
    Mixin chuyển đổi keyword arguments tiếng Anh cũ sang tên trường canonical tiếng Việt
    ngay khi khởi tạo instance model qua __init__.
    """
    def __init__(self, *args, **kwargs):
        if kwargs:
            for cls in reversed(self.__class__.__mro__):
                lmap = cls.__dict__.get("_LEGACY_MAP", None)
                if lmap:
                    for leg_k, can_k in lmap.items():
                        if leg_k in kwargs:
                            val = kwargs.pop(leg_k)
                            if can_k not in kwargs:
                                kwargs[can_k] = val
        super().__init__(*args, **kwargs)


class MoHinhThoiGian(LegacyKwargsMixin, models.Model):
    tao_luc = models.DateTimeField(auto_now_add=True)
    cap_nhat_luc = models.DateTimeField(auto_now=True)

    _LEGACY_MAP = {
        "created_at": "tao_luc",
        "updated_at": "cap_nhat_luc",
    }

    class Meta:
        abstract = True

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


class TimeStampedModel(MoHinhThoiGian):
    class Meta:
        abstract = True


class DanhMuc(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    duong_dan = models.SlugField(unique=True, blank=True)
    mo_ta = models.TextField(blank=True)
    anh_dai_dien = models.ImageField(upload_to="danh_muc/", blank=True, null=True)
    con_hoat_dong = models.BooleanField(default=True)

    _LEGACY_MAP = {
        "name": "ten",
        "slug": "duong_dan",
        "description": "mo_ta",
        "image": "anh_dai_dien",
        "is_active": "con_hoat_dong",
    }

    class Meta:
        db_table = "danh_muc"
        verbose_name = "Danh mục"

    def save(self, *args, **kwargs):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*args, **kwargs)

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

    @property
    def image(self):
        return self.anh_dai_dien

    @image.setter
    def image(self, val):
        self.anh_dai_dien = val

    @property
    def is_active(self):
        return self.con_hoat_dong

    @is_active.setter
    def is_active(self, val):
        self.con_hoat_dong = val

    def __str__(self):
        return self.ten


class TheMonAn(MoHinhThoiGian):
    ten = models.CharField(max_length=50)
    duong_dan = models.SlugField(unique=True, blank=True)

    _LEGACY_MAP = {
        "name": "ten",
        "slug": "duong_dan",
    }

    class Meta:
        db_table = "the_mon_an"
        verbose_name = "Thẻ món ăn"

    def save(self, *args, **kwargs):
        if not self.duong_dan:
            self.duong_dan = slugify(self.ten)
        super().save(*args, **kwargs)

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

    def __str__(self):
        return self.ten


class NguyenLieu(MoHinhThoiGian):
    ten = models.CharField(max_length=100, unique=True)
    don_vi = models.CharField(max_length=30, blank=True)
    ton_kho_hien_tai = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    ton_kho_toi_thieu = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    con_hoat_dong = models.BooleanField(default=True)

    _LEGACY_MAP = {
        "name": "ten",
        "unit": "don_vi",
        "current_stock": "ton_kho_hien_tai",
        "min_stock": "ton_kho_toi_thieu",
        "is_active": "con_hoat_dong",
    }

    class Meta:
        db_table = "nguyen_lieu"
        verbose_name = "Nguyên liệu"

    @property
    def name(self):
        return self.ten

    @name.setter
    def name(self, val):
        self.ten = val

    @property
    def unit(self):
        return self.don_vi

    @unit.setter
    def unit(self, val):
        self.don_vi = val

    @property
    def current_stock(self):
        return self.ton_kho_hien_tai

    @current_stock.setter
    def current_stock(self, val):
        self.ton_kho_hien_tai = val

    @property
    def min_stock(self):
        return self.ton_kho_toi_thieu

    @min_stock.setter
    def min_stock(self, val):
        self.ton_kho_toi_thieu = val

    @property
    def is_active(self):
        return self.con_hoat_dong

    @is_active.setter
    def is_active(self, val):
        self.con_hoat_dong = val

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

    _LEGACY_MAP = {
        "name": "ten",
        "price": "don_gia",
        "current_price": "don_gia",
        "category": "danh_muc",
        "category_id": "danh_muc_id",
        "slug": "duong_dan",
        "short_description": "mo_ta_ngan",
        "description": "mo_ta_chi_tiet",
        "is_available": "con_hang",
        "is_featured": "noi_bat",
        "is_vegetarian": "la_mon_chay",
        "spicy_level": "do_cay",
        "rating_avg": "diem_danh_gia",
        "review_count": "so_luot_danh_gia",
    }

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

    @property
    def current_price(self):
        return self.don_gia

    @current_price.setter
    def current_price(self, val):
        self.don_gia = val

    @property
    def price(self):
        return self.don_gia

    @price.setter
    def price(self, val):
        self.don_gia = val

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
    def is_active(self):
        return self.con_hang and self.hien_thi

    @is_active.setter
    def is_active(self, val):
        self.con_hang = bool(val)
        self.hien_thi = bool(val)

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
    def short_description(self):
        return self.mo_ta_ngan

    @short_description.setter
    def short_description(self, val):
        self.mo_ta_ngan = val

    @property
    def description(self):
        return self.mo_ta_chi_tiet or self.mo_ta_ngan

    @description.setter
    def description(self, val):
        self.mo_ta_chi_tiet = val

    @property
    def is_available(self):
        return self.con_hang

    @is_available.setter
    def is_available(self, val):
        self.con_hang = bool(val)

    @property
    def is_featured(self):
        return self.noi_bat

    @is_featured.setter
    def is_featured(self, val):
        self.noi_bat = bool(val)

    @property
    def is_vegetarian(self):
        return self.la_mon_chay

    @is_vegetarian.setter
    def is_vegetarian(self, val):
        self.la_mon_chay = bool(val)

    @property
    def spicy_level(self):
        return self.do_cay

    @spicy_level.setter
    def spicy_level(self, val):
        self.do_cay = val

    @property
    def rating_avg(self):
        return self.diem_danh_gia

    @rating_avg.setter
    def rating_avg(self, val):
        self.diem_danh_gia = val

    @property
    def review_count(self):
        return self.so_luot_danh_gia

    @review_count.setter
    def review_count(self, val):
        self.so_luot_danh_gia = val

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

    _LEGACY_MAP = {
        "food": "mon_an",
        "food_id": "mon_an_id",
        "image": "anh",
        "description": "van_ban_mo_ta",
        "is_primary": "la_anh_chinh",
        "order": "thu_tu",
    }

    class Meta:
        db_table = "hinh_anh_mon_an"

    @property
    def food(self):
        return self.mon_an

    @food.setter
    def food(self, val):
        self.mon_an = val

    @property
    def image(self):
        return self.anh

    @image.setter
    def image(self, val):
        self.anh = val

    @property
    def is_primary(self):
        return self.la_anh_chinh

    @is_primary.setter
    def is_primary(self, val):
        self.la_anh_chinh = bool(val)

    @property
    def order(self):
        return self.thu_tu

    @order.setter
    def order(self, val):
        self.thu_tu = val


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


# Backward-compatible model aliases
Category = DanhMuc
Tag = TheMonAn
Ingredient = NguyenLieu
Food = MonAn
FoodTag = MonAnThe
FoodIngredient = DinhMucNguyenLieu
FoodImage = HinhAnhMonAn
InventoryTransaction = LichSuXuatNhapKho
InventoryHistory = LichSuXuatNhapKho
