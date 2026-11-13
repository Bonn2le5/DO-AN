"""Tách tồn kho nguyên liệu theo chi nhánh (1/3): bảng ton_kho_chi_nhanh và cột chi_nhanh của lịch sử kho."""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0002_chinhanh_idx_chi_nhanh_toa_do"),
        ("orders", "0005_gan_khach_don_tai_cho"),
        ("reservations", "0010_tat_chinh_sach_coc_chung_trung"),
        ("foods", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lichsuxuatnhapkho",
            name="chi_nhanh",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="lich_su_kho", to="branches.chinhanh"),
        ),
        migrations.CreateModel(
            name="TonKhoChiNhanh",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tao_luc", models.DateTimeField(auto_now_add=True)),
                ("cap_nhat_luc", models.DateTimeField(auto_now=True)),
                ("ton_kho_hien_tai", models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ("ton_kho_toi_thieu", models.DecimalField(decimal_places=3, default=0, max_digits=14)),
                ("chi_nhanh", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ton_kho_nguyen_lieu", to="branches.chinhanh")),
                ("nguyen_lieu", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ton_kho_chi_nhanh", to="foods.nguyenlieu")),
            ],
            options={
                "verbose_name": "Tồn kho chi nhánh",
                "db_table": "ton_kho_chi_nhanh",
                "constraints": [models.UniqueConstraint(fields=("nguyen_lieu", "chi_nhanh"), name="uq_ton_kho_nguyen_lieu_chi_nhanh")],
            },
        ),
    ]
