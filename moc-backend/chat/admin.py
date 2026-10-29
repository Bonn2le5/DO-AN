from django.contrib import admin
from .models import HoiThoai, TinNhan


class TinNhanInline(admin.TabularInline):
    model = TinNhan
    extra = 0
    readonly_fields = ("nguoi_gui", "loai_tin_nhan", "noi_dung", "da_doc", "doc_luc", "tao_luc")


@admin.register(HoiThoai)
class HoiThoaiAdmin(admin.ModelAdmin):
    list_display = ("id", "khach_hang", "nhan_vien", "trang_thai", "tin_nhan_cuoi_luc", "tao_luc")
    list_filter = ("trang_thai",)
    search_fields = ("khach_hang__username", "nhan_vien__username")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
    inlines = [TinNhanInline]


@admin.register(TinNhan)
class TinNhanAdmin(admin.ModelAdmin):
    list_display = ("id", "hoi_thoai", "nguoi_gui", "loai_tin_nhan", "da_doc", "doc_luc", "tao_luc")
    list_filter = ("loai_tin_nhan", "da_doc")
    search_fields = ("noi_dung", "nguoi_gui__username")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
