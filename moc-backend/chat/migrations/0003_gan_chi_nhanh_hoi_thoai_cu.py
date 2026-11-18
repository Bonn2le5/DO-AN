"""Gắn chi nhánh cho các hội thoại tạo trước khi chat chia theo chi nhánh.

Chi nhánh lấy theo lượt đặt bàn của khách (không tính lượt đã huỷ): lượt sắp tới
gần nhất, nếu không có thì lượt gần đây nhất. Khách chưa từng đặt bàn thì để trống,
hội thoại nằm ở hộp thư chung của admin. Chỉ điền vào chỗ đang trống, không ghi đè.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import migrations


def gan_chi_nhanh(apps, schema_editor):
    HoiThoai = apps.get_model("chat", "HoiThoai")
    DatBan = apps.get_model("reservations", "DatBan")
    hom_nay = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()

    for hoi_thoai in HoiThoai.objects.filter(chi_nhanh__isnull=True).only("id", "khach_hang_id"):
        dat_ban = DatBan.objects.filter(nguoi_dung_id=hoi_thoai.khach_hang_id).exclude(trang_thai="da_huy")
        chi_nhanh_id = (
            dat_ban.filter(ngay_dat__gte=hom_nay).order_by("ngay_dat", "gio_bat_dau").values_list("chi_nhanh_id", flat=True).first()
            or dat_ban.order_by("-ngay_dat", "-gio_bat_dau").values_list("chi_nhanh_id", flat=True).first()
        )
        if chi_nhanh_id:
            HoiThoai.objects.filter(pk=hoi_thoai.pk, chi_nhanh__isnull=True).update(chi_nhanh_id=chi_nhanh_id)


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_hoi_thoai_chi_nhanh"),
        ("reservations", "0010_tat_chinh_sach_coc_chung_trung"),
    ]

    # Quay lại không cần bỏ gắn: cột chi_nhanh bị xoá ở 0002 khi đảo ngược.
    operations = [migrations.RunPython(gan_chi_nhanh, migrations.RunPython.noop)]
