from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_xacthucemail"),
        ("branches", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="nguoidung",
            name="chi_nhanh_quan_ly",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="nguoi_dung_quan_ly",
                to="branches.chinhanh",
            ),
        ),
    ]
