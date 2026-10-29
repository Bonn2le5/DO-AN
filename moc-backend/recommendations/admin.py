from django.contrib import admin
from .models import TuongTacMonAn, GoiYMonAn


@admin.register(TuongTacMonAn)
class TuongTacMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "mon_an", "loai_tuong_tac", "trong_so", "tao_luc")
    list_filter = ("loai_tuong_tac",)
    search_fields = ("nguoi_dung__username", "mon_an__ten")
    readonly_fields = ("tao_luc", "cap_nhat_luc")


@admin.register(GoiYMonAn)
class GoiYMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "mon_an", "diem_tuong_dong", "phien_ban_model", "tao_luc")
    search_fields = ("nguoi_dung__username", "mon_an__ten", "phien_ban_model")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
