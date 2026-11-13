from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from branches.models import ChiNhanh
from foods.models import DanhMuc, DinhMucNguyenLieu, LichSuXuatNhapKho, MonAn, NguyenLieu, TonKhoChiNhanh
from foods.services import DichVuKho
from orders.models import ChiTietDonHang, DonHang
from orders.services import DichVuDonHang


class TruKhoTheoChiNhanhTest(TestCase):
    """Gửi bếp trừ kho của đúng chi nhánh phục vụ đơn; kho chi nhánh khác không đổi."""

    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="nv_kho", email="nv_kho@example.com", thu_dien_tu="nv_kho@example.com",
            password="x", is_staff=True,
        )
        self.cn1 = ChiNhanh.objects.create(ten="CN 1", dia_chi="a")
        self.cn2 = ChiNhanh.objects.create(ten="CN 2", dia_chi="b")
        dm = DanhMuc.objects.create(ten="Gỏi")
        self.mon = MonAn.objects.create(danh_muc=dm, ten="Gỏi Đu Đủ Cá Hồi", don_gia=189000)
        self.ca_hoi = NguyenLieu.objects.create(ten="Cá hồi", don_vi="kg")
        for cn in (self.cn1, self.cn2):
            TonKhoChiNhanh.objects.create(nguyen_lieu=self.ca_hoi, chi_nhanh=cn,
                                          ton_kho_hien_tai=Decimal("1.0"), ton_kho_toi_thieu=Decimal("0.5"))
        DinhMucNguyenLieu.objects.create(mon_an=self.mon, nguyen_lieu=self.ca_hoi, so_luong_can=Decimal("0.2"))
        self.don = DonHang.objects.create(
            ma_don_hang="DH-KHO-1", hinh_thuc=DonHang.HinhThuc.TAI_CHO, ten_khach="K", sdt_khach="0900000000",
            tien_hang=0, tong_tien=0, chi_nhanh=self.cn1,
        )
        self.line = ChiTietDonHang.objects.create(don_hang=self.don, mon_an=self.mon, so_luong=1, don_gia_luc_dat=189000, thanh_tien=189000)

    def ton(self, cn):
        return TonKhoChiNhanh.objects.get(nguyen_lieu=self.ca_hoi, chi_nhanh=cn).ton_kho_hien_tai

    def test_gui_bep_tru_dung_chi_nhanh_goi_them_bot_mon_va_huy(self):
        DichVuDonHang.doi_trang_thai(self.don, DonHang.TrangThai.DA_XAC_NHAN, self.staff)
        self.assertEqual(self.ton(self.cn1), Decimal("0.8"))
        self.assertEqual(self.ton(self.cn2), Decimal("1.0"))
        self.assertEqual(DichVuKho.canh_bao_sap_het([self.mon.id], self.cn1.id), [])

        self.line.so_luong = 3; self.line.save()
        DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don, nguoi_dung=self.staff)
        self.assertEqual(self.ton(self.cn1), Decimal("0.4"))
        warn = DichVuKho.canh_bao_sap_het([self.mon.id], self.cn1.id)
        self.assertEqual([(w["ten"], w["mon_an"]) for w in warn], [("Cá hồi", ["Gỏi Đu Đủ Cá Hồi"])])
        self.assertEqual(DichVuKho.canh_bao_sap_het([self.mon.id], self.cn2.id), [])  # kho CN2 vẫn đủ

        DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don, nguoi_dung=self.staff)  # gửi lại: không trừ thêm
        self.assertEqual(self.ton(self.cn1), Decimal("0.4"))

        self.line.so_luong = 2; self.line.save()
        DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don, nguoi_dung=self.staff)
        self.assertEqual(self.ton(self.cn1), Decimal("0.6"))

        DichVuDonHang.doi_trang_thai(self.don, DonHang.TrangThai.DA_HUY, self.staff)
        self.assertEqual((self.ton(self.cn1), self.ton(self.cn2)), (Decimal("1.0"), Decimal("1.0")))
        self.assertTrue(all(ls.chi_nhanh_id == self.cn1.id for ls in LichSuXuatNhapKho.objects.all()))

    def test_khong_du_kho_thi_chan(self):
        self.line.so_luong = 6; self.line.save()
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(self.don, DonHang.TrangThai.DA_XAC_NHAN, self.staff)
        self.assertEqual(self.ton(self.cn1), Decimal("1.0"))

    def test_don_khong_co_chi_nhanh_thi_chan(self):
        self.don.chi_nhanh = None; self.don.save()
        with self.assertRaises(ValidationError):
            DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don)

    def test_chuyen_kho(self):
        xuat, nhap = DichVuKho.chuyen_kho(nguyen_lieu_id=self.ca_hoi.id, tu_chi_nhanh_id=self.cn1.id,
                                          den_chi_nhanh_id=self.cn2.id, so_luong="0.3", ghi_chu="thiếu cá")
        self.assertEqual((self.ton(self.cn1), self.ton(self.cn2)), (Decimal("0.7"), Decimal("1.3")))
        self.assertEqual((xuat.loai_giao_dich, nhap.loai_giao_dich), ("xuat", "nhap"))
        self.assertEqual((xuat.id_tham_chieu, nhap.id_tham_chieu), (nhap.id, xuat.id))
        self.assertIn("CN 2", xuat.ghi_chu)
        with self.assertRaises(ValidationError):  # không đủ hàng ở kho gửi
            DichVuKho.chuyen_kho(nguyen_lieu_id=self.ca_hoi.id, tu_chi_nhanh_id=self.cn1.id,
                                 den_chi_nhanh_id=self.cn2.id, so_luong="5")
        with self.assertRaises(ValidationError):  # cùng chi nhánh
            DichVuKho.chuyen_kho(nguyen_lieu_id=self.ca_hoi.id, tu_chi_nhanh_id=self.cn1.id,
                                 den_chi_nhanh_id=self.cn1.id, so_luong="0.1")


class ApiKhoChiNhanhTest(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="ad_kho", email="ad_kho@example.com", thu_dien_tu="ad_kho@example.com", password="x",
        )
        self.c = APIClient()
        self.c.force_authenticate(self.admin)
        self.cn1 = ChiNhanh.objects.create(ten="CN 1", dia_chi="a")
        self.cn2 = ChiNhanh.objects.create(ten="CN 2", dia_chi="b")
        self.mon = MonAn.objects.create(danh_muc=DanhMuc.objects.create(ten="Lẩu"), ten="Lẩu Thái", don_gia=300000)

    def test_tao_nguyen_lieu_tao_ton_moi_chi_nhanh(self):
        r = self.c.post("/api/ingredients/", {"ten": "Tôm", "don_vi": "kg", "ton_kho_toi_thieu": "2"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        rows = TonKhoChiNhanh.objects.filter(nguyen_lieu_id=r.json()["id"]).order_by("chi_nhanh_id")
        self.assertEqual([(t.chi_nhanh_id, t.ton_kho_hien_tai, t.ton_kho_toi_thieu) for t in rows],
                         [(self.cn1.id, 0, 2), (self.cn2.id, 0, 2)])

    def test_phieu_kho_theo_chi_nhanh_va_danh_sach(self):
        nl = NguyenLieu.objects.create(ten="Nấm", don_vi="kg")
        url = "/api/inventory-transactions/"
        # Quản trị viên phải chọn chi nhánh khi lập phiếu
        self.assertEqual(self.c.post(url, {"nguyen_lieu": nl.id, "loai_giao_dich": "nhap", "so_luong": "3"}, format="json").status_code, 400)
        r = self.c.post(url, {"nguyen_lieu": nl.id, "chi_nhanh": self.cn1.id, "loai_giao_dich": "nhap", "so_luong": "3"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual((r.json()["chi_nhanh"], Decimal(r.json()["ton_kho_sau"])), (self.cn1.id, Decimal("3")))
        r = self.c.post(url, {"nguyen_lieu": nl.id, "chi_nhanh": self.cn2.id, "loai_giao_dich": "xuat", "so_luong": "1"}, format="json")
        self.assertEqual(r.status_code, 400)  # kho CN2 đang 0
        r = self.c.post(url, {"nguyen_lieu": nl.id, "chi_nhanh": self.cn1.id, "loai_giao_dich": "dieu_chinh", "so_luong": "2.5"}, format="json")
        self.assertEqual(Decimal(r.json()["ton_kho_sau"]), Decimal("2.5"))

        one = next(i for i in self.c.get(f"/api/ingredients/?chi_nhanh={self.cn1.id}").json() if i["id"] == nl.id)
        self.assertEqual((Decimal(one["ton_kho_hien_tai"]), len(one["ton_kho"])), (Decimal("2.5"), 1))
        tat_ca = next(i for i in self.c.get("/api/ingredients/").json() if i["id"] == nl.id)
        self.assertEqual(len(tat_ca["ton_kho"]), 2)
        self.assertEqual(len(self.c.get(f"{url}?chi_nhanh={self.cn2.id}").json()), 0)
        self.assertEqual(len(self.c.get(f"{url}?chi_nhanh={self.cn1.id}").json()), 2)

    def test_chuyen_kho_api_va_sua_toi_thieu(self):
        nl = NguyenLieu.objects.create(ten="Mực", don_vi="kg")
        DichVuKho.lap_phieu(nguyen_lieu_id=nl.id, chi_nhanh_id=self.cn1.id, loai_giao_dich="nhap", so_luong=4)
        r = self.c.post("/api/kho/chuyen-kho/", {"nguyen_lieu": nl.id, "tu_chi_nhanh": self.cn1.id,
                                                 "den_chi_nhanh": self.cn2.id, "so_luong": "1.5"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(Decimal(r.json()["nhap"]["ton_kho_sau"]), Decimal("1.5"))
        tk = TonKhoChiNhanh.objects.get(nguyen_lieu=nl, chi_nhanh=self.cn2)
        r = self.c.patch(f"/api/ton-kho/{tk.id}/", {"ton_kho_toi_thieu": "1", "ton_kho_hien_tai": "999"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        tk.refresh_from_db()
        self.assertEqual((tk.ton_kho_toi_thieu, tk.ton_kho_hien_tai), (Decimal("1"), Decimal("1.5")))

    def test_xoa_nguyen_lieu_da_co_lich_su_bi_chan(self):
        nl = NguyenLieu.objects.create(ten="Bơ", don_vi="kg")
        DichVuKho.lap_phieu(nguyen_lieu_id=nl.id, chi_nhanh_id=self.cn1.id, loai_giao_dich="nhap", so_luong=1)
        r = self.c.delete(f"/api/ingredients/{nl.id}/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("không thể xoá", r.json()["nguyen_lieu"])
