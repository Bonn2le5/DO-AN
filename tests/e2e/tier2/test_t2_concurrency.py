"""
Tier 2: Concurrency Race Condition & Corner Cases Tests (T2_concurrency)
Verifies:
1. High-concurrency race condition: 10 threads attempting to hold the same table simultaneously.
   Exactly 1 thread succeeds (HTTP 200), remaining 9 receive HTTP 409 Conflict.
2. Expired hold token cannot be confirmed in Phase 2 (HTTP 400 HOLD_EXPIRED).
3. Token hijacking prevention: wrong token rejected with HTTP 403 INVALID_TOKEN.
4. Double confirmation idempotency/prevention: duplicate confirmation returns HTTP 409.
5. Automatic re-availability after TTL expiration.
"""

import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from tests.e2e.helpers.redis_lock_sim import RedisTableLockSimulator


class TestTier2Concurrency(unittest.TestCase):
    """Tier 2: Concurrency Race Conditions & Corner Cases"""

    def setUp(self):
        self.sim = RedisTableLockSimulator()
        self.ban_id = 10
        self.ngay = "2026-10-22"
        self.gio = "19:00:00"

    def test_t2_concurrency_01_multi_threaded_race_condition(self):
        """Test 1: 10 concurrent threads attempt to hold the same table simultaneously.
        Atomic SET NX ensures exactly 1 gets HTTP 200, and 9 get HTTP 409 Conflict."""
        num_threads = 10
        results = []

        def attempt_hold(user_id):
            return self.sim.hold_table(
                ban_id=self.ban_id,
                ngay=self.ngay,
                gio=self.gio,
                user_id=user_id,
                ttl_seconds=600,
            )

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(attempt_hold, user_id=100 + i) for i in range(num_threads)]
            for f in futures:
                results.append(f.result())

        status_codes = [status for status, _ in results]
        success_count = status_codes.count(200)
        conflict_count = status_codes.count(409)

        self.assertEqual(success_count, 1, f"Expected exactly 1 success, got {success_count}")
        self.assertEqual(conflict_count, num_threads - 1, f"Expected {num_threads - 1} conflicts, got {conflict_count}")

    def test_t2_concurrency_02_expired_hold_token_fails_confirmation(self):
        """Test 2: A hold token that expired (TTL passed) is rejected during Phase 2 confirmation."""
        # Hold with 0-second TTL (immediately expires)
        status, data = self.sim.hold_table(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=201,
            ttl_seconds=0,
        )
        self.assertEqual(status, 200)
        token = data["id_giu_ban"]

        # Confirm should fail because TTL expired
        confirm_status, confirm_data = self.sim.confirm_booking(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=201,
            hold_token=token,
        )
        self.assertEqual(confirm_status, 400)
        self.assertEqual(confirm_data["error_code"], "HOLD_EXPIRED")

    def test_t2_concurrency_03_token_hijacking_rejected(self):
        """Test 3: Confirming with a forged or mismatched hold token returns HTTP 403."""
        status, _ = self.sim.hold_table(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=201,
            ttl_seconds=600,
        )
        self.assertEqual(status, 200)

        # Attacker tries to confirm using fake token
        confirm_status, confirm_data = self.sim.confirm_booking(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=999,
            hold_token="HOLD_FORGED_TOKEN_XYZ",
        )
        self.assertEqual(confirm_status, 403)
        self.assertEqual(confirm_data["error_code"], "INVALID_TOKEN")

    def test_t2_concurrency_04_double_confirmation_prevented(self):
        """Test 4: Re-confirming an already confirmed table returns HTTP 409 Conflict."""
        status, data = self.sim.hold_table(
            ban_id=self.ban_id,
            ngay=self.ngay,
            gio=self.gio,
            user_id=201,
            ttl_seconds=600,
        )
        token = data["id_giu_ban"]

        # 1st confirm -> 201 Created
        c_status1, _ = self.sim.confirm_booking(
            self.ban_id, self.ngay, self.gio, user_id=201, hold_token=token
        )
        self.assertEqual(c_status1, 201)

        # 2nd confirm with same token -> 409 Conflict (Table already confirmed in DB)
        c_status2, c_data2 = self.sim.confirm_booking(
            self.ban_id, self.ngay, self.gio, user_id=201, hold_token=token
        )
        self.assertEqual(c_status2, 409)
        self.assertEqual(c_data2["error_code"], "TABLE_ALREADY_CONFIRMED")

    def test_t2_concurrency_05_re_hold_after_ttl_expiry(self):
        """Test 5: After a hold expires, a subsequent customer can immediately acquire the table."""
        # Hold with 0s TTL
        self.sim.hold_table(self.ban_id, self.ngay, self.gio, user_id=201, ttl_seconds=0)

        # Customer 2 attempts to hold
        status2, data2 = self.sim.hold_table(
            self.ban_id, self.ngay, self.gio, user_id=202, ttl_seconds=600
        )
        self.assertEqual(status2, 200)
        self.assertEqual(data2["status"], "success")


if __name__ == "__main__":
    unittest.main()
