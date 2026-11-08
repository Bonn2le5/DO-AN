from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("branches", "0001_initial"),
        ("reservations", "0008_private_rooms"),
    ]

    operations = [
        migrations.AlterField(
            model_name="banan",
            name="trang_thai",
            field=models.CharField(
                choices=[
                    ("trong", "Trống"),
                    ("dang_giu", "Đang giữ"),
                    ("da_dat", "Đã đặt"),
                    ("dang_phuc_vu", "Đang phục vụ"),
                    ("cho_don", "Chờ dọn"),
                    ("bao_tri", "Bảo trì"),
                ],
                default="trong",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="datban",
            name="check_in_luc",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="PhienPhucVu",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tao_luc", models.DateTimeField(auto_now_add=True)),
                ("cap_nhat_luc", models.DateTimeField(auto_now=True)),
                ("ma_phien", models.CharField(editable=False, max_length=24, unique=True)),
                ("so_luong_khach", models.PositiveIntegerField()),
                ("ten_khach", models.CharField(blank=True, max_length=150)),
                ("sdt_khach", models.CharField(blank=True, max_length=20)),
                ("ghi_chu", models.TextField(blank=True)),
                ("trang_thai", models.CharField(
                    choices=[("dang_phuc_vu", "Đang phục vụ"), ("cho_don", "Chờ dọn"), ("da_dong", "Đã đóng")],
                    db_index=True, default="dang_phuc_vu", max_length=20,
                )),
                ("bat_dau_luc", models.DateTimeField(auto_now_add=True)),
                ("check_out_luc", models.DateTimeField(blank=True, null=True)),
                ("da_don_luc", models.DateTimeField(blank=True, null=True)),
                ("ban_an", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="danh_sach_phien_phuc_vu", to="reservations.banan")),
                ("chi_nhanh", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="danh_sach_phien_phuc_vu", to="branches.chinhanh")),
                ("dat_ban", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="phien_phuc_vu", to="reservations.datban")),
                ("nguoi_bat_dau", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="phien_phuc_vu_bat_dau", to=settings.AUTH_USER_MODEL)),
                ("nguoi_check_out", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="phien_phuc_vu_check_out", to=settings.AUTH_USER_MODEL)),
                ("nguoi_xac_nhan_don", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="phien_phuc_vu_da_don", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Phiên phục vụ",
                "db_table": "phien_phuc_vu",
                "ordering": ("-bat_dau_luc",),
            },
        ),
        migrations.AddConstraint(
            model_name="phienphucvu",
            constraint=models.CheckConstraint(
                condition=models.Q(("so_luong_khach__gte", 1), ("so_luong_khach__lte", 12)),
                name="phien_phuc_vu_so_khach_1_12",
            ),
        ),
        migrations.AddConstraint(
            model_name="phienphucvu",
            constraint=models.UniqueConstraint(
                condition=models.Q(("trang_thai__in", ["dang_phuc_vu", "cho_don"])),
                fields=("ban_an",),
                name="mot_phien_con_hieu_luc_moi_ban",
            ),
        ),
    ]
