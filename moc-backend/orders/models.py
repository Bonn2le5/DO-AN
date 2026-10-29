import uuid
from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn


class DonHang(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        CHO_TIEP_NHAN = "cho_tiep_nhan", "Chờ tiếp nhận"
        DA_XAC_NHAN = "da_xac_nhan", "Đã xác nhận"
        DANG_CHE_BIEN = "dang_che_bien", "Đang chế biến"
        SAN_SANG = "san_sang", "Sẵn sàng"
        HOAN_TAT = "hoan_tat", "Hoàn tất"
        DA_HUY = "da_huy", "Đã hủy"

    class HinhThuc(models.TextChoices):
        GIAO_HANG = "giao_hang", "Giao hàng"
        TU_DEN_LAY = "tu_den_lay", "Tự đến lấy"

    ma_don_hang = models.CharField(max_length=20, unique=True, editable=False)
    khach_hang = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_don_hang", on_delete=models.PROTECT
    )
    chi_nhanh = models.ForeignKey(
        "branches.ChiNhanh", related_name="danh_sach_don_hang",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    dat_ban = models.ForeignKey(
        "reservations.DatBan", related_name="danh_sach_don_hang",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    hinh_thuc = models.CharField(max_length=15, choices=HinhThuc.choices)
    trang_thai = models.CharField(
        max_length=20, choices=TrangThai.choices,
        default=TrangThai.CHO_TIEP_NHAN, db_index=True
    )
    ten_khach = models.CharField(max_length=150)
    sdt_khach = models.CharField(max_length=20)
    dia_chi_giao = models.TextField(null=True, blank=True)
    ghi_chu = models.TextField(blank=True)
    tien_hang = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tien_giam = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tong_tien = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    khuyen_mai = models.ForeignKey(
        "promotions.KhuyenMai", null=True, blank=True, on_delete=models.SET_NULL
    )

    _LEGACY_MAP = {
        "code": "ma_don_hang",
        "order_number": "ma_don_hang",
        "customer": "khach_hang",
        "user": "khach_hang",
        "customer_id": "khach_hang_id",
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh_id",
        "reservation": "dat_ban",
        "reservation_id": "dat_ban_id",
        "order_type": "hinh_thuc",
        "type": "hinh_thuc",
        "status": "trang_thai",
        "customer_name": "ten_khach",
        "customer_phone": "sdt_khach",
        "phone": "sdt_khach",
        "delivery_address": "dia_chi_giao",
        "address": "dia_chi_giao",
        "note": "ghi_chu",
        "subtotal": "tien_hang",
        "discount": "tien_giam",
        "discount_amount": "tien_giam",
        "total": "tong_tien",
        "total_amount": "tong_tien",
        "promotion": "khuyen_mai",
        "promotion_id": "khuyen_mai_id",
    }

    class Meta:
        db_table = "don_hang"
        verbose_name = "Đơn hàng"
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(hinh_thuc="giao_hang") | models.Q(dia_chi_giao__isnull=False),
                name="kiem_tra_giao_hang_can_dia_chi",
            )
        ]

    def save(self, *a, **kw):
        if not self.ma_don_hang:
            self.ma_don_hang = f"MOC{uuid.uuid4().hex[:8].upper()}"
        super().save(*a, **kw)

    def __str__(self):
        return self.ma_don_hang

    @property
    def total(self):
        return self.tong_tien

    @total.setter
    def total(self, val):
        self.tong_tien = val

    @property
    def total_amount(self):
        return self.tong_tien

    @total_amount.setter
    def total_amount(self, val):
        self.tong_tien = val

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def customer(self):
        return self.khach_hang

    @customer.setter
    def customer(self, val):
        self.khach_hang = val

    @property
    def user(self):
        return self.khach_hang

    @user.setter
    def user(self, val):
        self.khach_hang = val

    @property
    def customer_id(self):
        return self.khach_hang_id

    @customer_id.setter
    def customer_id(self, val):
        self.khach_hang_id = val

    @property
    def code(self):
        return self.ma_don_hang

    @code.setter
    def code(self, val):
        self.ma_don_hang = val

    @property
    def order_number(self):
        return self.ma_don_hang

    @order_number.setter
    def order_number(self, val):
        self.ma_don_hang = val

    @property
    def branch(self):
        return self.chi_nhanh

    @branch.setter
    def branch(self, val):
        self.chi_nhanh = val

    @property
    def branch_id(self):
        return self.chi_nhanh_id

    @branch_id.setter
    def branch_id(self, val):
        self.chi_nhanh_id = val

    @property
    def reservation(self):
        return self.dat_ban

    @reservation.setter
    def reservation(self, val):
        self.dat_ban = val

    @property
    def reservation_id(self):
        return self.dat_ban_id

    @reservation_id.setter
    def reservation_id(self, val):
        self.dat_ban_id = val

    @property
    def order_type(self):
        return self.hinh_thuc

    @order_type.setter
    def order_type(self, val):
        self.hinh_thuc = val

    @property
    def type(self):
        return self.hinh_thuc

    @type.setter
    def type(self, val):
        self.hinh_thuc = val

    @property
    def customer_name(self):
        return self.ten_khach

    @customer_name.setter
    def customer_name(self, val):
        self.ten_khach = val

    @property
    def customer_phone(self):
        return self.sdt_khach

    @customer_phone.setter
    def customer_phone(self, val):
        self.sdt_khach = val

    @property
    def phone(self):
        return self.sdt_khach

    @phone.setter
    def phone(self, val):
        self.sdt_khach = val

    @property
    def delivery_address(self):
        return self.dia_chi_giao

    @delivery_address.setter
    def delivery_address(self, val):
        self.dia_chi_giao = val

    @property
    def address(self):
        return self.dia_chi_giao

    @address.setter
    def address(self, val):
        self.dia_chi_giao = val

    @property
    def note(self):
        return self.ghi_chu

    @note.setter
    def note(self, val):
        self.ghi_chu = val

    @property
    def subtotal(self):
        return self.tien_hang

    @subtotal.setter
    def subtotal(self, val):
        self.tien_hang = val

    @property
    def discount(self):
        return self.tien_giam

    @discount.setter
    def discount(self, val):
        self.tien_giam = val

    @property
    def discount_amount(self):
        return self.tien_giam

    @discount_amount.setter
    def discount_amount(self, val):
        self.tien_giam = val

    @property
    def promotion(self):
        return self.khuyen_mai

    @promotion.setter
    def promotion(self, val):
        self.khuyen_mai = val

    @property
    def items(self):
        return self.danh_sach_mon

    @items.setter
    def items(self, val):
        if self.pk and hasattr(self.danh_sach_mon, "set"):
            self.danh_sach_mon.set(val)
        else:
            self._uncommitted_items = val


class ChiTietDonHang(MoHinhThoiGian):
    don_hang = models.ForeignKey(DonHang, related_name="danh_sach_mon", on_delete=models.CASCADE)
    mon_an = models.ForeignKey(MonAn, on_delete=models.PROTECT)
    so_luong = models.PositiveIntegerField()
    don_gia_luc_dat = models.DecimalField(max_digits=12, decimal_places=2)
    thanh_tien = models.DecimalField(max_digits=12, decimal_places=2)

    _LEGACY_MAP = {
        "order": "don_hang",
        "order_id": "don_hang_id",
        "food": "mon_an",
        "food_id": "mon_an_id",
        "quantity": "so_luong",
        "price": "don_gia_luc_dat",
        "unit_price": "don_gia_luc_dat",
        "subtotal": "thanh_tien",
        "total": "thanh_tien",
    }

    class Meta:
        db_table = "chi_tiet_don_hang"

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
    def price(self):
        return self.don_gia_luc_dat

    @price.setter
    def price(self, val):
        self.don_gia_luc_dat = val

    @property
    def unit_price(self):
        return self.don_gia_luc_dat

    @unit_price.setter
    def unit_price(self, val):
        self.don_gia_luc_dat = val

    @property
    def subtotal(self):
        return self.thanh_tien

    @subtotal.setter
    def subtotal(self, val):
        self.thanh_tien = val

    @property
    def total(self):
        return self.thanh_tien

    @total.setter
    def total(self, val):
        self.thanh_tien = val


class LichSuTrangThaiDon(MoHinhThoiGian):
    don_hang = models.ForeignKey(DonHang, related_name="lich_su_trang_thai", on_delete=models.CASCADE)
    tu_trang_thai = models.CharField(
        max_length=20, choices=DonHang.TrangThai.choices, null=True, blank=True
    )
    sang_trang_thai = models.CharField(max_length=20, choices=DonHang.TrangThai.choices)
    doi_boi = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    ghi_chu = models.CharField(max_length=255, blank=True)

    _LEGACY_MAP = {
        "order": "don_hang",
        "order_id": "don_hang_id",
        "from_status": "tu_trang_thai",
        "to_status": "sang_trang_thai",
        "changed_by": "doi_boi",
        "note": "ghi_chu",
    }

    class Meta:
        db_table = "lich_su_trang_thai_don"


# Backward-compatible model aliases
Order = DonHang
OrderItem = ChiTietDonHang
OrderStatusHistory = LichSuTrangThaiDon
DonHang.Status = DonHang.TrangThai
DonHang.Type = DonHang.HinhThuc
Order.Status = DonHang.TrangThai
Order.Type = DonHang.HinhThuc
