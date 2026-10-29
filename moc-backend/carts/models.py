from django.conf import settings
from django.db import models
from django.db.models import Q
from foods.models import MoHinhThoiGian, MonAn, Food


class GioHang(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        DANG_SU_DUNG = "dang_su_dung", "Đang sử dụng"
        DA_THANH_TOAN = "da_thanh_toan", "Đã thanh toán"
        BO_DO = "bo_do", "Bỏ dở"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_gio_hang", on_delete=models.CASCADE
    )
    trang_thai = models.CharField(
        max_length=20, choices=TrangThai.choices, default=TrangThai.DANG_SU_DUNG
    )

    _LEGACY_MAP = {
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "status": "trang_thai",
    }

    class Meta:
        db_table = "gio_hang"
        verbose_name = "Giỏ hàng"
        constraints = [
            models.UniqueConstraint(
                fields=["nguoi_dung"],
                condition=Q(trang_thai="dang_su_dung"),
                name="uq_gio_hang_active"
            )
        ]

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
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def items(self):
        return self.danh_sach_mon

    @items.setter
    def items(self, val):
        if self.pk and hasattr(self.danh_sach_mon, "set"):
            self.danh_sach_mon.set(val)
        else:
            self._uncommitted_items = val


class ChiTietGioHang(MoHinhThoiGian):
    gio_hang = models.ForeignKey(GioHang, related_name="danh_sach_mon", on_delete=models.CASCADE)
    mon_an = models.ForeignKey("foods.MonAn", related_name="chi_tiet_gio_hang", on_delete=models.PROTECT)
    so_luong = models.PositiveIntegerField()
    don_gia_luc_dat = models.DecimalField(max_digits=12, decimal_places=2)
    ghi_chu = models.TextField(blank=True)

    _LEGACY_MAP = {
        "cart": "gio_hang",
        "cart_id": "gio_hang_id",
        "food": "mon_an",
        "food_id": "mon_an_id",
        "quantity": "so_luong",
        "unit_price": "don_gia_luc_dat",
        "price": "don_gia_luc_dat",
        "note": "ghi_chu",
    }

    class Meta:
        db_table = "chi_tiet_gio_hang"
        unique_together = ("gio_hang", "mon_an")
        verbose_name = "Chi tiết giỏ hàng"

    @property
    def cart(self):
        return self.gio_hang

    @cart.setter
    def cart(self, val):
        self.gio_hang = val

    @property
    def cart_id(self):
        return self.gio_hang_id

    @cart_id.setter
    def cart_id(self, val):
        self.gio_hang_id = val

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
    def quantity(self):
        return self.so_luong

    @quantity.setter
    def quantity(self, val):
        self.so_luong = val

    @property
    def unit_price(self):
        return self.don_gia_luc_dat

    @unit_price.setter
    def unit_price(self, val):
        self.don_gia_luc_dat = val

    @property
    def price(self):
        return self.don_gia_luc_dat

    @price.setter
    def price(self, val):
        self.don_gia_luc_dat = val

    @property
    def note(self):
        return self.ghi_chu

    @note.setter
    def note(self, val):
        self.ghi_chu = val


# Backward-compatible model aliases
Cart = GioHang
CartItem = ChiTietGioHang
GioHang.Status = GioHang.TrangThai
Cart.Status = GioHang.TrangThai
