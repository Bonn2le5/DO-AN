import uuid
from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn
from branches.models import ChiNhanh


class BanAn(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        TRONG = "trong", "Trống"
        DANG_GIU = "dang_giu", "Đang giữ"
        DA_DAT = "da_dat", "Đã đặt"
        DANG_PHUC_VU = "dang_phuc_vu", "Đang phục vụ"
        BAO_TRI = "bao_tri", "Bảo trì"

    chi_nhanh = models.ForeignKey(ChiNhanh, related_name="danh_sach_ban", on_delete=models.CASCADE)
    so_ban = models.CharField(max_length=20)
    khu_vuc = models.CharField(max_length=50, blank=True)
    suc_chua = models.PositiveIntegerField()
    trang_thai = models.CharField(max_length=20, choices=TrangThai.choices, default=TrangThai.TRONG)

    _LEGACY_MAP = {
        "status": "trang_thai",
        "capacity": "suc_chua",
        "table_number": "so_ban",
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh_id",
        "area": "khu_vuc",
    }

    class Meta:
        db_table = "ban_an"
        unique_together = ("chi_nhanh", "so_ban")
        verbose_name = "Bàn ăn"

    def __str__(self):
        return f"Bàn {self.so_ban} - {self.chi_nhanh.ten}"

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def capacity(self):
        return self.suc_chua

    @capacity.setter
    def capacity(self, val):
        self.suc_chua = val

    @property
    def table_number(self):
        return self.so_ban

    @table_number.setter
    def table_number(self, val):
        self.so_ban = val

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
    def area(self):
        return self.khu_vuc

    @area.setter
    def area(self, val):
        self.khu_vuc = val


class ChinhSachDatCoc(MoHinhThoiGian):
    chi_nhanh = models.ForeignKey(
        ChiNhanh, related_name="chinh_sach_coc", null=True, blank=True, on_delete=models.CASCADE
    )
    phan_tram_coc = models.DecimalField(max_digits=5, decimal_places=2)
    thoi_gian_giu_cho_phut = models.PositiveIntegerField(default=10)
    han_thanh_toan_phut = models.PositiveIntegerField(default=15)
    so_dien_thoai_lien_he = models.CharField(max_length=30, blank=True)
    noi_dung_huong_dan = models.TextField(blank=True)
    con_ap_dung = models.BooleanField(default=True)

    class Meta:
        db_table = "chinh_sach_dat_coc"
        verbose_name = "Chính sách đặt cọc"


from foods.models import MoHinhThoiGian, MonAn, LegacyKwargsMixin


class QuyTacHuyDatCoc(LegacyKwargsMixin, models.Model):
    class MocThoiGian(models.TextChoices):
        TRUOC_24H = "truoc_24h", "Trước 24h"
        TU_6_DEN_24H = "tu_6_den_24h", "6–24h"
        TRONG_6H = "trong_6h", "Trong 6h"
        KHACH_KHONG_DEN = "khach_khong_den", "Khách không đến"

    chinh_sach = models.ForeignKey(
        ChinhSachDatCoc, related_name="quy_tac_huy", on_delete=models.CASCADE
    )
    moc_thoi_gian = models.CharField(max_length=20, choices=MocThoiGian.choices)
    phan_tram_hoan_tien = models.DecimalField(max_digits=5, decimal_places=2)

    _LEGACY_MAP = {
        "policy": "chinh_sach",
        "policy_id": "chinh_sach_id",
        "time_milestone": "moc_thoi_gian",
        "refund_percentage": "phan_tram_hoan_tien",
    }

    class Meta:
        db_table = "quy_tac_huy_dat_coc"
        unique_together = ("chinh_sach", "moc_thoi_gian")


class DatBan(MoHinhThoiGian):
    class HinhThuc(models.TextChoices):
        CHI_GIU_CHO = "chi_giu_cho", "Chỉ giữ chỗ"
        DAT_BAN_VA_GOI_MON = "dat_ban_va_goi_mon", "Đặt bàn + gọi món"
        DAT_BAN_GOI_MON_CHINH_SUA = "dat_ban_goi_mon_chinh_sua", "Đặt bàn + gọi món (chỉnh sửa)"

    class TrangThai(models.TextChoices):
        CHO_XAC_NHAN = "cho_xac_nhan", "Chờ nhà hàng xác nhận"
        CHO_THANH_TOAN = "cho_thanh_toan", "Chờ thanh toán"
        DA_XAC_NHAN = "da_xac_nhan", "Đã xác nhận"
        KHACH_DA_DEN = "khach_da_den", "Khách đã đến"
        HOAN_TAT = "hoan_tat", "Hoàn tất"
        DA_HUY = "da_huy", "Đã hủy"
        KHACH_KHONG_DEN = "khach_khong_den", "Khách không đến"

    class TrangThaiCoc(models.TextChoices):
        CHUA_THANH_TOAN = "chua_thanh_toan", "Chưa thanh toán"
        DANG_XU_LY = "dang_xu_ly", "Đang xử lý"
        THANH_CONG = "thanh_cong", "Thành công"
        THAT_BAI = "that_bai", "Thất bại"
        DA_HOAN_TIEN = "da_hoan_tien", "Đã hoàn tiền"
        HOAN_TIEN_MOT_PHAN = "hoan_tien_mot_phan", "Hoàn tiền một phần"

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_dat_ban",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    chi_nhanh = models.ForeignKey(ChiNhanh, related_name="danh_sach_dat_ban", on_delete=models.PROTECT)
    ban_an = models.ForeignKey(BanAn, related_name="danh_sach_dat_ban", on_delete=models.PROTECT)
    ma_dat_ban = models.CharField(max_length=20, unique=True, editable=False)
    ngay_dat = models.DateField(db_index=True)
    gio_bat_dau = models.TimeField()
    gio_ket_thuc = models.TimeField(null=True, blank=True)
    so_luong_khach = models.PositiveIntegerField()
    hinh_thuc = models.CharField(max_length=30, choices=HinhThuc.choices)
    trang_thai = models.CharField(max_length=20, choices=TrangThai.choices, default=TrangThai.CHO_XAC_NHAN)
    yeu_cau_dat_coc = models.BooleanField(default=False)
    so_tien_coc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    trang_thai_coc = models.CharField(
        max_length=20, choices=TrangThaiCoc.choices, default=TrangThaiCoc.CHUA_THANH_TOAN
    )
    thanh_toan_coc_luc = models.DateTimeField(null=True, blank=True)
    ten_khach = models.CharField(max_length=150)
    sdt_khach = models.CharField(max_length=20)
    ghi_chu = models.TextField(blank=True)
    huy_luc = models.DateTimeField(null=True, blank=True)
    ly_do_huy = models.TextField(blank=True)
    phien_ban = models.IntegerField(default=0)  # optimistic locking

    _LEGACY_MAP = {
        "code": "ma_dat_ban",
        "reservation_number": "ma_dat_ban",
        "user": "nguoi_dung",
        "user_id": "nguoi_dung_id",
        "customer": "nguoi_dung",
        "customer_id": "nguoi_dung_id",
        "branch": "chi_nhanh",
        "branch_id": "chi_nhanh_id",
        "table": "ban_an",
        "table_id": "ban_an_id",
        "reservation_date": "ngay_dat",
        "date": "ngay_dat",
        "start_time": "gio_bat_dau",
        "time": "gio_bat_dau",
        "end_time": "gio_ket_thuc",
        "guest_count": "so_luong_khach",
        "guests": "so_luong_khach",
        "num_guests": "so_luong_khach",
        "reservation_type": "hinh_thuc",
        "type": "hinh_thuc",
        "status": "trang_thai",
        "requires_deposit": "yeu_cau_dat_coc",
        "deposit_amount": "so_tien_coc",
        "deposit_status": "trang_thai_coc",
        "deposit_paid_at": "thanh_toan_coc_luc",
        "customer_name": "ten_khach",
        "customer_phone": "sdt_khach",
        "phone": "sdt_khach",
        "note": "ghi_chu",
        "cancelled_at": "huy_luc",
        "cancel_reason": "ly_do_huy",
        "version": "phien_ban",
    }

    class Meta:
        db_table = "dat_ban"
        indexes = [
            models.Index(fields=["chi_nhanh", "ngay_dat", "gio_bat_dau"])
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(hinh_thuc="chi_giu_cho") | (
                    models.Q(yeu_cau_dat_coc=False) & models.Q(so_tien_coc=0)
                ),
                name="kiem_tra_chi_giu_cho",
            )
        ]
        verbose_name = "Đặt bàn"

    def save(self, *args, **kwargs):
        if not self.ma_dat_ban:
            import uuid
            self.ma_dat_ban = f"DB{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def status(self):
        return self.trang_thai

    @status.setter
    def status(self, val):
        self.trang_thai = val

    @property
    def deposit_status(self):
        return self.trang_thai_coc

    @deposit_status.setter
    def deposit_status(self, val):
        self.trang_thai_coc = val

    @property
    def deposit_paid_at(self):
        return self.thanh_toan_coc_luc

    @deposit_paid_at.setter
    def deposit_paid_at(self, val):
        self.thanh_toan_coc_luc = val

    @property
    def version(self):
        return self.phien_ban

    @version.setter
    def version(self, val):
        self.phien_ban = val

    @property
    def code(self):
        return self.ma_dat_ban

    @code.setter
    def code(self, val):
        self.ma_dat_ban = val

    @property
    def reservation_number(self):
        return self.ma_dat_ban

    @reservation_number.setter
    def reservation_number(self, val):
        self.ma_dat_ban = val

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
    def customer(self):
        return self.nguoi_dung

    @customer.setter
    def customer(self, val):
        self.nguoi_dung = val

    @property
    def customer_id(self):
        return self.nguoi_dung_id

    @customer_id.setter
    def customer_id(self, val):
        self.nguoi_dung_id = val

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
    def table(self):
        return self.ban_an

    @table.setter
    def table(self, val):
        self.ban_an = val

    @property
    def table_id(self):
        return self.ban_an_id

    @table_id.setter
    def table_id(self, val):
        self.ban_an_id = val

    @property
    def reservation_date(self):
        return self.ngay_dat

    @reservation_date.setter
    def reservation_date(self, val):
        self.ngay_dat = val

    @property
    def date(self):
        return self.ngay_dat

    @date.setter
    def date(self, val):
        self.ngay_dat = val

    @property
    def start_time(self):
        return self.gio_bat_dau

    @start_time.setter
    def start_time(self, val):
        self.gio_bat_dau = val

    @property
    def time(self):
        return self.gio_bat_dau

    @time.setter
    def time(self, val):
        self.gio_bat_dau = val

    @property
    def end_time(self):
        return self.gio_ket_thuc

    @end_time.setter
    def end_time(self, val):
        self.gio_ket_thuc = val

    @property
    def guest_count(self):
        return self.so_luong_khach

    @guest_count.setter
    def guest_count(self, val):
        self.so_luong_khach = val

    @property
    def guests(self):
        return self.so_luong_khach

    @guests.setter
    def guests(self, val):
        self.so_luong_khach = val

    @property
    def num_guests(self):
        return self.so_luong_khach

    @num_guests.setter
    def num_guests(self, val):
        self.so_luong_khach = val

    @property
    def reservation_type(self):
        return self.hinh_thuc

    @reservation_type.setter
    def reservation_type(self, val):
        self.hinh_thuc = val

    @property
    def type(self):
        return self.hinh_thuc

    @type.setter
    def type(self, val):
        self.hinh_thuc = val

    @property
    def requires_deposit(self):
        return self.yeu_cau_dat_coc

    @requires_deposit.setter
    def requires_deposit(self, val):
        self.yeu_cau_dat_coc = bool(val)

    @property
    def deposit_amount(self):
        return self.so_tien_coc

    @deposit_amount.setter
    def deposit_amount(self, val):
        self.so_tien_coc = val

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
    def note(self):
        return self.ghi_chu

    @note.setter
    def note(self, val):
        self.ghi_chu = val

    @property
    def cancelled_at(self):
        return self.huy_luc

    @cancelled_at.setter
    def cancelled_at(self, val):
        self.huy_luc = val

    @property
    def cancel_reason(self):
        return self.ly_do_huy

    @cancel_reason.setter
    def cancel_reason(self, val):
        self.ly_do_huy = val


class MonAnTrongDatBan(MoHinhThoiGian):
    dat_ban = models.ForeignKey(DatBan, related_name="danh_sach_mon", on_delete=models.CASCADE)
    mon_an = models.ForeignKey(MonAn, on_delete=models.PROTECT)
    so_luong = models.PositiveIntegerField()
    don_gia_luc_dat = models.DecimalField(max_digits=12, decimal_places=2)

    _LEGACY_MAP = {
        "reservation": "dat_ban",
        "reservation_id": "dat_ban_id",
        "food": "mon_an",
        "food_id": "mon_an_id",
        "quantity": "so_luong",
        "price": "don_gia_luc_dat",
        "unit_price": "don_gia_luc_dat",
    }

    class Meta:
        db_table = "mon_an_trong_dat_ban"
        unique_together = ("dat_ban", "mon_an")

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


# Backward-compatible model aliases
Table = BanAn
DepositPolicy = ChinhSachDatCoc
DepositRefundRule = QuyTacHuyDatCoc
Reservation = DatBan
ReservationItem = MonAnTrongDatBan
ReservationFoodItem = MonAnTrongDatBan

# Enum aliases (Challenger 1 requirement)
BanAn.Status = BanAn.TrangThai
BanAn.TrangThaiBan = BanAn.TrangThai
Table.Status = BanAn.TrangThai
Table.TrangThaiBan = BanAn.TrangThai

DatBan.Status = DatBan.TrangThai
DatBan.DepositStatus = DatBan.TrangThaiCoc
DatBan.Type = DatBan.HinhThuc
Reservation.Status = DatBan.TrangThai
Reservation.DepositStatus = DatBan.TrangThaiCoc
Reservation.Type = DatBan.HinhThuc
