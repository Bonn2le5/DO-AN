from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("reservations", "0004_pending_confirmation_status")]

    operations = [
        migrations.AlterField(
            model_name="datban",
            name="ban_an",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="danh_sach_dat_ban",
                to="reservations.banan",
            ),
        ),
    ]
