from django.contrib import admin
from .models import (
    BanAn,
    ChinhSachDatCoc,
    QuyTacHuyDatCoc,
    DatBan,
    MonAnTrongDatBan,
    PhongRieng,
    PhienPhucVu,
)


@admin.register(BanAn)
class BanAnAdmin(admin.ModelAdmin):
    list_display = ("id", "so_ban", "chi_nhanh", "khu_vuc", "phong_rieng", "suc_chua", "trang_thai", "da_luu_tru")
    list_filter = ("chi_nhanh", "trang_thai", "khu_vuc", "da_luu_tru")
    search_fields = ("so_ban", "khu_vuc")


@admin.register(PhongRieng)
class PhongRiengAdmin(admin.ModelAdmin):
    list_display = ("ten_phong", "chi_nhanh", "tang", "suc_chua", "con_hoat_dong")
    list_filter = ("chi_nhanh", "tang", "con_hoat_dong")
    search_fields = ("ten_phong",)


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


@admin.register(PhienPhucVu)
class PhienPhucVuAdmin(admin.ModelAdmin):
    list_display = ("ma_phien", "chi_nhanh", "ban_an", "dat_ban", "so_luong_khach", "trang_thai", "bat_dau_luc", "check_out_luc")
    list_filter = ("chi_nhanh", "trang_thai")
    search_fields = ("ma_phien", "ten_khach", "sdt_khach", "ban_an__so_ban", "dat_ban__ma_dat_ban")
    readonly_fields = ("ma_phien", "bat_dau_luc", "check_out_luc", "da_don_luc", "tao_luc", "cap_nhat_luc")
