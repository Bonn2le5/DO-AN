from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reservations", "0001_initial")]
    operations = [
        migrations.AddField(model_name="chinhsachdatcoc", name="so_dien_thoai_lien_he", field=models.CharField(blank=True, max_length=30)),
        migrations.AddField(model_name="chinhsachdatcoc", name="noi_dung_huong_dan", field=models.TextField(blank=True)),
    ]
