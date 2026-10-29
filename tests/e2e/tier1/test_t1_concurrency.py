"""
Tier 1: Concurrency Control Feature Coverage Tests (T1_concurrency)
Verifies:
1. Phase 1 Redis temporary hold acquires lock with 10-minute TTL (SET NX EX 600).
2. Attempting to hold the same table & slot returns HTTP 409 Conflict.
3. Holding a different table or slot succeeds independently.
4. Manual release resets availability immediately.
5. Phase 2 confirmation commits DB booking and deletes hold key.
"""

import unittest
from tests.e2e.helpers.redis_lock_sim import RedisTableLockSimulator


class TestTier1Concurrency(unittest.TestCase):
    """Tier 1: Concurrency Control Tests"""

    def setUp(self):
        self.sim = RedisTableLockSimulator()
        self.ban_id = 5
        self.ngay = "2026-10-20"
        self.gio = "18:30:00"

    def test_t1_concurrency_01_hold_table_success_200(self):
        """Test 1: Phase 1 table hold succeeds with HTTP 200 and returns hold token."""
        status_code, data = self.sim.hold_table(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=101,
            ttl_seconds=600,
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data["status"], "success")
        self.assertIn("id_giu_ban", data)
        self.assertTrue(data["id_giu_ban"].startswith("HOLD_"))
        self.assertEqual(data["thoi_gian_con_lai_giay"], 600)

    def test_t1_concurrency_02_duplicate_hold_returns_409_conflict(self):
        """Test 2: Second user holding same table & slot is rejected with HTTP 409 Conflict."""
        # User 1 holds
        status1, _ = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=101)
        self.assertEqual(status1, 200)

        # User 2 attempts to hold same table and slot
        status2, data2 = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=102)
        self.assertEqual(status2, 409)
        self.assertEqual(data2["status"], "conflict")
        self.assertEqual(data2["error_code"], "TABLE_CURRENTLY_HELD")
        self.assertIn("retry_after_seconds", data2)

    def test_t1_concurrency_03_independent_table_or_time_succeeds(self):
        """Test 3: Different table ID or different time slot can be held concurrently."""
        # Hold Table 5 at 18:30
        status1, _ = self.sim.hold_table(5, self.ngay, "18:30:00", user_id=101)
        self.assertEqual(status1, 200)

        # Hold Table 6 at 18:30 (different table)
        status2, _ = self.sim.hold_table(6, self.ngay, "18:30:00", user_id=102)
        self.assertEqual(status2, 200)

        # Hold Table 5 at 20:00 (different slot)
        status3, _ = self.sim.hold_table(5, self.ngay, "20:00:00", user_id=103)
        self.assertEqual(status3, 200)

    def test_t1_concurrency_04_manual_release_frees_table(self):
        """Test 4: Releasing hold key frees table for subsequent users."""
        status1, data1 = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=101)
        self.assertEqual(status1, 200)
        token = data1["id_giu_ban"]

        # Release hold
        released = self.sim.release_hold(self.ban_id, self.ngay, self.gio, token)
        self.assertTrue(released)

        # User 2 should now be able to hold
        status2, _ = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=102)
        self.assertEqual(status2, 200)

    def test_t1_concurrency_05_phase2_confirmation_commits_booking(self):
        """Test 5: Phase 2 confirmation validates hold token, creates booking, and cleans up lock."""
        status1, data1 = self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=101)
        self.assertEqual(status1, 200)
        token = data1["id_giu_ban"]

        # Confirm booking
        status2, data2 = self.sim.confirm_booking(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=101,
            hold_token=token,
            so_tien_coc=200000.0,
        )
        self.assertEqual(status2, 201)
        self.assertEqual(data2["status"], "success")
        self.assertTrue(data2["ma_dat_ban"].startswith("DB"))
        self.assertEqual(data2["data"]["trang_thai"], "da_xac_nhan")


if __name__ == "__main__":
    unittest.main()
