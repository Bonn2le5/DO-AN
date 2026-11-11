"""WebSocket: kiểm Origin theo tên miền frontend, và vẫn chạy khi Redis lỗi."""
from unittest import mock

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.security.websocket import OriginValidator
from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings

from api.tests_channels_helper import WebsocketCommunicator

# Giống cấu hình Render: frontend và backend ở hai tên miền khác nhau.
NGUON_PRODUCTION = [
    "https://mockitchen.id.vn", "https://www.mockitchen.id.vn",
    "api.mockitchen.id.vn", "moc-backend.onrender.com",
]


class _Echo(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()


class OriginWebSocketTest(SimpleTestCase):
    async def _ket_noi(self, origin):
        headers = [(b"origin", origin.encode())] if origin else []
        c = WebsocketCommunicator(OriginValidator(_Echo.as_asgi(), NGUON_PRODUCTION), "/ws/x/", headers=headers)
        ok, _ = await c.connect()
        await c.disconnect()
        return ok

    async def test_trang_frontend_khac_ten_mien_backend_duoc_ket_noi(self):
        self.assertTrue(await self._ket_noi("https://mockitchen.id.vn"))
        self.assertTrue(await self._ket_noi("https://www.mockitchen.id.vn"))

    async def test_trang_la_bi_chan(self):
        for origin in ("https://evil.example", "https://mockitchen.id.vn.evil.example", "http://mockitchen.id.vn", None):
            self.assertFalse(await self._ket_noi(origin), origin)

    def test_mac_dinh_gom_ca_cors_va_allowed_hosts(self):
        for nguon in settings.CORS_ALLOWED_ORIGINS:
            self.assertIn(nguon, settings.WEBSOCKET_NGUON_HOP_LE)


class RedisLoiTest(TestCase):
    @override_settings(GIOI_HAN_TAN_SUAT={"khach": "100/m"})
    def test_cache_loi_thi_api_van_chay(self):
        with mock.patch("django.core.cache.backends.locmem.LocMemCache.get", side_effect=ConnectionError("redis sập")):
            self.assertEqual(self.client.get("/api/danh-muc/").status_code, 200)

    def test_channel_layer_loi_tin_nhan_van_luu(self):
        from accounts.models import NguoiDung
        from chat.models import HoiThoai, TinNhan
        from rest_framework.test import APIClient

        kh = NguoiDung.objects.create_user(username="kh", thu_dien_tu="kh@moc.vn", email="kh@moc.vn", password="Passw0rd!x")
        phong = HoiThoai.objects.create(khach_hang=kh)
        c = APIClient()
        c.force_authenticate(kh)
        with mock.patch("chat.services.get_channel_layer", side_effect=ConnectionError("redis sập")):
            r = c.post(f"/api/hoi-thoai/{phong.id}/tin-nhan/", {"noi_dung": "xin chào"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(TinNhan.objects.filter(hoi_thoai=phong, noi_dung="xin chào").exists())
