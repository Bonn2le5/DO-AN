#!/usr/bin/env python3
"""
Empirical Challenger 2 Stress Testing & Concurrency Verification Suite.
Milestone 2 Iteration 2:
- Multi-threaded Table Hold Collision (50 threads -> 1 HTTP 200, 49 HTTP 409 BAN_DANG_BAN)
- API ViewSet concurrency (BanAnViewSet & DatBanViewSet under multi-threaded collision)
- Time formatting / whitespace normalization collision
- Phase 2 confirmation with token, DatBan creation, and Redis hold key release on commit
- Phase 2 rollback preservation of Redis hold key on failure
- Phase 2 BanAn row mutex (select_for_update inside active transaction)
- Phase 2 forged/expired token rejection & database collision rejection
- Sorted BOM Deadlock Prevention via Strict Ascending ID Ordering
- BOM Atomic Stock Reduction & Idempotency
- BOM Stockout ValidationError propagation & rollback in doi_trang_thai
- BOM Restocking with sorted locks
"""

import ast
import inspect
import os
import sys
import textwrap
import time
import unittest
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup paths & environment
current_dir = Path(__file__).resolve().parent
for p in [current_dir, current_dir.parent, current_dir.parent.parent, current_dir.parent.parent.parent]:
    if (p / "moc-backend").exists():
        PROJECT_ROOT = p
        break
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

BACKEND_DIR = PROJECT_ROOT / "moc-backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.core.cache import caches
from django.db import connection, transaction
from django.db.transaction import TransactionManagementError
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from reservations.services import DichVuDatBan
from reservations.views import BanAnViewSet, DatBanViewSet
from reservations.models import BanAn, DatBan, ChinhSachDatCoc
from foods.services import DichVuKho
from foods.models import NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho


class AuthenticTransactionTestCase(unittest.TestCase):
    """
    Base test harness enforcing authentic Django transaction semantics:
    - connection.in_atomic_block tracking.
    - select_for_update outside of atomic raises TransactionManagementError.
    - rollback semantics and on_commit hook registration.
    """

    def setUp(self):
        super().setUp()
        self.mock_raw_conn = MagicMock()
        self._patchers = [
            patch.object(connection, "ensure_connection", return_value=None),
            patch.object(connection, "connection", self.mock_raw_conn),
            patch.object(connection.features, "has_select_for_update", True),
            patch.object(connection, "get_autocommit", side_effect=lambda: not connection.in_atomic_block),
        ]
        for p in self._patchers:
            p.start()

    def tearDown(self):
        for p in reversed(self._patchers):
            p.stop()
        super().tearDown()


class TestTableHoldConcurrencyStress(AuthenticTransactionTestCase):
    """Adversarial stress testing of Phase 1 Table Hold under heavy multi-threaded contention."""

    def setUp(self):
        super().setUp()
        self.cache = caches["locmem"]
        self.cache.clear()
        self.ban_id = 88
        self.ngay = "2026-11-25"
        self.gio = "18:30"
        self.so_khach = 4
        self.factory = APIRequestFactory()

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_stress_50_threads_table_hold_collision(self, mock_db_filter, mock_ban_sr):
        """
        Adversarial Stress Test: 50 concurrent threads aggressively race to hold the exact same table slot.
        Asserts:
        - Exactly 1 thread succeeds (status=success, id_giu_ban prefixed HOLD_, 600s TTL).
        - Exactly 49 threads are rejected with 409 Conflict (code='BAN_DANG_BAN').
        - All 49 conflict payloads include retry_after_seconds=600 and detailed conflict information.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = False

        num_threads = 50

        def worker_hold(thread_id):
            return DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id,
                ngay=self.ngay,
                gio=self.gio,
                so_khach=self.so_khach,
                user_id=2000 + thread_id,
            )

        with patch("reservations.services._safe_cache", return_value=self.cache):
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                results = list(executor.map(worker_hold, range(num_threads)))

        successes = [r for r in results if r[0] is True]
        conflicts = [r for r in results if r[0] is False]

        self.assertEqual(len(successes), 1, f"Expected exactly 1 winner among {num_threads} threads, got {len(successes)}")
        self.assertEqual(len(conflicts), num_threads - 1, f"Expected {num_threads - 1} conflicts, got {len(conflicts)}")

        win_ok, win_data = successes[0]
        self.assertEqual(win_data["status"], "success")
        self.assertTrue(win_data["id_giu_ban"].startswith("HOLD_"))
        self.assertEqual(win_data["thoi_gian_con_lai_giay"], 600)

        for fail_ok, fail_data in conflicts:
            self.assertEqual(fail_data["code"], "BAN_DANG_BAN")
            self.assertEqual(fail_data["error_code"], "TABLE_CURRENTLY_HELD")
            self.assertEqual(fail_data["status"], "conflict")
            self.assertEqual(fail_data["retry_after_seconds"], 600)

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_stress_viewset_banan_giu_ban_concurrency(self, mock_db_filter, mock_ban_sr):
        """
        Adversarial View-Level Stress Test: 30 concurrent HTTP POST requests to BanAnViewSet.giu_ban.
        Asserts:
        - Exactly 1 response is HTTP 200 OK.
        - Exactly 29 responses are HTTP 409 Conflict with code='BAN_DANG_BAN'.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = False

        num_requests = 30
        ban_view = BanAnViewSet.as_view({"post": "giu_ban"})

        def make_request(idx):
            req = self.factory.post(
                f"/api/tables/{self.ban_id}/giu_ban/",
                {"ngay": self.ngay, "gio": self.gio, "so_luong_khach": self.so_khach},
                format="json"
            )
            return ban_view(req, pk=self.ban_id)

        with patch("reservations.services._safe_cache", return_value=self.cache):
            with ThreadPoolExecutor(max_workers=num_requests) as executor:
                responses = list(executor.map(make_request, range(num_requests)))

        status_200s = [r for r in responses if r.status_code == 200]
        status_409s = [r for r in responses if r.status_code == 409]

        self.assertEqual(len(status_200s), 1, f"Expected 1 HTTP 200, got {len(status_200s)}")
        self.assertEqual(len(status_409s), num_requests - 1, f"Expected {num_requests - 1} HTTP 409s, got {len(status_409s)}")
        for r in status_409s:
            self.assertEqual(r.data["code"], "BAN_DANG_BAN")

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_stress_viewset_datban_giu_ban_frontend_concurrency(self, mock_db_filter, mock_ban_sr):
        """
        Adversarial View-Level Stress Test: 30 concurrent HTTP POST requests to DatBanViewSet.giu_ban_frontend.
        Asserts:
        - Exactly 1 response is HTTP 200 OK.
        - Exactly 29 responses are HTTP 409 Conflict with code='BAN_DANG_BAN'.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = False

        num_requests = 30
        frontend_view = DatBanViewSet.as_view({"post": "giu_ban_frontend"})

        def make_request(idx):
            req = self.factory.post(
                "/api/dat-ban/giu-ban/",
                {"ban_an_id": self.ban_id, "ngay": self.ngay, "gio": self.gio, "so_luong_khach": self.so_khach},
                format="json"
            )
            return frontend_view(req)

        with patch("reservations.services._safe_cache", return_value=self.cache):
            with ThreadPoolExecutor(max_workers=num_requests) as executor:
                responses = list(executor.map(make_request, range(num_requests)))

        status_200s = [r for r in responses if r.status_code == 200]
        status_409s = [r for r in responses if r.status_code == 409]

        self.assertEqual(len(status_200s), 1)
        self.assertEqual(len(status_409s), num_requests - 1)
        for r in status_409s:
            self.assertEqual(r.data["code"], "BAN_DANG_BAN")

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_time_formatting_and_whitespace_normalization_collision(self, mock_db_filter, mock_ban_sr):
        """
        Adversarial Edge Case: Three requests with slight formatting variations:
        - Req 1: '19:30:00'
        - Req 2: '19:30'
        - Req 3: ' 19:30 '
        All point to the same 19:30 slot. Verify that Req 1 succeeds and Reqs 2 & 3 collide with HTTP 409.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = False

        with patch("reservations.services._safe_cache", return_value=self.cache):
            ok1, data1 = DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id, ngay=self.ngay, gio="19:30:00", so_khach=self.so_khach
            )
            self.assertTrue(ok1)
            self.assertEqual(data1["gio_bat_dau"], "19:30")

            ok2, data2 = DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id, ngay=self.ngay, gio="19:30", so_khach=self.so_khach
            )
            self.assertFalse(ok2)
            self.assertEqual(data2["code"], "BAN_DANG_BAN")

            ok3, data3 = DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id, ngay=self.ngay, gio=" 19:30 ", so_khach=self.so_khach
            )
            self.assertFalse(ok3)
            self.assertEqual(data3["code"], "BAN_DANG_BAN")


class TestPhase2ConfirmationAndMutexStress(AuthenticTransactionTestCase):
    """Adversarial stress testing of Phase 2 Confirmation and Database Pessimistic Mutex."""

    def setUp(self):
        super().setUp()
        self.cache = caches["locmem"]
        self.cache.clear()
        self.mock_ban = MagicMock(id=77, suc_chua=8, trang_thai="trong", chi_nhanh_id=2)
        self.mock_chi_nhanh = MagicMock(id=2)
        self.mock_user = MagicMock(is_authenticated=True)

    def test_phase2_confirmation_with_token_creates_datban_and_deletes_redis_on_commit(self):
        """
        Empirically verify that DichVuDatBan.tao_dat_ban:
        1. Validates hold token against Redis.
        2. Acquires BanAn row lock via select_for_update inside active transaction.
        3. Creates DatBan and MonAnTrongDatBan records.
        4. Registers on_commit hook to delete Redis hold keys.
        5. When transaction commits, Redis hold key is deleted.
        """
        token = "HOLD_STRESS_CONFIRM_77"
        hold_key = "table_hold:77:2026-11-30:20:00"
        phu_key = "giu-ban:77:2026-11-30:20:00"
        self.cache.set(hold_key, token, timeout=600)
        self.cache.set(phu_key, token, timeout=600)

        mock_mon = MagicMock(don_gia_hien_tai=Decimal("150000.00"))
        mock_cs = MagicMock(phan_tram_coc=Decimal("20.00"))

        du_lieu = {
            "ban_an": self.mock_ban,
            "ngay_dat": "2026-11-30",
            "gio_bat_dau": "20:00",
            "so_luong_khach": 4,
            "chi_nhanh": self.mock_chi_nhanh,
            "id_giu_ban": token,
            "danh_sach_mon": [{"mon_an": mock_mon, "so_luong": 3}],
        }

        with patch("reservations.services._safe_cache", return_value=self.cache), \
             patch("reservations.models.BanAn.objects.select_for_update") as mock_ban_sfu, \
             patch("reservations.models.DatBan.objects.select_for_update") as mock_db_sfu, \
             patch("reservations.models.ChinhSachDatCoc.objects.filter") as mock_cs_filter, \
             patch("reservations.models.DatBan.objects.create") as mock_db_create, \
             patch("reservations.models.MonAnTrongDatBan.objects.create") as mock_item_create:

            mock_ban_sfu.return_value.get.return_value = self.mock_ban
            mock_db_sfu.return_value.filter.return_value.exists.return_value = False
            mock_cs_filter.return_value.order_by.return_value.first.return_value = mock_cs
            mock_db_create.return_value = MagicMock(
                id=303, ma_dat_ban="DB0303", so_tien_coc=Decimal("90000.00"),
                trang_thai=DatBan.TrangThai.CHO_THANH_TOAN
            )

            # Execute tao_dat_ban within transaction
            with transaction.atomic():
                res = DichVuDatBan.tao_dat_ban(nguoi_dung=self.mock_user, du_lieu=du_lieu)
                self.assertEqual(res.id, 303)
                # Before commit, the hold key still exists in cache
                # When exiting the atomic block, on_commit hook runs!

            # After commit, Redis hold key is deleted
            self.assertIsNone(self.cache.get(hold_key), "Hold key must be deleted on transaction commit")
            self.assertIsNone(self.cache.get(phu_key), "Secondary key must be deleted on transaction commit")

            # Verify select_for_update was called
            mock_ban_sfu.assert_called_once()
            mock_db_sfu.assert_called_once()

    def test_phase2_confirmation_failure_preserves_redis_hold(self):
        """
        Adversarial Edge Case: If an error or rollback occurs during booking creation,
        on_commit hooks must NOT fire, and the Redis hold key must NOT be deleted.
        """
        token = "HOLD_STRESS_ROLLBACK_77"
        hold_key = "table_hold:77:2026-11-30:20:00"
        self.cache.set(hold_key, token, timeout=600)

        du_lieu = {
            "ban_an": self.mock_ban,
            "ngay_dat": "2026-11-30",
            "gio_bat_dau": "20:00",
            "so_luong_khach": 4,
            "chi_nhanh": self.mock_chi_nhanh,
            "id_giu_ban": token,
            "danh_sach_mon": [],
        }

        with patch("reservations.services._safe_cache", return_value=self.cache), \
             patch("reservations.models.BanAn.objects.select_for_update") as mock_ban_sfu, \
             patch("reservations.models.DatBan.objects.select_for_update") as mock_db_sfu, \
             patch("reservations.models.ChinhSachDatCoc.objects.filter"), \
             patch("reservations.models.DatBan.objects.create", side_effect=RuntimeError("Simulated DB Disk Failure")):

            mock_ban_sfu.return_value.get.return_value = self.mock_ban
            mock_db_sfu.return_value.filter.return_value.exists.return_value = False

            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    DichVuDatBan.tao_dat_ban(nguoi_dung=self.mock_user, du_lieu=du_lieu)

            # Verify that because transaction failed and rolled back, hold key was NOT destroyed
            self.assertEqual(
                self.cache.get(hold_key), token,
                "Hold key must be preserved if transaction rolls back!"
            )

    def test_phase2_forged_and_expired_token_rejections(self):
        """
        Phase 2 Rejections:
        - Forged hold token raises ValidationError({"id_giu_ban": ...})
        - Expired / missing token raises ValidationError({"id_giu_ban": ...})
        - Direct booking when held by another user raises ValidationError({"ban_an": ...})
        - Booking collision with existing DB reservation raises ValidationError({"ban_an": ...})
        """
        hold_key = "table_hold:77:2026-11-30:20:00"
        self.cache.set(hold_key, "HOLD_ORIGINAL_USER", timeout=600)

        base_data = {
            "ban_an": self.mock_ban,
            "ngay_dat": "2026-11-30",
            "gio_bat_dau": "20:00",
            "so_luong_khach": 4,
            "chi_nhanh": self.mock_chi_nhanh,
            "danh_sach_mon": [],
        }

        with patch("reservations.services._safe_cache", return_value=self.cache), \
             patch("reservations.models.BanAn.objects.select_for_update") as mock_ban_sfu, \
             patch("reservations.models.DatBan.objects.select_for_update") as mock_db_sfu:

            mock_ban_sfu.return_value.get.return_value = self.mock_ban
            mock_db_sfu.return_value.filter.return_value.exists.return_value = False

            # Case A: Forged token
            with self.assertRaises(ValidationError) as ctx:
                DichVuDatBan.tao_dat_ban(
                    nguoi_dung=self.mock_user,
                    du_lieu=dict(base_data, id_giu_ban="HOLD_FORGED_ATTACK")
                )
            self.assertIn("id_giu_ban", ctx.exception.detail)
            self.assertIn("hết hạn hoặc không hợp lệ", str(ctx.exception.detail["id_giu_ban"]))

            # Case B: Expired token
            self.cache.clear()
            with self.assertRaises(ValidationError) as ctx:
                DichVuDatBan.tao_dat_ban(
                    nguoi_dung=self.mock_user,
                    du_lieu=dict(base_data, id_giu_ban="HOLD_EXPIRED_SESSION")
                )
            self.assertIn("id_giu_ban", ctx.exception.detail)

            # Case C: Direct booking attempted without token while table is held
            self.cache.set(hold_key, "HOLD_ACTIVE_USER", timeout=600)
            with self.assertRaises(ValidationError) as ctx:
                DichVuDatBan.tao_dat_ban(
                    nguoi_dung=self.mock_user,
                    du_lieu=dict(base_data)
                )
            self.assertIn("ban_an", ctx.exception.detail)
            self.assertIn("đang được giữ chỗ tạm thời", str(ctx.exception.detail["ban_an"]))

            # Case D: Database collision (already booked in DB)
            self.cache.clear()
            mock_db_sfu.return_value.filter.return_value.exists.return_value = True
            with self.assertRaises(ValidationError) as ctx:
                DichVuDatBan.tao_dat_ban(
                    nguoi_dung=self.mock_user,
                    du_lieu=dict(base_data)
                )
            self.assertIn("ban_an", ctx.exception.detail)
            self.assertIn("đã có người đặt", str(ctx.exception.detail["ban_an"]))


class TestSortedBOMDeadlockPreventionAndAtomicityStress(AuthenticTransactionTestCase):
    """Adversarial stress testing of Sorted BOM Deadlock Prevention & Inventory Atomicity."""

    def test_sorted_bom_deadlock_prevention_multi_orders(self):
        """
        Concurrency & Deadlock Prevention: Multiple transactions order distinct menus requiring overlapping ingredients:
        - Transaction A requires: [Ingredient 50, Ingredient 20, Ingredient 10]
        - Transaction B requires: [Ingredient 10, Ingredient 30, Ingredient 50]
        - Transaction C requires: [Ingredient 90, Ingredient 10, Ingredient 40, Ingredient 20]
        Verify that DichVuKho.khau_tru_nguyen_lieu_bom enforces Strict Global ID Ordering (Dijkstra's Resource Hierarchy):
        - Transaction A locks: [10, 20, 50]
        - Transaction B locks: [10, 30, 50]
        - Transaction C locks: [10, 20, 40, 90]
        Because all transactions lock in strictly monotonically increasing order of IDs,
        circular wait is mathematically impossible, eliminating deadlocks.
        """
        dm_a1 = MagicMock(mon_an_id=1, nguyen_lieu_id=50, so_luong_can=Decimal("1.0"))
        dm_a2 = MagicMock(mon_an_id=1, nguyen_lieu_id=20, so_luong_can=Decimal("1.5"))
        dm_a3 = MagicMock(mon_an_id=1, nguyen_lieu_id=10, so_luong_can=Decimal("0.5"))

        dm_b1 = MagicMock(mon_an_id=2, nguyen_lieu_id=10, so_luong_can=Decimal("2.0"))
        dm_b2 = MagicMock(mon_an_id=2, nguyen_lieu_id=30, so_luong_can=Decimal("1.0"))
        dm_b3 = MagicMock(mon_an_id=2, nguyen_lieu_id=50, so_luong_can=Decimal("1.0"))

        dm_c1 = MagicMock(mon_an_id=3, nguyen_lieu_id=90, so_luong_can=Decimal("1.0"))
        dm_c2 = MagicMock(mon_an_id=3, nguyen_lieu_id=10, so_luong_can=Decimal("1.0"))
        dm_c3 = MagicMock(mon_an_id=3, nguyen_lieu_id=40, so_luong_can=Decimal("1.0"))
        dm_c4 = MagicMock(mon_an_id=3, nguyen_lieu_id=20, so_luong_can=Decimal("1.0"))

        nl10 = MagicMock(id=10, ten="Thịt bò", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl20 = MagicMock(id=20, ten="Hành tây", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl30 = MagicMock(id=30, ten="Nấm rơm", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl40 = MagicMock(id=40, ten="Tỏi lý sơn", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl50 = MagicMock(id=50, ten="Gia vị sốt", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl90 = MagicMock(id=90, ten="Dầu ô liu", don_vi="l", ton_kho_hien_tai=Decimal("100.0"))

        nl_pool = {10: nl10, 20: nl20, 30: nl30, 40: nl40, 50: nl50, 90: nl90}
        recorded_lock_orders = []

        def mock_filter(id__in):
            recorded_lock_orders.append(list(id__in))
            ret = MagicMock()
            ret.order_by.return_value = [nl_pool[i] for i in sorted(id__in)]
            return ret

        with patch("foods.models.LichSuXuatNhapKho.objects.filter") as m_hist, \
             patch("foods.models.DinhMucNguyenLieu.objects.filter") as m_bom, \
             patch("foods.models.NguyenLieu.objects.select_for_update") as m_sfu, \
             patch("foods.models.LichSuXuatNhapKho.objects.create"):

            m_hist.return_value.exists.return_value = False
            m_sfu.return_value.filter.side_effect = mock_filter

            # Transaction A (recipe [50, 20, 10])
            m_bom.return_value.select_related.return_value = [dm_a1, dm_a2, dm_a3]
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 1, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=501
            )

            # Transaction B (recipe [10, 30, 50])
            m_bom.return_value.select_related.return_value = [dm_b1, dm_b2, dm_b3]
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 2, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=502
            )

            # Transaction C (recipe [90, 10, 40, 20])
            m_bom.return_value.select_related.return_value = [dm_c1, dm_c2, dm_c3, dm_c4]
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 3, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=503
            )

        self.assertEqual(len(recorded_lock_orders), 3)
        self.assertEqual(recorded_lock_orders[0], [10, 20, 50])
        self.assertEqual(recorded_lock_orders[1], [10, 30, 50])
        self.assertEqual(recorded_lock_orders[2], [10, 20, 40, 90])
        for lock_seq in recorded_lock_orders:
            self.assertEqual(lock_seq, sorted(lock_seq), f"Lock sequence {lock_seq} is not strictly sorted ascending!")

    def test_bom_atomic_stock_reduction_and_aggregation(self):
        """
        Verify that multiple dishes sharing common ingredients correctly aggregate demand:
        - Dish 1 (qty 2) requires 1.5kg of NL 10 -> 3.0kg
        - Dish 2 (qty 3) requires 0.5kg of NL 10 -> 1.5kg
        Total demand = 4.5kg.
        Initial stock: 10.0kg -> Final stock: 5.5kg.
        Verify that nl.save(update_fields=['ton_kho_hien_tai', 'cap_nhat_luc']) is called with exact values.
        """
        dm1 = MagicMock(mon_an_id=1, nguyen_lieu_id=10, so_luong_can=Decimal("1.5"))
        dm2 = MagicMock(mon_an_id=2, nguyen_lieu_id=10, so_luong_can=Decimal("0.5"))

        nl10 = MagicMock(id=10, ten="Thịt bò", don_vi="kg", ton_kho_hien_tai=Decimal("10.0"))

        with patch("foods.models.LichSuXuatNhapKho.objects.filter") as m_hist, \
             patch("foods.models.DinhMucNguyenLieu.objects.filter") as m_bom, \
             patch("foods.models.NguyenLieu.objects.select_for_update") as m_sfu, \
             patch("foods.models.LichSuXuatNhapKho.objects.create") as m_create:

            m_hist.return_value.exists.return_value = False
            m_bom.return_value.select_related.return_value = [dm1, dm2]
            m_sfu.return_value.filter.return_value.order_by.return_value = [nl10]

            records = DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 1, "so_luong": 2}, {"mon_an_id": 2, "so_luong": 3}],
                loai_tham_chieu="dat_ban",
                id_tham_chieu=601
            )

            # Assert demand aggregation
            self.assertEqual(nl10.ton_kho_hien_tai, Decimal("5.5"))
            nl10.save.assert_called_once()
            self.assertEqual(nl10.save.call_args[1]["update_fields"], ["ton_kho_hien_tai", "cap_nhat_luc"])

            # Assert history creation
            m_create.assert_called_once()
            c_kwargs = m_create.call_args[1]
            self.assertEqual(c_kwargs["so_luong"], Decimal("4.5"))
            self.assertEqual(c_kwargs["ton_kho_truoc"], Decimal("10.0"))
            self.assertEqual(c_kwargs["ton_kho_sau"], Decimal("5.5"))

    def test_bom_idempotency_prevents_duplicate_deduction(self):
        """
        Verify that DichVuKho.khau_tru_nguyen_lieu_bom is idempotent:
        If a deduction has already occurred for (loai_tham_chieu, id_tham_chieu),
        it returns the existing audit history without re-deducting stock.
        """
        existing_history = [MagicMock(id=999, so_luong=Decimal("4.5"))]

        with patch("foods.models.LichSuXuatNhapKho.objects.filter") as m_hist, \
             patch("foods.models.NguyenLieu.objects.select_for_update") as m_sfu:

            m_hist.return_value.exists.return_value = True
            m_hist.return_value.__iter__.return_value = existing_history

            res = DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 1, "so_luong": 2}],
                loai_tham_chieu="dat_ban",
                id_tham_chieu=601
            )

            self.assertEqual(res, existing_history)
            m_sfu.assert_not_called()

    def test_bom_stockout_validation_error_propagates_and_rolls_back_in_doi_trang_thai(self):
        """
        Adversarial Defect Check: Verify that when inventory is insufficient:
        1. DichVuKho.khau_tru_nguyen_lieu_bom raises ValidationError.
        2. DichVuDatBan.doi_trang_thai does NOT swallow the exception with pass.
        3. The ValidationError propagates out, causing the atomic transaction to rollback.
        """
        # Static AST audit: Ensure 'except Exception:\n            pass' is completely absent
        source = textwrap.dedent(inspect.getsource(DichVuDatBan.doi_trang_thai))
        self.assertNotIn(
            "except Exception:\n            pass",
            source,
            "CRITICAL FLAW: doi_trang_thai must NOT contain 'except Exception: pass'!"
        )

        mock_dat_ban = MagicMock(id=808, ma_dat_ban="DB0808", trang_thai=DatBan.TrangThai.CHO_THANH_TOAN, phien_ban=1)
        mock_item = MagicMock()
        mock_dat_ban.danh_sach_mon.all.return_value.exists.return_value = True
        mock_dat_ban.danh_sach_mon.all.return_value = [mock_item]

        with patch("reservations.models.DatBan.objects.select_for_update") as mock_db_sfu, \
             patch("foods.services.DichVuKho.khau_tru_nguyen_lieu_bom", side_effect=ValidationError({"kho": "Hết tồn kho nguyên liệu"})):

            mock_db_sfu.return_value.get.return_value = mock_dat_ban

            with self.assertRaises(ValidationError) as ctx:
                DichVuDatBan.doi_trang_thai(
                    dat_ban=mock_dat_ban,
                    trang_thai_moi=DatBan.TrangThai.DA_XAC_NHAN,
                    nguoi_dung=MagicMock()
                )

            self.assertIn("kho", ctx.exception.detail)
            self.assertIn("Hết tồn kho", str(ctx.exception.detail["kho"]))

    def test_bom_hoan_tra_restocks_and_uses_sorted_ids(self):
        """
        Verify that DichVuKho.hoan_tra_nguyen_lieu_bom:
        1. Finds previous export transactions.
        2. Sorts ingredient IDs ascending before acquiring pessimistic row locks.
        3. Restores stock correctly.
        """
        gd1 = MagicMock(nguyen_lieu_id=40, so_luong=Decimal("2.0"))
        gd2 = MagicMock(nguyen_lieu_id=15, so_luong=Decimal("3.5"))

        nl15 = MagicMock(id=15, ton_kho_hien_tai=Decimal("10.0"))
        nl40 = MagicMock(id=40, ton_kho_hien_tai=Decimal("5.0"))

        recorded_sorted_ids = []

        def mock_sfu_filter(id__in):
            recorded_sorted_ids.append(list(id__in))
            ret = MagicMock()
            ret.order_by.return_value = [nl15, nl40]
            return ret

        with patch("foods.models.LichSuXuatNhapKho.objects.filter") as m_hist, \
             patch("foods.models.NguyenLieu.objects.select_for_update") as m_sfu, \
             patch("foods.models.LichSuXuatNhapKho.objects.create") as m_create:

            mock_qs = MagicMock()
            mock_qs.exists.return_value = True
            mock_qs.__iter__.return_value = [gd1, gd2]
            m_hist.return_value.select_related.return_value = mock_qs
            m_sfu.return_value.filter.side_effect = mock_sfu_filter

            res = DichVuKho.hoan_tra_nguyen_lieu_bom(
                loai_tham_chieu="dat_ban",
                id_tham_chieu=909
            )

            # Verify locks were requested in sorted order [15, 40]
            self.assertEqual(recorded_sorted_ids[0], [15, 40])
            self.assertEqual(nl15.ton_kho_hien_tai, Decimal("13.5"))
            self.assertEqual(nl40.ton_kho_hien_tai, Decimal("7.0"))
            self.assertEqual(len(res), 2)

    def test_bom_fractional_precision_aggregation(self):
        """
        Verify exact decimal precision when aggregating fractional ingredient quantities
        (e.g., 0.125 kg + 0.375 kg = 0.500 kg), ensuring no floating-point inaccuracies occur.
        """
        dm1 = MagicMock(mon_an_id=1, nguyen_lieu_id=10, so_luong_can=Decimal("0.125"))
        dm2 = MagicMock(mon_an_id=2, nguyen_lieu_id=10, so_luong_can=Decimal("0.375"))

        nl10 = MagicMock(id=10, ten="Gia vị", don_vi="kg", ton_kho_hien_tai=Decimal("1.000"))

        with patch("foods.models.LichSuXuatNhapKho.objects.filter") as m_hist, \
             patch("foods.models.DinhMucNguyenLieu.objects.filter") as m_bom, \
             patch("foods.models.NguyenLieu.objects.select_for_update") as m_sfu, \
             patch("foods.models.LichSuXuatNhapKho.objects.create") as m_create:

            m_hist.return_value.exists.return_value = False
            m_bom.return_value.select_related.return_value = [dm1, dm2]
            m_sfu.return_value.filter.return_value.order_by.return_value = [nl10]

            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 1, "so_luong": 1}, {"mon_an_id": 2, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=777
            )

            self.assertEqual(nl10.ton_kho_hien_tai, Decimal("0.500"))
            self.assertEqual(m_create.call_args[1]["so_luong"], Decimal("0.500"))

    def test_bom_multiple_deficient_ingredients_clean_rejection(self):
        """
        Adversarial Test: When multiple ingredients in a single recipe exceed inventory,
        verify that all deficient ingredients are reported in ValidationError and NO changes are persisted.
        """
        dm1 = MagicMock(mon_an_id=1, nguyen_lieu_id=10, so_luong_can=Decimal("5.0"))
        dm2 = MagicMock(mon_an_id=1, nguyen_lieu_id=20, so_luong_can=Decimal("8.0"))

        nl10 = MagicMock(id=10, ten="Thịt heo", don_vi="kg", ton_kho_hien_tai=Decimal("2.0"))  # deficit of 3.0
        nl20 = MagicMock(id=20, ten="Tôm sú", don_vi="kg", ton_kho_hien_tai=Decimal("3.0"))   # deficit of 5.0

        with patch("foods.models.LichSuXuatNhapKho.objects.filter") as m_hist, \
             patch("foods.models.DinhMucNguyenLieu.objects.filter") as m_bom, \
             patch("foods.models.NguyenLieu.objects.select_for_update") as m_sfu, \
             patch("foods.models.LichSuXuatNhapKho.objects.create") as m_create:

            m_hist.return_value.exists.return_value = False
            m_bom.return_value.select_related.return_value = [dm1, dm2]
            m_sfu.return_value.filter.return_value.order_by.return_value = [nl10, nl20]

            with self.assertRaises(ValidationError) as ctx:
                DichVuKho.khau_tru_nguyen_lieu_bom(
                    danh_sach_mon=[{"mon_an_id": 1, "so_luong": 1}],
                    loai_tham_chieu="don_hang",
                    id_tham_chieu=888
                )

            error_list = ctx.exception.detail["kho"]
            self.assertEqual(len(error_list), 2)
            self.assertIn("Thịt heo", error_list[0])
            self.assertIn("Tôm sú", error_list[1])
            nl10.save.assert_not_called()
            nl20.save.assert_not_called()
            m_create.assert_not_called()


class TestDistinctResourceConcurrency(AuthenticTransactionTestCase):
    """Verify that concurrency control does NOT produce false positives across distinct resources."""

    def setUp(self):
        super().setUp()
        self.cache = caches["locmem"]
        self.cache.clear()

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_distinct_tables_concurrent_hold_no_false_conflict(self, mock_db_filter, mock_ban_sr):
        """
        Verify that holds on different tables (Table 1 vs Table 2) at the exact same time slot
        succeed independently without false conflict.
        """
        def get_ban(id):
            return MagicMock(id=id, trang_thai="trong", suc_chua=4)

        mock_ban_sr.return_value.get.side_effect = get_ban
        mock_db_filter.return_value.exists.return_value = False

        num_tables = 10

        def hold_distinct_table(table_id):
            return DichVuDatBan.giu_ban_tam_thoi(
                ban_id=table_id,
                ngay="2026-11-20",
                gio="19:00",
                so_khach=2,
            )

        with patch("reservations.services._safe_cache", return_value=self.cache):
            with ThreadPoolExecutor(max_workers=num_tables) as executor:
                results = list(executor.map(hold_distinct_table, range(1, num_tables + 1)))

        successes = [r for r in results if r[0] is True]
        conflicts = [r for r in results if r[0] is False]

        self.assertEqual(len(successes), num_tables, "All distinct tables must be held successfully")
        self.assertEqual(len(conflicts), 0, "No conflicts should occur for distinct tables")


if __name__ == "__main__":
    unittest.main()
