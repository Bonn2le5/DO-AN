from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from foods.models import DanhMuc, MonAn, NguyenLieu, DinhMucNguyenLieu
from foods.services import DichVuKho
from orders.models import DonHang, ChiTietDonHang
from orders.services import DichVuDonHang


class TruKhoKhiGuiBepTest(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="nv_kho", email="nv_kho@example.com", thu_dien_tu="nv_kho@example.com",
            password="x", is_staff=True,
        )
        dm = DanhMuc.objects.create(ten="Gỏi")
        self.mon = MonAn.objects.create(danh_muc=dm, ten="Gỏi Đu Đủ Cá Hồi", don_gia=189000)
        self.ca_hoi = NguyenLieu.objects.create(ten="Cá hồi", don_vi="kg", ton_kho_hien_tai=Decimal("1.0"), ton_kho_toi_thieu=Decimal("0.5"))
        DinhMucNguyenLieu.objects.create(mon_an=self.mon, nguyen_lieu=self.ca_hoi, so_luong_can=Decimal("0.2"))
        self.don = DonHang.objects.create(
            ma_don_hang="DH-KHO-1", hinh_thuc=DonHang.HinhThuc.TAI_CHO, ten_khach="K", sdt_khach="0900000000",
            tien_hang=0, tong_tien=0,
        )
        self.line = ChiTietDonHang.objects.create(don_hang=self.don, mon_an=self.mon, so_luong=1, don_gia_luc_dat=189000, thanh_tien=189000)

    def ton(self):
        self.ca_hoi.refresh_from_db()
        return self.ca_hoi.ton_kho_hien_tai

    def test_gui_bep_tru_kho_goi_them_bot_mon_va_huy(self):
        DichVuDonHang.doi_trang_thai(self.don, DonHang.TrangThai.DA_XAC_NHAN, self.staff)
        self.assertEqual(self.ton(), Decimal("0.8"))
        self.assertEqual(DichVuKho.canh_bao_sap_het([self.mon.id]), [])

        # gọi thêm 2 món rồi gửi bếp lần 2
        self.line.so_luong = 3; self.line.save()
        DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don, nguoi_dung=self.staff)
        self.assertEqual(self.ton(), Decimal("0.4"))
        warn = DichVuKho.canh_bao_sap_het([self.mon.id])
        self.assertEqual([w["ten"] for w in warn], ["Cá hồi"])
        self.assertEqual(warn[0]["mon_an"], ["Gỏi Đu Đủ Cá Hồi"])

        # gửi lại không đổi gì -> không trừ thêm
        DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don, nguoi_dung=self.staff)
        self.assertEqual(self.ton(), Decimal("0.4"))

        # bớt 1 món -> hoàn kho
        self.line.so_luong = 2; self.line.save()
        DichVuKho.dong_bo_nguyen_lieu_don(don_hang=self.don, nguoi_dung=self.staff)
        self.assertEqual(self.ton(), Decimal("0.6"))

        # hủy đơn -> hoàn toàn bộ
        DichVuDonHang.doi_trang_thai(self.don, DonHang.TrangThai.DA_HUY, self.staff)
        self.assertEqual(self.ton(), Decimal("1.0"))

    def test_khong_du_kho_thi_chan(self):
        self.line.so_luong = 6; self.line.save()
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            DichVuDonHang.doi_trang_thai(self.don, DonHang.TrangThai.DA_XAC_NHAN, self.staff)
        self.assertEqual(self.ton(), Decimal("1.0"))


from rest_framework.test import APIClient
from foods.models import LichSuXuatNhapKho


class ApiNguyenLieuKhoTest(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="ad_kho", email="ad_kho@example.com", thu_dien_tu="ad_kho@example.com", password="x",
        )
        self.c = APIClient()
        self.c.force_authenticate(self.admin)
        dm = DanhMuc.objects.create(ten="Lẩu")
        self.mon = MonAn.objects.create(danh_muc=dm, ten="Lẩu Thái", don_gia=300000)

    def test_tao_nguyen_lieu_ghi_ton_dau_ky_va_khong_sua_ton_truc_tiep(self):
        r = self.c.post("/api/ingredients/", {"ten": "Tôm", "don_vi": "kg", "ton_kho_hien_tai": "5", "ton_kho_toi_thieu": "2"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        nl_id = r.json()["id"]
        gd = LichSuXuatNhapKho.objects.get(nguyen_lieu_id=nl_id)
        self.assertEqual((gd.loai_giao_dich, gd.so_luong, gd.ton_kho_sau), ("nhap", Decimal("5"), Decimal("5")))

        r = self.c.patch(f"/api/ingredients/{nl_id}/", {"ton_kho_hien_tai": "999"}, format="json")
        self.assertEqual(Decimal(r.json()["ton_kho_hien_tai"]), Decimal("5"))

    def test_phieu_kho_dinh_muc_va_xoa(self):
        nl = NguyenLieu.objects.create(ten="Nấm", don_vi="kg", ton_kho_hien_tai=Decimal("3"), ton_kho_toi_thieu=Decimal("1"))
        r = self.c.post("/api/inventory-transactions/", {"nguyen_lieu": nl.id, "loai_giao_dich": "xuat", "so_luong": "2.5"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(Decimal(r.json()["ton_kho_sau"]), Decimal("0.5"))
        self.assertEqual(r.json()["loai_tham_chieu"], "thu_cong")
        self.assertEqual(self.c.post("/api/inventory-transactions/", {"nguyen_lieu": nl.id, "loai_giao_dich": "xuat", "so_luong": "1"}, format="json").status_code, 400)
        self.assertEqual(self.c.post("/api/inventory-transactions/", {"nguyen_lieu": nl.id, "loai_giao_dich": "dieu_chinh", "so_luong": "4"}, format="json").status_code, 201)
        self.assertEqual(len(self.c.get(f"/api/inventory-transactions/?nguyen_lieu={nl.id}").json()), 2)
        self.assertEqual(self.c.delete("/api/inventory-transactions/1/").status_code, 405)

        r = self.c.post("/api/dinh-muc-nguyen-lieu/", {"mon_an": self.mon.id, "nguyen_lieu": nl.id, "so_luong_can": "0.1"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(self.c.post("/api/dinh-muc-nguyen-lieu/", {"mon_an": self.mon.id, "nguyen_lieu": nl.id, "so_luong_can": "0.1"}, format="json").status_code, 400)
        self.assertEqual(self.c.post("/api/dinh-muc-nguyen-lieu/", {"mon_an": self.mon.id, "nguyen_lieu": nl.id, "so_luong_can": "0"}, format="json").status_code, 400)
        row = next(i for i in self.c.get("/api/ingredients/").json() if i["id"] == nl.id)
        self.assertEqual(row["so_mon_dinh_muc"], 1)

        r = self.c.delete(f"/api/ingredients/{nl.id}/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("không thể xoá", r.json()["nguyen_lieu"])
