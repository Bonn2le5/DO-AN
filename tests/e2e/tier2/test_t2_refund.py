"""
Tier 2: Deposit Refund Policy Boundary & Corner Cases Tests (T2_refund)
Verifies:
1. Cancellation at >24h (e.g. 25h): 100% refund, 0 penalty, status 'da_hoan_tien'.
2. Cancellation at exactly 24.0h boundary: 50% refund, 50% penalty, status 'hoan_tien_mot_phan'.
3. Cancellation within 6h to 24h (e.g. 12h): 50% refund, 50% penalty, status 'hoan_tien_mot_phan'.
4. Cancellation under 6h (e.g. 5h50m): 0% refund, 100% penalty, status 'that_bai'.
5. No-show (khach_khong_den) & PhieuHoanTien audit receipt generation.
"""

import unittest
from datetime import datetime, timedelta
from tests.e2e.helpers.refund_calculator import calculate_refund, generate_refund_receipt


class TestTier2Refund(unittest.TestCase):
    """Tier 2: Deposit Refund Boundaries Tests"""

    def setUp(self):
        self.booking_time = datetime(2026, 10, 25, 19, 0, 0)
        self.deposit_amount = 300000.0  # 300,000 VND

    def test_t2_refund_01_cancellation_above_24h_100_percent(self):
        """Test 1: Cancellation at 25h before reservation gives 100% refund."""
        cancel_time = self.booking_time - timedelta(hours=25)
        moc, pct, refund, penalty, status = calculate_refund(
            self.booking_time, cancel_time, self.deposit_amount
        )
        self.assertEqual(moc, "truoc_24h")
        self.assertEqual(pct, 100.0)
        self.assertEqual(refund, 300000.0)
        self.assertEqual(penalty, 0.0)
        self.assertEqual(status, "da_hoan_tien")

    def test_t2_refund_02_cancellation_exactly_24h_50_percent(self):
        """Test 2: Cancellation at exactly 24.0h gives 50% refund."""
        cancel_time = self.booking_time - timedelta(hours=24)
        moc, pct, refund, penalty, status = calculate_refund(
            self.booking_time, cancel_time, self.deposit_amount
        )
        self.assertEqual(moc, "tu_6_den_24h")
        self.assertEqual(pct, 50.0)
        self.assertEqual(refund, 150000.0)
        self.assertEqual(penalty, 150000.0)
        self.assertEqual(status, "hoan_tien_mot_phan")

    def test_t2_refund_03_cancellation_between_6h_and_24h_50_percent(self):
        """Test 3: Cancellation at 10.5 hours before reservation gives 50% refund."""
        cancel_time = self.booking_time - timedelta(hours=10, minutes=30)
        moc, pct, refund, penalty, status = calculate_refund(
            self.booking_time, cancel_time, self.deposit_amount
        )
        self.assertEqual(moc, "tu_6_den_24h")
        self.assertEqual(pct, 50.0)
        self.assertEqual(refund, 150000.0)
        self.assertEqual(penalty, 150000.0)
        self.assertEqual(status, "hoan_tien_mot_phan")

    def test_t2_refund_04_cancellation_under_6h_0_percent(self):
        """Test 4: Cancellation at 5 hours 50 minutes before reservation gives 0% refund."""
        cancel_time = self.booking_time - timedelta(hours=5, minutes=50)
        moc, pct, refund, penalty, status = calculate_refund(
            self.booking_time, cancel_time, self.deposit_amount
        )
        self.assertEqual(moc, "trong_6h")
        self.assertEqual(pct, 0.0)
        self.assertEqual(refund, 0.0)
        self.assertEqual(penalty, 300000.0)
        self.assertEqual(status, "that_bai")

    def test_t2_refund_05_no_show_and_receipt_generation(self):
        """Test 5: No-show forfeits 100% of deposit and generates audit receipt."""
        receipt = generate_refund_receipt(
            ma_dat_ban="DB889900",
            khach_hang_info={"ho_ten": "Le Van C", "so_dien_thoai": "0912345678"},
            chi_nhanh_info={"id": 1, "ten": "Chi nhánh Tân Bình"},
            thoi_gian_dat=self.booking_time,
            thoi_gian_huy=self.booking_time + timedelta(hours=1),
            so_tien_coc=self.deposit_amount,
            ly_do_huy="Khách không đến",
            is_no_show=True,
        )
        self.assertEqual(receipt["chinh_sach_ap_dung"]["moc"], "khach_khong_den")
        self.assertEqual(receipt["chinh_sach_ap_dung"]["ty_le_hoan_phan_tram"], 0.0)
        self.assertEqual(receipt["tai_chinh"]["so_tien_hoan_tra"], 0.0)
        self.assertEqual(receipt["tai_chinh"]["so_tien_khau_tru_phat"], 300000.0)
        self.assertEqual(receipt["trang_thai"], "that_bai")
        self.assertTrue(receipt["ma_phieu_hoan"].startswith("RF-DB889900"))


if __name__ == "__main__":
    unittest.main()
