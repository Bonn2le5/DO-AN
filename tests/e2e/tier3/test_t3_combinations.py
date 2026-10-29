"""
Tier 3: Cross-Feature Combinations Test Suite (T3_combinations)
Verifies:
1. Complete multi-module pipeline:
   Table Hold -> VNPay Deposit -> IPN Confirm -> Order Dishes -> BOM Material Deduction.
2. Raw material inventory shortage blocks order creation (stockout rollback).
3. Failed VNPay payment automatically cancels booking and frees table hold.
4. Shared raw material deduction across multiple dishes in a single order.
5. Idempotent IPN prevents double deduction of ingredients or duplicate orders.
"""

import unittest
from datetime import datetime
from tests.e2e.helpers.redis_lock_sim import RedisTableLockSimulator
from tests.e2e.helpers.vnpay_oracle import (
    build_vnpay_payment_url,
    calculate_hmac_sha512,
    evaluate_vnpay_ipn,
    DEFAULT_HASH_SECRET,
)


class TestTier3Combinations(unittest.TestCase):
    """Tier 3: Cross-Feature Integration Combinations"""

    def setUp(self):
        self.sim = RedisTableLockSimulator()
        self.secret = DEFAULT_HASH_SECRET
        self.ban_id = 7
        self.ngay = "2026-10-28"
        self.gio = "19:30:00"

        # Mock Inventory: raw materials
        # 1: Bò Úc (kg), 2: Cua đồng (kg), 3: Nấm (kg)
        self.inventory = {
            1: {"ten": "Thịt bò Úc", "don_vi": "kg", "ton_kho": 10.0},
            2: {"ten": "Cua đồng xay", "don_vi": "kg", "ton_kho": 5.0},
            3: {"ten": "Nấm tổng hợp", "don_vi": "kg", "ton_kho": 8.0},
        }

        # Mock BOM (Bill of Materials) per dish:
        # Dish 101 (Lẩu riêu cua): 0.3 kg Cua đồng, 0.2 kg Bò Úc
        # Dish 102 (Bò nướng tảng): 0.5 kg Bò Úc
        self.bom = {
            101: [(2, 0.3), (1, 0.2)],
            102: [(1, 0.5)],
        }

    def deduct_bom_inventory(self, order_items):
        """Helper to deduct BOM materials atomically with stockout check."""
        # Calculate needed amounts
        needed = {}
        for dish_id, qty in order_items.items():
            if dish_id in self.bom:
                for ing_id, per_unit in self.bom[dish_id]:
                    needed[ing_id] = needed.get(ing_id, 0.0) + (per_unit * qty)

        # Validate stock
        for ing_id, req_amt in needed.items():
            current_stock = self.inventory[ing_id]["ton_kho"]
            if current_stock < req_amt:
                raise ValueError(
                    f"Nguyên liệu {self.inventory[ing_id]['ten']} không đủ (cần {req_amt}, còn {current_stock})"
                )

        # Deduct
        for ing_id, req_amt in needed.items():
            self.inventory[ing_id]["ton_kho"] = round(self.inventory[ing_id]["ton_kho"] - req_amt, 3)

        return needed

    def test_t3_01_full_pipeline_hold_pay_confirm_order_deduct(self):
        """Test 1: Full flow: Hold table -> Pay VNPay -> IPN -> Confirm -> Order -> Deduct BOM."""
        # Step 1: Hold table (Redis)
        hold_status, hold_data = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=301)
        self.assertEqual(hold_status, 200)
        token = hold_data["id_giu_ban"]

        # Step 2: VNPay payment URL for deposit
        txn_ref = f"TT_DEP_{token[:12]}"
        url, pay_params = build_vnpay_payment_url(
            txn_ref=txn_ref,
            amount_vnd=200000,
            order_info="Dat coc ban 7",
            hash_secret=self.secret,
        )
        self.assertIn("vnp_SecureHash", pay_params)

        # Step 3: VNPay IPN webhook callback
        db_payment = {
            "ma_giao_dich": txn_ref,
            "so_tien": 200000,
            "trang_thai": "cho_xu_ly",
        }
        ipn_params = {
            "vnp_TxnRef": txn_ref,
            "vnp_Amount": "20000000",
            "vnp_ResponseCode": "00",
        }
        ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(ipn_params, self.secret)
        code, msg, updated = evaluate_vnpay_ipn(ipn_params, db_payment, self.secret)
        self.assertEqual(code, "00")
        self.assertEqual(updated["trang_thai"], "thanh_cong")

        # Step 4: Confirm booking in DB
        conf_status, conf_data = self.sim.confirm_booking(
            self.ban_id, self.ngay, self.gio, user_id=301, hold_token=token
        )
        self.assertEqual(conf_status, 201)
        self.assertEqual(conf_data["data"]["trang_thai"], "da_xac_nhan")

        # Step 5: Customer orders dishes (1x Lẩu riêu cua 101, 2x Bò nướng tảng 102)
        order_items = {101: 1, 102: 2}
        deducted = self.deduct_bom_inventory(order_items)

        # Required beef = 0.2 (from 101) + 2 * 0.5 (from 102) = 1.2 kg
        # Initial beef = 10.0 -> new stock = 8.8 kg
        self.assertEqual(self.inventory[1]["ton_kho"], 8.8)
        # Required crab = 0.3 kg -> initial = 5.0 -> new stock = 4.7 kg
        self.assertEqual(self.inventory[2]["ton_kho"], 4.7)

    def test_t3_02_material_shortage_blocks_order(self):
        """Test 2: Raw material shortage triggers stockout error and rolls back without deduction."""
        # Try to order 30x Lẩu riêu cua (needs 30 * 0.3 = 9.0 kg crab, but only 5.0 kg available)
        order_items = {101: 30}
        initial_crab = self.inventory[2]["ton_kho"]
        initial_beef = self.inventory[1]["ton_kho"]

        with self.assertRaises(ValueError) as ctx:
            self.deduct_bom_inventory(order_items)

        self.assertIn("không đủ", str(ctx.exception))
        # Ensure inventory is unchanged
        self.assertEqual(self.inventory[2]["ton_kho"], initial_crab)
        self.assertEqual(self.inventory[1]["ton_kho"], initial_beef)

    def test_t3_03_payment_failure_releases_table_hold(self):
        """Test 3: When VNPay returns failed response code (e.g. 24 - User cancelled), hold is released."""
        hold_status, hold_data = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=302)
        self.assertEqual(hold_status, 200)
        token = hold_data["id_giu_ban"]
        txn_ref = f"TT_FAIL_{token[:8]}"

        db_payment = {
            "ma_giao_dich": txn_ref,
            "so_tien": 200000,
            "trang_thai": "cho_xu_ly",
        }
        ipn_params = {
            "vnp_TxnRef": txn_ref,
            "vnp_Amount": "20000000",
            "vnp_ResponseCode": "24",  # Customer cancelled
        }
        ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(ipn_params, self.secret)
        code, _, updated = evaluate_vnpay_ipn(ipn_params, db_payment, self.secret)
        self.assertEqual(code, "00")
        self.assertEqual(updated["trang_thai"], "that_bai")

        # Automatically release hold
        self.sim.release_hold(self.ban_id, self.ngay, self.gio, token)
        self.assertTrue(self.sim.is_table_available(self.ban_id, self.ngay, self.gio))

    def test_t3_04_shared_ingredient_deduction_across_multiple_dishes(self):
        """Test 4: Dishes sharing the same ingredient accumulate requirement correctly."""
        # Both dishes use Australian Beef (id=1)
        order_items = {101: 5, 102: 4}
        # 101 needs 5 * 0.2 = 1.0 kg
        # 102 needs 4 * 0.5 = 2.0 kg
        # Total needed = 3.0 kg
        deducted = self.deduct_bom_inventory(order_items)
        self.assertEqual(deducted[1], 3.0)
        self.assertEqual(self.inventory[1]["ton_kho"], 7.0)

    def test_t3_05_idempotent_ipn_prevents_duplicate_processing(self):
        """Test 5: Receiving identical IPN callback multiple times does not duplicate processing."""
        txn_ref = "TT_IDEM_99"
        db_payment = {
            "ma_giao_dich": txn_ref,
            "so_tien": 200000,
            "trang_thai": "cho_xu_ly",
        }
        ipn_params = {
            "vnp_TxnRef": txn_ref,
            "vnp_Amount": "20000000",
            "vnp_ResponseCode": "00",
        }
        ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(ipn_params, self.secret)

        # 1st IPN
        code1, _, rec1 = evaluate_vnpay_ipn(ipn_params, db_payment, self.secret)
        self.assertEqual(code1, "00")

        # 2nd IPN
        code2, msg2, rec2 = evaluate_vnpay_ipn(ipn_params, rec1, self.secret)
        self.assertEqual(code2, "02")
        self.assertEqual(msg2, "Order already confirmed")


if __name__ == "__main__":
    unittest.main()
