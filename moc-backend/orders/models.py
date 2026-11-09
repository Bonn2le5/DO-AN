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
        TAI_CHO = "tai_cho", "Dùng tại bàn"

    ma_don_hang = models.CharField(max_length=20, unique=True, editable=False)
    khach_hang = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_don_hang",
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    chi_nhanh = models.ForeignKey(
        "branches.ChiNhanh", related_name="danh_sach_don_hang",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    dat_ban = models.ForeignKey(
        "reservations.DatBan", related_name="danh_sach_don_hang",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    phien_phuc_vu = models.OneToOneField(
        "reservations.PhienPhucVu", related_name="don_hang",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    hinh_thuc = models.CharField(max_length=15, choices=HinhThuc.choices, default=HinhThuc.TAI_CHO)
    trang_thai = models.CharField(
        max_length=20, choices=TrangThai.choices,
        default=TrangThai.CHO_TIEP_NHAN, db_index=True
    )
    ten_khach = models.CharField(max_length=150)
    sdt_khach = models.CharField(max_length=20)
    ghi_chu = models.TextField(blank=True)
    tien_hang = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tien_giam = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tong_tien = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    khuyen_mai = models.ForeignKey(
        "promotions.KhuyenMai", null=True, blank=True, on_delete=models.SET_NULL
    )


    class Meta:
        db_table = "don_hang"
        verbose_name = "Đơn hàng"

    def save(self, *a, **kw):
        if not self.ma_don_hang:
            self.ma_don_hang = f"MOC{uuid.uuid4().hex[:8].upper()}"
        super().save(*a, **kw)

    def __str__(self):
        return self.ma_don_hang


class ChiTietDonHang(MoHinhThoiGian):
    don_hang = models.ForeignKey(DonHang, related_name="danh_sach_mon", on_delete=models.CASCADE)
    mon_an = models.ForeignKey(MonAn, on_delete=models.PROTECT)
    so_luong = models.PositiveIntegerField()
    don_gia_luc_dat = models.DecimalField(max_digits=12, decimal_places=2)
    thanh_tien = models.DecimalField(max_digits=12, decimal_places=2)
    ghi_chu = models.TextField(blank=True)


    class Meta:
        db_table = "chi_tiet_don_hang"


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
