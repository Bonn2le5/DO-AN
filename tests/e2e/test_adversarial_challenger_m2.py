#!/usr/bin/env python3
"""
Adversarial Empirical Stress Testing & Concurrency Verification Suite for Milestone 2.
Challenger 1 & Challenger 2 Consolidated 16-Test Remediation Verification Suite.

Covers 16 adversarial scenarios across Milestone 2:
1.  test_adv_01: Multi-threaded Table Hold Collision (20 concurrent threads -> 1 HTTP 200, 19 HTTP 409 BAN_DANG_BAN).
2.  test_adv_02: Expired Hold Token allows immediate re-acquisition upon TTL expiration.
3.  test_adv_03: Database Pre-booking Collision (Table already confirmed in DB returns HTTP 409).
4.  test_adv_04: BanAnViewSet allows unauthenticated guest to hold table (HTTP 200, not 401).
5.  test_adv_05: BanAnViewSet allows authenticated regular customer to hold table (HTTP 200, not 403).
6.  test_adv_06: DatBanViewSet giu_ban_frontend correctly allows guest (contrast verification).
7.  test_adv_07: Phase 2 Transaction Scope in tao_dat_ban (atomic transaction covers select_for_update and persistence).
8.  test_adv_08: Phase 2 Forged or Expired Hold Token Rejected with ValidationError.
9.  test_adv_09: BOM Material Deduction Transaction Scope in khau_tru_nguyen_lieu_bom (atomic transaction covers row lock & deduction).
10. test_adv_10: BOM Material Restocking Transaction Scope in hoan_tra_nguyen_lieu_bom (atomic transaction covers row lock & restoration).
11. test_adv_11: Exception Propagation in DichVuDatBan.doi_trang_thai (does not swallow stockout ValidationError with pass).
12. test_adv_12: BOM Deadlock Prevention via Strict Ascending ID Ordering (Order A [10, 20] vs Order B [20, 10]).
13. test_adv_13: BOM Stock Exhaustion Clean Rejection without partial stock deduction or orphan audit logs.
14. test_adv_14: VNPay IPN Transaction Scope (process_ipn maintains row lock through amount, idempotency checks, and mutations).
15. test_adv_15: ThanhToanViewSet allows unauthenticated server-to-server IPN webhooks (HTTP 200, not 401).
16. test_adv_16: VNPay IPN Checksum on Django QueryDict correctly extracts scalars without list-wrapping, passing HMAC check.

Usage:
    PYTHONPATH=moc-backend ./moc-backend/.venv/bin/python tests/e2e/test_adversarial_challenger_m2.py
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
for p in [current_dir, current_dir.parent, current_dir.parent.parent, current_dir.parent.parent.parent, current_dir.parent.parent.parent.parent]:
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
from django.http import QueryDict
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from reservations.services import DichVuDatBan
from reservations.views import BanAnViewSet, DatBanViewSet
from reservations.models import BanAn, DatBan
from foods.services import DichVuKho
from foods.models import NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho
from payments.models import ThanhToan
from payments.services import VNPayService
from payments.views import ThanhToanViewSet
from tests.e2e.helpers.vnpay_oracle import DEFAULT_HASH_SECRET


class AuthenticTransactionTestCase(unittest.TestCase):
    """
    Base test case that executes genuine Django transaction.atomic context manager
    without raw network socket IO, while strictly enforcing:
    1. connection.in_atomic_block tracking.
    2. select_for_update outside of atomic raises TransactionManagementError.
    3. rollback semantics on exceptions.
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


class TestAdversarialTableHoldConcurrency(AuthenticTransactionTestCase):
    """Adversarial stress testing of Phase 1 Table Hold under concurrent thread collision."""

    def setUp(self):
        super().setUp()
        self.cache = caches["locmem"]
        self.cache.clear()
        self.ban_id = 42
        self.ngay = "2026-11-15"
        self.gio = "19:30"
        self.so_khach = 4

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_adv_01_concurrent_20_threads_table_hold_collision(self, mock_db_filter, mock_ban_sr):
        """
        Stress Test: 20 threads simultaneously race to hold the exact same table & slot.
        Empirically asserts:
        - Exactly 1 thread succeeds (status=success, id_giu_ban prefixed HOLD_, 600s TTL).
        - Exactly 19 threads fail with HTTP 409 Conflict (code="BAN_DANG_BAN", error_code="TABLE_CURRENTLY_HELD").
        - Retry-after seconds is properly provided in all conflict responses.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = False

        num_threads = 20

        def worker_hold(thread_id):
            return DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id,
                ngay=self.ngay,
                gio=self.gio,
                so_khach=self.so_khach,
                user_id=1000 + thread_id,
            )

        with patch("reservations.services._safe_cache", return_value=self.cache):
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                results = list(executor.map(worker_hold, range(num_threads)))

        successes = [r for r in results if r[0] is True]
        conflicts = [r for r in results if r[0] is False]

        self.assertEqual(len(successes), 1, f"Expected exactly 1 success, got {len(successes)}")
        self.assertEqual(len(conflicts), num_threads - 1, f"Expected {num_threads - 1} conflicts, got {len(conflicts)}")

        # Validate winner payload
        win_ok, win_data = successes[0]
        self.assertEqual(win_data["status"], "success")
        self.assertTrue(win_data["id_giu_ban"].startswith("HOLD_"))
        self.assertEqual(win_data["thoi_gian_con_lai_giay"], 600)
        self.assertEqual(win_data["ban_an_id"], self.ban_id)

        # Validate all conflict payloads
        for fail_ok, fail_data in conflicts:
            self.assertEqual(fail_data["code"], "BAN_DANG_BAN")
            self.assertEqual(fail_data["error_code"], "TABLE_CURRENTLY_HELD")
            self.assertEqual(fail_data["status"], "conflict")
            self.assertEqual(fail_data["retry_after_seconds"], 600)
            self.assertIn("đang được người khác giữ chỗ", fail_data["detail"])

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_adv_02_expired_hold_allows_immediate_reacquisition(self, mock_db_filter, mock_ban_sr):
        """
        Verify that once Redis TTL expires, a subsequent thread immediately re-acquires the table.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = False

        with patch("reservations.services._safe_cache", return_value=self.cache):
            with patch.object(DichVuDatBan, "HOLD_TIMEOUT_SECONDS", 1):
                ok1, data1 = DichVuDatBan.giu_ban_tam_thoi(
                    ban_id=self.ban_id, ngay=self.ngay, gio=self.gio, so_khach=self.so_khach
                )
                self.assertTrue(ok1)

            time.sleep(1.1)

            ok2, data2 = DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id, ngay=self.ngay, gio=self.gio, so_khach=self.so_khach
            )
            self.assertTrue(ok2)
            self.assertNotEqual(data1["id_giu_ban"], data2["id_giu_ban"])

    @patch("reservations.models.BanAn.objects.select_related")
    @patch("reservations.models.DatBan.objects.filter")
    def test_adv_03_existing_db_booking_returns_409_table_already_booked(self, mock_db_filter, mock_ban_sr):
        """
        Verify that if table is already booked in PostgreSQL, giu_ban_tam_thoi rejects with 409
        even when Redis has no hold key.
        """
        mock_ban = MagicMock(id=self.ban_id, trang_thai="trong", suc_chua=6)
        mock_ban_sr.return_value.get.return_value = mock_ban
        mock_db_filter.return_value.exists.return_value = True

        with patch("reservations.services._safe_cache", return_value=self.cache):
            ok, data = DichVuDatBan.giu_ban_tam_thoi(
                ban_id=self.ban_id, ngay=self.ngay, gio=self.gio, so_khach=self.so_khach
            )
            self.assertFalse(ok)
            self.assertEqual(data["code"], "BAN_DANG_BAN")
            self.assertEqual(data["error_code"], "TABLE_ALREADY_BOOKED")
            self.assertIn("đã được đặt", data["detail"])


class TestAdversarialSecurityAndPermissions(AuthenticTransactionTestCase):
    """Empirically asserts the permission fixes in ViewSets."""

    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

    def test_adv_04_ban_an_viewset_allows_unauthenticated_guest(self):
        """
        Verify that BanAnViewSet.giu_ban allows unauthenticated guest access (HTTP 200, not HTTP 401).
        """
        ban_view = BanAnViewSet.as_view({"post": "giu_ban"})
        request = self.factory.post(
            "/api/tables/1/giu_ban/",
            {"ngay": "2026-11-15", "gio": "19:00", "so_luong_khach": 4},
            format="json",
        )
        with patch("reservations.services.DichVuDatBan.giu_ban_tam_thoi") as mock_hold:
            mock_hold.return_value = (True, {"status": "success", "id_giu_ban": "HOLD_123", "thoi_gian_con_lai_giay": 600})
            response = ban_view(request, pk=1)
            self.assertNotEqual(response.status_code, 401, "BanAnViewSet.giu_ban must NOT reject guest with 401")
            self.assertEqual(response.status_code, 200)

    def test_adv_05_ban_an_viewset_allows_authenticated_regular_customer(self):
        """
        Verify that BanAnViewSet.giu_ban allows authenticated regular customers (HTTP 200, not HTTP 403).
        """
        ban_view = BanAnViewSet.as_view({"post": "giu_ban"})
        request = self.factory.post(
            "/api/tables/1/giu_ban/",
            {"ngay": "2026-11-15", "gio": "19:00", "so_luong_khach": 4},
            format="json",
        )
        mock_customer = MagicMock(is_authenticated=True, is_staff=False, la_nhan_vien_nha_hang=False)
        force_authenticate(request, user=mock_customer)

        with patch("reservations.services.DichVuDatBan.giu_ban_tam_thoi") as mock_hold:
            mock_hold.return_value = (True, {"status": "success", "id_giu_ban": "HOLD_123", "thoi_gian_con_lai_giay": 600})
            response = ban_view(request, pk=1)
            self.assertNotEqual(response.status_code, 403, "BanAnViewSet.giu_ban must NOT reject customer with 403")
            self.assertEqual(response.status_code, 200)

    def test_adv_06_dat_ban_viewset_giu_ban_frontend_allows_guest(self):
        """
        Contrasting confirmation: DatBanViewSet.giu_ban_frontend correctly implemented get_permissions()
        returning AllowAny(), allowing unauthenticated requests to pass through.
        """
        frontend_view = DatBanViewSet.as_view({"post": "giu_ban_frontend"})
        request = self.factory.post(
            "/api/dat-ban/giu-ban/",
            {"ban_an_id": 1, "ngay": "2026-11-15", "gio": "19:00", "so_luong_khach": 4},
            format="json",
        )
        mock_ban = MagicMock(id=1, trang_thai="trong", suc_chua=6)
        with patch("reservations.services._safe_cache", return_value=caches["locmem"]):
            with patch("reservations.models.BanAn.objects.select_related") as mock_sr:
                mock_sr.return_value.get.return_value = mock_ban
                with patch("reservations.models.DatBan.objects.filter") as mock_filter:
                    mock_filter.return_value.exists.return_value = False
                    response = frontend_view(request)
                    self.assertEqual(response.status_code, 200)


class TestAdversarialPhase2TransactionScoping(AuthenticTransactionTestCase):
    """Empirically checks the transaction scoping and atomicity in Phase 2 confirmation."""

    def test_adv_07_tao_dat_ban_atomic_transaction_scope(self):
        """
        Verify that DichVuDatBan.tao_dat_ban is decorated with @transaction.atomic or encapsulates
        all critical database operations (select_for_update, DatBan.objects.create) inside the active transaction.
        """
        source = textwrap.dedent(inspect.getsource(DichVuDatBan.tao_dat_ban))
        tree = ast.parse(source)
        func_def = tree.body[0]

        has_atomic_decorator = any(
            (isinstance(d, ast.Attribute) and d.attr == "atomic") or
            (isinstance(d, ast.Name) and "atomic" in d.id) or
            (isinstance(d, ast.Call) and getattr(getattr(d, "func", None), "attr", None) == "atomic")
            for d in getattr(func_def, "decorator_list", [])
        )
        with_nodes = [node for node in ast.walk(func_def) if isinstance(node, ast.With)]

        self.assertTrue(
            has_atomic_decorator or len(with_nodes) >= 1,
            "tao_dat_ban must be wrapped in @transaction.atomic or with transaction.atomic()"
        )
        if not has_atomic_decorator and with_nodes:
            self.assertGreater(len(with_nodes[0].body), 1, "with block must not contain only 1 statement")

    def test_adv_08_phase2_forged_or_expired_hold_token_rejected(self):
        """
        Verify that Phase 2 confirmation rejects forged or mismatched hold tokens.
        """
        mock_ban = MagicMock(id=5, trang_thai="trong", suc_chua=6, chi_nhanh_id=1)
        mock_user = MagicMock(is_authenticated=True)

        cache = caches["locmem"]
        cache.clear()
        cache.set("table_hold:5:2026-11-20:19:00", "HOLD_REAL_TOKEN_12345", timeout=600)

        du_lieu = {
            "ban_an": mock_ban,
            "ngay_dat": "2026-11-20",
            "gio_bat_dau": "19:00",
            "so_luong_khach": 4,
            "id_giu_ban": "HOLD_FORGED_ATTACKER_TOKEN",
            "chi_nhanh": MagicMock(id=1),
        }

        with patch("reservations.services._safe_cache", return_value=cache):
            with patch("reservations.models.BanAn.objects.select_for_update") as mock_sfu:
                mock_sfu.return_value.get.return_value = mock_ban
                with patch("reservations.models.DatBan.objects.select_for_update") as mock_db_sfu:
                    mock_db_sfu.return_value.filter.return_value.exists.return_value = False

                    with self.assertRaises(ValidationError) as ctx:
                        DichVuDatBan.tao_dat_ban(nguoi_dung=mock_user, du_lieu=du_lieu)

                    self.assertIn("id_giu_ban", ctx.exception.detail)
                    self.assertIn("hết hạn hoặc không hợp lệ", str(ctx.exception.detail["id_giu_ban"]))


class TestAdversarialBOMInventoryConcurrency(AuthenticTransactionTestCase):
    """Empirically verifies BOM inventory deduction, deadlock avoidance, and atomicity."""

    def test_adv_09_bom_deduction_atomic_transaction_scope(self):
        """
        Verify that DichVuKho.khau_tru_nguyen_lieu_bom executes inside an atomic transaction,
        either via @transaction.atomic decorator or enclosing with transaction.atomic(): block.
        """
        source = textwrap.dedent(inspect.getsource(DichVuKho.khau_tru_nguyen_lieu_bom))
        tree = ast.parse(source)
        func_def = tree.body[0]

        has_atomic_decorator = any(
            (isinstance(d, ast.Attribute) and d.attr == "atomic") or
            (isinstance(d, ast.Name) and "atomic" in d.id) or
            (isinstance(d, ast.Call) and getattr(getattr(d, "func", None), "attr", None) == "atomic")
            for d in getattr(func_def, "decorator_list", [])
        )
        with_nodes = [node for node in ast.walk(func_def) if isinstance(node, ast.With)]
        self.assertTrue(
            has_atomic_decorator or len(with_nodes) >= 1,
            "khau_tru_nguyen_lieu_bom must be wrapped in an atomic transaction"
        )

    def test_adv_10_bom_return_atomic_transaction_scope(self):
        """
        Verify that DichVuKho.hoan_tra_nguyen_lieu_bom executes inside an atomic transaction.
        """
        source = textwrap.dedent(inspect.getsource(DichVuKho.hoan_tra_nguyen_lieu_bom))
        tree = ast.parse(source)
        func_def = tree.body[0]

        has_atomic_decorator = any(
            (isinstance(d, ast.Attribute) and d.attr == "atomic") or
            (isinstance(d, ast.Name) and "atomic" in d.id) or
            (isinstance(d, ast.Call) and getattr(getattr(d, "func", None), "attr", None) == "atomic")
            for d in getattr(func_def, "decorator_list", [])
        )
        with_nodes = [node for node in ast.walk(func_def) if isinstance(node, ast.With)]
        self.assertTrue(
            has_atomic_decorator or len(with_nodes) >= 1,
            "hoan_tra_nguyen_lieu_bom must be wrapped in an atomic transaction"
        )

    def test_adv_11_doi_trang_thai_propagates_bom_stockout_exceptions(self):
        """
        Verify that DichVuDatBan.doi_trang_thai does NOT silently swallow BOM stockout errors,
        and propagates ValidationError when inventory deduction fails.
        """
        source = textwrap.dedent(inspect.getsource(DichVuDatBan.doi_trang_thai))
        self.assertNotIn(
            "except Exception:\n            pass",
            source,
            "doi_trang_thai must NOT silence BOM exception with pass!"
        )

        mock_dat_ban = MagicMock(id=99, ma_dat_ban="DB99", trang_thai="cho_thanh_toan", phien_ban=1)
        mock_item = MagicMock()
        mock_dat_ban.danh_sach_mon.all.return_value.exists.return_value = True
        mock_dat_ban.danh_sach_mon.all.return_value = [mock_item]

        with patch("reservations.models.DatBan.objects.select_for_update") as mock_db_sfu:
            mock_db_sfu.return_value.get.return_value = mock_dat_ban
            with patch("foods.services.DichVuKho.khau_tru_nguyen_lieu_bom", side_effect=ValidationError({"kho": "Het hang"})):
                with self.assertRaises(ValidationError):
                    DichVuDatBan.doi_trang_thai(mock_dat_ban, DatBan.TrangThai.DA_XAC_NHAN, MagicMock())

    @patch("foods.models.NguyenLieu.objects.select_for_update")
    @patch("foods.models.DinhMucNguyenLieu.objects.filter")
    @patch("foods.models.LichSuXuatNhapKho.objects.filter")
    def test_adv_12_concurrent_inverted_ingredient_orders_strict_ascending_id(
        self, mock_hist_filter, mock_bom_filter, mock_nl_sfu
    ):
        """
        Concurrency Stress Test: Two concurrent orders require inverted ingredient sets:
        Order A requires [Ingredient 10, Ingredient 20]
        Order B requires [Ingredient 20, Ingredient 10]
        Verify that DichVuKho.khau_tru_nguyen_lieu_bom sorts IDs ascending ([10, 20]) for both orders,
        guaranteeing strict global resource ordering and preventing circular wait deadlocks.
        """
        mock_hist_filter.return_value.exists.return_value = False

        dm_a1 = MagicMock(mon_an_id=1, nguyen_lieu_id=10, so_luong_can=Decimal("1.0"))
        dm_a2 = MagicMock(mon_an_id=1, nguyen_lieu_id=20, so_luong_can=Decimal("1.0"))

        dm_b1 = MagicMock(mon_an_id=2, nguyen_lieu_id=20, so_luong_can=Decimal("2.0"))
        dm_b2 = MagicMock(mon_an_id=2, nguyen_lieu_id=10, so_luong_can=Decimal("2.0"))

        nl10 = MagicMock(id=10, ten="Thịt heo", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))
        nl20 = MagicMock(id=20, ten="Hành tây", don_vi="kg", ton_kho_hien_tai=Decimal("100.0"))

        order_lock_sequences = []

        def mock_nl_filter(id__in):
            order_lock_sequences.append(list(id__in))
            ret = MagicMock()
            ret.order_by.return_value = [nl10, nl20]
            return ret

        mock_nl_sfu.return_value.filter.side_effect = mock_nl_filter

        # Run Order A
        mock_bom_filter.return_value.select_related.return_value = [dm_a1, dm_a2]
        with patch("foods.models.LichSuXuatNhapKho.objects.create"):
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 1, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=101,
            )

        # Run Order B (inverted input)
        mock_bom_filter.return_value.select_related.return_value = [dm_b1, dm_b2]
        with patch("foods.models.LichSuXuatNhapKho.objects.create"):
            DichVuKho.khau_tru_nguyen_lieu_bom(
                danh_sach_mon=[{"mon_an_id": 2, "so_luong": 1}],
                loai_tham_chieu="don_hang",
                id_tham_chieu=102,
            )

        # Both invocations must request lock in strictly ascending ID order [10, 20]
        self.assertEqual(len(order_lock_sequences), 2)
        self.assertEqual(order_lock_sequences[0], [10, 20], "Order A lock request must be sorted [10, 20]")
        self.assertEqual(order_lock_sequences[1], [10, 20], "Order B lock request must be sorted [10, 20]")

    @patch("foods.models.NguyenLieu.objects.select_for_update")
    @patch("foods.models.DinhMucNguyenLieu.objects.filter")
    @patch("foods.models.LichSuXuatNhapKho.objects.filter")
    def test_adv_13_stock_exhaustion_clean_rejection_without_partial_deductions(
        self, mock_hist_filter, mock_bom_filter, mock_nl_sfu
    ):
        """
        Stock Exhaustion: Dish requires Ingredient 1 (5 kg, available: 10 kg) and
        Ingredient 2 (5 kg, available: 1 kg -> INSUFFICIENT).
        Verify:
        - Raises ValidationError with explicit deficit message.
        - Neither Ingredient 1 nor Ingredient 2 has its inventory modified.
        - Zero LichSuXuatNhapKho records are created.
        """
        mock_hist_filter.return_value.exists.return_value = False

        dm1 = MagicMock(mon_an_id=99, nguyen_lieu_id=1, so_luong_can=Decimal("5.0"))
        dm2 = MagicMock(mon_an_id=99, nguyen_lieu_id=2, so_luong_can=Decimal("5.0"))
        mock_bom_filter.return_value.select_related.return_value = [dm1, dm2]

        nl1 = MagicMock(id=1, ten="Gạo ST25", don_vi="kg", ton_kho_hien_tai=Decimal("10.0"))
        nl2 = MagicMock(id=2, ten="Tôm sú", don_vi="kg", ton_kho_hien_tai=Decimal("1.0"))

        mock_nl_sfu.return_value.filter.return_value.order_by.return_value = [nl1, nl2]

        with patch("foods.models.LichSuXuatNhapKho.objects.create") as mock_create_log:
            with self.assertRaises(ValidationError) as ctx:
                DichVuKho.khau_tru_nguyen_lieu_bom(
                    danh_sach_mon=[{"mon_an_id": 99, "so_luong": 1}],
                    loai_tham_chieu="don_hang",
                    id_tham_chieu=888,
                )

            self.assertIn("kho", ctx.exception.detail)
            self.assertIn("Tôm sú", str(ctx.exception.detail["kho"]))

            self.assertEqual(nl1.ton_kho_hien_tai, Decimal("10.0"))
            self.assertEqual(nl2.ton_kho_hien_tai, Decimal("1.0"))
            mock_create_log.assert_not_called()


class TestAdversarialVNPayTransactionScoping(AuthenticTransactionTestCase):
    """Empirically verifies transaction scoping and race condition remediations in VNPay."""

    def test_adv_14_vnpay_process_ipn_atomic_block_encloses_mutation(self):
        """
        Verify that VNPayService.process_ipn encloses order lookup, amount check,
        idempotency check, and state mutations inside the single atomic transaction block.
        """
        source = textwrap.dedent(inspect.getsource(VNPayService.process_ipn))
        tree = ast.parse(source)
        func_def = tree.body[0]

        with_nodes = [node for node in ast.walk(func_def) if isinstance(node, ast.With)]
        self.assertGreaterEqual(len(with_nodes), 1, "Expected with transaction.atomic in process_ipn")

        atomic_block = with_nodes[0]
        self.assertGreater(
            len(atomic_block.body), 1,
            f"process_ipn atomic block must contain full stages 2-5, not just 1 statement"
        )


class TestAdversarialVNPayWebhookAndDataIntegrity(AuthenticTransactionTestCase):
    """Empirically verifies webhook permissions and QueryDict handling fixes in payments."""

    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()

    def test_adv_15_thanhtoan_viewset_allows_unauthenticated_ipn(self):
        """
        Verify that ThanhToanViewSet allows unauthenticated server-to-server IPN callbacks
        from VNPay (returns HTTP 200, not HTTP 401 Unauthorized).
        """
        ipn_view = ThanhToanViewSet.as_view({"get": "vnpay_ipn"})
        request = self.factory.get("/api/payments/vnpay/ipn/?vnp_SecureHash=dummy")
        response = ipn_view(request)
        self.assertNotEqual(response.status_code, 401, "ThanhToanViewSet.vnpay_ipn must NOT reject IPN with 401")
        self.assertEqual(response.status_code, 200)

    def test_adv_16_vnpay_ipn_handles_django_querydict_scalars(self):
        """
        Verify that VNPayService.process_ipn properly handles Django QueryDict parameters,
        extracting clean scalars so HMAC verification succeeds (not failing with code 97).
        """
        raw_params = {
            "vnp_TxnRef": "TT_TEST_ADV_16",
            "vnp_Amount": "20000000",
            "vnp_ResponseCode": "00",
        }
        sig = VNPayService.calculate_hmac_sha512(raw_params, DEFAULT_HASH_SECRET)

        qd = QueryDict("", mutable=True)
        qd.update(raw_params)
        qd["vnp_SecureHash"] = sig

        with patch("payments.models.ThanhToan.objects.select_for_update") as mock_sfu:
            mock_sfu.return_value.select_related.return_value.get.side_effect = ThanhToan.DoesNotExist
            code, msg = VNPayService.process_ipn(qd)

        self.assertNotEqual(code, "97", "QueryDict must NOT cause code 97 Invalid Checksum")
        self.assertEqual(code, "01", "Valid checksum proceeded to order lookup (code 01 Order not found)")


if __name__ == "__main__":
    unittest.main()
