from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn, Food


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

    _LEGACY_MAP = {
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "food": "mon_an",
        "food_id": "mon_an_id",
        "order": "don_hang",
        "order_id": "don_hang_id",
        "order_item": "chi_tiet_don_hang",
        "order_item_id": "chi_tiet_don_hang_id",
        "rating": "diem_danh_gia",
        "score": "diem_danh_gia",
        "comment": "nhan_xet",
        "review": "nhan_xet",
        "is_visible": "hien_thi",
    }

    class Meta:
        db_table = "danh_gia"
        verbose_name = "Đánh giá"
        indexes = [models.Index(fields=["mon_an"])]

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
    def food(self):
        return self.mon_an

    @food.setter
    def food(self, val):
        self.mon_an = val

    @property
    def food_id(self):
        return self.mon_an_id

    @food_id.setter
    def food_id(self, val):
        self.mon_an_id = val

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
    def order_item(self):
        return self.chi_tiet_don_hang

    @order_item.setter
    def order_item(self, val):
        self.chi_tiet_don_hang = val

    @property
    def order_item_id(self):
        return self.chi_tiet_don_hang_id

    @order_item_id.setter
    def order_item_id(self, val):
        self.chi_tiet_don_hang_id = val

    @property
    def rating(self):
        return self.diem_danh_gia

    @rating.setter
    def rating(self, val):
        self.diem_danh_gia = val

    @property
    def score(self):
        return self.diem_danh_gia

    @score.setter
    def score(self, val):
        self.diem_danh_gia = val

    @property
    def comment(self):
        return self.nhan_xet

    @comment.setter
    def comment(self, val):
        self.nhan_xet = val

    @property
    def review(self):
        return self.nhan_xet

    @review.setter
    def review(self, val):
        self.nhan_xet = val

    @property
    def is_visible(self):
        return self.hien_thi

    @is_visible.setter
    def is_visible(self, val):
        self.hien_thi = bool(val)


# Backward-compatible model aliases
Review = DanhGia