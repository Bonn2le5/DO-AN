from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0002_initial"),
        ("reservations", "0009_dining_session_and_table_cleaning"),
    ]

    operations = [
        migrations.AlterField(
            model_name="donhang",
            name="khach_hang",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="danh_sach_don_hang", to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="donhang",
            name="hinh_thuc",
            field=models.CharField(
                choices=[("giao_hang", "Giao hàng"), ("tu_den_lay", "Tự đến lấy"), ("tai_cho", "Dùng tại bàn")],
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name="donhang",
            name="phien_phuc_vu",
            field=models.OneToOneField(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="don_hang", to="reservations.phienphucvu",
            ),
        ),
        migrations.AddField(
            model_name="chitietdonhang",
            name="ghi_chu",
            field=models.TextField(blank=True),
        ),
    ]
