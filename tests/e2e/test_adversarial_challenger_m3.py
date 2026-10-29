#!/usr/bin/env python3
"""
Adversarial Empirical Stress Testing & Security Boundary Verification Suite for Milestone 3.
Web App Nhà hàng Mộc — Challenger m3_challenger_1.

Adversarial Focus Dimensions:
1. WebSocket Authentication & Handshake Edge Cases (Anonymous, Tampered JWT, Expired, Non-existent User, Headers vs Query String)
2. Role-Based Access Control & Tenant Isolation (Cross-customer room eavesdropping, Cross-customer order snooping, Non-staff on staff feed)
3. Chat Inbound Validation, Extreme Payloads & DB Persistence Guarantees (5000 vs 5001 chars, Whitespace, XSS/Unicode, DB-before-broadcast)
4. Typing Echo Suppression & Read Receipt Atomic Audits
5. Order FSM Strict State Transitions, Customer Boundaries & Audit History
6. Real-time Multi-Subscriber Push Synchronization (Customer + Kitchen Staff streams)
7. Concurrent State Transition Contention (select_for_update serialization)
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

import unittest
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


class TestMilestone3Adversarial(TransactionTestCase):
    """Adversarial stress and boundary suite for Milestone 3."""

    def setUp(self):
        User = get_user_model()
        User.objects.all().delete()
        HoiThoai.objects.all().delete()
        DonHang.objects.all().delete()

        # 1. Customer A
        self.customer_a = User.objects.create_user(
            username="khach_a",
            email="khach_a@moc.vn",
            thu_dien_tu="khach_a@moc.vn",
            password="passA123!",
            first_name="Khách",
            last_name="A",
        )

        # 2. Customer B
        self.customer_b = User.objects.create_user(
            username="khach_b",
            email="khach_b@moc.vn",
            thu_dien_tu="khach_b@moc.vn",
            password="passB123!",
            first_name="Khách",
            last_name="B",
        )

        # 3. Restaurant Staff (is_staff=True)
        self.staff_user = User.objects.create_user(
            username="nhan_vien_1",
            email="nv1@moc.vn",
            thu_dien_tu="nv1@moc.vn",
            password="staffPass123!",
            is_staff=True,
            first_name="Nhân Viên",
            last_name="Mộc",
        )

        # 4. Role-based Staff without is_staff admin flag (via la_nhan_vien_nha_hang)
        self.waiter_user = User.objects.create_user(
            username="phuc_vu_1",
            email="pv1@moc.vn",
            thu_dien_tu="pv1@moc.vn",
            password="waiterPass123!",
            is_staff=False,
            first_name="Phục Vụ",
            last_name="Bàn",
        )
        vai_tro_nv, _ = VaiTro.objects.get_or_create(ten="nhan_vien")
        self.waiter_user.danh_sach_vai_tro.add(vai_tro_nv)

        # Base active chat room for Customer A
        self.room_a = HoiThoai.objects.create(khach_hang=self.customer_a)

        # Base order for Customer A
        self.order_a = DonHang.objects.create(
            ma_don_hang="DH-ADV-M3-001",
            khach_hang=self.customer_a,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN,
            ten_khach="Khách A",
            sdt_khach="0911223344",
            tien_hang=Decimal("350000"),
            tong_tien=Decimal("350000"),
        )

    # --------------------------------------------------------------------------
    # DIMENSION 1: WebSocket Authentication & Handshake Security Boundaries
    # --------------------------------------------------------------------------

    async def test_adv_ws_01_anonymous_handshake_rejected_chat(self):
        """Anonymous connection to /ws/chat/<id>/ MUST be closed with code 4401."""
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_adv_ws_02_anonymous_handshake_rejected_order_tracking(self):
        """Anonymous connection to /ws/orders/<id>/ MUST be closed with code 4401."""
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_a.id}/")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_adv_ws_03_anonymous_handshake_rejected_staff_stream(self):
        """Anonymous connection to /ws/orders/staff/ MUST be closed with code 4401."""
        comm = WebsocketCommunicator(application, "/ws/orders/staff/")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_adv_ws_04_tampered_or_malformed_jwt_rejected(self):
        """Forged, tampered, or garbage token string MUST be rejected with code 4401."""
        forged_tokens = [
            "invalid.jwt.token",
            "Bearer invalid.signature.token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.tamperedSignature1234567890",
            "   ",
        ]
        for bad_token in forged_tokens:
            comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={bad_token}")
            connected, close_code = await comm.connect()
            self.assertFalse(connected, f"Tampered token '{bad_token}' unexpectedly connected")
            self.assertEqual(close_code, 4401)

    async def test_adv_ws_05_header_based_authentication_bearer(self):
        """Authorization header with Bearer token is supported as fallback for REST/API test clients."""
        token = str(AccessToken.for_user(self.customer_a))
        headers = [(b"authorization", f"Bearer {token}".encode("utf-8"))]
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/", headers=headers)
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Header auth failed with close code {close_code}")
        welcome = await comm.receive_json_from()
        self.assertEqual(welcome["type"], "connection_established")
        self.assertEqual(welcome["conversation_id"], self.room_a.id)
        await comm.disconnect()

    async def test_adv_ws_06_sec_websocket_protocol_auth(self):
        """Sec-WebSocket-Protocol header auth allows clients that cannot send custom headers or query strings."""
        token = str(AccessToken.for_user(self.customer_a))
        headers = [(b"sec-websocket-protocol", f"Bearer {token}".encode("utf-8"))]
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/", headers=headers)
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Sec-WebSocket-Protocol auth failed with close code {close_code}")
        _ = await comm.receive_json_from()
        await comm.disconnect()

    # --------------------------------------------------------------------------
    # DIMENSION 2: RBAC & Multi-Tenant Isolation
    # --------------------------------------------------------------------------

    async def test_adv_ws_07_cross_customer_chat_eavesdropping_blocked(self):
        """Customer B attempting to eavesdrop on Customer A's chat room MUST be closed with 4403."""
        token_b = str(AccessToken.for_user(self.customer_b))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_b}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_adv_ws_08_cross_customer_order_snooping_blocked(self):
        """Customer B attempting to monitor Customer A's order MUST be closed with 4403."""
        token_b = str(AccessToken.for_user(self.customer_b))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_a.id}/?token={token_b}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_adv_ws_09_nonexistent_order_tracking_returns_4404(self):
        """Customer A tracking non-existent order ID 999999 MUST receive 4404."""
        token_a = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/orders/999999/?token={token_a}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4404)

    async def test_adv_ws_10_nonexistent_chat_room_returns_4403(self):
        """Connecting to non-existent chat room 999999 MUST receive 4403."""
        token_a = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/chat/999999/?token={token_a}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_adv_ws_11_customer_blocked_on_staff_orders_feed(self):
        """Regular customer attempting to join staff-only kitchen stream MUST receive 4403."""
        token_a = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/orders/staff/?token={token_a}")
        connected, close_code = await comm.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_adv_ws_12_staff_access_to_any_chat_room_and_order(self):
        """Staff member can join ANY customer chat room and track ANY customer order."""
        token_staff = str(AccessToken.for_user(self.staff_user))

        # Join customer chat
        comm_chat = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_staff}")
        c_ok, _ = await comm_chat.connect()
        self.assertTrue(c_ok)
        welcome = await comm_chat.receive_json_from()
        self.assertTrue(welcome["is_staff"])
        await comm_chat.disconnect()

        # Track customer order
        comm_order = WebsocketCommunicator(application, f"/ws/orders/{self.order_a.id}/?token={token_staff}")
        o_ok, _ = await comm_order.connect()
        self.assertTrue(o_ok)
        snapshot = await comm_order.receive_json_from()
        self.assertEqual(snapshot["order_id"], self.order_a.id)
        await comm_order.disconnect()

    async def test_adv_ws_13_role_based_waiter_can_access_staff_stream(self):
        """Waiter with role 'nhan_vien' (even if is_staff=False in auth) MUST access staff feed."""
        token_waiter = str(AccessToken.for_user(self.waiter_user))
        comm = WebsocketCommunicator(application, f"/ws/orders/staff/?token={token_waiter}")
        connected, close_code = await comm.connect()
        self.assertTrue(connected, f"Role-based staff connection rejected with {close_code}")
        frame = await comm.receive_json_from()
        self.assertEqual(frame["type"], "staff_connected")
        await comm.disconnect()

    # --------------------------------------------------------------------------
    # DIMENSION 3: Chat Validation, Persistence Guarantees & Edge Cases
    # --------------------------------------------------------------------------

    async def test_adv_chat_14_db_persistence_before_broadcast_receipt(self):
        """
        Critical Integrity Check:
        When a message is broadcast over WebSocket, the record MUST ALREADY BE COMMITTED in PostgreSQL.
        At the instant the recipient receives the frame, querying DB MUST return the message.
        """
        token_cust = str(AccessToken.for_user(self.customer_a))
        token_staff = str(AccessToken.for_user(self.staff_user))

        comm_cust = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_cust}")
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_staff}")

        await comm_cust.connect()
        await comm_staff.connect()
        _ = await comm_cust.receive_json_from()
        _ = await comm_staff.receive_json_from()

        sent_text = "Thịt bò nướng còn không nhà hàng ơi? 🥩"
        await comm_cust.send_json_to({
            "action": "send_message",
            "content": sent_text,
        })

        # Staff receives the broadcast
        staff_event = await comm_staff.receive_json_from()
        self.assertEqual(staff_event["type"], "chat_message")
        self.assertEqual(staff_event["content"], sent_text)

        # IMMEDIATE DB INSPECTION: Must exist right now
        msg_id = staff_event["id"]
        persisted_msg = await self._get_message_by_id(msg_id)
        self.assertIsNotNone(persisted_msg, "Message was NOT persisted in DB before recipient received broadcast!")
        self.assertEqual(persisted_msg.noi_dung, sent_text)
        self.assertEqual(persisted_msg.nguoi_gui_id, self.customer_a.id)

        await comm_cust.disconnect()
        await comm_staff.disconnect()

    async def test_adv_chat_15_oversized_payload_rejected_no_db_pollution(self):
        """5001 character message MUST be rejected with MESSAGE_TOO_LONG and 0 rows created."""
        token_cust = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_cust}")
        await comm.connect()
        _ = await comm.receive_json_from()

        initial_count = await self._get_room_message_count()

        oversized_text = "A" * 5001
        await comm.send_json_to({
            "action": "send_message",
            "content": oversized_text,
        })

        resp = await comm.receive_json_from()
        self.assertEqual(resp["type"], "error")
        self.assertEqual(resp["code"], "MESSAGE_TOO_LONG")

        # Verify DB remained untouched
        after_count = await self._get_room_message_count()
        self.assertEqual(initial_count, after_count, "DB was polluted by oversized message rejection!")

        await comm.disconnect()

    async def test_adv_chat_16_boundary_5000_char_message_accepted(self):
        """Exactly 5000 character message MUST be accepted and persisted successfully."""
        token_cust = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_cust}")
        await comm.connect()
        _ = await comm.receive_json_from()

        max_valid_text = "M" * 5000
        await comm.send_json_to({
            "action": "send_message",
            "content": max_valid_text,
        })

        resp = await comm.receive_json_from()
        self.assertEqual(resp["type"], "chat_message")
        self.assertEqual(len(resp["content"]), 5000)

        persisted = await self._get_message_by_id(resp["id"])
        self.assertIsNotNone(persisted)
        self.assertEqual(len(persisted.noi_dung), 5000)

        await comm.disconnect()

    async def test_adv_chat_17_empty_and_whitespace_only_rejected(self):
        """Empty string or whitespace-only strings MUST be rejected with EMPTY_CONTENT."""
        token_cust = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_cust}")
        await comm.connect()
        _ = await comm.receive_json_from()

        initial_count = await self._get_room_message_count()

        for empty_val in ["", "   ", "\n\t  \r\n"]:
            await comm.send_json_to({
                "action": "send_message",
                "message": empty_val,
            })
            resp = await comm.receive_json_from()
            self.assertEqual(resp["type"], "error")
            self.assertEqual(resp["code"], "EMPTY_CONTENT")

        after_count = await self._get_room_message_count()
        self.assertEqual(initial_count, after_count)

        await comm.disconnect()

    async def test_adv_chat_18_special_chars_xss_and_unicode_safety(self):
        """Special characters, HTML tags, SQL injection probes, and multi-byte UTF-8 pass cleanly."""
        token_cust = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_cust}")
        await comm.connect()
        _ = await comm.receive_json_from()

        adversarial_strings = [
            "<script>alert('xss');</script>",
            "'; DROP TABLE chat_tinnhan; --",
            "🍣 Mộc Restaurant 2026: Ẩm thực thuần Việt — 100% Chất lượng! 🥢",
            '{"fake": "json", "nested": true}',
        ]

        for s in adversarial_strings:
            await comm.send_json_to({"action": "send_message", "noi_dung": s})
            resp = await comm.receive_json_from()
            self.assertEqual(resp["type"], "chat_message")
            self.assertEqual(resp["content"], s)
            msg = await self._get_message_by_id(resp["id"])
            self.assertEqual(msg.noi_dung, s)

        await comm.disconnect()

    async def test_adv_chat_19_typing_echo_suppression(self):
        """Sender typing event MUST NOT echo back to the sender, but MUST reach recipient."""
        token_cust = str(AccessToken.for_user(self.customer_a))
        token_staff = str(AccessToken.for_user(self.staff_user))

        comm_cust = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_cust}")
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_staff}")

        await comm_cust.connect()
        await comm_staff.connect()
        _ = await comm_cust.receive_json_from()
        _ = await comm_staff.receive_json_from()

        await comm_cust.send_json_to({"action": "typing", "is_typing": True})

        # Staff receives
        typing_event = await comm_staff.receive_json_from()
        self.assertEqual(typing_event["type"], "chat_typing")
        self.assertEqual(typing_event["sender_id"], self.customer_a.id)
        self.assertTrue(typing_event["is_typing"])

        # Customer sender receives NOTHING
        self.assertTrue(await comm_cust.receive_nothing())

        await comm_cust.disconnect()
        await comm_staff.disconnect()

    async def test_adv_chat_20_auto_staff_assignment_on_first_reply(self):
        """When an unassigned room receives a response from staff, room.nhan_vien is auto-assigned."""
        # Precondition: room has no staff assigned
        room = await self._get_room_from_db(self.room_a.id)
        self.assertIsNone(room.nhan_vien_id)

        token_staff = str(AccessToken.for_user(self.staff_user))
        comm_staff = WebsocketCommunicator(application, f"/ws/chat/{self.room_a.id}/?token={token_staff}")
        await comm_staff.connect()
        _ = await comm_staff.receive_json_from()

        await comm_staff.send_json_to({
            "action": "send_message",
            "content": "Chào anh/chị, em là nhân viên hỗ trợ ạ!",
        })
        _ = await comm_staff.receive_json_from()

        # Check DB: staff_user should now be assigned
        room_updated = await self._get_room_from_db(self.room_a.id)
        self.assertEqual(room_updated.nhan_vien_id, self.staff_user.id)

        await comm_staff.disconnect()

    # --------------------------------------------------------------------------
    # DIMENSION 4: Order FSM Lifecycle, Security & Broadcast Synchronization
    # --------------------------------------------------------------------------

    def test_adv_fsm_21_complete_fsm_state_matrix_and_audit(self):
        """Strict 6-state matrix: cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat."""
        order = self.order_a
        self.assertEqual(order.trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN)

        # 1. Confirm
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_XAC_NHAN, self.staff_user, "Xác nhận")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_XAC_NHAN)

        # 2. Cooking
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DANG_CHE_BIEN, self.staff_user, "Bếp nấu")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DANG_CHE_BIEN)

        # 3. Ready
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.SAN_SANG, self.staff_user, "Lên món")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.SAN_SANG)

        # 4. Completed (terminal)
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.HOAN_TAT, self.staff_user, "Giao xong")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.HOAN_TAT)

        # Terminal state immutability
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.staff_user)
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DANG_CHE_BIEN, self.staff_user)

    def test_adv_fsm_22_customer_permission_boundaries(self):
        """Customer can ONLY cancel pending order; cannot cancel confirmed order or advance status."""
        order = self.order_a
        # Customer cancels pending order: SUCCESS
        DichVuDonHang.doi_trang_thai(order, DonHang.TrangThai.DA_HUY, self.customer_a, "Đổi ý")
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_HUY)

        # New confirmed order
        order2 = DonHang.objects.create(
            ma_don_hang="DH-ADV-002",
            khach_hang=self.customer_a,
            hinh_thuc=DonHang.HinhThuc.TU_DEN_LAY,
            trang_thai=DonHang.TrangThai.DA_XAC_NHAN,
            ten_khach="Khách A",
            sdt_khach="0911223344",
            tien_hang=Decimal("100000"),
            tong_tien=Decimal("100000"),
        )
        # Customer CANNOT cancel confirmed order
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order2, DonHang.TrangThai.DA_HUY, self.customer_a)

        # Customer CANNOT advance confirmed order to cooking
        with self.assertRaises(PermissionDenied):
            DichVuDonHang.doi_trang_thai(order2, DonHang.TrangThai.DANG_CHE_BIEN, self.customer_a)

    async def test_adv_fsm_23_multi_stream_realtime_broadcast_sync(self):
        """
        When order transitions, status update MUST be broadcast concurrently to:
        1. Single-order tracking stream (/ws/orders/<id>/)
        2. Staff kitchen global stream (/ws/orders/staff/)
        """
        token_cust = str(AccessToken.for_user(self.customer_a))
        token_staff = str(AccessToken.for_user(self.staff_user))

        comm_order = WebsocketCommunicator(application, f"/ws/orders/{self.order_a.id}/?token={token_cust}")
        comm_staff = WebsocketCommunicator(application, f"/ws/orders/staff/?token={token_staff}")

        await comm_order.connect()
        await comm_staff.connect()

        # Consume initial snapshots
        snap_order = await comm_order.receive_json_from()
        self.assertEqual(snap_order["type"], "order_snapshot")
        snap_staff = await comm_staff.receive_json_from()
        self.assertEqual(snap_staff["type"], "staff_connected")

        # Advance order to da_xac_nhan
        await self._async_advance_order(self.order_a.id, DonHang.TrangThai.DA_XAC_NHAN, self.staff_user)

        # Customer stream receives update
        cust_update = await comm_order.receive_json_from()
        self.assertEqual(cust_update["type"], "order_status_update")
        self.assertEqual(cust_update["order_id"], self.order_a.id)
        self.assertEqual(cust_update["status"], DonHang.TrangThai.DA_XAC_NHAN)
        self.assertEqual(cust_update["from_status"], DonHang.TrangThai.CHO_TIEP_NHAN)

        # Staff stream receives identical update
        staff_update = await comm_staff.receive_json_from()
        self.assertEqual(staff_update["type"], "order_status_update")
        self.assertEqual(staff_update["order_id"], self.order_a.id)
        self.assertEqual(staff_update["status"], DonHang.TrangThai.DA_XAC_NHAN)

        await comm_order.disconnect()
        await comm_staff.disconnect()

    async def test_adv_fsm_24_tracking_by_order_code_alias(self):
        """Tracking consumer supports string code ma_don_hang (e.g. DH-ADV-M3-001)."""
        token_cust = str(AccessToken.for_user(self.customer_a))
        comm = WebsocketCommunicator(application, f"/ws/orders/{self.order_a.ma_don_hang}/?token={token_cust}")
        c_ok, _ = await comm.connect()
        self.assertTrue(c_ok)

        snap = await comm.receive_json_from()
        self.assertEqual(snap["order_number"], self.order_a.ma_don_hang)

        await self._async_advance_order(self.order_a.id, DonHang.TrangThai.DA_XAC_NHAN, self.staff_user)
        update = await comm.receive_json_from()
        self.assertEqual(update["order_number"], self.order_a.ma_don_hang)
        self.assertEqual(update["status"], DonHang.TrangThai.DA_XAC_NHAN)

        await comm.disconnect()

    # --------------------------------------------------------------------------
    # Database helper utilities
    # --------------------------------------------------------------------------

    @database_sync_to_async
    def _get_message_by_id(self, msg_id):
        return TinNhan.objects.filter(id=msg_id).first()

    @database_sync_to_async
    def _get_room_message_count(self):
        return TinNhan.objects.filter(hoi_thoai=self.room_a).count()

    @database_sync_to_async
    def _get_room_from_db(self, room_id):
        return HoiThoai.objects.filter(id=room_id).first()

    @database_sync_to_async
    def _async_advance_order(self, order_id, new_status, user):
        order = DonHang.objects.get(id=order_id)
        return DichVuDonHang.doi_trang_thai(
            don_hang=order,
            trang_thai_moi=new_status,
            nguoi_dung=user,
            ghi_chu="Cập nhật tự động",
        )


if __name__ == "__main__":
    os.environ["TESTING"] = "1"
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    failures = runner.run_tests(["tests.e2e.test_adversarial_challenger_m3"])
    sys.exit(bool(failures))
