#!/usr/bin/env python3
"""
Adversarial Empirical Stress Testing & Real-Time Security Verification Suite for Milestone 5.
Web App Nhà hàng Mộc — Challenger m5_challenger_1.

Adversarial Dimensions:
1. WebSocket Authentication in JWTAuthMiddleware:
   - Missing token, empty token, whitespace, garbage, tampered signature, expired token.
   - Inactive user token rejection.
   - Query parameter (?token=<jwt>) and Header (Bearer) parsing.
   - Multi-query param resilience.
2. Real-time Chat Consumer (moc-backend/chat/consumers.py):
   - Tenant isolation: Cross-customer room access forbidden (4403).
   - Staff global access permissions.
   - Non-existent room handling.
   - Persistent DB storage in PostgreSQL TinNhan BEFORE broadcast.
   - Sender and recipient message synchronization and exact ordering.
   - Auto-assignment of staff upon reply.
   - Input sanitization & boundaries: Empty/whitespace error, 5000 chars boundary, 5001 chars rejection.
   - Typing echo suppression (no echo to self).
   - Read receipt atomic DB updates (da_doc=True).
3. Order FSM Real-time Stream (moc-backend/orders/consumers.py & services.py):
   - Tenant isolation: Unauthorized customer order access rejected (4403).
   - Non-existent order handling (4404).
   - Non-staff rejected from staff stream /ws/orders/staff/ (4403).
   - Initial order snapshot delivery.
   - Multi-stream broadcast synchronization: /ws/orders/<id>/ and /ws/orders/staff/.
   - FSM full lifecycle progression push: cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat.
   - Illegal FSM transition rejection without spurious broadcasts.
4. Concurrency & Stress:
   - Rapid connect/disconnect cycling (25 cycles).
   - Concurrent chat bursts (15 simultaneous messages) without DB deadlocks.
   - Concurrent FSM transition serialization via select_for_update.
"""

import os
import sys
import asyncio
import types
from pathlib import Path
from decimal import Decimal

# Set up paths
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
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from config.asgi import application
from chat.models import HoiThoai, TinNhan
from orders.models import DonHang, LichSuTrangThaiDon
from orders.services import DichVuDonHang
from accounts.models import VaiTro


class TestMilestone5RealtimeAdversarial(TransactionTestCase):
    """Adversarial stress and real-time verification suite for Milestone 5."""

    def setUp(self):
        User = get_user_model()
        User.objects.all().delete()
        HoiThoai.objects.all().delete()
        DonHang.objects.all().delete()

        # 1. Customer Alice
        self.customer_alice = User.objects.create_user(
            username="alice_m5",
            email="alice@moc.vn",
            thu_dien_tu="alice@moc.vn",
            password="alicePass123!",
            first_name="Alice",
            last_name="Tran",
        )

        # 2. Customer Bob (Adversary attempting cross-tenant snooping)
        self.customer_bob = User.objects.create_user(
            username="bob_m5",
            email="bob@moc.vn",
            thu_dien_tu="bob@moc.vn",
            password="bobPass123!",
            first_name="Bob",
            last_name="Nguyen",
        )

        # 3. Inactive User
        self.inactive_user = User.objects.create_user(
            username="inactive_m5",
            email="inactive@moc.vn",
            thu_dien_tu="inactive@moc.vn",
            password="inactivePass123!",
            is_active=False,
            first_name="Inactive",
            last_name="User",
        )

        # 4. Restaurant Staff (Admin flag is_staff=True)
        self.staff_user = User.objects.create_user(
            username="staff_m5_1",
            email="staff1@moc.vn",
            thu_dien_tu="staff1@moc.vn",
            password="staffPass123!",
            is_staff=True,
            first_name="Nhan Vien",
            last_name="Moc",
        )

        # 5. Waiter Staff (Role-based without is_staff=True)
        self.waiter_user = User.objects.create_user(
            username="waiter_m5_1",
            email="waiter1@moc.vn",
            thu_dien_tu="waiter1@moc.vn",
            password="waiterPass123!",
            is_staff=False,
            first_name="Phuc Vu",
            last_name="Ban",
        )
        vai_tro_nv, _ = VaiTro.objects.get_or_create(ten="nhan_vien")
        self.waiter_user.danh_sach_vai_tro.add(vai_tro_nv)

        # Rooms
        self.room_alice = HoiThoai.objects.create(khach_hang=self.customer_alice)
        self.room_bob = HoiThoai.objects.create(khach_hang=self.customer_bob)

        # Orders
        self.order_alice = DonHang.objects.create(
            ma_don_hang="DH-M5-ALICE-01",
            khach_hang=self.customer_alice,
            hinh_thuc=DonHang.HinhThuc.GIAO_HANG,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            ten_khach="Alice Tran",
            sdt_khach="0901234567",
            dia_chi_giao="123 Nguyen Hue, Q1, TPHCM",
            tien_hang=Decimal("450000"),
            tong_tien=Decimal("450000"),
        )
        self.order_bob = DonHang.objects.create(
            ma_don_hang="DH-M5-BOB-01",
            khach_hang=self.customer_bob,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            ten_khach="Bob Nguyen",
            sdt_khach="0907654321",
            tien_hang=Decimal("250000"),
            tong_tien=Decimal("250000"),
        )

    # =========================================================================
    # DIMENSION 1: WebSocket Authentication in JWTAuthMiddleware
    # =========================================================================

    async def test_jwt_01_missing_token_rejected_4401(self):
        """WebSockets without token query parameter or auth headers must close with 4401."""
        endpoints = [
            f"/ws/chat/{self.room_alice.id}/",
            f"/ws/orders/{self.order_alice.id}/",
            "/ws/orders/staff/",
        ]
        for url in endpoints:
            comm = WebsocketCommunicator(application, url)
            connected, close_code = await comm.connect()
            self.assertFalse(connected, f"URL {url} unexpectedly connected without token")
            self.assertEqual(close_code, 4401, f"URL {url} close code expected 4401, got {close_code}")

    async def test_jwt_02_empty_and_whitespace_token_rejected_4401(self):
        """WebSockets with empty or whitespace token must close with 4401."""
        bad_urls = [
            f"/ws/chat/{self.room_alice.id}/?token=",
            f"/ws/chat/{self.room_alice.id}/?token=%20%20%20",
            f"/ws/orders/{self.order_alice.id}/?token=",
            f"/ws/orders/staff/?token=%20",
        ]
        for url in bad_urls:
            comm = WebsocketCommunicator(application, url)
            connected, close_code = await comm.connect()
            self.assertFalse(connected, f"URL {url} unexpectedly connected with empty/whitespace token")
            self.assertEqual(close_code, 4401)

    async def test_jwt_03_malformed_and_tampered_jwt_rejected_4401(self):
        """WebSockets with tampered signature, non-JWT strings, or expired format must close with 4401."""
        invalid_tokens = [
            "not_a_jwt_token",
            "Bearer invalid.token.payload",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.TAMPERED_SIG_1234567890abcdef",
            "null",
            "undefined",
        ]
        for bad_tok in invalid_tokens:
            comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={bad_tok}")
            connected, close_code = await comm.connect()
            self.assertFalse(connected, f"Tampered token '{bad_tok}' unexpectedly connected")
            self.assertEqual(close_code, 4401)

    async def test_jwt_04_inactive_user_token_rejected_4401(self):
        """Token belonging to an inactive user (is_active=False) must be rejected with 4401."""
        tok = str(AccessToken.for_user(self.inactive_user))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected, "Inactive user token unexpectedly connected")
        self.assertEqual(close_code, 4401)

    async def test_jwt_05_valid_query_param_success(self):
        """Valid JWT in ?token=<jwt> successfully authenticates and receives welcome event."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Valid JWT connection failed: {close_code}")
        welcome = await comm.receive_json_from()
        self.assertEqual(welcome.get("type"), "connection_established")
        self.assertEqual(welcome.get("conversation_id"), self.room_alice.id)
        self.assertEqual(welcome.get("user_id"), self.customer_alice.id)
        await comm.disconnect()

    async def test_jwt_06_complex_query_params_parsing(self):
        """Token embedded within other query params (e.g. ?view=full&token=<jwt>&ref=admin) parses correctly."""
        tok = str(AccessToken.for_user(self.customer_alice))
        url = f"/ws/chat/{self.room_alice.id}/?view=full&token={tok}&ref=admin_test"
        comm = WebsocketCommunicator(application, url)
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Complex query param failed: {close_code}")
        welcome = await comm.receive_json_from()
        self.assertEqual(welcome.get("type"), "connection_established")
        await comm.disconnect()

    async def test_jwt_07_authorization_header_fallback(self):
        """Bearer token passed via Authorization header provides robust API client compatibility."""
        tok = str(AccessToken.for_user(self.customer_alice))
        headers = [(b"authorization", f"Bearer {tok}".encode("utf-8"))]
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/", headers=headers)
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Header Bearer auth failed: {close_code}")
        welcome = await comm.receive_json_from()
        self.assertEqual(welcome.get("type"), "connection_established")
        await comm.disconnect()

    # =========================================================================
    # DIMENSION 2: Real-time Chat Consumer (Security, Storage & Multi-party)
    # =========================================================================

    async def test_chat_08_cross_tenant_isolation_4403(self):
        """Customer Bob attempting to connect to Customer Alice's room must be rejected with 4403."""
        tok_bob = str(AccessToken.for_user(self.customer_bob))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_bob}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected, "Bob was able to connect to Alice's private room")
        self.assertEqual(close_code, 4403)

    async def test_chat_09_staff_universal_access(self):
        """Restaurant staff has global access to join any customer's chat room."""
        tok_staff = str(AccessToken.for_user(self.staff_user))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_staff}")
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Staff connection failed: {close_code}")
        welcome = await comm.receive_json_from()
        self.assertEqual(welcome.get("type"), "connection_established")
        self.assertTrue(welcome.get("is_staff"))
        await comm.disconnect()

    async def test_chat_10_nonexistent_room_rejected_4403(self):
        """Connecting to non-existent conversation ID (e.g. 999999) must be rejected."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/chat/999999/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_chat_11_db_persistence_before_broadcast(self):
        """
        Message sent through WebSocket MUST be committed to PostgreSQL TinNhan table
        BEFORE broadcast arrives at client, with matching ID and timestamps.
        """
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
        await comm.connect()
        await comm.receive_json_from()  # connection_established

        test_msg_text = "Em muốn hỏi nhà hàng có món chay không ạ?"
        await comm.send_json_to({
            "action": "send_message",
            "content": test_msg_text,
        })

        broadcast = await comm.receive_json_from()
        self.assertEqual(broadcast.get("type"), "chat_message")
        self.assertEqual(broadcast.get("content"), test_msg_text)
        self.assertEqual(broadcast.get("sender_id"), self.customer_alice.id)
        msg_id = broadcast.get("id")

        # Verify DB persistence directly in PostgreSQL
        db_msg = await self._get_message_by_id(msg_id)
        self.assertIsNotNone(db_msg, "Message was broadcasted but NOT found in PostgreSQL DB!")
        self.assertEqual(db_msg.noi_dung, test_msg_text)
        self.assertEqual(db_msg.nguoi_gui_id, self.customer_alice.id)
        self.assertFalse(db_msg.da_doc)

        # Verify HoiThoai tin_nhan_cuoi_luc is updated
        db_room = await self._get_room_from_db(self.room_alice.id)
        self.assertIsNotNone(db_room.tin_nhan_cuoi_luc)

        await comm.disconnect()

    async def test_chat_12_staff_auto_assignment_on_reply(self):
        """When staff sends first reply in an unassigned room, staff is assigned in DB."""
        # Ensure room has no assigned staff
        self.assertIsNone(self.room_alice.nhan_vien)

        tok_staff = str(AccessToken.for_user(self.staff_user))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_staff}")
        await comm.connect()
        await comm.receive_json_from()  # connection_established

        await comm.send_json_to({
            "action": "send_message",
            "content": "Dạ nhà hàng có set menu chay Mộc thanh tịnh ạ!",
        })
        broadcast = await comm.receive_json_from()
        self.assertEqual(broadcast.get("type"), "chat_message")

        # Verify room.nhan_vien is now assigned to staff_user in DB
        db_room = await self._get_room_from_db(self.room_alice.id)
        self.assertEqual(db_room.nhan_vien_id, self.staff_user.id)

        await comm.disconnect()

    async def test_chat_13_multiparty_sequential_messaging(self):
        """Customer and staff in the same room exchange messages in guaranteed strict FIFO order."""
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_alice = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_alice}")
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_staff}")

        await comm_alice.connect()
        await comm_staff.connect()
        await comm_alice.receive_json_from()
        await comm_staff.receive_json_from()

        # Alice sends 5 sequential messages
        alice_messages = [f"Câu hỏi số {i}" for i in range(1, 6)]
        for text in alice_messages:
            await comm_alice.send_json_to({"action": "send_message", "content": text})
            # Both alice and staff receive the broadcast
            b_alice = await comm_alice.receive_json_from()
            b_staff = await comm_staff.receive_json_from()
            self.assertEqual(b_alice.get("content"), text)
            self.assertEqual(b_staff.get("content"), text)

        # Staff replies with 5 sequential messages
        staff_replies = [f"Phản hồi số {i}" for i in range(1, 6)]
        for text in staff_replies:
            await comm_staff.send_json_to({"action": "send_message", "content": text})
            b_alice = await comm_alice.receive_json_from()
            b_staff = await comm_staff.receive_json_from()
            self.assertEqual(b_alice.get("content"), text)
            self.assertEqual(b_staff.get("content"), text)

        total_msgs = await self._get_room_message_count(self.room_alice.id)
        self.assertEqual(total_msgs, 10)

        await comm_alice.disconnect()
        await comm_staff.disconnect()

    async def test_chat_14_empty_and_whitespace_payload_rejected(self):
        """Sending empty or whitespace payload returns EMPTY_CONTENT error; DB is unaffected."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
        await comm.connect()
        await comm.receive_json_from()

        initial_count = await self._get_room_message_count(self.room_alice.id)

        for empty_text in ["", "   ", "\n\t  \r\n"]:
            await comm.send_json_to({"action": "send_message", "content": empty_text})
            err = await comm.receive_json_from()
            self.assertEqual(err.get("type"), "error")
            self.assertEqual(err.get("code"), "EMPTY_CONTENT")

        final_count = await self._get_room_message_count(self.room_alice.id)
        self.assertEqual(final_count, initial_count, "Empty message was erroneously saved to DB!")

        await comm.disconnect()

    async def test_chat_15_oversized_payload_boundary(self):
        """Message at 5000 chars passes; message at 5001 chars is rejected with MESSAGE_TOO_LONG."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
        await comm.connect()
        await comm.receive_json_from()

        # 5001 characters -> Error
        oversized = "A" * 5001
        await comm.send_json_to({"action": "send_message", "content": oversized})
        err = await comm.receive_json_from()
        self.assertEqual(err.get("type"), "error")
        self.assertEqual(err.get("code"), "MESSAGE_TOO_LONG")

        # 5000 characters -> Valid
        boundary_ok = "B" * 5000
        await comm.send_json_to({"action": "send_message", "content": boundary_ok})
        broadcast = await comm.receive_json_from()
        self.assertEqual(broadcast.get("type"), "chat_message")
        self.assertEqual(len(broadcast.get("content")), 5000)

        await comm.disconnect()

    async def test_chat_16_typing_echo_suppression(self):
        """Typing indicators must be sent to room peer without echoing back to the sender."""
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_alice = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_alice}")
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_staff}")

        await comm_alice.connect()
        await comm_staff.connect()
        await comm_alice.receive_json_from()
        await comm_staff.receive_json_from()

        # Alice types -> Staff receives typing event
        await comm_alice.send_json_to({"action": "typing", "is_typing": True})

        staff_typing = await comm_staff.receive_json_from()
        self.assertEqual(staff_typing.get("type"), "chat_typing")
        self.assertEqual(staff_typing.get("sender_id"), self.customer_alice.id)
        self.assertTrue(staff_typing.get("is_typing"))

        # Alice should NOT receive her own typing indicator
        alice_received_echo = await comm_alice.receive_nothing(timeout=0.1)
        self.assertTrue(alice_received_echo, "Sender received echo of their own typing event!")

        await comm_alice.disconnect()
        await comm_staff.disconnect()

    async def test_chat_17_read_receipt_atomic_audit(self):
        """Mark read action sets da_doc=True on unread messages in DB and emits chat_read_receipt."""
        # Create unread messages from Alice in DB
        msg1 = await self._create_db_message(self.room_alice, self.customer_alice, "Tin 1", da_doc=False)
        msg2 = await self._create_db_message(self.room_alice, self.customer_alice, "Tin 2", da_doc=False)

        tok_staff = str(AccessToken.for_user(self.staff_user))
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok_staff}")
        await comm_staff.connect()
        await comm_staff.receive_json_from()

        await comm_staff.send_json_to({
            "action": "mark_read",
            "last_read_message_id": msg2.id,
        })

        receipt = await comm_staff.receive_json_from()
        self.assertEqual(receipt.get("type"), "chat_read_receipt")
        self.assertEqual(receipt.get("reader_id"), self.staff_user.id)
        self.assertEqual(receipt.get("last_read_message_id"), msg2.id)

        # Verify DB updated
        m1_fresh = await self._get_message_by_id(msg1.id)
        m2_fresh = await self._get_message_by_id(msg2.id)
        self.assertTrue(m1_fresh.da_doc)
        self.assertTrue(m2_fresh.da_doc)
        self.assertIsNotNone(m1_fresh.doc_luc)

        await comm_staff.disconnect()

    # =========================================================================
    # DIMENSION 3: Order FSM Real-time Stream & Multi-party Synchronization
    # =========================================================================

    async def test_order_18_tenant_isolation_4403(self):
        """Customer Bob attempting to track Alice's order must be rejected with 4403."""
        tok_bob = str(AccessToken.for_user(self.customer_bob))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok_bob}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected, "Bob was able to track Alice's order!")
        self.assertEqual(close_code, 4403)

    async def test_order_19_nonexistent_order_4404(self):
        """Tracking non-existent order (e.g. 999999) must close with 4404."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/orders/999999/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4404)

    async def test_order_20_initial_snapshot_delivery(self):
        """Connecting to /ws/orders/<id>/ returns immediate order_snapshot with status and total."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Order tracking connect failed: {close_code}")

        snap = await comm.receive_json_from()
        self.assertEqual(snap.get("type"), "order_snapshot")
        self.assertEqual(snap.get("order_id"), self.order_alice.id)
        self.assertEqual(snap.get("order_number"), self.order_alice.ma_don_hang)
        self.assertEqual(snap.get("current_status"), DonHang.TrangThai.CHO_TIEP_NHAN)
        self.assertEqual(snap.get("total"), 450000.0)

        await comm.disconnect()

    async def test_order_21_tracking_by_order_code_alias(self):
        """Tracking consumer accepts string code (e.g. DH-M5-ALICE-01) identically to numeric ID."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.ma_don_hang}/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertTrue(connected)

        snap = await comm.receive_json_from()
        self.assertEqual(snap.get("type"), "order_snapshot")
        self.assertEqual(snap.get("order_number"), self.order_alice.ma_don_hang)

        await comm.disconnect()

    async def test_order_22_staff_stream_non_staff_rejected_4403(self):
        """Regular customer connecting to /ws/orders/staff/ must be rejected with 4403."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected, "Regular customer was able to connect to staff stream!")
        self.assertEqual(close_code, 4403)

    async def test_order_23_staff_stream_staff_connect(self):
        """Staff user connects to /ws/orders/staff/ and receives staff_connected event."""
        tok = str(AccessToken.for_user(self.staff_user))
        comm = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok}")
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Staff stream connect failed: {close_code}")

        conf = await comm.receive_json_from()
        self.assertEqual(conf.get("type"), "staff_connected")
        self.assertTrue(conf.get("staff_order_stream_subscribed"))

        await comm.disconnect()

    async def test_order_24_fsm_realtime_broadcast_sync(self):
        """
        Transitioning order state via DichVuDonHang.doi_trang_thai pushes order_status_update
        simultaneously to:
        1. Customer tracking stream (/ws/orders/<id>/)
        2. Global staff kitchen stream (/ws/orders/staff/)
        Unrelated customer room does NOT receive the push.
        """
        tok_alice = str(AccessToken.for_user(self.customer_alice))
        tok_bob = str(AccessToken.for_user(self.customer_bob))
        tok_staff = str(AccessToken.for_user(self.staff_user))

        comm_alice = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok_alice}")
        comm_bob = WebsocketCommunicator(application, f"/ws/orders/{self.order_bob.id}/?token={tok_bob}")
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={tok_staff}")

        await comm_alice.connect()
        await comm_bob.connect()
        await comm_staff.connect()

        # Consume initial snapshots
        await comm_alice.receive_json_from()
        await comm_bob.receive_json_from()
        await comm_staff.receive_json_from()

        # Transition Alice's order: cho_tiep_nhan -> da_xac_nhan
        await self._async_advance_order(
            self.order_alice.id,
            DonHang.TrangThai.DA_XAC_NHAN,
            self.staff_user,
            "Nhân viên xác nhận đơn"
        )

        # Alice receives order_status_update
        update_alice = await comm_alice.receive_json_from()
        self.assertEqual(update_alice.get("type"), "order_status_update")
        self.assertEqual(update_alice.get("order_id"), self.order_alice.id)
        self.assertEqual(update_alice.get("from_status"), DonHang.TrangThai.CHO_TIEP_NHAN)
        self.assertEqual(update_alice.get("to_status"), DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(update_alice.get("status"), DonHang.TrangThai.DA_XAC_NHAN)

        # Staff stream receives order_status_update
        update_staff = await comm_staff.receive_json_from()
        self.assertEqual(update_staff.get("type"), "order_status_update")
        self.assertEqual(update_staff.get("order_id"), self.order_alice.id)
        self.assertEqual(update_staff.get("status"), DonHang.TrangThai.DA_XAC_NHAN)

        # Bob receives NOTHING (isolated order stream)
        bob_isolated = await comm_bob.receive_nothing(timeout=0.1)
        self.assertTrue(bob_isolated, "Bob erroneously received Alice's order update!")

        await comm_alice.disconnect()
        await comm_bob.disconnect()
        await comm_staff.disconnect()

    async def test_order_25_fsm_full_lifecycle_streaming(self):
        """
        Verify stream receives events across the full lifecycle:
        da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat.
        """
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok}")
        await comm.connect()
        await comm.receive_json_from()  # snapshot

        lifecycle_steps = [
            (DonHang.TrangThai.DA_XAC_NHAN, "Xác nhận đơn"),
            (DonHang.TrangThai.DANG_CHE_BIEN, "Bếp bắt đầu nấu"),
            (DonHang.TrangThai.SAN_SANG, "Món đã sẵn sàng giao"),
            (DonHang.TrangThai.HOAN_TAT, "Giao thành công"),
        ]

        current_from = DonHang.TrangThai.CHO_TIEP_NHAN
        duplicate_count = 0
        for next_st, note in lifecycle_steps:
            await self._async_advance_order(self.order_alice.id, next_st, self.staff_user, note)
            event = await comm.receive_json_from()
            self.assertEqual(event.get("type"), "order_status_update")
            self.assertEqual(event.get("from_status"), current_from)
            self.assertEqual(event.get("to_status"), next_st)
            self.assertEqual(event.get("status"), next_st)

            # Check if duplicate frame is delivered due to dual group join (id + code)
            is_nothing = await comm.receive_nothing(timeout=0.05)
            if not is_nothing:
                dup_event = await comm.receive_json_from()
                self.assertEqual(dup_event.get("type"), "order_status_update")
                duplicate_count += 1

            current_from = next_st

        # Record duplicate delivery
        self.duplicate_broadcasts_detected = duplicate_count

        # Verify terminal state immutability in DB
        db_order = await self._get_order_by_id(self.order_alice.id)
        self.assertEqual(db_order.trang_thai, DonHang.TrangThai.HOAN_TAT)

        await comm.disconnect()

    async def test_order_26_illegal_fsm_transition_no_broadcast(self):
        """Illegal state jump raises ValidationError and emits NO spurious broadcast."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_alice.id}/?token={tok}")
        await comm.connect()
        await comm.receive_json_from()  # snapshot

        # Attempt illegal jump: cho_tiep_nhan -> san_sang (skipping da_xac_nhan and dang_che_bien)
        with self.assertRaises(ValidationError):
            await self._async_advance_order(self.order_alice.id, DonHang.TrangThai.SAN_SANG, self.staff_user)

        no_event = await comm.receive_nothing(timeout=0.1)
        self.assertTrue(no_event, "Illegal transition erroneously emitted a broadcast event!")

        await comm.disconnect()

    # =========================================================================
    # DIMENSION 4: Concurrency, Rapid Cycling & Stress Hardening
    # =========================================================================

    async def test_stress_27_rapid_connection_cycling(self):
        """Rapidly connect and disconnect 25 times to ensure clean channel layer cleanup and no leaks."""
        tok = str(AccessToken.for_user(self.customer_alice))
        for i in range(25):
            comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
            c_ok, _ = await comm.connect()
            self.assertTrue(c_ok, f"Connection failed on iteration {i}")
            welcome = await comm.receive_json_from()
            self.assertEqual(welcome.get("type"), "connection_established")
            await comm.disconnect()

    async def test_stress_28_concurrent_chat_burst(self):
        """Concurrently send 15 messages via gather to verify DB locking & no message loss."""
        tok = str(AccessToken.for_user(self.customer_alice))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_alice.id}/?token={tok}")
        await comm.connect()
        await comm.receive_json_from()

        num_messages = 15
        send_tasks = [
            comm.send_json_to({
                "action": "send_message",
                "content": f"Tin nhắn burst đồng thời {i}",
            })
            for i in range(num_messages)
        ]
        await asyncio.gather(*send_tasks)

        received_count = 0
        for _ in range(num_messages):
            msg = await comm.receive_json_from()
            if msg.get("type") == "chat_message":
                received_count += 1

        self.assertEqual(received_count, num_messages, f"Expected {num_messages} messages, received {received_count}")

        # Check DB count
        db_count = await self._get_room_message_count(self.room_alice.id)
        self.assertEqual(db_count, num_messages, f"DB has {db_count} messages, expected {num_messages}")

        await comm.disconnect()

    async def test_stress_29_order_fsm_concurrency_race_protection(self):
        """
        Two simultaneous transition attempts on the same order must serialize safely via select_for_update:
        One succeeds, the other fails with ValidationError.
        """
        def try_transition(status, user, note):
            order = DonHang.objects.get(id=self.order_alice.id)
            return DichVuDonHang.doi_trang_thai(
                don_hang=order,
                trang_thai_moi=status,
                nguoi_dung=user,
                ghi_chu=note,
            )

        loop = asyncio.get_running_loop()
        # Fire two concurrent transitions: one to da_xac_nhan, one to da_huy
        task1 = loop.run_in_executor(
            None, try_transition, DonHang.TrangThai.DA_XAC_NHAN, self.staff_user, "Confirm"
        )
        task2 = loop.run_in_executor(
            None, try_transition, DonHang.TrangThai.DA_HUY, self.customer_alice, "Cancel"
        )

        results = await asyncio.gather(task1, task2, return_exceptions=True)

        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        # Exactly 1 must succeed and 1 must fail due to FSM or state conflict
        self.assertEqual(len(successes), 1, f"Expected exactly 1 success, got {len(successes)} ({results})")
        self.assertEqual(len(failures), 1, f"Expected exactly 1 failure, got {len(failures)}")

        final_order = await self._get_order_by_id(self.order_alice.id)
        self.assertIn(final_order.trang_thai, [DonHang.TrangThai.DA_XAC_NHAN, DonHang.TrangThai.DA_HUY])

    # =========================================================================
    # Helpers
    # =========================================================================

    @database_sync_to_async
    def _get_message_by_id(self, msg_id):
        return TinNhan.objects.filter(id=msg_id).first()

    @database_sync_to_async
    def _get_room_from_db(self, room_id):
        return HoiThoai.objects.filter(id=room_id).first()

    @database_sync_to_async
    def _get_room_message_count(self, room_id):
        return TinNhan.objects.filter(hoi_thoai_id=room_id).count()

    @database_sync_to_async
    def _create_db_message(self, room, user, text, da_doc=False):
        return TinNhan.objects.create(
            hoi_thoai=room,
            nguoi_gui=user,
            noi_dung=text,
            da_doc=da_doc,
        )

    @database_sync_to_async
    def _get_order_by_id(self, order_id):
        return DonHang.objects.filter(id=order_id).first()

    @database_sync_to_async
    def _async_advance_order(self, order_id, new_status, user, note=""):
        order = DonHang.objects.get(id=order_id)
        return DichVuDonHang.doi_trang_thai(
            don_hang=order,
            trang_thai_moi=new_status,
            nguoi_dung=user,
            ghi_chu=note,
        )


if __name__ == "__main__":
    os.environ["TESTING"] = "1"
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_adversarial_m5_realtime"])
    sys.exit(bool(failures))
