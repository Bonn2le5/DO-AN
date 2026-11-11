from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("analytics", "0002_adminsetting")]

    operations = [
        migrations.RenameModel(old_name="AdminSetting", new_name="CaiDatQuanTri"),
    ]
