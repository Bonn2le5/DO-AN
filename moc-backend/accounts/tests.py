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
        self.assertEqual(data["thu_dien_tu"], "profile_test@moc.vn")
        self.assertEqual(data["ho_ten"], "Văn Vũ")
        self.assertEqual(data["username"], "khach_test_profile")

    def test_api_auth_profile_endpoint(self):
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["thu_dien_tu"], "profile_test@moc.vn")
        self.assertEqual(response.data["ho_ten"], "Văn Vũ")

    def test_doi_email_can_mat_khau(self):
        url = "/api/auth/profile/"
        r = self.client.patch(url, {"thu_dien_tu": "moi@moc.vn"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(url, {"thu_dien_tu": "moi@moc.vn", "mat_khau_hien_tai": "sai"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(url, {"thu_dien_tu": "moi@moc.vn", "mat_khau_hien_tai": "Password@123"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.thu_dien_tu, "moi@moc.vn")

    def test_sua_ho_ten_khong_can_mat_khau(self):
        r = self.client.patch("/api/auth/profile/", {"first_name": "Mai", "last_name": "Nguyễn", "thu_dien_tu": "profile_test@moc.vn"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["ho_ten"], "Mai Nguyễn")

    def test_danh_gia_mine_chi_tra_cua_minh(self):
        self.assertEqual(self.client.get("/api/reviews/", {"mine": 1}).status_code, 200)
        self.assertEqual(len(APIClient().get("/api/reviews/", {"mine": 1}).data), 0)  # khách vãng lai không thấy gì



class DangKyTestCase(TestCase):
    URL = "/api/auth/register/"

    def setUp(self):
        self.client = APIClient()
        self.payload = {"ho_ten": "Nguyen Van A", "thu_dien_tu": "a@moc.vn", "so_dien_thoai": "0901234567", "mat_khau": "secret123",
                        "dong_y_chinh_sach": True, "phien_ban_chinh_sach": "1.0"}

    def test_luu_bang_chung_dong_y_chinh_sach(self):
        self.assertEqual(self.client.post(self.URL, self.payload, format="json").status_code, 201)
        nd = NguoiDung.objects.get(thu_dien_tu="a@moc.vn")
        self.assertIsNotNone(nd.dong_y_chinh_sach_luc)
        self.assertEqual(nd.phien_ban_chinh_sach, "1.0")

    def test_khong_dong_y_thi_khong_tao_tai_khoan(self):
        for thieu in ({"dong_y_chinh_sach": False}, {"dong_y_chinh_sach": None}):
            r = self.client.post(self.URL, {**self.payload, **thieu}, format="json")
            self.assertEqual(r.status_code, 400)
            self.assertIn("dong_y_chinh_sach", r.data)
        payload = {k: v for k, v in self.payload.items() if k != "dong_y_chinh_sach"}
        self.assertEqual(self.client.post(self.URL, payload, format="json").status_code, 400)
        self.assertFalse(NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").exists())

    def test_email_hoa_thuong_va_trung(self):
        self.assertEqual(self.client.post(self.URL, dict(self.payload, thu_dien_tu="A@Moc.vn"), format="json").status_code, 201)
        self.assertTrue(NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").exists())
        NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").update(is_active=True)
        r = self.client.post(self.URL, dict(self.payload, so_dien_thoai="0907654321"), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.data["thu_dien_tu"][0], "Email này đã được đăng ký.")

    def test_so_dien_thoai(self):
        r = self.client.post(self.URL, dict(self.payload, so_dien_thoai="abc"), format="json")
        self.assertEqual(r.data["so_dien_thoai"][0], "Số điện thoại không hợp lệ.")
        self.client.post(self.URL, self.payload, format="json")
        r = self.client.post(self.URL, dict(self.payload, thu_dien_tu="b@moc.vn"), format="json")
        self.assertEqual(r.data["so_dien_thoai"][0], "Số điện thoại này đã được sử dụng.")

    def test_dang_ky_lai_khi_chua_xac_thuc(self):
        self.client.post(self.URL, self.payload, format="json")
        r = self.client.post(self.URL, dict(self.payload, mat_khau="moi12345"), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(NguoiDung.objects.filter(thu_dien_tu="a@moc.vn").count(), 1)

    def test_khong_tao_lai_tai_khoan_bi_khoa(self):
        NguoiDung.objects.create_user(username="khoa", thu_dien_tu="a@moc.vn", password="x" * 8, is_active=False)
        self.assertEqual(self.client.post(self.URL, self.payload, format="json").status_code, 400)

    def test_dang_nhap_email_hoa_va_loi_tieng_viet(self):
        NguoiDung.objects.create_user(username="ok", thu_dien_tu="a@moc.vn", password="secret123")
        self.assertEqual(self.client.post("/api/auth/login/", {"thu_dien_tu": "A@MOC.VN", "password": "secret123"}, format="json").status_code, 200)
        r = self.client.post("/api/auth/login/", {"thu_dien_tu": "a@moc.vn", "password": "sai"}, format="json")
        self.assertIn("chưa xác thực email", r.data["detail"])
