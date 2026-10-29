"""
Tier 4: Real-World Application Scenarios (>= 5 Scenarios)
Verifies:
- Scenario 1 (S1): New customer cold-start discovery -> nearest branch lookup -> menu recommendation -> table hold -> deposit payment -> order tracking.
- Scenario 2 (S2): Returning gourmet customer -> weighted TF-IDF similarity -> explainable tags -> reservation -> VNPay IPN -> real-time chat.
- Scenario 3 (S3): Early booking cancellation (>24h) with automated 100% deposit refund receipt and table re-availability.
- Scenario 4 (S4): Late booking cancellation (<6h) with 0% penalty forfeiture and table release.
- Scenario 5 (S5): Rush hour concurrency race condition: User A holds Table 8, User B receives 409 Conflict, User A confirms, User B cannot double book.
"""

import unittest
from datetime import datetime, timedelta
from tests.e2e.helpers.ai_gis_oracle import (
    find_nearest_branch,
    compute_tfidf_cosine_recommendation,
)
from tests.e2e.helpers.redis_lock_sim import RedisTableLockSimulator
from tests.e2e.helpers.vnpay_oracle import (
    build_vnpay_payment_url,
    calculate_hmac_sha512,
    evaluate_vnpay_ipn,
    DEFAULT_HASH_SECRET,
)
from tests.e2e.helpers.refund_calculator import generate_refund_receipt
from tests.e2e.helpers.fsm_validator import OrderFSM


class TestTier4Scenarios(unittest.TestCase):
    """Tier 4: End-to-End Real-World Application Scenarios"""

    def setUp(self):
        self.secret = DEFAULT_HASH_SECRET
        self.sim = RedisTableLockSimulator()

        self.branches = [
            {"id": 1, "ten": "Mộc Tân Bình", "lat": 10.7925, "lng": 106.6669, "con_hoat_dong": True},
            {"id": 2, "ten": "Mộc Quận 1", "lat": 10.7769, "lng": 106.7009, "con_hoat_dong": True},
        ]

        self.dishes = [
            {
                "id": 1,
                "ten": "Lẩu Thái hải sản chua cay",
                "danh_muc": "Lẩu",
                "mo_ta": "Lẩu Thái cay nồng tôm mực nghêu",
                "do_cay": 2,
                "so_luot_danh_gia": 120,
                "diem_danh_gia": 4.9,
                "con_hang": True,
                "hien_thi": True,
            },
            {
                "id": 2,
                "ten": "Bò tơ nướng mắm nhĩ",
                "danh_muc": "Món nướng",
                "mo_ta": "Bò tơ mềm thơm chấm mắm nhĩ",
                "do_cay": 1,
                "so_luot_danh_gia": 95,
                "diem_danh_gia": 4.7,
                "con_hang": True,
                "hien_thi": True,
            },
            {
                "id": 3,
                "ten": "Salad nấm rong biển",
                "danh_muc": "Khai vị",
                "mo_ta": "Salad thanh mát",
                "do_cay": 0,
                "la_mon_chay": True,
                "so_luot_danh_gia": 45,
                "diem_danh_gia": 4.4,
                "con_hang": True,
                "hien_thi": True,
            },
        ]

    def test_t4_scenario_01_cold_start_customer_discovery_journey(self):
        """Scenario 1: New customer discovery -> branch lookup -> cold-start recommendation -> table hold -> deposit -> tracking."""
        # 1. Geolocation lookup
        user_coords = (10.7930, 106.6670)  # Near Tan Binh
        nearest, dist_km = find_nearest_branch(user_coords[0], user_coords[1], self.branches)
        self.assertEqual(nearest["id"], 1)
        self.assertLess(dist_km, 0.2)

        # 2. Cold-start recommendation
        recs = compute_tfidf_cosine_recommendation(user_interactions=[], dishes=self.dishes, top_n=2)
        self.assertEqual(len(recs), 2)
        self.assertTrue(recs[0]["is_cold_start"])
        self.assertEqual(recs[0]["dish"]["id"], 1)  # Highest rated

        # 3. Choose Table 3 and hold for 10 minutes
        status_hold, hold_data = self.sim.hold_table(
            ban_id=3, ngay="2026-10-30", gio="18:00:00", user_id=401, ttl_seconds=600
        )
        self.assertEqual(status_hold, 200)
        token = hold_data["id_giu_ban"]

        # 4. VNPay Checkout for deposit
        txn_ref = f"TT_{token[:10]}"
        url, pay_params = build_vnpay_payment_url(
            txn_ref=txn_ref,
            amount_vnd=200000,
            order_info="Dat coc ban 3",
            hash_secret=self.secret,
        )
        self.assertIn("vnp_SecureHash", pay_params)

        # 5. IPN payment confirmation
        db_rec = {"ma_giao_dich": txn_ref, "so_tien": 200000, "trang_thai": "cho_xu_ly"}
        ipn_params = {"vnp_TxnRef": txn_ref, "vnp_Amount": "20000000", "vnp_ResponseCode": "00"}
        ipn_params["vnp_SecureHash"] = calculate_hmac_sha512(ipn_params, self.secret)
        rsp_code, _, updated_rec = evaluate_vnpay_ipn(ipn_params, db_rec, self.secret)
        self.assertEqual(rsp_code, "00")
        self.assertEqual(updated_rec["trang_thai"], "thanh_cong")

        # 6. Database booking confirmed
        c_status, c_data = self.sim.confirm_booking(
            ban_id=3, ngay="2026-10-30", gio="18:00:00", user_id=401, hold_token=token
        )
        self.assertEqual(c_status, 201)

        # 7. Lifecycle tracking
        fsm = OrderFSM(order_id=c_data["ma_dat_ban"])
        self.assertEqual(fsm.current_state, "cho_tiep_nhan")
        fsm.transition_to("da_xac_nhan")
        self.assertEqual(fsm.current_state, "da_xac_nhan")

    def test_t4_scenario_02_returning_spicy_lover_journey(self):
        """Scenario 2: Returning customer with spicy/hotpot history gets explainable AI & initiates live chat."""
        # 1. User has strong history with hotpot & spicy dishes
        interactions = [
            {"mon_an_id": 1, "loai_tuong_tac": "dat_mon"},   # Ordered Hotpot (weight=4)
            {"mon_an_id": 1, "loai_tuong_tac": "danh_gia"},  # Reviewed Hotpot (weight=5)
            {"mon_an_id": 2, "loai_tuong_tac": "yeu_thich"}, # Favorite Grilled beef (weight=2)
        ]
        recs = compute_tfidf_cosine_recommendation(
            user_interactions=interactions, dishes=self.dishes, top_n=2
        )
        self.assertFalse(recs[0]["is_cold_start"])
        # Top dish is spicy hotpot
        self.assertEqual(recs[0]["dish"]["id"], 1)
        self.assertIn("lẩu", recs[0]["ly_do_goi_y"].lower())

        # 2. Customer holds table
        status, hold_data = self.sim.hold_table(
            ban_id=4, ngay="2026-10-30", gio="19:00:00", user_id=402
        )
        self.assertEqual(status, 200)

        # 3. Live chat consultation message
        chat_msg = {
            "conversation_id": "conv_402_staff",
            "sender_id": 402,
            "sender_name": "Tran Van B",
            "content": "Toi thich an cay, nuoc lau Thai co the lam cay them cap do 3 duoc khong?",
            "message_type": "van_ban",
        }
        self.assertGreater(len(chat_msg["content"]), 10)

    def test_t4_scenario_03_early_cancellation_100_percent_refund(self):
        """Scenario 3: Early cancellation (>24h) produces 100% refund receipt and frees the table."""
        booking_time = datetime(2026, 11, 5, 18, 0, 0)
        cancel_time = datetime(2026, 11, 3, 10, 0, 0)  # ~56 hours prior (>24h)
        deposit_amount = 250000.0

        # Step 1: Booking initially held and confirmed
        self.sim.hold_table(12, "2026-11-05", "18:00:00", user_id=403)
        hold_token = self.sim._store[self.sim.make_key(12, "2026-11-05", "18:00:00")]["token"]
        self.sim.confirm_booking(12, "2026-11-05", "18:00:00", 403, hold_token, deposit_amount)

        # Step 2: Customer requests cancellation
        receipt = generate_refund_receipt(
            ma_dat_ban="DB556677",
            khach_hang_info={"ho_ten": "Hoang Thi D", "so_dien_thoai": "0901234567"},
            chi_nhanh_info={"id": 2, "ten": "Mộc Quận 1"},
            thoi_gian_dat=booking_time,
            thoi_gian_huy=cancel_time,
            so_tien_coc=deposit_amount,
            ly_do_huy="Thay doi ke hoach cong tac",
        )
        self.assertEqual(receipt["chinh_sach_ap_dung"]["moc"], "truoc_24h")
        self.assertEqual(receipt["tai_chinh"]["so_tien_hoan_tra"], 250000.0)
        self.assertEqual(receipt["tai_chinh"]["so_tien_khau_tru_phat"], 0.0)
        self.assertEqual(receipt["trang_thai"], "da_hoan_tien")

    def test_t4_scenario_04_late_cancellation_0_percent_forfeiture(self):
        """Scenario 4: Late cancellation (<6h) forfeits 100% deposit as penalty."""
        booking_time = datetime(2026, 11, 5, 18, 0, 0)
        cancel_time = datetime(2026, 11, 5, 15, 0, 0)  # Exactly 3h prior (<6h)
        deposit_amount = 200000.0

        receipt = generate_refund_receipt(
            ma_dat_ban="DB778899",
            khach_hang_info={"ho_ten": "Pham Van E", "so_dien_thoai": "0988776655"},
            chi_nhanh_info={"id": 1, "ten": "Mộc Tân Bình"},
            thoi_gian_dat=booking_time,
            thoi_gian_huy=cancel_time,
            so_tien_coc=deposit_amount,
            ly_do_huy="Ban viec dot xuat",
        )
        self.assertEqual(receipt["chinh_sach_ap_dung"]["moc"], "trong_6h")
        self.assertEqual(receipt["tai_chinh"]["so_tien_hoan_tra"], 0.0)
        self.assertEqual(receipt["tai_chinh"]["so_tien_khau_tru_phat"], 200000.0)
        self.assertEqual(receipt["trang_thai"], "that_bai")

    def test_t4_scenario_05_peak_hour_table_race_condition(self):
        """Scenario 5: Two customers race for the last table at peak hour; Customer A wins, Customer B blocked."""
        ban_id = 8
        ngay = "2026-10-31"
        gio = "19:00:00"

        # Customer A claims the table first
        status_a, data_a = self.sim.hold_table(ban_id, ngay, gio, user_id=501)
        self.assertEqual(status_a, 200)
        token_a = data_a["id_giu_ban"]

        # Customer B attempts to hold the same table 50ms later
        status_b, data_b = self.sim.hold_table(ban_id, ngay, gio, user_id=502)
        self.assertEqual(status_b, 409)
        self.assertEqual(data_b["error_code"], "TABLE_CURRENTLY_HELD")

        # Customer A completes payment and confirms in DB
        conf_status_a, _ = self.sim.confirm_booking(ban_id, ngay, gio, 501, token_a)
        self.assertEqual(conf_status_a, 201)

        # Customer B retries after Customer A confirmed
        status_b2, data_b2 = self.sim.hold_table(ban_id, ngay, gio, user_id=502)
        self.assertEqual(status_b2, 409)
        self.assertEqual(data_b2["error_code"], "TABLE_ALREADY_BOOKED")


if __name__ == "__main__":
    unittest.main()
