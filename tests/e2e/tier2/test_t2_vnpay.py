"""
Tier 2: VNPay Security, Tampering & Corner Cases Tests (T2_vnpay)
Verifies:
1. Invalid Checksum / Tampered parameters returns RspCode '97'.
2. Duplicate IPN callback idempotency returns RspCode '02' without double processing.
3. Tampered amount returns RspCode '04'.
4. Non-existent transaction reference returns RspCode '01'.
5. Unicode encoding & URL escaping integrity with Vietnamese characters.
"""

import unittest
from tests.e2e.helpers.vnpay_oracle import (
    build_vnpay_payment_url,
    calculate_hmac_sha512,
    evaluate_vnpay_ipn,
    DEFAULT_HASH_SECRET,
    DEFAULT_TMN_CODE,
)


class TestTier2VNPay(unittest.TestCase):
    """Tier 2: VNPay Boundary and Corner Cases Tests"""

    def setUp(self):
        self.txn_ref = "TT2001_1728879000"
        self.amount = 350000  # 350,000 VND
        self.secret = DEFAULT_HASH_SECRET
        self.db_record = {
            "ma_giao_dich": self.txn_ref,
            "so_tien": self.amount,
            "trang_thai": "cho_xu_ly",
        }

    def test_t2_vnpay_01_invalid_checksum_returns_rspcode_97(self):
        """Test 1: Tampered query param or fake signature returns RspCode '97' (Invalid Checksum)."""
        ipn_params = {
            "vnp_TxnRef": self.txn_ref,
            "vnp_Amount": str(int(self.amount * 100)),
            "vnp_ResponseCode": "00",
            "vnp_SecureHash": "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
        }
        rsp_code, msg, _ = evaluate_vnpay_ipn(ipn_params, self.db_record, self.secret)
        self.assertEqual(rsp_code, "97")
        self.assertEqual(msg, "Invalid Checksum")

    def test_t2_vnpay_02_duplicate_ipn_idempotency_returns_rspcode_02(self):
        """Test 2: Second IPN callback for already confirmed payment returns RspCode '02'."""
        confirmed_db_record = {
            "ma_giao_dich": self.txn_ref,
            "so_tien": self.amount,
            "trang_thai": "thanh_cong",  # Already confirmed
        }

        ipn_params = {
            "vnp_TxnRef": self.txn_ref,
            "vnp_Amount": str(int(self.amount * 100)),
            "vnp_ResponseCode": "00",
        }
        ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(ipn_params, self.secret)

        rsp_code, msg, updated = evaluate_vnpay_ipn(ipn_params, confirmed_db_record, self.secret)
        self.assertEqual(rsp_code, "02")
        self.assertEqual(msg, "Order already confirmed")
        # Ensure status was not mutated
        self.assertEqual(updated["trang_thai"], "thanh_cong")

    def test_t2_vnpay_03_tampered_amount_returns_rspcode_04(self):
        """Test 3: Malicious client paying less than expected amount triggers RspCode '04' (Invalid amount)."""
        tampered_ipn_params = {
            "vnp_TxnRef": self.txn_ref,
            "vnp_Amount": "1000000",  # Only 10,000 VND instead of 350,000 VND
            "vnp_ResponseCode": "00",
        }
        tampered_ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(tampered_ipn_params, self.secret)

        rsp_code, msg, _ = evaluate_vnpay_ipn(tampered_ipn_params, self.db_record, self.secret)
        self.assertEqual(rsp_code, "04")
        self.assertEqual(msg, "Invalid amount")

    def test_t2_vnpay_04_missing_order_returns_rspcode_01(self):
        """Test 4: IPN with unknown or deleted txn_ref returns RspCode '01' (Order not found)."""
        unknown_params = {
            "vnp_TxnRef": "UNKNOWN_TRANSACTION_ID",
            "vnp_Amount": "35000000",
            "vnp_ResponseCode": "00",
        }
        unknown_params["vnp_SecureHash"] = calculate_hmac_sha512(unknown_params, self.secret)

        rsp_code, msg, _ = evaluate_vnpay_ipn(unknown_params, db_record=None, hash_secret=self.secret)
        self.assertEqual(rsp_code, "01")
        self.assertEqual(msg, "Order not found")

    def test_t2_vnpay_05_vietnamese_diacritics_encoding_integrity(self):
        """Test 5: Verify URL encoding and HMAC hash fidelity with Vietnamese accents and spaces."""
        vietnamese_order_info = "Thanh toán cọc bàn Nhà hàng Mộc - Bàn 12 VIP"
        url, params = build_vnpay_payment_url(
            txn_ref="TT_VN_001",
            amount_vnd=500000,
            order_info=vietnamese_order_info,
            hash_secret=self.secret,
        )
        self.assertIn("vnp_SecureHash", params)
        # Recalculate hash independently to confirm deterministic quote_plus handling
        hash_recalculated = calculate_hmac_sha512(params, self.secret)
        self.assertEqual(params["vnp_SecureHash"], hash_recalculated)


if __name__ == "__main__":
    unittest.main()
