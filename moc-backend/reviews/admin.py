from django.contrib import admin
from .models import DanhGia, DanhGiaBuaAn


@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nguoi_dung", "mon_an", "don_hang",
        "diem_danh_gia", "hien_thi", "tao_luc"
    )
    list_filter = ("diem_danh_gia", "hien_thi")
    search_fields = ("nguoi_dung__username", "mon_an__ten", "nhan_xet")
    readonly_fields = ("tao_luc", "cap_nhat_luc")


@admin.register(DanhGiaBuaAn)
class DanhGiaBuaAnAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "don_hang", "diem_phuc_vu", "diem_khong_gian", "hien_thi", "tao_luc")
    list_filter = ("diem_phuc_vu", "diem_khong_gian", "hien_thi")
    search_fields = ("nguoi_dung__username", "don_hang__ma_don_hang", "nhan_xet")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
