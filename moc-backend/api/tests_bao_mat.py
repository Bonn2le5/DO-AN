"""Test thu hồi token JWT, giới hạn đăng nhập admin và cấu hình HTTPS."""
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import NguoiDung

DANG_NHAP = "/api/xac-thuc/dang-nhap/"
LAM_MOI = "/api/xac-thuc/lam-moi/"
MAT_KHAU = "Passw0rd!x"


class ThuHoiTokenTest(TestCase):
    def setUp(self):
        self.user = NguoiDung.objects.create_user(
            username="kh", thu_dien_tu="kh@moc.vn", email="kh@moc.vn", password=MAT_KHAU
        )
        self.client = APIClient()

    def _dang_nhap(self):
        r = self.client.post(DANG_NHAP, {"thu_dien_tu": "kh@moc.vn", "password": MAT_KHAU}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        return r.data["refresh"]

    def test_lam_moi_xoay_vong_va_thu_hoi_token_cu(self):
        cu = self._dang_nhap()
        r = self.client.post(LAM_MOI, {"refresh": cu}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("refresh", r.data)
        self.assertNotEqual(r.data["refresh"], cu)
        # Refresh cũ đã bị thu hồi, không dùng lại được
        self.assertEqual(self.client.post(LAM_MOI, {"refresh": cu}, format="json").status_code, 401)
        self.assertEqual(self.client.post(LAM_MOI, {"refresh": r.data["refresh"]}, format="json").status_code, 200)

    def test_dang_xuat_thu_hoi_refresh(self):
        refresh = self._dang_nhap()
        r = self.client.post("/api/xac-thuc/dang-xuat/", {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.post(LAM_MOI, {"refresh": refresh}, format="json").status_code, 401)
        # Gửi lại token đã thu hồi / token rác vẫn trả 200 (đã đăng xuất)
        self.assertEqual(self.client.post("/api/xac-thuc/dang-xuat/", {"refresh": refresh}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/xac-thuc/dang-xuat/", {"refresh": "rac"}, format="json").status_code, 200)
        self.assertEqual(self.client.post("/api/xac-thuc/dang-xuat/", {}, format="json").status_code, 400)

    def test_doi_mat_khau_dang_xuat_moi_thiet_bi(self):
        may_1, may_2 = self._dang_nhap(), self._dang_nhap()
        self.client.force_authenticate(self.user)
        r = self.client.post(
            "/api/xac-thuc/doi-mat-khau/",
            {"mat_khau_cu": MAT_KHAU, "mat_khau_moi": "MatKhauMoi!2026", "xac_nhan_mat_khau": "MatKhauMoi!2026"},
            format="json",
        )
        self.assertEqual(r.status_code, 200, r.content)
        self.client.force_authenticate(None)
        for refresh in (may_1, may_2):
            self.assertEqual(self.client.post(LAM_MOI, {"refresh": refresh}, format="json").status_code, 401)


class DangNhapAdminTest(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(GIOI_HAN_TAN_SUAT={"dang_nhap_admin": "3/h"})
    def test_dang_nhap_admin_sai_nhieu_lan_bi_chan(self):
        c = Client()
        url = f"/{settings.ADMIN_URL}login/"
        for _ in range(3):
            self.assertEqual(c.post(url, {"username": "x@moc.vn", "password": "sai"}).status_code, 200)
        r = c.post(url, {"username": "x@moc.vn", "password": "sai"})
        self.assertEqual(r.status_code, 429)
        self.assertIn("thử lại sau", r.content.decode())
        # Xem trang đăng nhập (GET) không bị tính
        self.assertEqual(c.get(url).status_code, 200)

    def test_trang_chu_khong_lo_duong_dan_admin(self):
        r = Client().get("/")
        self.assertNotIn("admin", r.json()["endpoints"])
