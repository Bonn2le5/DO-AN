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

    def test_doi_email_can_mat_khau_va_ma_gui_toi_email_moi(self):
        from django.core import mail
        url = "/api/auth/profile/"
        r = self.client.patch(url, {"thu_dien_tu": "moi@moc.vn"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(url, {"thu_dien_tu": "moi@moc.vn", "mat_khau_hien_tai": "sai"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.client.patch(url, {"thu_dien_tu": "Moi@moc.vn", "mat_khau_hien_tai": "Password@123"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["email_cho_xac_nhan"], "moi@moc.vn")
        self.user.refresh_from_db()
        self.assertEqual(self.user.thu_dien_tu, "profile_test@moc.vn")  # chưa đổi khi chưa nhập mã
        self.assertEqual(mail.outbox[-1].to, ["moi@moc.vn"])
        self.assertEqual(mail.outbox[-1].subject, "[Mộc Kitchen Accounts] - Mã xác thực OTP")

        url_xn = "/api/auth/xac-nhan-doi-email/"
        self.assertEqual(self.client.post(url_xn, {"ma_xac_thuc": "000000"}, format="json").status_code, 400)
        ma = self.user.xac_thuc_email.ma_xac_thuc
        r = self.client.post(url_xn, {"ma_xac_thuc": ma}, format="json")
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual((self.user.thu_dien_tu, self.user.email), ("moi@moc.vn", "moi@moc.vn"))
        self.assertTrue(self.user.xac_thuc_email.da_xac_thuc)  # bản ghi tạo mới không biến tài khoản thành "chờ xác thực"
        thu_bao = mail.outbox[-1]
        self.assertEqual((thu_bao.to, thu_bao.subject), (["profile_test@moc.vn"], "Bạn Đã Thay Đổi Địa Chỉ Email Của Mình"))
        self.assertIn("pro*********@mo***.vn", thu_bao.body)
        # Mã đã dùng thì không dùng lại được.
        self.assertEqual(self.client.post(url_xn, {"ma_xac_thuc": ma}, format="json").status_code, 400)

    def test_doi_email_trung_bi_tu_choi(self):
        NguoiDung.objects.create_user(username="khac", thu_dien_tu="da_co@moc.vn", password="x" * 8)
        r = self.client.patch("/api/auth/profile/", {"thu_dien_tu": "DA_CO@moc.vn", "mat_khau_hien_tai": "Password@123"}, format="json")
        self.assertEqual(r.data["thu_dien_tu"][0], "Email này đã được sử dụng.")

    def test_an_email(self):
        from accounts.services_email import an_email
        self.assertEqual(an_email("vuvan200705@gmail.com"), "vuv********@gm***.com")
        self.assertEqual(an_email("ab@x.vn"), "ab*@x***.vn")

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


class QuenMatKhauTestCase(TestCase):
    QUEN, DAT_LAI = "/api/auth/quen-mat-khau/", "/api/auth/dat-lai-mat-khau/"

    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # giới hạn tần suất dùng cache
        self.client = APIClient()
        self.user = NguoiDung.objects.create_user(
            username="quen", thu_dien_tu="quen@moc.vn", so_dien_thoai="0912345678", password="cu123456")

    def ma(self):
        self.user.xac_thuc_email.refresh_from_db()
        return self.user.xac_thuc_email.ma_xac_thuc

    def test_tim_bang_sdt_gui_ma_ve_email_va_dat_lai(self):
        from django.core import mail
        from rest_framework_simplejwt.tokens import RefreshToken
        r = self.client.post(self.QUEN, {"tai_khoan": "0912 345 678"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data, {"email_an": "que*@mo***.vn"})  # không lộ email đầy đủ
        self.assertEqual(mail.outbox[-1].to, ["quen@moc.vn"])
        refresh_cu = RefreshToken.for_user(self.user)

        du_lieu = {"tai_khoan": "0912345678", "ma_xac_thuc": "000000", "mat_khau_moi": "moi12345"}
        self.assertIn("Còn 4", self.client.post(self.DAT_LAI, du_lieu, format="json").data["detail"])
        self.assertEqual(self.client.post(self.DAT_LAI, dict(du_lieu, mat_khau_moi="123"), format="json").status_code, 400)
        r = self.client.post(self.DAT_LAI, dict(du_lieu, ma_xac_thuc=self.ma()), format="json")
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("moi12345"))
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": str(refresh_cu)}, format="json").status_code, 401)
        # Mã đã dùng thì hết hiệu lực.
        self.assertEqual(self.client.post(self.DAT_LAI, dict(du_lieu, ma_xac_thuc="x"), format="json").status_code, 400)

    def test_khong_tim_thay_va_sdt_trung(self):
        self.assertEqual(self.client.post(self.QUEN, {"tai_khoan": "khong@moc.vn"}, format="json").data["detail"], "Không tìm thấy tài khoản.")
        NguoiDung.objects.create_user(username="trung", thu_dien_tu="trung@moc.vn", so_dien_thoai="0912345678", password="x" * 8)
        self.assertIn("nhiều tài khoản", self.client.post(self.QUEN, {"tai_khoan": "0912345678"}, format="json").data["detail"])
        self.assertEqual(self.client.post(self.QUEN, {"tai_khoan": "QUEN@moc.vn"}, format="json").status_code, 200)

    def test_tai_khoan_bi_khoa_khong_dat_lai_duoc(self):
        NguoiDung.objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.client.post(self.QUEN, {"tai_khoan": "quen@moc.vn"}, format="json").status_code, 400)

    def test_ma_doi_email_va_ma_quen_mat_khau_khong_dung_lan(self):
        dang_nhap = APIClient()
        dang_nhap.force_authenticate(self.user)
        # Đang chờ đổi email: mã đổi email (gửi tới email mới) không đặt lại được mật khẩu.
        dang_nhap.patch("/api/auth/profile/", {"thu_dien_tu": "moi@moc.vn", "mat_khau_hien_tai": "cu123456"}, format="json")
        r = self.client.post(self.DAT_LAI, {"tai_khoan": "quen@moc.vn", "ma_xac_thuc": self.ma(), "mat_khau_moi": "moi12345"}, format="json")
        self.assertEqual(r.status_code, 400)
        # Cách A: gửi mã quên mật khẩu thì huỷ yêu cầu đổi email; mã mới không đổi được email.
        self.client.post(self.QUEN, {"tai_khoan": "quen@moc.vn"}, format="json")
        r = dang_nhap.post("/api/auth/xac-nhan-doi-email/", {"ma_xac_thuc": self.ma()}, format="json")
        self.assertEqual(r.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.thu_dien_tu, "quen@moc.vn")
