from django.contrib import admin
from .models import ThanhToan, PhieuHoanTien


@admin.register(ThanhToan)
class ThanhToanAdmin(admin.ModelAdmin):
    list_display = (
        "id", "ma_giao_dich", "nguoi_dung", "loai_thanh_toan",
        "phuong_thuc", "so_tien", "trang_thai", "thanh_toan_luc", "tao_luc"
    )
    list_filter = ("trang_thai", "loai_thanh_toan", "phuong_thuc")
    search_fields = ("ma_giao_dich", "nguoi_dung__username", "nguoi_dung__thu_dien_tu")
    readonly_fields = ("tao_luc", "cap_nhat_luc")


@admin.register(PhieuHoanTien)
class PhieuHoanTienAdmin(admin.ModelAdmin):
    list_display = (
        "id", "ma_phieu_hoan", "dat_ban", "so_tien_coc_goc", "phan_tram_hoan",
        "so_tien_hoan", "so_tien_phat", "moc_thoi_gian", "trang_thai", "tao_luc"
    )
    list_filter = ("trang_thai", "moc_thoi_gian", "phuong_thuc_hoan")
    search_fields = ("ma_phieu_hoan", "dat_ban__ma_dat_ban")
    readonly_fields = ("tao_luc", "cap_nhat_luc")

