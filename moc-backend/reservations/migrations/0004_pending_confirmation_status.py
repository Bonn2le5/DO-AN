from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reservations", "0003_deposit_policy_admin_contact")]

    operations = [
        migrations.AlterField(
            model_name="datban",
            name="trang_thai",
            field=models.CharField(
                choices=[
                    ("cho_xac_nhan", "Chờ nhà hàng xác nhận"),
                    ("cho_thanh_toan", "Chờ thanh toán"),
                    ("da_xac_nhan", "Đã xác nhận"),
                    ("khach_da_den", "Khách đã đến"),
                    ("hoan_tat", "Hoàn tất"),
                    ("da_huy", "Đã hủy"),
                    ("khach_khong_den", "Khách không đến"),
                ],
                default="cho_xac_nhan",
                max_length=20,
            ),
        ),
    ]
