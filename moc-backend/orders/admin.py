from django.contrib import admin
from .models import DonHang, ChiTietDonHang, LichSuTrangThaiDon


class ChiTietDonHangInline(admin.TabularInline):
    model = ChiTietDonHang
    extra = 0
    readonly_fields = ("mon_an", "so_luong", "don_gia_luc_dat", "thanh_tien")


class LichSuTrangThaiDonInline(admin.TabularInline):
    model = LichSuTrangThaiDon
    extra = 0
    readonly_fields = ("tu_trang_thai", "sang_trang_thai", "doi_boi", "ghi_chu", "tao_luc")


@admin.register(DonHang)
class DonHangAdmin(admin.ModelAdmin):
    list_display = (
        "ma_don_hang", "ten_khach", "sdt_khach", "hinh_thuc",
        "trang_thai", "tong_tien", "chi_nhanh", "tao_luc"
    )
    list_filter = ("trang_thai", "hinh_thuc", "chi_nhanh", "tao_luc")
    search_fields = ("ma_don_hang", "ten_khach", "sdt_khach")
    readonly_fields = ("ma_don_hang", "tao_luc", "cap_nhat_luc")
    inlines = [ChiTietDonHangInline, LichSuTrangThaiDonInline]


@admin.register(ChiTietDonHang)
class ChiTietDonHangAdmin(admin.ModelAdmin):
    list_display = ("id", "don_hang", "mon_an", "so_luong", "don_gia_luc_dat", "thanh_tien")
    search_fields = ("don_hang__ma_don_hang", "mon_an__ten")


@admin.register(LichSuTrangThaiDon)
class LichSuTrangThaiDonAdmin(admin.ModelAdmin):
    list_display = ("id", "don_hang", "tu_trang_thai", "sang_trang_thai", "doi_boi", "tao_luc")
    list_filter = ("sang_trang_thai",)
    search_fields = ("don_hang__ma_don_hang", "ghi_chu")
