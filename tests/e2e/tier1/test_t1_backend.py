"""
Tier 1: Backend Feature Coverage Tests (T1_backend)
Verifies:
1. Seed data file existence and >= 100 dishes content.
2. Database schema SQL integrity & enum types.
3. Django backend project structure & 13 modular apps.
4. Django configuration settings & installed apps.
5. Seed data parsing & structure validation.
"""

import os
import unittest
from pathlib import Path


PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
BACKEND_DIR = PROJECT_ROOT / "moc-backend"


class TestTier1Backend(unittest.TestCase):
    """Tier 1: Backend Feature Coverage Tests"""

    def test_t1_backend_01_seed_data_file_has_100_plus_foods(self):
        """Test 1: Verify Du-lieu-test.txt exists and contains at least 100 food items."""
        seed_file = PROJECT_ROOT / "Du-lieu-test.txt"
        self.assertTrue(seed_file.exists(), f"Seed data file not found at {seed_file}")

        content = seed_file.read_text(encoding="utf-8")
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        # Count food entries by checking lines with price pattern (VND or số tiền)
        food_lines = [l for l in lines if any(sep in l for sep in [",", "|", "\t"]) and any(char.isdigit() for char in l)]
        self.assertGreaterEqual(
            len(food_lines),
            100,
            f"Expected at least 100 food items in Du-lieu-test.txt, found {len(food_lines)}"
        )

    def test_t1_backend_02_schema_sql_defines_core_enums_and_tables(self):
        """Test 2: Verify moc_schema_tieng_viet.sql defines core enums and required tables."""
        schema_file = PROJECT_ROOT / "moc_schema_tieng_viet.sql"
        self.assertTrue(schema_file.exists(), "Schema file moc_schema_tieng_viet.sql not found")

        sql_content = schema_file.read_text(encoding="utf-8")

        required_enums = [
            "trang_thai_ban",
            "hinh_thuc_dat_ban",
            "trang_thai_dat_ban",
            "trang_thai_coc",
            "moc_huy_dat_ban",
            "trang_thai_don_hang",
            "loai_thanh_toan",
            "trang_thai_thanh_toan",
            "loai_tuong_tac",
        ]
        for enum_name in required_enums:
            self.assertIn(
                enum_name,
                sql_content,
                f"Enum {enum_name} not defined in moc_schema_tieng_viet.sql"
            )

        required_tables = [
            "chi_nhanh",
            "ban_an",
            "dat_ban",
            "mon_an",
            "don_hang",
            "thanh_toan",
            "chinh_sach_dat_coc",
            "quy_tac_huy_dat_coc",
            "tin_nhan",
            "tuong_tac_mon_an",
        ]
        for tbl in required_tables:
            self.assertIn(
                tbl,
                sql_content,
                f"Table {tbl} not defined in moc_schema_tieng_viet.sql"
            )

    def test_t1_backend_03_backend_project_layout(self):
        """Test 3: Verify Django backend contains all required 13 modular apps."""
        self.assertTrue(BACKEND_DIR.exists(), "moc-backend directory not found")

        required_apps = [
            "accounts", "foods", "branches", "reservations", "orders",
            "payments", "carts", "promotions", "reviews", "chat",
            "recommendations", "analytics", "posts"
        ]
        for app_name in required_apps:
            app_path = BACKEND_DIR / app_name
            self.assertTrue(
                app_path.is_dir(),
                f"App module {app_name} not found in {BACKEND_DIR}"
            )
            self.assertTrue(
                (app_path / "models.py").exists(),
                f"models.py missing in {app_name}"
            )

    def test_t1_backend_04_django_settings_and_installed_apps(self):
        """Test 4: Verify config/settings.py contains required framework and modular apps."""
        settings_path = BACKEND_DIR / "config" / "settings.py"
        self.assertTrue(settings_path.exists(), "config/settings.py not found")

        content = settings_path.read_text(encoding="utf-8")
        self.assertIn("rest_framework", content)
        self.assertIn("corsheaders", content)
        self.assertIn("reservations", content)
        self.assertIn("payments", content)

        # Check channels is provisioned in requirements.txt
        req_file = BACKEND_DIR / "requirements.txt"
        self.assertTrue(req_file.exists())
        self.assertIn("channels", req_file.read_text(encoding="utf-8"))

    def test_t1_backend_05_seed_data_categories_parsing(self):
        """Test 5: Verify seed data contains the 5 restaurant categories from Du-lieu-test.txt."""
        seed_file = PROJECT_ROOT / "Du-lieu-test.txt"
        content = seed_file.read_text(encoding="utf-8")

        # Authoritative categories defined in Du-lieu-test.txt (lines 6-11)
        expected_categories = ["Lẩu", "Nướng", "Gỏi", "Nhâm nhi", "Đồ uống"]
        found = [k for k in expected_categories if k in content]
        self.assertEqual(
            len(found),
            5,
            f"Expected all 5 categories in seed file, found: {found}"
        )


if __name__ == "__main__":
    unittest.main()
