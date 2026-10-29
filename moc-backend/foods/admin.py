from django.contrib import admin
from .models import (
    DanhMuc,
    TheMonAn,
    NguyenLieu,
    MonAn,
    HinhAnhMonAn,
    DinhMucNguyenLieu,
    MonAnThe,
    LichSuXuatNhapKho,
)


@admin.register(DanhMuc)
class DanhMucAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "duong_dan", "con_hoat_dong", "tao_luc")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ten", "duong_dan")
    prepopulated_fields = {"duong_dan": ("ten",)}


@admin.register(TheMonAn)
class TheMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "duong_dan", "tao_luc")
    search_fields = ("ten", "duong_dan")
    prepopulated_fields = {"duong_dan": ("ten",)}


@admin.register(NguyenLieu)
class NguyenLieuAdmin(admin.ModelAdmin):
    list_display = ("id", "ten", "don_vi", "ton_kho_hien_tai", "ton_kho_toi_thieu", "con_hoat_dong")
    list_filter = ("con_hoat_dong",)
    search_fields = ("ten",)


class HinhAnhMonAnInline(admin.TabularInline):
    model = HinhAnhMonAn
    extra = 1


class DinhMucNguyenLieuInline(admin.TabularInline):
    model = DinhMucNguyenLieu
    extra = 1


@admin.register(MonAn)
class MonAnAdmin(admin.ModelAdmin):
    list_display = (
        "id", "ten", "danh_muc", "don_gia", "con_hang",
        "hien_thi", "noi_bat", "la_mon_chay", "diem_danh_gia", "so_luot_danh_gia"
    )
    list_filter = ("con_hang", "hien_thi", "noi_bat", "la_mon_chay", "danh_muc")
    search_fields = ("ten", "mo_ta_ngan")
    prepopulated_fields = {"duong_dan": ("ten",)}
    inlines = [HinhAnhMonAnInline, DinhMucNguyenLieuInline]


@admin.register(HinhAnhMonAn)
class HinhAnhMonAnAdmin(admin.ModelAdmin):
    list_display = ("id", "mon_an", "anh", "la_anh_chinh", "thu_tu")
    list_filter = ("la_anh_chinh",)
    search_fields = ("mon_an__ten",)


@admin.register(DinhMucNguyenLieu)
class DinhMucNguyenLieuAdmin(admin.ModelAdmin):
    list_display = ("id", "mon_an", "nguyen_lieu", "so_luong_can")
    search_fields = ("mon_an__ten", "nguyen_lieu__ten")


@admin.register(MonAnThe)
class MonAnTheAdmin(admin.ModelAdmin):
    list_display = ("id", "mon_an", "the")
    search_fields = ("mon_an__ten", "the__ten")


@admin.register(LichSuXuatNhapKho)
class LichSuXuatNhapKhoAdmin(admin.ModelAdmin):
    list_display = (
        "id", "nguyen_lieu", "loai_giao_dich", "so_luong",
        "ton_kho_truoc", "ton_kho_sau", "tao_boi", "tao_luc"
    )
    list_filter = ("loai_giao_dich", "tao_luc")
    search_fields = ("nguyen_lieu__ten", "ghi_chu")
    readonly_fields = ("tao_luc", "cap_nhat_luc")
