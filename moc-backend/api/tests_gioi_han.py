"""Test giới hạn tần suất (rate limiting) và tham số sai kiểu."""
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import NguoiDung, XacThucEmail
from branches.models import ChiNhanh

DANG_NHAP = "/api/xac-thuc/dang-nhap/"


class GioiHanTanSuatTest(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = NguoiDung.objects.create_user(
            username="kh", thu_dien_tu="kh@moc.vn", email="kh@moc.vn", password="Passw0rd!x"
        )

    def _dang_nhap(self, email="kh@moc.vn", ip="10.0.0.1", mat_khau="sai"):
        return self.client.post(
            DANG_NHAP, {"thu_dien_tu": email, "password": mat_khau}, format="json", REMOTE_ADDR=ip
        )

    @override_settings(GIOI_HAN_TAN_SUAT={"dang_nhap_ip": "3/m"})
    def test_dang_nhap_sai_lien_tuc_bi_chan_theo_ip(self):
        for i in range(3):
            self.assertEqual(self._dang_nhap(email=f"x{i}@moc.vn").status_code, 401)
        r = self._dang_nhap(email="x9@moc.vn")
        self.assertEqual(r.status_code, 429)
        self.assertIn("thử lại sau", r.data["detail"])
        self.assertGreaterEqual(r.data["thu_lai_sau"], 1)
        # IP khác vẫn đăng nhập được
        self.assertEqual(self._dang_nhap(ip="10.0.0.2", mat_khau="Passw0rd!x").status_code, 200)

    @override_settings(GIOI_HAN_TAN_SUAT={"dang_nhap_tai_khoan": "3/h"})
    def test_do_mot_tai_khoan_tu_nhieu_ip_bi_chan(self):
        for i in range(3):
            self._dang_nhap(email="KH@moc.vn ", ip=f"10.0.1.{i}")
        self.assertEqual(self._dang_nhap(ip="10.0.1.99").status_code, 429)

    @override_settings(GIOI_HAN_TAN_SUAT={"nhap_otp": "5/m"})
    def test_do_ma_otp_bi_chan(self):
        moi = NguoiDung.objects.create_user(
            username="moi", thu_dien_tu="moi@moc.vn", email="moi@moc.vn", password="Passw0rd!x", is_active=False
        )
        xt = XacThucEmail.objects.create(nguoi_dung=moi)
        ma = xt.tao_ma()
        url = "/api/xac-thuc/xac-thuc-email/"
        for i in range(5):
            r = self.client.post(url, {"email": "moi@moc.vn", "ma_xac_thuc": "000000"}, format="json",
                                 REMOTE_ADDR=f"10.0.2.{i}")
            self.assertEqual(r.status_code, 400)
        r = self.client.post(url, {"email": "moi@moc.vn", "ma_xac_thuc": ma}, format="json", REMOTE_ADDR="10.0.2.9")
        self.assertEqual(r.status_code, 429)

    @override_settings(GIOI_HAN_TAN_SUAT={"dang_ky": "2/h"})
    def test_dang_ky_qua_nhieu_bi_chan_ca_url_bi_danh(self):
        for url in ("/api/xac-thuc/dang-ky/", "/api/xac-thuc/register/"):
            self.client.post(url, {}, format="json")
        self.assertEqual(self.client.post("/api/xac-thuc/dang_ky/", {}, format="json").status_code, 429)

    @override_settings(GIOI_HAN_TAN_SUAT={"khach": "2/m", "nguoi_dung": "3/m"})
    def test_gioi_han_chung_va_health_khong_bi_chan(self):
        for _ in range(2):
            self.assertEqual(self.client.get("/api/danh-muc/").status_code, 200)
        self.assertEqual(self.client.get("/api/danh-muc/").status_code, 429)
        for _ in range(5):
            self.assertEqual(self.client.get("/api/health/").status_code, 200)
        # Tài khoản đã đăng nhập dùng bộ đếm riêng
        self.client.force_authenticate(self.user)
        for _ in range(3):
            self.assertEqual(self.client.get("/api/danh-muc/").status_code, 200)
        self.assertEqual(self.client.get("/api/danh-muc/").status_code, 429)

    def test_khong_cau_hinh_thi_khong_gioi_han(self):
        for _ in range(30):
            self.assertNotEqual(self._dang_nhap().status_code, 429)


class ThamSoSaiKieuTest(TestCase):
    def test_tham_so_so_nguyen_sai_tra_400(self):
        ChiNhanh.objects.create(ten="CN", dia_chi="a")
        c = APIClient()
        for url in (
            "/api/ban-an/?chi_nhanh=1' OR '1'='1",
            "/api/ban-an/?guest_count=1 OR 1=1",
            "/api/dat-ban/khung-gio-trong/?chi_nhanh_id=1 OR 1=1&ngay=2026-11-12",
        ):
            self.assertEqual(c.get(url).status_code, 400, url)


class DoMaOtpTest(TestCase):
    """Chặn dò mã OTP 6 số: giới hạn theo đúng trường email của view + vô hiệu mã sau 5 lần sai."""
    URL = "/api/xac-thuc/xac-thuc-email/"

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.nd = NguoiDung.objects.create_user(
            username="moi", thu_dien_tu="moi@moc.vn", email="moi@moc.vn", password="Passw0rd!x", is_active=False
        )
        self.xt = XacThucEmail.objects.create(nguoi_dung=self.nd)
        self.ma = self.xt.tao_ma()

    def _nhap(self, ma, **them):
        return self.client.post(self.URL, {"email": "moi@moc.vn", "ma_xac_thuc": ma, **them}, format="json",
                                REMOTE_ADDR=them.pop("ip", "10.9.0.1"))

    @override_settings(GIOI_HAN_TAN_SUAT={"nhap_otp": "3/m"})
    def test_truong_gia_khong_lam_lech_bo_dem(self):
        # Kẻ tấn công gửi email nạn nhân ở trường view dùng + chuỗi ngẫu nhiên ở trường khác,
        # mỗi lần một IP: bộ đếm vẫn tính theo email nạn nhân.
        for i in range(3):
            r = self.client.post(self.URL, {"email": "moi@moc.vn", "thu_dien_tu": f"gia{i}@x.vn", "ma_xac_thuc": "000000"},
                                 format="json", REMOTE_ADDR=f"10.9.1.{i}")
            self.assertEqual(r.status_code, 400)
        r = self.client.post(self.URL, {"email": "moi@moc.vn", "thu_dien_tu": "gia9@x.vn", "ma_xac_thuc": self.ma},
                             format="json", REMOTE_ADDR="10.9.1.99")
        self.assertEqual(r.status_code, 429)

    def test_sai_5_lan_thi_ma_vo_hieu_ke_ca_ma_dung(self):
        for con_lai in (4, 3, 2, 1):
            r = self._nhap("000000")
            self.assertIn(f"Còn {con_lai} lần", r.data["detail"])
        self.assertIn("quá nhiều lần", self._nhap("000000").data["detail"])
        r = self._nhap(self.ma)
        self.assertEqual(r.status_code, 400)
        self.assertIn("gửi mã mới", r.data["detail"])
        self.nd.refresh_from_db()
        self.assertFalse(self.nd.is_active)

        # Xin mã mới thì bộ đếm về 0 và mã mới dùng được
        self.xt.refresh_from_db()
        ma_moi = self.xt.tao_ma()
        r = self._nhap(ma_moi)
        self.assertEqual(r.status_code, 200, r.content)
        self.nd.refresh_from_db()
        self.assertTrue(self.nd.is_active)

    def test_du_lieu_sai_kieu_khong_loi_500(self):
        for body in ({"email": ["moi@moc.vn"], "ma_xac_thuc": 123456}, {"email": 1, "ma_xac_thuc": None}):
            self.assertIn(self.client.post(self.URL, body, format="json").status_code, (400, 404))
