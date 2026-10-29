from django.contrib import admin
from .models import ChiNhanh


@admin.register(ChiNhanh)
class ChiNhanhAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "so_dien_thoai", "dia_chi", "con_hoat_dong", "tao_luc")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ten", "dia_chi", "so_dien_thoai")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
