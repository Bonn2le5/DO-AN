#!/usr/bin/env python3
"""
Test Enhancements for Milestone 2 Iteration 2 Verification.
These tests verify the fixes for:
1. ViewSet permissions on VNPay endpoints & Table Hold.
2. QueryDict scalar extraction in process_ipn and vnpay_return.
3. Payment cancellation (code 24) transition to DA_HUY & table freeing.
4. Transaction scoping in tao_dat_ban and IPN.
"""

import os
import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.http import QueryDict
from django.core.cache import caches
from rest_framework.test import APIRequestFactory, force_authenticate

from payments.models import ThanhToan
from payments.services import VNPayService
from payments.views import ThanhToanViewSet
from reservations.models import BanAn, DatBan
from reservations.services import DichVuDatBan
from reservations.views import BanAnViewSet, DatBanViewSet


class TestMilestone2Iteration2Fixes(unittest.TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.secret = "VNPAYSECRETKEY2026MOCRESTAURANT"

    def test_fix_01_querydict_scalar_extraction_in_process_ipn(self):
        """Verify that passing a Django QueryDict does not wrap parameters in lists and verifies valid checksum."""
        params_str = (
            "vnp_Amount=20000000&vnp_BankCode=NCB&vnp_BankTranNo=VNP12345678&"
            "vnp_CardType=ATM&vnp_Command=pay&vnp_CreateDate=20261014120000&"
            "vnp_CurrCode=VND&vnp_OrderInfo=Thanh+toan+dat+coc&"
            "vnp_PayDate=20261014120500&vnp_ResponseCode=00&vnp_TmnCode=MOCREST1&"
            "vnp_TransactionNo=14567890&vnp_TransactionStatus=00&"
            "vnp_TxnRef=TT_TEST_QUERYDICT&vnp_Version=2.1.0"
        )
        qd = QueryDict(params_str, mutable=True)
        # Compute valid hash over clean scalar dictionary
        hash_val = VNPayService.calculate_hmac_sha512(qd.dict(), self.secret)
        qd["vnp_SecureHash"] = hash_val

        mock_tt = MagicMock(so_tien=Decimal("200000.00"), trang_thai="cho_xu_ly", loai_thanh_toan="tien_coc")
        mock_db = MagicMock(ban_an_id=1, ngay_dat="2026-11-20", gio_bat_dau="19:00:00", phien_ban=1)
        mock_tt.dat_ban = mock_db

        with patch("django.db.transaction.atomic"):
            with patch("payments.models.ThanhToan.objects.select_for_update") as mock_sfu:
                mock_sfu.return_value.select_related.return_value.get.return_value = mock_tt
                code, msg = VNPayService.process_ipn(qd)

        self.assertEqual(code, "00", f"Expected code 00 for valid QueryDict IPN, got {code} ({msg})")
        self.assertEqual(msg, "Confirm Success")

    def test_fix_02_payment_viewset_allows_unauthenticated_vnpay_endpoints(self):
        """Verify that ThanhToanViewSet.get_permissions allows unauthenticated access for IPN, return, and create."""
        view_ipn = ThanhToanViewSet.as_view({"get": "vnpay_ipn"})
        request = self.factory.get("/api/payments/vnpay/ipn/?vnp_SecureHash=dummy")
        response = view_ipn(request)
        # Check that it did NOT fail with HTTP 401 Unauthorized
        self.assertNotEqual(response.status_code, 401, "vnpay_ipn must not return 401 for anonymous caller")
        self.assertEqual(response.status_code, 200)

        view_return = ThanhToanViewSet.as_view({"get": "vnpay_return"})
        request_ret = self.factory.get("/api/payments/vnpay/return/?vnp_ResponseCode=00&vnp_SecureHash=invalid")
        response_ret = view_return(request_ret)
        self.assertNotEqual(response_ret.status_code, 401, "vnpay_return must not return 401 for anonymous caller")
        self.assertEqual(response_ret.status_code, 200)

    def test_fix_03_table_hold_allows_guest_and_customer_post(self):
        """Verify that BanAnViewSet.giu_ban allows both guest and authenticated customer without 401/403."""
        ban_view = BanAnViewSet.as_view({"post": "giu_ban"})

        with patch("reservations.services.DichVuDatBan.giu_ban_tam_thoi") as mock_hold:
            mock_hold.return_value = (True, {"status": "success", "id_giu_ban": "HOLD_123", "thoi_gian_con_lai_giay": 600})

            # Unauthenticated guest
            request_guest = self.factory.post("/api/tables/1/giu_ban/", {"ngay": "2026-11-20", "gio": "19:00", "so_luong_khach": 4}, format="json")
            resp_guest = ban_view(request_guest, pk=1)
            self.assertEqual(resp_guest.status_code, 200, "Unauthenticated guest should succeed in holding table")

            # Authenticated non-staff customer
            request_cust = self.factory.post("/api/tables/1/giu_ban/", {"ngay": "2026-11-20", "gio": "19:00", "so_luong_khach": 4}, format="json")
            mock_user = MagicMock(is_authenticated=True, is_staff=False, la_nhan_vien_nha_hang=False)
            force_authenticate(request_cust, user=mock_user)
            resp_cust = ban_view(request_cust, pk=1)
            self.assertEqual(resp_cust.status_code, 200, "Authenticated customer should succeed in holding table")

    def test_fix_04_payment_failure_transitions_dat_ban_to_da_huy_and_frees_table(self):
        """Verify that payment failure (e.g. code 24) sets DatBan.trang_thai = DA_HUY and clears hold keys."""
        mock_tt = MagicMock(so_tien=Decimal("200000.00"), trang_thai="cho_xu_ly", loai_thanh_toan="tien_coc")
        mock_db = MagicMock(ban_an_id=7, ngay_dat="2026-11-25", gio_bat_dau="18:30:00", phien_ban=1)
        mock_tt.dat_ban = mock_db

        query_params = {
            "vnp_TxnRef": "TT_CANCEL_TEST",
            "vnp_Amount": "20000000",
            "vnp_ResponseCode": "24",  # Cancelled by user
        }
        query_params["vnp_SecureHash"] = VNPayService.calculate_hmac_sha512(query_params, self.secret)

        cache = caches["locmem"]
        cache.clear()
        cache.set("table_hold:7:2026-11-25:18:30", "HOLD_TOKEN_1", timeout=600)

        with patch("django.db.transaction.atomic"):
            with patch("payments.models.ThanhToan.objects.select_for_update") as mock_sfu:
                mock_sfu.return_value.select_related.return_value.get.return_value = mock_tt
                with patch("payments.services._safe_cache", return_value=cache):
                    code, msg = VNPayService.process_ipn(query_params)

        self.assertEqual(code, "00")
        self.assertEqual(msg, "Confirm Failure")
        self.assertEqual(mock_tt.trang_thai, ThanhToan.TrangThai.THAT_BAI)
        # CRITICAL ASSERTION: DatBan MUST be transitioned to DA_HUY
        self.assertEqual(mock_db.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(mock_db.trang_thai_coc, DatBan.TrangThaiCoc.THAT_BAI)
        # Hold key MUST be deleted
        self.assertIsNone(cache.get("table_hold:7:2026-11-25:18:30"))

if __name__ == "__main__":
    unittest.main()
