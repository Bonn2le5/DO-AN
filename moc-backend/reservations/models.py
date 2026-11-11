import uuid
from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian, MonAn
from branches.models import ChiNhanh


class PhongRieng(MoHinhThoiGian):
    chi_nhanh = models.ForeignKey(ChiNhanh, related_name="danh_sach_phong_rieng", on_delete=models.CASCADE)
    ten_phong = models.CharField(max_length=80)
    tang = models.CharField(max_length=50, blank=True)
    suc_chua = models.PositiveIntegerField(default=12)
    con_hoat_dong = models.BooleanField(default=True)

    class Meta:
        db_table = "phong_rieng"
        unique_together = (("chi_nhanh", "ten_phong"),)
        ordering = ("chi_nhanh_id", "tang", "ten_phong")

    def __str__(self):
        return f"{self.ten_phong} - {self.chi_nhanh.ten}"


class BanAn(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        TRONG = "trong", "Trống"
        DANG_GIU = "dang_giu", "Đang giữ"
        DA_DAT = "da_dat", "Đã đặt"
        DANG_PHUC_VU = "dang_phuc_vu", "Đang phục vụ"
        CHO_DON = "cho_don", "Chờ dọn"
        BAO_TRI = "bao_tri", "Bảo trì"

    chi_nhanh = models.ForeignKey(ChiNhanh, related_name="danh_sach_ban", on_delete=models.CASCADE)
    so_ban = models.CharField(max_length=20)
    khu_vuc = models.CharField(max_length=50, blank=True)
    suc_chua = models.PositiveIntegerField()
    trang_thai = models.CharField(max_length=20, choices=TrangThai.choices, default=TrangThai.TRONG)
    da_luu_tru = models.BooleanField(default=False)
    phong_rieng = models.ForeignKey(
        PhongRieng, related_name="danh_sach_ban", null=True, blank=True, on_delete=models.SET_NULL
    )


    class Meta:
        db_table = "ban_an"
        unique_together = ("chi_nhanh", "so_ban")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(suc_chua__gte=1, suc_chua__lte=12),
                name="ban_an_suc_chua_1_12",
            )
        ]
        verbose_name = "Bàn ăn"

    def __str__(self):
        return f"Bàn {self.so_ban} - {self.chi_nhanh.ten}"


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


from foods.models import MoHinhThoiGian, MonAn


class QuyTacHuyDatCoc(models.Model):
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
    ban_an = models.ForeignKey(
        BanAn, related_name="danh_sach_dat_ban", null=True, blank=True, on_delete=models.PROTECT
    )
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
    check_in_luc = models.DateTimeField(null=True, blank=True)
    ten_khach = models.CharField(max_length=150)
    sdt_khach = models.CharField(max_length=20)
    ghi_chu = models.TextField(blank=True)
    huy_luc = models.DateTimeField(null=True, blank=True)
    ly_do_huy = models.TextField(blank=True)
    phien_ban = models.IntegerField(default=0)  # optimistic locking


    class Meta:
        db_table = "dat_ban"
        indexes = [
            models.Index(fields=["chi_nhanh", "ngay_dat", "gio_bat_dau"])
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(so_luong_khach__gte=1, so_luong_khach__lte=12),
                name="dat_ban_so_khach_1_12",
            ),
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


class PhienPhucVu(MoHinhThoiGian):
    """Một lượt phục vụ tại bàn, dùng chung cho walk-in và khách đã đặt trước."""

    class TrangThai(models.TextChoices):
        DANG_PHUC_VU = "dang_phuc_vu", "Đang phục vụ"
        CHO_DON = "cho_don", "Chờ dọn"
        DA_DONG = "da_dong", "Đã đóng"

    ma_phien = models.CharField(max_length=24, unique=True, editable=False)
    chi_nhanh = models.ForeignKey(
        ChiNhanh, related_name="danh_sach_phien_phuc_vu", on_delete=models.PROTECT
    )
    ban_an = models.ForeignKey(
        BanAn, related_name="danh_sach_phien_phuc_vu", on_delete=models.PROTECT
    )
    dat_ban = models.OneToOneField(
        DatBan, related_name="phien_phuc_vu", null=True, blank=True, on_delete=models.PROTECT
    )
    so_luong_khach = models.PositiveIntegerField()
    ten_khach = models.CharField(max_length=150, blank=True)
    sdt_khach = models.CharField(max_length=20, blank=True)
    ghi_chu = models.TextField(blank=True)
    trang_thai = models.CharField(
        max_length=20, choices=TrangThai.choices, default=TrangThai.DANG_PHUC_VU, db_index=True
    )
    bat_dau_luc = models.DateTimeField(auto_now_add=True)
    check_out_luc = models.DateTimeField(null=True, blank=True)
    da_don_luc = models.DateTimeField(null=True, blank=True)
    nguoi_bat_dau = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="phien_phuc_vu_bat_dau",
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    nguoi_check_out = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="phien_phuc_vu_check_out",
        null=True, blank=True, on_delete=models.SET_NULL,
    )
    nguoi_xac_nhan_don = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="phien_phuc_vu_da_don",
        null=True, blank=True, on_delete=models.SET_NULL,
    )

    class Meta:
        db_table = "phien_phuc_vu"
        verbose_name = "Phiên phục vụ"
        ordering = ("-bat_dau_luc",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(so_luong_khach__gte=1, so_luong_khach__lte=12),
                name="phien_phuc_vu_so_khach_1_12",
            ),
            models.UniqueConstraint(
                fields=("ban_an",),
                condition=models.Q(trang_thai__in=["dang_phuc_vu", "cho_don"]),
                name="mot_phien_con_hieu_luc_moi_ban",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.ma_phien:
            self.ma_phien = f"PV{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ma_phien} · {self.ban_an}"


class MonAnTrongDatBan(MoHinhThoiGian):
    dat_ban = models.ForeignKey(DatBan, related_name="danh_sach_mon", on_delete=models.CASCADE)
    mon_an = models.ForeignKey(MonAn, on_delete=models.PROTECT)
    so_luong = models.PositiveIntegerField()
    don_gia_luc_dat = models.DecimalField(max_digits=12, decimal_places=2)


    class Meta:
        db_table = "mon_an_trong_dat_ban"
        unique_together = ("dat_ban", "mon_an")
