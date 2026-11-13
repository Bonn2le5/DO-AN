"""Tách tồn kho nguyên liệu theo chi nhánh (3/3): bỏ hai cột tồn kho chung trên nguyen_lieu."""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("foods", "0003_chep_ton_kho_sang_chi_nhanh"),
    ]

    operations = [
        migrations.RemoveField(model_name="nguyenlieu", name="ton_kho_hien_tai"),
        migrations.RemoveField(model_name="nguyenlieu", name="ton_kho_toi_thieu"),
    ]
