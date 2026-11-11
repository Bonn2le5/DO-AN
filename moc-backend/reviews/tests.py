from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from foods.models import DanhMuc, MonAn
from orders.models import DonHang, ChiTietDonHang
from recommendations.models import TuongTacMonAn
from .models import DanhGia, DanhGiaBuaAn


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


class DanhGiaBuaAnTest(TestCase):
    """Màn hình "Đánh giá bữa ăn": liệt kê đơn chờ đánh giá và gửi một lần cho cả đơn."""

    def setUp(self):
        User = get_user_model()
        self.khach = User.objects.create_user(username="khach_ba", email="ba@x.vn", thu_dien_tu="ba@x.vn", password="password123")
        self.khac = User.objects.create_user(username="khac_ba", email="kb@x.vn", thu_dien_tu="kb@x.vn", password="password123")
        dm = DanhMuc.objects.create(ten="Lẩu", duong_dan="lau-ba")
        self.lau = MonAn.objects.create(danh_muc=dm, ten="Lẩu Thái", duong_dan="lau-thai-ba", don_gia=Decimal("200000"), con_hang=True, hien_thi=True)
        self.nuong = MonAn.objects.create(danh_muc=dm, ten="Bò nướng", duong_dan="bo-nuong-ba", don_gia=Decimal("150000"), con_hang=True, hien_thi=True)
        self.don = self._don(DonHang.TrangThai.HOAN_TAT)
        self.dong_lau = self._dong(self.don, self.lau)
        self.dong_nuong = self._dong(self.don, self.nuong)
        self.don_dang_an = self._don(DonHang.TrangThai.DANG_CHE_BIEN)
        self._dong(self.don_dang_an, self.lau)
        self.client = APIClient()
        self.client.force_authenticate(self.khach)

    def _don(self, trang_thai, khach=None):
        return DonHang.objects.create(khach_hang=khach or self.khach, ten_khach="K", sdt_khach="0900000000", trang_thai=trang_thai)

    def _dong(self, don, mon):
        return ChiTietDonHang.objects.create(don_hang=don, mon_an=mon, so_luong=1, don_gia_luc_dat=mon.don_gia, thanh_tien=mon.don_gia)

    def _gui(self, body):
        return self.client.post("/api/danh-gia/bua-an/", body, format="json")

    def test_chi_liet_ke_don_hoan_tat_cua_minh(self):
        self._dong(self._don(DonHang.TrangThai.HOAN_TAT, khach=self.khac), self.lau)
        r = self.client.get("/api/danh-gia/cho-danh-gia/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual([d["id"] for d in r.data], [self.don.id])
        self.assertEqual([m["ten_mon"] for m in r.data[0]["mon"]], ["Lẩu Thái", "Bò nướng"])
        self.assertIsNone(r.data[0]["danh_gia_bua_an"])

    def test_gui_ca_bua_mot_lan(self):
        r = self._gui({
            "don_hang": self.don.id,
            "mon": [
                {"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 5, "nhan_xet": "Ngon"},
                {"chi_tiet_don_hang": self.dong_nuong.id, "diem_danh_gia": 2},
            ],
            "diem_phuc_vu": 4, "diem_khong_gian": 5, "nhan_xet": "Nhân viên nhiệt tình",
        })
        self.assertEqual(r.status_code, 201, r.data)
        self.lau.refresh_from_db()
        self.assertEqual(float(self.lau.diem_danh_gia), 5.0)
        self.assertEqual(DanhGiaBuaAn.objects.get(don_hang=self.don).diem_phuc_vu, 4)
        # Tín hiệu gợi ý theo số sao: 5★ → +5, 2★ → −2.5
        w = dict(TuongTacMonAn.objects.filter(nguoi_dung=self.khach, loai_tuong_tac="danh_gia").values_list("mon_an_id", "trong_so"))
        self.assertEqual((float(w[self.lau.id]), float(w[self.nuong.id])), (5.0, -2.5))
        # Đã chấm đủ → đơn biến khỏi danh sách chờ
        self.assertEqual(self.client.get("/api/danh-gia/cho-danh-gia/").data, [])

    def test_danh_gia_tung_phan_va_khong_cho_cham_lai(self):
        r = self._gui({"don_hang": self.don.id, "mon": [{"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 4}]})
        self.assertEqual(r.status_code, 201)
        con_lai = self.client.get("/api/danh-gia/cho-danh-gia/").data[0]["mon"]
        self.assertEqual([m["danh_gia"] is None for m in con_lai], [False, True])

        r = self._gui({"don_hang": self.don.id, "mon": [{"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 1}]})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(DanhGia.objects.filter(chi_tiet_don_hang=self.dong_lau).count(), 1)

        self.assertEqual(self._gui({"don_hang": self.don.id, "diem_phuc_vu": 5, "diem_khong_gian": 5}).status_code, 201)
        self.assertEqual(self._gui({"don_hang": self.don.id, "diem_phuc_vu": 1, "diem_khong_gian": 1}).status_code, 400)

    def test_tu_choi_du_lieu_sai(self):
        don_khac = self._don(DonHang.TrangThai.HOAN_TAT, khach=self.khac)
        dong_khac = self._dong(don_khac, self.lau)
        cases = [
            {"don_hang": don_khac.id, "mon": [{"chi_tiet_don_hang": dong_khac.id, "diem_danh_gia": 5}]},  # đơn người khác
            {"don_hang": self.don_dang_an.id, "diem_phuc_vu": 5, "diem_khong_gian": 5},                  # chưa hoàn tất
            {"don_hang": self.don.id, "mon": [{"chi_tiet_don_hang": dong_khac.id, "diem_danh_gia": 5}]},  # dòng không thuộc đơn
            {"don_hang": self.don.id, "mon": [{"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 6}]},
            {"don_hang": self.don.id, "diem_phuc_vu": 5},                                                 # thiếu điểm không gian
            {"don_hang": self.don.id},                                                                    # không chấm gì
            {"don_hang": self.don.id, "mon": [
                {"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 5},
                {"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 4},
            ]},                                                                                           # trùng dòng
        ]
        for body in cases:
            self.assertEqual(self._gui(body).status_code, 400, body)
        self.assertFalse(DanhGia.objects.exists())
        self.assertFalse(DanhGiaBuaAn.objects.exists())

    def test_co_the_danh_gia_mon(self):
        url = "/api/danh-gia/co-the/?mon_an={}"
        self.assertTrue(self.client.get(url.format(self.lau.id)).data["co_the"])
        self._gui({"don_hang": self.don.id, "mon": [{"chi_tiet_don_hang": self.dong_lau.id, "diem_danh_gia": 5}]})
        self.assertFalse(self.client.get(url.format(self.lau.id)).data["co_the"])

        self.client.force_authenticate(self.khac)
        self.assertFalse(self.client.get(url.format(self.nuong.id)).data["co_the"])
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(url.format(self.lau.id)).status_code, (401, 403))
        self.assertIn(self.client.get("/api/danh-gia/cho-danh-gia/").status_code, (401, 403))
