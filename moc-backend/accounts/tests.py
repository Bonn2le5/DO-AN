from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.serializers import NguoiDungSerializer

NguoiDung = get_user_model()


class AuthProfileTestCase(TestCase):
    def setUp(self):
        self.user = NguoiDung.objects.create_user(
            username="khach_test_profile",
            email="profile_test@moc.vn",
            thu_dien_tu="profile_test@moc.vn",
            first_name="Văn",
            last_name="Vũ",
            password="Password@123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_nguoi_dung_serializer(self):
        serializer = NguoiDungSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["email"], "profile_test@moc.vn")
        self.assertEqual(data["name"], "Văn Vũ")
        self.assertEqual(data["username"], "khach_test_profile")

    def test_api_auth_profile_endpoint(self):
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "profile_test@moc.vn")
        self.assertEqual(response.data["name"], "Văn Vũ")



class DangKyTestCase(TestCase):
    URL = "/api/auth/register/"

    def setUp(self):
        self.client = APIClient()
        self.payload = {"name": "Nguyen Van A", "email": "a@moc.vn", "phone": "0901234567", "password": "secret123"}

    def test_email_hoa_thuong_va_trung(self):
        self.assertEqual(self.client.post(self.URL, dict(self.payload, email="A@Moc.vn"), format="json").status_code, 201)
        self.assertTrue(NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").exists())
        NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").update(is_active=True)
        r = self.client.post(self.URL, dict(self.payload, phone="0907654321"), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["thu_dien_tu"][0], "Email này đã được đăng ký.")

    def test_so_dien_thoai(self):
        r = self.client.post(self.URL, dict(self.payload, phone="abc"), format="json")
        self.assertEqual(r.data["so_dien_thoai"][0], "Số điện thoại không hợp lệ.")
        self.client.post(self.URL, self.payload, format="json")
        r = self.client.post(self.URL, dict(self.payload, email="b@moc.vn"), format="json")
        self.assertEqual(r.data["so_dien_thoai"][0], "Số điện thoại này đã được sử dụng.")

    def test_dang_ky_lai_khi_chua_xac_thuc(self):
        self.client.post(self.URL, self.payload, format="json")
        r = self.client.post(self.URL, dict(self.payload, password="moi12345"), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").count(), 1)

    def test_khong_tao_lai_tai_khoan_bi_khoa(self):
        NguoiDung.objects.create_user(username="khoa", thu_dien_tu="a@moc.vn", password="x" * 8, is_active=False)
        self.assertEqual(self.client.post(self.URL, self.payload, format="json").status_code, 400)

    def test_dang_nhap_email_hoa_va_loi_tieng_viet(self):
        NguoiDung.objects.create_user(username="ok", thu_dien_tu="a@moc.vn", password="secret123")
        self.assertEqual(self.client.post("/api/auth/login/", {"email": "A@MOC.VN", "password": "secret123"}, format="json").status_code, 200)
        r = self.client.post("/api/auth/login/", {"email": "a@moc.vn", "password": "sai"}, format="json")
        self.assertIn("chưa xác thực email", r.data["detail"])
