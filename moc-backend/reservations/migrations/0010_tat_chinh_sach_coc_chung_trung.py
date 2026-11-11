"""Tắt các chính sách cọc chung bị tạo trùng.

Trước đây GET /dat-ban/chinh_sach_coc/?branch=... tạo thêm một chính sách chung mỗi lần khách mở
trang đặt bàn. Giữ bản cũ nhất còn áp dụng, các bản chung còn lại chuyển con_ap_dung=False
(không xoá, để lịch sử vẫn đọc được).
"""
from django.db import migrations


def tat_ban_trung(apps, schema_editor):
    ChinhSachDatCoc = apps.get_model("reservations", "ChinhSachDatCoc")
    chung = ChinhSachDatCoc.objects.filter(chi_nhanh__isnull=True, con_ap_dung=True).order_by("id")
    giu = chung.first()
    if giu:
        chung.exclude(pk=giu.pk).update(con_ap_dung=False)


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0009_dining_session_and_table_cleaning"),
    ]

    operations = [
        migrations.RunPython(tat_ban_trung, migrations.RunPython.noop),
    ]
