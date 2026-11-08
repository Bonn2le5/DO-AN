from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("branches", "0001_initial"),
        ("reservations", "0007_archive_tables"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhongRieng",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tao_luc", models.DateTimeField(auto_now_add=True)),
                ("cap_nhat_luc", models.DateTimeField(auto_now=True)),
                ("ten_phong", models.CharField(max_length=80)),
                ("tang", models.CharField(blank=True, max_length=50)),
                ("suc_chua", models.PositiveIntegerField(default=12)),
                ("con_hoat_dong", models.BooleanField(default=True)),
                ("chi_nhanh", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="danh_sach_phong_rieng", to="branches.chinhanh")),
            ],
            options={
                "db_table": "phong_rieng",
                "ordering": ("chi_nhanh_id", "tang", "ten_phong"),
                "unique_together": {("chi_nhanh", "ten_phong")},
            },
        ),
        migrations.AddField(
            model_name="banan",
            name="phong_rieng",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="danh_sach_ban", to="reservations.phongrieng"),
        ),
    ]
