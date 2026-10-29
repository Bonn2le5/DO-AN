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

    _LEGACY_MAP = {
        "code": "ma_giam_gia",
        "name": "ten",
        "title": "ten",
        "description": "mo_ta",
        "discount_type": "kieu_giam",
        "discount_value": "gia_tri_giam",
        "min_order_value": "don_hang_toi_thieu",
        "max_discount": "giam_toi_da",
        "start_at": "bat_dau_luc",
        "start_date": "bat_dau_luc",
        "end_at": "ket_thuc_luc",
        "end_date": "ket_thuc_luc",
        "usage_limit": "gioi_han_su_dung",
        "used_count": "so_lan_da_dung",
        "is_active": "con_hoat_dong",
    }

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

    @property
    def code(self):
        return self.ma_giam_gia

    @code.setter
    def code(self, val):
        self.ma_giam_gia = val

    @property
    def name(self):
        return self.ten

    @name.setter
    def name(self, val):
        self.ten = val

    @property
    def title(self):
        return self.ten

    @title.setter
    def title(self, val):
        self.ten = val

    @property
    def description(self):
        return self.mo_ta

    @description.setter
    def description(self, val):
        self.mo_ta = val

    @property
    def discount_type(self):
        return self.kieu_giam

    @discount_type.setter
    def discount_type(self, val):
        self.kieu_giam = val

    @property
    def discount_value(self):
        return self.gia_tri_giam

    @discount_value.setter
    def discount_value(self, val):
        self.gia_tri_giam = val

    @property
    def min_order_value(self):
        return self.don_hang_toi_thieu

    @min_order_value.setter
    def min_order_value(self, val):
        self.don_hang_toi_thieu = val

    @property
    def max_discount(self):
        return self.giam_toi_da

    @max_discount.setter
    def max_discount(self, val):
        self.giam_toi_da = val

    @property
    def is_active(self):
        return self.con_hoat_dong

    @is_active.setter
    def is_active(self, val):
        self.con_hoat_dong = bool(val)

    @property
    def start_at(self):
        return self.bat_dau_luc

    @start_at.setter
    def start_at(self, val):
        self.bat_dau_luc = val

    @property
    def start_date(self):
        return self.bat_dau_luc

    @start_date.setter
    def start_date(self, val):
        self.bat_dau_luc = val

    @property
    def end_at(self):
        return self.ket_thuc_luc

    @end_at.setter
    def end_at(self, val):
        self.ket_thuc_luc = val

    @property
    def end_date(self):
        return self.ket_thuc_luc

    @end_date.setter
    def end_date(self, val):
        self.ket_thuc_luc = val

    @property
    def usage_limit(self):
        return self.gioi_han_su_dung

    @usage_limit.setter
    def usage_limit(self, val):
        self.gioi_han_su_dung = val

    @property
    def used_count(self):
        return self.so_lan_da_dung

    @used_count.setter
    def used_count(self, val):
        self.so_lan_da_dung = val

    @property
    def codes(self):
        return self.danh_sach_ma

    @codes.setter
    def codes(self, val):
        if self.pk and hasattr(self.danh_sach_ma, "set"):
            self.danh_sach_ma.set(val)
        else:
            self._uncommitted_codes = val


class MaKhuyenMai(MoHinhThoiGian):
    """Mã phụ/cá nhân hoá phát sinh dưới 1 KhuyenMai."""
    khuyen_mai = models.ForeignKey(KhuyenMai, related_name="danh_sach_ma", on_delete=models.CASCADE)
    ma = models.CharField(max_length=50, unique=True)
    gioi_han = models.PositiveIntegerField(null=True, blank=True)
    da_dung = models.PositiveIntegerField(default=0)
    con_hoat_dong = models.BooleanField(default=True)

    _LEGACY_MAP = {
        "promotion": "khuyen_mai",
        "promotion_id": "khuyen_mai_id",
        "code": "ma",
        "limit": "gioi_han",
        "used_count": "da_dung",
        "is_active": "con_hoat_dong",
    }

    class Meta:
        db_table = "ma_khuyen_mai"

    @property
    def promotion(self):
        return self.khuyen_mai

    @promotion.setter
    def promotion(self, val):
        self.khuyen_mai = val

    @property
    def promotion_id(self):
        return self.khuyen_mai_id

    @promotion_id.setter
    def promotion_id(self, val):
        self.khuyen_mai_id = val

    @property
    def code(self):
        return self.ma

    @code.setter
    def code(self, val):
        self.ma = val

    @property
    def limit(self):
        return self.gioi_han

    @limit.setter
    def limit(self, val):
        self.gioi_han = val

    @property
    def used_count(self):
        return self.da_dung

    @used_count.setter
    def used_count(self, val):
        self.da_dung = val

    @property
    def is_active(self):
        return self.con_hoat_dong

    @is_active.setter
    def is_active(self, val):
        self.con_hoat_dong = bool(val)


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

    _LEGACY_MAP = {
        "promotion": "khuyen_mai",
        "promotion_id": "khuyen_mai_id",
        "coupon": "ma_khuyen_mai",
        "coupon_id": "ma_khuyen_mai_id",
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "order": "don_hang",
        "order_id": "don_hang_id",
        "discount_amount": "so_tien_giam",
    }

    class Meta:
        db_table = "lich_su_dung_khuyen_mai"
        unique_together = ("don_hang", "khuyen_mai")

    @property
    def promotion(self):
        return self.khuyen_mai

    @promotion.setter
    def promotion(self, val):
        self.khuyen_mai = val

    @property
    def coupon(self):
        return self.ma_khuyen_mai

    @coupon.setter
    def coupon(self, val):
        self.ma_khuyen_mai = val

    @property
    def user(self):
        return self.nguoi_dung

    @user.setter
    def user(self, val):
        self.nguoi_dung = val

    @property
    def order(self):
        return self.don_hang

    @order.setter
    def order(self, val):
        self.don_hang = val

    @property
    def discount_amount(self):
        return self.so_tien_giam

    @discount_amount.setter
    def discount_amount(self, val):
        self.so_tien_giam = val


# Backward-compatible model aliases
Promotion = KhuyenMai
PromotionCode = MaKhuyenMai
PromotionUsage = LichSuDungKhuyenMai
DiscountType = KhuyenMai.KieuGiam
KhuyenMai.DiscountType = KhuyenMai.KieuGiam
Promotion.DiscountType = KhuyenMai.KieuGiam
