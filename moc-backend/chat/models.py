from django.conf import settings
from django.db import models
from foods.models import MoHinhThoiGian


class HoiThoai(MoHinhThoiGian):
    class TrangThai(models.TextChoices):
        MO = "mo", "Mở"
        DONG = "dong", "Đóng"

    khach_hang = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="danh_sach_hoi_thoai", on_delete=models.CASCADE
    )
    nhan_vien = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="hoi_thoai_phu_trach",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    trang_thai = models.CharField(max_length=10, choices=TrangThai.choices, default=TrangThai.MO)
    tin_nhan_cuoi_luc = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = "hoi_thoai"
        verbose_name = "Hội thoại"


class TinNhan(MoHinhThoiGian):
    class LoaiTinNhan(models.TextChoices):
        VAN_BAN = "van_ban", "Văn bản"
        HINH_ANH = "hinh_anh", "Hình ảnh"
        HE_THONG = "he_thong", "Hệ thống"

    hoi_thoai = models.ForeignKey(HoiThoai, related_name="danh_sach_tin_nhan", on_delete=models.CASCADE)
    nguoi_gui = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    loai_tin_nhan = models.CharField(
        max_length=10, choices=LoaiTinNhan.choices, default=LoaiTinNhan.VAN_BAN
    )
    noi_dung = models.TextField()
    da_doc = models.BooleanField(default=False)
    doc_luc = models.DateTimeField(null=True, blank=True)


    class Meta:
        db_table = "tin_nhan"
        verbose_name = "Tin nhắn"
