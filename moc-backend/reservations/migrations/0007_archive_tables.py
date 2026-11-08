from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("reservations", "0006_capacity_limits_1_12"),
    ]

    operations = [
        migrations.AddField(
            model_name="banan",
            name="da_luu_tru",
            field=models.BooleanField(default=False),
        ),
    ]
