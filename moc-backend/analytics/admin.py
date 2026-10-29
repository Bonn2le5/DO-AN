from django.contrib import admin
from .models import ThongBao


@admin.register(ThongBao)
class ThongBaoAdmin(admin.ModelAdmin):
    list_display = ("id", "nguoi_dung", "loai", "tieu_de", "da_doc", "doc_luc", "tao_luc")
    list_filter = ("loai", "da_doc")
    search_fields = ("tieu_de", "noi_dung", "nguoi_dung__username")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
