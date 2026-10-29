from django.contrib import admin
from .models import KhuyenMai, MaKhuyenMai, LichSuDungKhuyenMai


class MaKhuyenMaiInline(admin.TabularInline):
    model = MaKhuyenMai
    extra = 1


@admin.register(KhuyenMai)
class KhuyenMaiAdmin(admin.ModelAdmin):
    list_display = (
        "ma_giam_gia", "ten", "kieu_giam", "gia_tri_giam",
        "don_hang_toi_thieu", "bat_dau_luc", "ket_thuc_luc",
        "con_hoat_dong", "so_lan_da_dung"
    )
    list_filter = ("kieu_giam", "con_hoat_dong")
    search_fields = ("ma_giam_gia", "ten")
    inlines = [MaKhuyenMaiInline]


@admin.register(MaKhuyenMai)
class MaKhuyenMaiAdmin(admin.ModelAdmin):
    list_display = ("id", "khuyen_mai", "ma", "gioi_han", "da_dung", "con_hoat_dong")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ma", "khuyen_mai__ten")


@admin.register(LichSuDungKhuyenMai)
class LichSuDungKhuyenMaiAdmin(admin.ModelAdmin):
    list_display = (
        "id", "khuyen_mai", "ma_khuyen_mai", "nguoi_dung",
        "don_hang", "so_tien_giam", "tao_luc"
    )
    search_fields = ("khuyen_mai__ten", "nguoi_dung__username", "don_hang__ma_don_hang")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
