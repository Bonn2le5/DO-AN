from django.contrib import admin
from .models import DanhMucBaiViet, BaiViet


@admin.register(DanhMucBaiViet)
class DanhMucBaiVietAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "duong_dan", "tao_luc")
    search_fields = ("ten", "duong_dan")
    prepopulated_fields = {"duong_dan": ("ten",)}
    readonly_fields = ("tao_luc", "cap_nhat_luc")


@admin.register(BaiViet)
class BaiVietAdmin(admin.ModelAdmin):
    list_display = ("id", "tieu_de", "danh_muc", "tac_gia", "trang_thai", "dang_luc", "tao_luc")
    list_filter = ("trang_thai", "danh_muc")
    search_fields = ("tieu_de", "noi_dung", "tac_gia__username")
    prepopulated_fields = {"duong_dan": ("tieu_de",)}
    readonly_fields = ("tao_luc", "cap_nhat_luc")
