from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import VaiTro, NguoiDung, User, Role


@admin.register(NguoiDung)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "thu_dien_tu", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("username", "thu_dien_tu", "first_name", "last_name", "so_dien_thoai")


@admin.register(VaiTro)
class VaiTroAdmin(admin.ModelAdmin):
    list_display = ("ten", "mo_ta", "tao_luc", "cap_nhat_luc")
    search_fields = ("ten",)