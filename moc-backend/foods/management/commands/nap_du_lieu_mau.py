"""
Alias command for seed_data.
Run via: python manage.py nap_du_lieu_mau
"""
from foods.management.commands.seed_data import Command as SeedDataCommand


class Command(SeedDataCommand):
    help = "Lệnh tiếng Việt: Nạp dữ liệu mẫu nhà hàng Mộc (danh mục, 100 món, bàn ăn, chi nhánh GIS, tài khoản)"
