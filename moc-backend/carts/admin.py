from django.contrib import admin
from .models import GioHang, ChiTietGioHang


class ChiTietGioHangInline(admin.TabularInline):
    model = ChiTietGioHang
    extra = 0
    readonly_fields = ("mon_an", "so_luong", "don_gia_luc_dat", "ghi_chu")


@admin.register(GioHang)
class GioHangAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "trang_thai", "tao_luc", "cap_nhat_luc")
    list_filter = ("trang_thai",)
    search_fields = ("nguoi_dung__username",)
    readonly_fields = ("tao_luc", "cap_nhat_luc")
    inlines = [ChiTietGioHangInline]


@admin.register(ChiTietGioHang)
class ChiTietGioHangAdmin(admin.ModelAdmin):
    list_display = ("id", "gio_hang", "mon_an", "so_luong", "don_gia_luc_dat")
    search_fields = ("gio_hang__nguoi_dung__username", "mon_an__ten")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
