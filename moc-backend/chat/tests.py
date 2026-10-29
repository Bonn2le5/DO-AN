"""
Comprehensive Unit & Integration Test Suite for Chat WebSocket & REST API.
"""

from decimal import Decimal
from django.test import TransactionTestCase, TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from api.tests_channels_helper import WebsocketCommunicator
from config.asgi import application
from chat.models import HoiThoai, TinNhan


class ChatWebSocketTestCase(TransactionTestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="khach_test",
            email="khach@example.com",
            thu_dien_tu="khach@example.com",
            password="password123",
            first_name="Văn",
            last_name="Vũ",
        )
        self.other_user = User.objects.create_user(
            username="khach_khac",
            email="khach_khac@example.com",
            thu_dien_tu="khach_khac@example.com",
            password="password123",
            first_name="Khác",
            last_name="User",
        )
        self.staff_user = User.objects.create_user(
            username="nhan_vien_test",
            email="nv@example.com",
            thu_dien_tu="nv@example.com",
            password="password123",
            is_staff=True,
            first_name="Nhân",
            last_name="Viên",
        )
        self.hoi_thoai = HoiThoai.objects.create(khach_hang=self.user)

    async def test_chat_anonymous_connection_rejected(self):
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/"
        )
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

    async def test_chat_forbidden_customer_rejected(self):
        token = str(AccessToken.for_user(self.other_user))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4403)

    async def test_chat_customer_connect_and_send_message(self):
        token = str(AccessToken.for_user(self.user))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        welcome = await communicator.receive_json_from()
        self.assertEqual(welcome["type"], "connection_established")
        self.assertEqual(welcome["conversation_id"], self.hoi_thoai.id)

        test_msg = "Xin chào nhà hàng Mộc!"
        await communicator.send_json_to({
            "action": "send_message",
            "message": test_msg,
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "chat_message")
        self.assertEqual(response["content"], test_msg)
        self.assertEqual(response["conversation_id"], self.hoi_thoai.id)

        await communicator.disconnect()

        # Verify DB persistence
        tin_nhan_count = await self._get_message_count()
        self.assertEqual(tin_nhan_count, 1)

    async def test_chat_staff_connection_allowed(self):
        token = str(AccessToken.for_user(self.staff_user))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        welcome = await communicator.receive_json_from()
        self.assertEqual(welcome["type"], "connection_established")
        self.assertTrue(welcome["is_staff"])
        await communicator.disconnect()

    async def test_chat_empty_message_validation(self):
        token = str(AccessToken.for_user(self.user))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        _ = await communicator.receive_json_from()  # welcome frame

        await communicator.send_json_to({
            "action": "send_message",
            "content": "   ",
        })

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "error")
        self.assertEqual(response["code"], "EMPTY_CONTENT")

        await communicator.disconnect()

        tin_nhan_count = await self._get_message_count()
        self.assertEqual(tin_nhan_count, 0)

    async def test_chat_typing_indicator(self):
        token1 = str(AccessToken.for_user(self.user))
        token2 = str(AccessToken.for_user(self.staff_user))

        comm1 = WebsocketCommunicator(application, f"/ws/chat/{self.hoi_thoai.id}/?token={token1}")
        comm2 = WebsocketCommunicator(application, f"/ws/chat/{self.hoi_thoai.id}/?token={token2}")

        c1_ok, _ = await comm1.connect()
        c2_ok, _ = await comm2.connect()
        self.assertTrue(c1_ok)
        self.assertTrue(c2_ok)

        _ = await comm1.receive_json_from()
        _ = await comm2.receive_json_from()

        # comm1 sends typing
        await comm1.send_json_to({"action": "typing", "is_typing": True})

        # comm2 should receive typing event
        typing_event = await comm2.receive_json_from()
        self.assertEqual(typing_event["type"], "chat_typing")
        self.assertEqual(typing_event["sender_id"], self.user.id)
        self.assertTrue(typing_event["is_typing"])

        # comm1 should NOT receive its own typing event
        self.assertTrue(await comm1.receive_nothing())

        await comm1.disconnect()
        await comm2.disconnect()

    async def test_chat_read_receipt(self):
        token = str(AccessToken.for_user(self.staff_user))
        await self._create_customer_message("Tin nhắn chưa đọc")

        comm = WebsocketCommunicator(application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}")
        c_ok, _ = await comm.connect()
        self.assertTrue(c_ok)
        _ = await comm.receive_json_from()

        await comm.send_json_to({"action": "mark_read"})
        receipt = await comm.receive_json_from()
        self.assertEqual(receipt["type"], "chat_read_receipt")
        self.assertEqual(receipt["reader_id"], self.staff_user.id)

        unread_count = await self._get_unread_message_count()
        self.assertEqual(unread_count, 0)

        await comm.disconnect()

    async def _get_message_count(self):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def count():
            return TinNhan.objects.filter(hoi_thoai=self.hoi_thoai).count()

        return await count()

    async def _get_unread_message_count(self):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def count():
            return TinNhan.objects.filter(hoi_thoai=self.hoi_thoai, da_doc=False).count()

        return await count()

    async def _create_customer_message(self, text):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def create():
            return TinNhan.objects.create(
                hoi_thoai=self.hoi_thoai,
                nguoi_gui=self.user,
                noi_dung=text,
            )

        return await create()


class ChatRESTApiTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="khach_rest",
            email="khach_rest@example.com",
            thu_dien_tu="khach_rest@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_active_conversation_creation_and_retrieval(self):
        response = self.client.get("/api/chat/conversations/active/")
        self.assertEqual(response.status_code, 200)
        room_id = response.data["id"]

        # Calling again should return the same active conversation
        response2 = self.client.get("/api/chat/conversations/active/")
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data["id"], room_id)

    def test_conversation_messages_endpoint(self):
        room = HoiThoai.objects.create(khach_hang=self.user)
        TinNhan.objects.create(hoi_thoai=room, nguoi_gui=self.user, noi_dung="Alo alo")

        response = self.client.get(f"/api/chat/conversations/{room.id}/messages/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["noi_dung"], "Alo alo")
