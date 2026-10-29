#!/usr/bin/env python3
"""
Auditor Independent Adversarial Test Suite for Milestone 2.
Written and executed by m2_auditor_1 to independently stress-test
VNPay HMAC, Concurrency, Refund arithmetic, and BOM deadlock isolation.
"""

import sys
import unittest
import threading
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
BACKEND_DIR = PROJECT_ROOT / "moc-backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.core.cache import caches
from rest_framework.exceptions import ValidationError
from payments.services import VNPayService, RefundService
from payments.models import ThanhToan, PhieuHoanTien
from reservations.services import DichVuDatBan
from reservations.models import BanAn, DatBan
from foods.services import DichVuKho
from foods.models import NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho


class TestAuditorAdversarialVNPay(unittest.TestCase):
    def setUp(self):
        self.secret = "AUDITOR_TEST_SECRET_KEY_1234567890"

    def test_special_characters_and_vietnamese_accents(self):
        """Test HMAC calculation with Vietnamese accents and special characters."""
        params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_OrderInfo": "Thanh toán lẩu gà lá é & bò nhúng dấm @ 100% ngon!",
            "vnp_Amount": "25000000",
            "vnp_TxnRef": "TT_SPECIAL_001",
        }
        h1 = VNPayService.calculate_hmac_sha512(params, self.secret)
        self.assertEqual(len(h1), 128)
        self.assertTrue(VNPayService.verify_signature(params, h1, self.secret))

    def test_hash_strips_both_hash_fields(self):
        """Verify both vnp_SecureHash and vnp_SecureHashType are excluded from signature."""
        params = {
            "vnp_TxnRef": "TT_002",
            "vnp_Amount": "10000000",
            "vnp_SecureHash": "SHOULD_BE_IGNORED",
            "vnp_SecureHashType": "SHA512",
        }
        clean_params = {"vnp_TxnRef": "TT_002", "vnp_Amount": "10000000"}
        h_with_hash = VNPayService.calculate_hmac_sha512(params, self.secret)
        h_clean = VNPayService.calculate_hmac_sha512(clean_params, self.secret)
        self.assertEqual(h_with_hash, h_clean)

    def test_none_and_empty_values_filtered(self):
        """Verify None and empty strings are filtered and do not alter hash."""
        p1 = {"vnp_TxnRef": "TT_003", "vnp_Amount": "10000000"}
        p2 = {"vnp_TxnRef": "TT_003", "vnp_Amount": "10000000", "vnp_BankCode": "", "vnp_Extra": None}
        h1 = VNPayService.calculate_hmac_sha512(p1, self.secret)
        h2 = VNPayService.calculate_hmac_sha512(p2, self.secret)
        self.assertEqual(h1, h2)

    @patch("django.db.transaction.atomic")
    @patch("payments.models.ThanhToan.objects.select_for_update")
    def test_ipn_spoofed_signature_fails_fast_without_db(self, mock_sfu, mock_atomic):
        """Spoofed signature must return 97 without querying database."""
        spoofed = {
            "vnp_TxnRef": "TT_SPOOFED",
            "vnp_Amount": "10000000",
            "vnp_ResponseCode": "00",
            "vnp_SecureHash": "fake_hash_value_128_hex_000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        }
        code, msg = VNPayService.process_ipn(spoofed)
        self.assertEqual(code, "97")
        self.assertEqual(msg, "Invalid Checksum")
        mock_sfu.assert_not_called()


class TestAuditorAdversarialRefund(unittest.TestCase):
    def setUp(self):
        self.target = datetime(2026, 12, 1, 19, 0, 0)

    def test_exact_microsecond_boundary_24h(self):
        """Test exact microsecond boundaries around 24 hours."""
        # 24 hours + 1 microsecond -> > 24h -> 100%
        t_plus = self.target - timedelta(hours=24, microseconds=1)
        moc, pct, hoan, phat, st = RefundService.calculate_refund(self.target, t_plus, 100000)
        self.assertEqual(pct, 100.0)
        self.assertEqual(moc, "truoc_24h")

        # Exactly 24 hours -> 50%
        t_exact = self.target - timedelta(hours=24)
        moc, pct, hoan, phat, st = RefundService.calculate_refund(self.target, t_exact, 100000)
        self.assertEqual(pct, 50.0)
        self.assertEqual(moc, "tu_6_den_24h")

        # 24 hours - 1 microsecond -> 50%
        t_minus = self.target - timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
        moc, pct, hoan, phat, st = RefundService.calculate_refund(self.target, t_minus, 100000)
        self.assertEqual(pct, 50.0)
        self.assertEqual(moc, "tu_6_den_24h")

    def test_exact_microsecond_boundary_6h(self):
        """Test exact microsecond boundaries around 6 hours."""
        # Exactly 6 hours -> 50%
        t_exact = self.target - timedelta(hours=6)
        moc, pct, hoan, phat, st = RefundService.calculate_refund(self.target, t_exact, 100000)
        self.assertEqual(pct, 50.0)
        self.assertEqual(moc, "tu_6_den_24h")

        # 6 hours - 1 microsecond -> 0%
        t_minus = self.target - timedelta(hours=5, minutes=59, seconds=59, microseconds=999999)
        moc, pct, hoan, phat, st = RefundService.calculate_refund(self.target, t_minus, 100000)
        self.assertEqual(pct, 0.0)
        self.assertEqual(moc, "trong_6h")

    def test_odd_amount_penny_conservation(self):
        """Odd deposit amounts must conserve every penny: refund + penalty == original."""
        odd_amounts = [333333.33, 999999.0, 100001.0, 50005.55]
        t = self.target - timedelta(hours=10)  # 50% refund bracket
        for amt in odd_amounts:
            moc, pct, hoan, phat, st = RefundService.calculate_refund(self.target, t, amt)
            self.assertAlmostEqual(hoan + phat, amt, places=2)


class TestAuditorAdversarialConcurrency(unittest.TestCase):
    def setUp(self):
        self.cache = caches["locmem"]
        self.cache.clear()

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_maintenance_table_cannot_be_held(self, mock_filter, mock_ban_sr):
        """Table under maintenance must raise ValidationError."""
        mock_ban = MagicMock(id=1, trang_thai=BanAn.TrangThai.BAO_TRI, suc_chua=4)
        mock_ban_sr.return_value.get.return_value = mock_ban
        with patch("reservations.services._safe_cache", return_value=self.cache):
            with self.assertRaises(ValidationError):
                DichVuDatBan.giu_ban_tam_thoi(ban_id=1, ngay="2026-10-25", gio="19:00", so_khach=2)

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_capacity_overflow_cannot_be_held(self, mock_filter, mock_ban_sr):
        """Requesting guests exceeding table capacity must raise ValidationError."""
        mock_ban = MagicMock(id=1, trang_thai=BanAn.TrangThai.TRONG, suc_chua=4)
        mock_ban_sr.return_value.get.return_value = mock_ban
        with patch("reservations.services._safe_cache", return_value=self.cache):
            with self.assertRaises(ValidationError):
                DichVuDatBan.giu_ban_tam_thoi(ban_id=1, ngay="2026-10-25", gio="19:00", so_khach=8)

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_concurrent_threads_race_for_same_hold(self, mock_filter, mock_ban_sr):
        """In a multi-threaded race condition for the same table, exactly 1 thread wins."""
        mock_ban = MagicMock(id=12, trang_thai=BanAn.TrangThai.TRONG, suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_filter.return_value.exists.return_value = False

        results = []
        def attempt():
            with patch("reservations.services._safe_cache", return_value=self.cache):
                ok, data = DichVuDatBan.giu_ban_tam_thoi(
                    ban_id=12, ngay="2026-11-01", gio="19:00", so_khach=4
                )
                results.append((ok, data))

        threads = [threading.Thread(target=attempt) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successes = [r for r in results if r[0] is True]
        conflicts = [r for r in results if r[0] is False]
        self.assertEqual(len(successes), 1, "Exactly 1 concurrent request should succeed")
        self.assertEqual(len(conflicts), 9, "All 9 others should receive conflict")
        for ok, data in conflicts:
            self.assertEqual(data["code"], "BAN_DANG_BAN")


class TestAuditorAdversarialBOM(unittest.TestCase):
    @patch("foods.models.NguyenLieu.objects.select_for_update")
    @patch("foods.models.DinhMucNguyenLieu.objects.filter")
    @patch("foods.models.LichSuXuatNhapKho.objects.filter")
    def test_strict_ordering_preserves_even_when_input_inverted(
        self, mock_hist_filter, mock_bom_filter, mock_nl_sfu
    ):
        """Even if dishes and BOM return reverse ID ordering, locking query must request ascending order."""
        mock_hist_filter.return_value.exists.return_value = False

        # Inverted IDs: 99, 50, 10
        dm1 = MagicMock(mon_an_id=1, nguyen_lieu_id=99, so_luong_can=Decimal("1.0"))
        dm2 = MagicMock(mon_an_id=1, nguyen_lieu_id=50, so_luong_can=Decimal("2.0"))
        dm3 = MagicMock(mon_an_id=1, nguyen_lieu_id=10, so_luong_can=Decimal("3.0"))
        mock_bom_filter.return_value.select_related.return_value = [dm1, dm2, dm3]

        nl10 = MagicMock(id=10, ten="A", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl50 = MagicMock(id=50, ten="B", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl99 = MagicMock(id=99, ten="C", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))

        mock_nl_filter = mock_nl_sfu.return_value.filter.return_value
        mock_nl_filter.order_by.return_value = [nl10, nl50, nl99]

        with patch("foods.models.LichSuXuatNhapKho.objects.create"):
            with patch("django.db.transaction.atomic"):
                DichVuKho.khau_tru_nguyen_lieu_bom(
                    danh_sach_mon=[{"mon_an_id": 1, "so_luong": 1}],
                    loai_tham_chieu="don_hang",
                    id_tham_chieu=888,
                )

        # Assert ID list requested is [10, 50, 99] strictly sorted
        mock_nl_sfu.return_value.filter.assert_called_with(id__in=[10, 50, 99])
        mock_nl_filter.order_by.assert_called_with("id")


if __name__ == "__main__":
    unittest.main()
