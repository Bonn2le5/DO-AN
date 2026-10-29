#!/usr/bin/env python3
"""
Adversarial Challenger Verification Suite for Milestone 5 (Round 2 — Post-Remediation):
Web App Nhà hàng Mộc — Challenger m5_r2_challenger_1.

Empirical Focus:
1. Dual-stream Live Broadcast Verification:
   - Order FSM transitions initiated by staff via REST API using both numeric `id` and string `ma_don_hang`.
   - Verification of concurrent live broadcast delivery to `/ws/orders/<id>/`, `/ws/orders/<ma_don_hang>/`, and `/ws/orders/staff/`.
2. Full lifecycle progression with alternating numeric ID and string code lookups.
3. Multi-listener fan-out (numeric listener, code listener, staff kitchen monitor).
4. Adversarial RBAC: Customer transition attempts blocked (HTTP 403) with no spurious broadcasts.
5. Non-existent ID/code lookups (HTTP 404) and illegal FSM state jumps (HTTP 400).
6. English/Vietnamese status aliases and case-insensitivity.
"""

import os
import sys
import types
import asyncio
from pathlib import Path
from decimal import Decimal

PROJECT_ROOT = Path("/Users/VuVan/Documents/DO-AN")
BACKEND_DIR = PROJECT_ROOT / "moc-backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Daphne mock stub for Channels testing in offline sandbox
if "daphne" not in sys.modules:
    daphne_mod = types.ModuleType("daphne")
    daphne_mod.testing = types.SimpleNamespace(DaphneProcess=object)
    sys.modules["daphne"] = daphne_mod
    sys.modules["daphne.testing"] = daphne_mod.testing

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

from config.asgi import application
from orders.models import DonHang, ChiTietDonHang, LichSuTrangThaiDon
from foods.models import MonAn, DanhMuc


class TestM5R2ChallengerFSMRealtime(TransactionTestCase):
    """Adversarial challenge tests for dual-stream live broadcast & FSM API transitions."""

    def setUp(self):
        User = get_user_model()
        User.objects.all().delete()
        DonHang.objects.all().delete()
        MonAn.objects.all().delete()
        DanhMuc.objects.all().delete()

        # Customer Alice
        self.customer_alice = User.objects.create_user(
            username="alice_m5_r2",
            email="alice_r2@moc.vn",
            thu_dien_tu="alice_r2@moc.vn",
            password="alicePass123!",
            first_name="Alice",
            last_name="Tran",
        )

        # Customer Bob (unauthorized adversary)
        self.customer_bob = User.objects.create_user(
            username="bob_m5_r2",
            email="bob_r2@moc.vn",
            thu_dien_tu="bob_r2@moc.vn",
            password="bobPass123!",
            first_name="Bob",
            last_name="Nguyen",
        )

        # Restaurant Staff
        self.staff_user = User.objects.create_user(
            username="staff_m5_r2",
            email="staff_r2@moc.vn",
            thu_dien_tu="staff_r2@moc.vn",
            password="staffPass123!",
            is_staff=True,
            first_name="Staff",
            last_name="Nguyen",
        )

        # Category and Dish
        self.cat = DanhMuc.objects.create(ten="Món Đặc Trưng")
        self.dish = MonAn.objects.create(
            ten="Gà Nướng Mắc Khén",
            danh_muc=self.cat,
            don_gia=Decimal("250000.00"),
        )

        # Alice's Order
        self.order_alice = DonHang.objects.create(
            ma_don_hang="DH-M5-R2-ALICE",
            khach_hang=self.customer_alice,
            ten_khach="Alice Tran",
            sdt_khach="0901234567",
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc="giao_hang",
            dia_chi_giao="123 Vo Van Tan, Q3",
            tong_tien=Decimal("500000.00"),
        )
        ChiTietDonHang.objects.create(
            don_hang=self.order_alice,
            mon_an=self.dish,
            so_luong=2,
            don_gia_luc_dat=Decimal("250000.00"),
            thanh_tien=Decimal("500000.00"),
        )

        # Bob's Order
        self.order_bob = DonHang.objects.create(
            ma_don_hang="DH-M5-R2-BOB",
            khach_hang=self.customer_bob,
            ten_khach="Bob Nguyen",
            sdt_khach="0909999888",
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            hinh_thuc="tai_ban",
            tong_tien=Decimal("250000.00"),
        )

    @database_sync_to_async
    def _staff_patch_status(self, lookup_val, status_str, note=""):
        client = APIClient()
        client.force_authenticate(user=self.staff_user)
        url = f"/api/orders/{lookup_val}/trang_thai/"
        response = client.patch(url, {"trang_thai": status_str, "ghi_chu": note}, format="json")
        return response.status_code, response.data

    @database_sync_to_async
    def _customer_patch_status(self, user, lookup_val, status_str, note=""):
        client = APIClient()
        client.force_authenticate(user=user)
        url = f"/api/orders/{lookup_val}/trang_thai/"
        response = client.patch(url, {"trang_thai": status_str, "ghi_chu": note}, format="json")
        return response.status_code, response.data

    async def test_01_staff_transition_by_numeric_id_broadcasts_to_customer_and_staff(self):
        """
        Scenario 1:
        Staff updates order status using numeric `id`.
        Verifies dual-stream live broadcast delivery to:
        - Customer tracking stream: /ws/orders/<id>/
        - Staff global kitchen stream: /ws/orders/staff/
        - Isolated stream /ws/orders/<bob_id>/ receives nothing.
        """
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_bob = str(AccessToken.for_user(self.customer_bob))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_alice = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok_alice}")
        comm_bob = WebsocketCommunicator(application, f"/ws/orders/{self.order_bob.id}/?token={tok_bob}")
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok_staff}")

        connected_alice, _ = await comm_alice.connect()
        connected_bob, _ = await comm_bob.connect()
        connected_staff, _ = await comm_staff.connect()

        self.assertTrue(connected_alice)
        self.assertTrue(connected_bob)
        self.assertTrue(connected_staff)

        # Drain snapshots
        snap_alice = await comm_alice.receive_json_from()
        self.assertEqual(snap_alice["type"], "order_snapshot")
        self.assertEqual(snap_alice["current_status"], DonHang.TrangThai.CHO_TIEP_NHAN)

        snap_bob = await comm_bob.receive_json_from()
        self.assertEqual(snap_bob["type"], "order_snapshot")

        snap_staff = await comm_staff.receive_json_from()
        self.assertEqual(snap_staff["type"], "staff_connected")

        # Staff executes PATCH using NUMERIC ID: /api/orders/<numeric_id>/trang_thai/
        status_code, data = await self._staff_patch_status(
            self.order_alice.id,
            "da_xac_nhan",
            "Nhân viên xác nhận đơn hàng qua numeric ID",
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data["trang_thai"], DonHang.TrangThai.DA_XAC_NHAN)

        # 1. Customer Alice receives live broadcast
        event_alice = await comm_alice.receive_json_from()
        self.assertEqual(event_alice.get("type"), "order_status_update")
        self.assertEqual(event_alice.get("order_id"), self.order_alice.id)
        self.assertEqual(event_alice.get("ma_don_hang"), self.order_alice.ma_don_hang)
        self.assertEqual(event_alice.get("from_status"), DonHang.TrangThai.CHO_TIEP_NHAN)
        self.assertEqual(event_alice.get("to_status"), DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(event_alice.get("status"), DonHang.TrangThai.DA_XAC_NHAN)

        # 2. Staff stream receives live broadcast
        event_staff = await comm_staff.receive_json_from()
        self.assertEqual(event_staff.get("type"), "order_status_update")
        self.assertEqual(event_staff.get("order_id"), self.order_alice.id)
        self.assertEqual(event_staff.get("ma_don_hang"), self.order_alice.ma_don_hang)
        self.assertEqual(event_staff.get("status"), DonHang.TrangThai.DA_XAC_NHAN)

        # 3. Customer Bob receives NOTHING (isolated order stream)
        bob_received_nothing = await comm_bob.receive_nothing(timeout=0.1)
        self.assertTrue(bob_received_nothing, "Unrelated order stream received broadcast leak!")

        await comm_alice.disconnect()
        await comm_bob.disconnect()
        await comm_staff.disconnect()

    async def test_02_staff_transition_by_string_order_code_broadcasts_to_customer_and_staff(self):
        """
        Scenario 2:
        Staff updates order status using string `ma_don_hang`.
        Customer connects via order code string /ws/orders/<ma_don_hang>/
        Verifies dual-stream live broadcast delivery to:
        - Customer stream: /ws/orders/<ma_don_hang>/
        - Staff stream: /ws/orders/staff/
        """
        # First ensure order is in da_xac_nhan
        await self._staff_patch_status(self.order_alice.id, "da_xac_nhan")

        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        # Customer connects using string order code!
        comm_alice = WebsocketCommunicator(
            application,
            f"/ws/orders/{self.order_alice.ma_don_hang}/?token={tok_alice}",
        )
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok_staff}")

        connected_alice, _ = await comm_alice.connect()
        connected_staff, _ = await comm_staff.connect()

        self.assertTrue(connected_alice)
        self.assertTrue(connected_staff)

        # Drain snapshots
        await comm_alice.receive_json_from()
        await comm_staff.receive_json_from()

        # Staff executes PATCH using STRING ORDER CODE: /api/orders/DH-M5-R2-ALICE/trang_thai/
        status_code, data = await self._staff_patch_status(
            self.order_alice.ma_don_hang,
            "dang_che_bien",
            "Bếp bắt đầu chế biến qua order code string",
        )
        self.assertEqual(status_code, 200, f"Order update by code failed: {data}")
        self.assertEqual(data["trang_thai"], DonHang.TrangThai.DANG_CHE_BIEN)

        # 1. Customer receives live broadcast
        event_alice = await comm_alice.receive_json_from()
        self.assertEqual(event_alice.get("type"), "order_status_update")
        self.assertEqual(event_alice.get("order_id"), self.order_alice.id)
        self.assertEqual(event_alice.get("ma_don_hang"), self.order_alice.ma_don_hang)
        self.assertEqual(event_alice.get("from_status"), DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(event_alice.get("to_status"), DonHang.TrangThai.DANG_CHE_BIEN)

        # 2. Staff receives live broadcast
        event_staff = await comm_staff.receive_json_from()
        self.assertEqual(event_staff.get("type"), "order_status_update")
        self.assertEqual(event_staff.get("order_id"), self.order_alice.id)
        self.assertEqual(event_staff.get("to_status"), DonHang.TrangThai.DANG_CHE_BIEN)

        await comm_alice.disconnect()
        await comm_staff.disconnect()

    async def test_03_full_fsm_lifecycle_alternating_numeric_and_code(self):
        """
        Scenario 3:
        Full order FSM lifecycle alternating between numeric ID and string ma_don_hang:
        1. cho_tiep_nhan -> da_xac_nhan (via numeric id)
        2. da_xac_nhan -> dang_che_bien (via string ma_don_hang)
        3. dang_che_bien -> san_sang (via numeric id)
        4. san_sang -> hoan_tat (via string ma_don_hang)
        Verifies both streams receive all events sequentially and audit log is 100% accurate.
        """
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_alice = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok_alice}")
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok_staff}")

        await comm_alice.connect()
        await comm_staff.connect()

        await comm_alice.receive_json_from()  # snapshot
        await comm_staff.receive_json_from()  # staff connected

        transitions = [
            (self.order_alice.id, "da_xac_nhan", DonHang.TrangThai.CHO_TIEP_NHAN, DonHang.TrangThai.DA_XAC_NHAN),
            (self.order_alice.ma_don_hang, "dang_che_bien", DonHang.TrangThai.DA_XAC_NHAN, DonHang.TrangThai.DANG_CHE_BIEN),
            (self.order_alice.id, "san_sang", DonHang.TrangThai.DANG_CHE_BIEN, DonHang.TrangThai.SAN_SANG),
            (self.order_alice.ma_don_hang, "hoan_tat", DonHang.TrangThai.SAN_SANG, DonHang.TrangThai.HOAN_TAT),
        ]

        for lookup_key, next_status, expected_from, expected_to in transitions:
            code, data = await self._staff_patch_status(lookup_key, next_status, f"Transition to {next_status}")
            self.assertEqual(code, 200, f"Transition with key '{lookup_key}' failed: {data}")
            self.assertEqual(data["trang_thai"], expected_to)

            ev_alice = await comm_alice.receive_json_from()
            self.assertEqual(ev_alice.get("type"), "order_status_update")
            self.assertEqual(ev_alice.get("from_status"), expected_from)
            self.assertEqual(ev_alice.get("to_status"), expected_to)

            # Drain duplicate frame delivered because consumer joins both order_<id> and order_<code_name>
            is_nothing = await comm_alice.receive_nothing(timeout=0.05)
            if not is_nothing:
                dup_alice = await comm_alice.receive_json_from()
                self.assertEqual(dup_alice.get("type"), "order_status_update")
                self.assertEqual(dup_alice.get("to_status"), expected_to)

            ev_staff = await comm_staff.receive_json_from()
            self.assertEqual(ev_staff.get("type"), "order_status_update")
            self.assertEqual(ev_staff.get("to_status"), expected_to)

        # Verify audit trail in DB
        audit_records = await database_sync_to_async(
            lambda: list(LichSuTrangThaiDon.objects.filter(don_hang=self.order_alice).order_by("tao_luc"))
        )()
        self.assertEqual(len(audit_records), 4)
        expected_chain = [
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.SAN_SANG,
            DonHang.TrangThai.HOAN_TAT,
        ]
        for record, exp_status in zip(audit_records, expected_chain):
            self.assertEqual(record.sang_trang_thai, exp_status)

        await comm_alice.disconnect()
        await comm_staff.disconnect()

    async def test_04_dual_listeners_id_and_code_simultaneous_reception(self):
        """
        Scenario 4:
        Multi-listener fan-out:
        - Listener 1: connected via /ws/orders/<id>/
        - Listener 2: connected via /ws/orders/<ma_don_hang>/
        - Listener 3: connected via /ws/orders/staff/
        All 3 listeners concurrently receive live update when staff modifies status.
        """
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_by_id = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok_alice}")
        comm_by_code = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.ma_don_hang}/?token={tok_alice}")
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok_staff}")

        await comm_by_id.connect()
        await comm_by_code.connect()
        await comm_staff.connect()

        await comm_by_id.receive_json_from()
        await comm_by_code.receive_json_from()
        await comm_staff.receive_json_from()

        # Update via code
        status_code, _ = await self._staff_patch_status(self.order_alice.ma_don_hang, "da_xac_nhan")
        self.assertEqual(status_code, 200)

        # All 3 receive the update
        ev1 = await comm_by_id.receive_json_from()
        ev2 = await comm_by_code.receive_json_from()
        ev3 = await comm_staff.receive_json_from()

        self.assertEqual(ev1["to_status"], DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(ev2["to_status"], DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(ev3["to_status"], DonHang.TrangThai.DA_XAC_NHAN)

        await comm_by_id.disconnect()
        await comm_by_code.disconnect()
        await comm_staff.disconnect()

    async def test_05_adversarial_customer_forbidden_transitions(self):
        """
        Scenario 5:
        Customer Bob attempts unauthorized order transitions:
        - Cross-tenant: Bob attempts to transition Alice's order -> 404 (queryset tenant isolation).
        - Self-unauthorized: Bob attempts to transition his own order to da_xac_nhan -> 403 Forbidden.
        - Must emit ZERO broadcasts on any WebSocket stream.
        """
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_alice = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok_alice}")
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok_staff}")

        await comm_alice.connect()
        await comm_staff.connect()
        await comm_alice.receive_json_from()
        await comm_staff.receive_json_from()

        # 1. Bob attempts cross-tenant access to Alice's order via numeric ID (Queryset isolation -> 404)
        code_cross_id, _ = await self._customer_patch_status(self.customer_bob, self.order_alice.id, "da_xac_nhan")
        self.assertIn(code_cross_id, [403, 404])

        # 2. Bob attempts cross-tenant access to Alice's order via string order code (Queryset isolation -> 404)
        code_cross_str, _ = await self._customer_patch_status(self.customer_bob, self.order_alice.ma_don_hang, "da_xac_nhan")
        self.assertIn(code_cross_str, [403, 404])

        # 3. Bob attempts unauthorized transition on his OWN order (Role check in DichVuDonHang -> 403)
        code_self, _ = await self._customer_patch_status(self.customer_bob, self.order_bob.id, "da_xac_nhan")
        self.assertEqual(code_self, 403)

        # Verify no broadcast leakage
        alice_silent = await comm_alice.receive_nothing(timeout=0.1)
        staff_silent = await comm_staff.receive_nothing(timeout=0.1)
        self.assertTrue(alice_silent)
        self.assertTrue(staff_silent)

        await comm_alice.disconnect()
        await comm_staff.disconnect()

    async def test_06_adversarial_invalid_lookups_and_illegal_fsm_jumps(self):
        """
        Scenario 6:
        - Non-existent numeric ID -> 404
        - Non-existent string code -> 404
        - Illegal state skip: cho_tiep_nhan -> hoan_tat -> 400
        - Terminal immutability: once hoan_tat, cannot change to da_huy -> 400
        """
        # Non-existent numeric ID
        code_num, _ = await self._staff_patch_status(9999999, "da_xac_nhan")
        self.assertEqual(code_num, 404)

        # Non-existent string code
        code_str, _ = await self._staff_patch_status("DH-DOES-NOT-EXIST-404", "da_xac_nhan")
        self.assertEqual(code_str, 404)

        # Illegal skip: cho_tiep_nhan -> hoan_tat
        code_skip, data_skip = await self._staff_patch_status(self.order_alice.id, "hoan_tat")
        self.assertEqual(code_skip, 400)
        self.assertIn("status", data_skip)

        # Advance to terminal state
        await self._staff_patch_status(self.order_alice.id, "da_xac_nhan")
        await self._staff_patch_status(self.order_alice.id, "dang_che_bien")
        await self._staff_patch_status(self.order_alice.id, "san_sang")
        await self._staff_patch_status(self.order_alice.id, "hoan_tat")

        # Try changing terminal state
        code_term, data_term = await self._staff_patch_status(self.order_alice.ma_don_hang, "da_huy")
        self.assertEqual(code_term, 400)
        self.assertIn("status", data_term)

    async def test_07_adversarial_casing_and_alias_status_handling(self):
        """
        Scenario 7:
        Verify status aliases and cased inputs through string order code:
        - "CONFIRMED" -> "da_xac_nhan"
        - "cooking" -> "dang_che_bien"
        - "Ready" -> "san_sang"
        - "Completed" -> "hoan_tat"
        Broadcast payloads must standardize to canonical Vietnamese keys.
        """
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        comm_alice = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.ma_don_hang}/?token={tok_alice}")
        await comm_alice.connect()
        await comm_alice.receive_json_from()

        alias_sequence = [
            ("CONFIRMED", DonHang.TrangThai.DA_XAC_NHAN),
            ("cooking", DonHang.TrangThai.DANG_CHE_BIEN),
            ("Ready", DonHang.TrangThai.SAN_SANG),
            ("Completed", DonHang.TrangThai.HOAN_TAT),
        ]

        for alias, canonical in alias_sequence:
            code, data = await self._staff_patch_status(self.order_alice.ma_don_hang, alias)
            self.assertEqual(code, 200, f"Alias '{alias}' failed with code {code}: {data}")
            self.assertEqual(data["trang_thai"], canonical)

            ev = await comm_alice.receive_json_from()
            self.assertEqual(ev["to_status"], canonical)
            self.assertEqual(ev["status"], canonical)

            # Drain duplicate frame if delivered
            is_nothing = await comm_alice.receive_nothing(timeout=0.05)
            if not is_nothing:
                dup_ev = await comm_alice.receive_json_from()
                self.assertEqual(dup_ev["to_status"], canonical)

        await comm_alice.disconnect()


if __name__ == "__main__":
    os.environ["TESTING"] = "1"
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_adversarial_challenger_m5_r2_fsm_realtime"])
    sys.exit(bool(failures))
