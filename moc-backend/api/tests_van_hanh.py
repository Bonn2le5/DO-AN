"""Sự kiện realtime "vận hành cập nhật" tới màn hình nhân viên."""
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import VaiTro
from api.tests_channels_helper import WebsocketCommunicator
from branches.models import ChiNhanh
from config.asgi import application
from reservations.models import BanAn
from reservations.services import DichVuPhienPhucVu

NguoiDung = get_user_model()


async def doc_den(comm, dieu_kien, toi_da=10):
    """Đọc khung tới khi gặp khung thoả điều kiện (bỏ qua các sự kiện khác)."""
    for _ in range(toi_da):
        khung = await comm.receive_json_from(timeout=2)
        if dieu_kien(khung):
            return khung
    raise AssertionError("Không nhận được sự kiện mong đợi")


class SuKienVanHanhTest(TransactionTestCase):
    def setUp(self):
        self.cn1 = ChiNhanh.objects.create(ten="CN1", dia_chi="a")
        self.cn2 = ChiNhanh.objects.create(ten="CN2", dia_chi="b")
        self.ban = BanAn.objects.create(chi_nhanh=self.cn1, so_ban="T1", suc_chua=4)
        self.admin = NguoiDung.objects.create_user(
            username="ad", thu_dien_tu="ad@moc.vn", email="ad@moc.vn", password="Passw0rd!x",
            is_superuser=True, is_staff=True,
        )
        self.nv_cn2 = NguoiDung.objects.create_user(
            username="nv2", thu_dien_tu="nv2@moc.vn", email="nv2@moc.vn", password="Passw0rd!x", is_staff=True,
        )
        self.nv_cn2.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten="quan_ly_chi_nhanh")[0])
        self.nv_cn2.chi_nhanh_quan_ly = self.cn2
        self.nv_cn2.save()

    async def _ket_noi(self, user):
        c = WebsocketCommunicator(application, f"/ws/don-hang/nhan-vien/?token={AccessToken.for_user(user)}")
        ok, _ = await c.connect()
        self.assertTrue(ok)
        self.assertEqual((await c.receive_json_from())["type"], "staff_connected")
        return c

    async def test_mo_ban_walk_in_bao_cho_admin_va_dung_chi_nhanh(self):
        admin = await self._ket_noi(self.admin)
        nv_khac = await self._ket_noi(self.nv_cn2)

        phien = await database_sync_to_async(DichVuPhienPhucVu.tao_walk_in)(
            nguoi_dung=self.admin, ban_an_id=self.ban.id, so_luong_khach=2,
        )
        khung = await doc_den(admin, lambda k: k["type"] == "van_hanh_cap_nhat" and k["doi_tuong"] == "phien_phuc_vu")
        self.assertEqual(khung["id"], phien.id)
        self.assertEqual(khung["chi_nhanh_id"], self.cn1.id)
        await doc_den(admin, lambda k: k.get("doi_tuong") == "ban_an" and k["id"] == self.ban.id)

        # Nhân viên chi nhánh khác không nhận sự kiện của chi nhánh 1
        self.assertTrue(await nv_khac.receive_nothing(timeout=0.5))
        await admin.disconnect()
        await nv_khac.disconnect()
