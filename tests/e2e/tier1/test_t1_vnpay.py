"""
Tier 1: VNPay Sandbox Feature Coverage Tests (T1_vnpay)
Verifies:
1. VNPay Sandbox URL generation with 2.1.0 mandatory parameters.
2. Checksum HMAC-SHA512 verification (128-hex digest).
3. Parameter sorting adherence (ASCII alphabetical order).
4. Server-to-server IPN webhook simulation returning RspCode 00.
5. Return URL callback parsing and signature validation.
"""

import unittest
from tests.e2e.helpers.vnpay_oracle import (
    build_vnpay_payment_url,
    calculate_hmac_sha512,
    verify_vnpay_signature,
    evaluate_vnpay_ipn,
    DEFAULT_HASH_SECRET,
    DEFAULT_TMN_CODE,
)


class TestTier1VNPay(unittest.TestCase):
    """Tier 1: VNPay Feature Coverage Tests"""

    def setUp(self):
        self.txn_ref = "TT1001_1728876400"
        self.amount = 200000  # 200,000 VND
        self.order_info = "Dat coc ban DB1001"
        self.secret = DEFAULT_HASH_SECRET

    def test_t1_vnpay_01_url_generation_contains_mandatory_params(self):
        """Test 1: Verify VNPay URL includes all mandatory v2.1.0 query parameters."""
        url, params = build_vnpay_payment_url(
            txn_ref=self.txn_ref,
            amount_vnd=self.amount,
            order_info=self.order_info,
            tmn_code=DEFAULT_TMN_CODE,
            hash_secret=self.secret,
        )

        mandatory_keys = [
            "vnp_Version", "vnp_Command", "vnp_TmnCode", "vnp_Amount",
            "vnp_CreateDate", "vnp_CurrCode", "vnp_IpAddr", "vnp_Locale",
            "vnp_OrderInfo", "vnp_OrderType", "vnp_ReturnUrl", "vnp_TxnRef",
            "vnp_SecureHash"
        ]
        for key in mandatory_keys:
            self.assertIn(key, params, f"Missing mandatory parameter {key}")
            self.assertIn(f"{key}=", url, f"URL missing query param {key}")

        self.assertEqual(params["vnp_Version"], "2.1.0")
        self.assertEqual(params["vnp_Command"], "pay")
        self.assertEqual(params["vnp_Amount"], "20000000")  # x 100

    def test_t1_vnpay_02_checksum_hmac_sha512_format(self):
        """Test 2: Verify checksum algorithm generates standard 128-char hex string."""
        sample_params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": "TESTCODE",
            "vnp_Amount": "10000000",
            "vnp_TxnRef": "TXN_999",
        }
        checksum = calculate_hmac_sha512(sample_params, self.secret)

        self.assertEqual(len(checksum), 128, "HMAC-SHA512 checksum must be 128 hex chars")
        self.assertTrue(all(c in "0123456789abcdefABCDEF" for c in checksum))
        # Self-verification
        self.assertTrue(verify_vnpay_signature(sample_params, checksum, self.secret))

    def test_t1_vnpay_03_parameter_sorting_ascii_order(self):
        """Test 3: Verify parameters are strictly sorted by ASCII key order before hashing."""
        params_unordered = {
            "z_param": "last",
            "a_param": "first",
            "m_param": "middle",
        }
        hash1 = calculate_hmac_sha512(params_unordered, self.secret)

        # Reverse input dictionary order
        params_reversed = {
            "a_param": "first",
            "m_param": "middle",
            "z_param": "last",
        }
        hash2 = calculate_hmac_sha512(params_reversed, self.secret)

        self.assertEqual(hash1, hash2, "Checksum must be independent of dict insertion order")

    def test_t1_vnpay_04_ipn_callback_success_simulation(self):
        """Test 4: Simulate successful VNPay IPN callback returning RspCode '00'."""
        db_record = {
            "ma_giao_dich": self.txn_ref,
            "so_tien": self.amount,
            "trang_thai": "cho_xu_ly",
        }

        # VNPay IPN params
        ipn_params = {
            "vnp_TxnRef": self.txn_ref,
            "vnp_Amount": str(int(self.amount * 100)),
            "vnp_ResponseCode": "00",
            "vnp_TransactionNo": "14298102",
            "vnp_BankCode": "NCB",
            "vnp_PayDate": "20261014103000",
        }
        # Compute valid hash
        ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(ipn_params, self.secret)

        rsp_code, message, updated_record = evaluate_vnpay_ipn(
            query_params=ipn_params,
            db_record=db_record,
            hash_secret=self.secret,
        )

        self.assertEqual(rsp_code, "00", f"Expected RspCode '00', got {rsp_code}")
        self.assertEqual(message, "Confirm Success")
        self.assertEqual(updated_record.get("trang_thai"), "thanh_cong")

    def test_t1_vnpay_05_return_url_signature_validation(self):
        """Test 5: Verify customer return redirect signature parsing and acceptance."""
        return_params = {
            "vnp_Amount": "20000000",
            "vnp_BankCode": "NCB",
            "vnp_CardType": "ATM",
            "vnp_OrderInfo": "Thanh toan tien coc",
            "vnp_PayDate": "20261014103000",
            "vnp_ResponseCode": "00",
            "vnp_TmnCode": DEFAULT_TMN_CODE,
            "vnp_TransactionNo": "14298102",
            "vnp_TransactionStatus": "00",
            "vnp_TxnRef": self.txn_ref,
        }
        sig = calculate_hmac_sha512(return_params, self.secret)
        is_valid = verify_vnpay_signature(return_params, sig, self.secret)
        self.assertTrue(is_valid, "Return URL signature must validate successfully")


if __name__ == "__main__":
    unittest.main()
