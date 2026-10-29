from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("analytics", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="AdminSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(default="restaurant", max_length=40, unique=True)),
                ("value", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "admin_setting"},
        ),
    ]
