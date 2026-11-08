from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0005_optional_reservation_table"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="banan",
            constraint=models.CheckConstraint(
                condition=models.Q(suc_chua__gte=1, suc_chua__lte=12),
                name="ban_an_suc_chua_1_12",
            ),
        ),
        migrations.AddConstraint(
            model_name="datban",
            constraint=models.CheckConstraint(
                condition=models.Q(so_luong_khach__gte=1, so_luong_khach__lte=12),
                name="dat_ban_so_khach_1_12",
            ),
        ),
    ]
