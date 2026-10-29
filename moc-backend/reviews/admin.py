from django.contrib import admin
from .models import DanhGia


@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nguoi_dung", "mon_an", "don_hang",
        "diem_danh_gia", "hien_thi", "tao_luc"
    )
    list_filter = ("diem_danh_gia", "hien_thi")
    search_fields = ("nguoi_dung__username", "mon_an__ten", "nhan_xet")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
