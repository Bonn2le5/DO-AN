"""
Comprehensive Unit & Integration Test Suite for Chat WebSocket & REST API.
"""

from decimal import Decimal
from django.test import TransactionTestCase, TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from api.tests_channels_helper import WebsocketCommunicator, ma_dong_khi_tu_choi
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
        # Vai trò thật để code phân quyền nhận ra nhân viên (is_staff thôi là chưa đủ).
        from accounts.models import VaiTro
        self.staff_user.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten="quan_tri_vien")[0])
        self.hoi_thoai = HoiThoai.objects.create(khach_hang=self.user)

    async def test_chat_anonymous_connection_rejected(self):
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/"
        )
        self.assertEqual(await ma_dong_khi_tu_choi(communicator), 4401)

    async def test_chat_forbidden_customer_rejected(self):
        token = str(AccessToken.for_user(self.other_user))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        self.assertEqual(await ma_dong_khi_tu_choi(communicator), 4403)

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

    async def test_customer_cannot_send_system_message(self):
        token = str(AccessToken.for_user(self.user))
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.hoi_thoai.id}/?token={token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.receive_json_from()  # welcome

        await communicator.send_json_to({
            "action": "send_message", "content": "Giả hệ thống", "message_type": "he_thong",
        })
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "chat_message")
        self.assertEqual(response["message_type"], "van_ban")
        await communicator.disconnect()

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
        self.assertEqual(response.data[0]["content"], "Alo alo")



class ChatQuyenSauKhiChuyenChiNhanhTest(TransactionTestCase):
    """Nhân viên đang mở phòng chat phải bị ngắt khi admin chuyển hội thoại sang chi nhánh khác."""

    def setUp(self):
        from accounts.models import NguoiDung, VaiTro
        from branches.models import ChiNhanh
        self.a = ChiNhanh.objects.create(ten="A", dia_chi="a")
        self.b = ChiNhanh.objects.create(ten="B", dia_chi="b")
        khach = NguoiDung.objects.create_user(username="k", thu_dien_tu="k@x.vn", email="k@x.vn", password="Passw0rd!x")
        self.nv = NguoiDung.objects.create_user(username="nv", thu_dien_tu="nv@x.vn", email="nv@x.vn", password="Passw0rd!x")
        self.nv.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten="nhan_vien_ban_hang")[0])
        self.nv.chi_nhanh_quan_ly = self.a
        self.nv.save()
        self.room = HoiThoai.objects.create(khach_hang=khach, chi_nhanh=self.a)

    async def _connect(self):
        token = str(AccessToken.for_user(self.nv))
        com = WebsocketCommunicator(application, f"/ws/chat/{self.room.id}/?token={token}")
        connected, _ = await com.connect()
        self.assertTrue(connected)
        self.assertEqual((await com.receive_json_from())["type"], "connection_established")
        return com

    async def test_bi_ngat_ngay_khi_admin_chuyen_chi_nhanh(self):
        from channels.db import database_sync_to_async
        from chat.services import broadcast_reassigned
        com = await self._connect()

        def chuyen():
            HoiThoai.objects.filter(pk=self.room.pk).update(chi_nhanh=self.b)
            self.room.refresh_from_db()
            broadcast_reassigned(self.room)
        await database_sync_to_async(chuyen)()
        self.assertEqual((await com.receive_json_from())["type"], "access_revoked")
        self.assertEqual((await com.receive_output())["type"], "websocket.close")

    async def test_khong_gui_duoc_tin_khi_da_mat_quyen(self):
        from channels.db import database_sync_to_async
        com = await self._connect()
        # Đổi chi nhánh trực tiếp trong DB, không phát sự kiện: lần gửi tiếp theo vẫn phải bị chặn.
        await database_sync_to_async(lambda: HoiThoai.objects.filter(pk=self.room.pk).update(chi_nhanh=self.b))()
        await com.send_json_to({"action": "send_message", "content": "Còn gửi được không?"})
        self.assertEqual((await com.receive_json_from())["type"], "access_revoked")
        self.assertEqual(await database_sync_to_async(lambda: TinNhan.objects.filter(hoi_thoai=self.room).count())(), 0)


class MigrationGanChiNhanhHoiThoaiCuTest(TestCase):
    """Migration 0003: gắn chi nhánh cho hội thoại cũ theo lịch sử đặt bàn, không ghi đè."""

    def test_gan_theo_dat_ban(self):
        import importlib
        from datetime import timedelta
        from django.apps import apps
        from accounts.models import NguoiDung
        from branches.models import ChiNhanh
        from foods.services import hom_nay_vn
        from reservations.models import DatBan
        mig = importlib.import_module("chat.migrations.0003_gan_chi_nhanh_hoi_thoai_cu")
        a = ChiNhanh.objects.create(ten="A", dia_chi="a")
        b = ChiNhanh.objects.create(ten="B", dia_chi="b")
        mk = lambda u: NguoiDung.objects.create_user(username=u, thu_dien_tu=f"{u}@x.vn", email=f"{u}@x.vn", password="Passw0rd!x")
        def dat(user, branch, days, status=DatBan.TrangThai.DA_XAC_NHAN):
            DatBan.objects.create(nguoi_dung=user, chi_nhanh=branch, ngay_dat=hom_nay_vn() + timedelta(days=days), gio_bat_dau="19:00",
                                  so_luong_khach=2, hinh_thuc=DatBan.HinhThuc.CHI_GIU_CHO, trang_thai=status, ten_khach="K", sdt_khach="09")
        sap_toi, da_qua, chua_dat, da_gan = mk("k1"), mk("k2"), mk("k3"), mk("k4")
        dat(sap_toi, a, -5); dat(sap_toi, b, 2); dat(sap_toi, a, 1, DatBan.TrangThai.DA_HUY)
        dat(da_qua, a, -10); dat(da_qua, b, -3)
        dat(da_gan, a, 1)
        rooms = {u: HoiThoai.objects.create(khach_hang=u) for u in (sap_toi, da_qua, chua_dat)}
        rooms[da_gan] = HoiThoai.objects.create(khach_hang=da_gan, chi_nhanh=b)

        mig.gan_chi_nhanh(apps, None)
        got = {u.username: HoiThoai.objects.get(pk=r.pk).chi_nhanh_id for u, r in rooms.items()}
        self.assertEqual(got, {"k1": b.id, "k2": b.id, "k3": None, "k4": b.id})
