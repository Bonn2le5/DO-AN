from django.contrib import admin
from .models import (
    BanAn,
    ChinhSachDatCoc,
    QuyTacHuyDatCoc,
    DatBan,
    MonAnTrongDatBan,
)


@admin.register(BanAn)
class BanAnAdmin(admin.ModelAdmin):
    list_display = ("id", "so_ban", "chi_nhanh", "khu_vuc", "suc_chua", "trang_thai")
    list_filter = ("chi_nhanh", "trang_thai", "khu_vuc")
    search_fields = ("so_ban", "khu_vuc")


class QuyTacHuyDatCocInline(admin.TabularInline):
    model = QuyTacHuyDatCoc
    extra = 1


@admin.register(ChinhSachDatCoc)
class ChinhSachDatCocAdmin(admin.ModelAdmin):
    list_display = (
        "id", "chi_nhanh", "phan_tram_coc",
        "thoi_gian_giu_cho_phut", "han_thanh_toan_phut", "con_ap_dung"
    )
    list_filter = ("con_ap_dung", "chi_nhanh")
    inlines = [QuyTacHuyDatCocInline]


@admin.register(QuyTacHuyDatCoc)
class QuyTacHuyDatCocAdmin(admin.ModelAdmin):
    list_display = ("id", "chinh_sach", "moc_thoi_gian", "phan_tram_hoan_tien")
    list_filter = ("moc_thoi_gian",)


class MonAnTrongDatBanInline(admin.TabularInline):
    model = MonAnTrongDatBan
    extra = 0
    readonly_fields = ("mon_an", "so_luong", "don_gia_luc_dat")


@admin.register(DatBan)
class DatBanAdmin(admin.ModelAdmin):
    list_display = (
        "ma_dat_ban", "ten_khach", "sdt_khach", "chi_nhanh", "ban_an",
        "ngay_dat", "gio_bat_dau", "hinh_thuc", "trang_thai",
        "trang_thai_coc", "so_tien_coc"
    )
    list_filter = ("trang_thai", "trang_thai_coc", "hinh_thuc", "chi_nhanh", "ngay_dat")
    search_fields = ("ma_dat_ban", "ten_khach", "sdt_khach")
    readonly_fields = ("ma_dat_ban", "phien_ban", "tao_luc", "cap_nhat_luc")
    inlines = [MonAnTrongDatBanInline]


@admin.register(MonAnTrongDatBan)
class MonAnTrongDatBanAdmin(admin.ModelAdmin):
    list_display = ("id", "dat_ban", "mon_an", "so_luong", "don_gia_luc_dat")
    search_fields = ("dat_ban__ma_dat_ban", "mon_an__ten")
