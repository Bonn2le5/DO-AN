from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from foods.models import DanhMuc, MonAn
from orders.models import DonHang, ChiTietDonHang


class DanhGiaTuTimMonDaDungTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.khach = User.objects.create_user(username="khach_dg", email="dg@x.vn", thu_dien_tu="dg@x.vn", password="password123")
        self.nguoi_la = User.objects.create_user(username="la_dg", email="la@x.vn", thu_dien_tu="la@x.vn", password="password123")
        dm = DanhMuc.objects.create(ten="Món Chính", duong_dan="mon-chinh-dg")
        self.mon = MonAn.objects.create(danh_muc=dm, ten="Bò lúc lắc", duong_dan="bo-luc-lac-dg", don_gia=Decimal("100000"), con_hang=True, hien_thi=True)
        don = DonHang.objects.create(khach_hang=self.khach, ten_khach="K", sdt_khach="0900000000", trang_thai=DonHang.TrangThai.HOAN_TAT)
        ChiTietDonHang.objects.create(don_hang=don, mon_an=self.mon, so_luong=1, don_gia_luc_dat=Decimal("100000"), thanh_tien=Decimal("100000"))
        self.client = APIClient()

    def _post(self, user):
        self.client.force_authenticate(user)
        return self.client.post("/api/reviews/", {"mon_an": self.mon.id, "diem_danh_gia": 5, "nhan_xet": "Ngon"}, format="json")

    def test_khach_da_dung_mon_danh_gia_duoc_mot_lan(self):
        self.assertEqual(self._post(self.khach).status_code, 201)
        self.assertEqual(self._post(self.khach).status_code, 400)  # đã đánh giá hết phần đã dùng

    def test_nguoi_chua_dung_mon_bi_tu_choi(self):
        self.assertEqual(self._post(self.nguoi_la).status_code, 400)
