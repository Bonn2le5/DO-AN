"""Test hồi quy cho các lỗi nghiệp vụ đặt bàn, huỷ và hoàn cọc."""
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung
from branches.models import ChiNhanh
from payments.models import PhieuHoanTien
from reservations.models import BanAn, DatBan, PhienPhucVu
from reservations.services import DichVuPhienPhucVu

VN = ZoneInfo("Asia/Ho_Chi_Minh")


class NghiepVuDatBanTest(TestCase):
    def setUp(self):
        self.cn = ChiNhanh.objects.create(ten="CN", dia_chi="a")
        self.b1 = BanAn.objects.create(chi_nhanh=self.cn, so_ban="T1", suc_chua=4)
        self.b2 = BanAn.objects.create(chi_nhanh=self.cn, so_ban="T2", suc_chua=4)
        self.admin = NguoiDung.objects.create_user(
            username="ad", thu_dien_tu="ad@x.vn", email="ad@x.vn", password="Passw0rd!x",
            is_superuser=True, is_staff=True,
        )
        self.kh = NguoiDung.objects.create_user(
            username="kh", thu_dien_tu="kh@x.vn", email="kh@x.vn", password="Passw0rd!x"
        )
        self.api_kh = APIClient()
        self.api_kh.force_authenticate(self.kh)
        self.api_ad = APIClient()
        self.api_ad.force_authenticate(self.admin)

    def _dat_ban(self, sau, **kw):
        hen = datetime.now(VN) + sau
        d = dict(
            nguoi_dung=self.kh, chi_nhanh=self.cn, ngay_dat=hen.date(),
            gio_bat_dau=hen.time().replace(microsecond=0), so_luong_khach=2,
            hinh_thuc="chi_giu_cho", ten_khach="K", sdt_khach="09",
        )
        d.update(kw)
        return DatBan.objects.create(**d)

    def _co_coc(self, sau, **kw):
        return self._dat_ban(
            sau, hinh_thuc="dat_ban_va_goi_mon", yeu_cau_dat_coc=True, so_tien_coc=Decimal("40000"), **kw
        )

    def test_hoan_coc_tinh_theo_gio_viet_nam(self):
        """Huỷ trước 20 giờ là mốc 6–24h (hoàn 50%), không phải >24h."""
        db = self._co_coc(timedelta(hours=20), trang_thai="da_xac_nhan", trang_thai_coc="thanh_cong")
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["moc_thoi_gian"], "tu_6_den_24h")
        self.assertEqual(r.data["so_tien_hoan"], 20000.0)

        db2 = self._co_coc(timedelta(hours=2), trang_thai="da_xac_nhan", trang_thai_coc="thanh_cong")
        r = self.api_kh.post(f"/api/dat-ban/{db2.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.data["moc_thoi_gian"], "trong_6h")
        self.assertEqual(r.data["so_tien_hoan"], 0.0)

    def test_huy_phieu_chua_tra_coc_khong_lap_phieu_hoan(self):
        db = self._co_coc(timedelta(days=3), trang_thai="cho_thanh_toan")
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(db.trang_thai_coc, DatBan.TrangThaiCoc.CHUA_THANH_TOAN)
        self.assertFalse(PhieuHoanTien.objects.filter(dat_ban=db).exists())
        self.assertEqual(r.data["so_tien_hoan"], 0.0)

    def test_huy_phien_roi_xep_lai_ban_khac(self):
        db = self._dat_ban(timedelta(hours=1), trang_thai="khach_da_den")
        p1 = DichVuPhienPhucVu.xep_ban_va_bat_dau(nguoi_dung=self.admin, dat_ban_id=db.id, ban_an_id=self.b1.id)
        DichVuPhienPhucVu.huy_phien(nguoi_dung=self.admin, phien_id=p1.id)
        p2 = DichVuPhienPhucVu.xep_ban_va_bat_dau(nguoi_dung=self.admin, dat_ban_id=db.id, ban_an_id=self.b2.id)
        p1.refresh_from_db()
        self.assertIsNone(p1.dat_ban_id)
        self.assertIn(db.ma_dat_ban, p1.ghi_chu)
        self.assertEqual(p2.dat_ban_id, db.id)
        self.assertEqual(PhienPhucVu.objects.get(dat_ban=db).ban_an_id, self.b2.id)

    def test_ghi_nhan_hoan_coc_nhieu_phieu(self):
        for i in range(2):
            db = self._co_coc(
                timedelta(days=2, minutes=i), trang_thai="da_huy", trang_thai_coc="thanh_cong", huy_luc=timezone.now()
            )
            r = self.api_ad.post(
                f"/api/dat-ban/{db.id}/ghi-nhan-hoan-tien/", {"percent": 100, "reference": f"REF{i}"}, format="json"
            )
            self.assertEqual(r.status_code, 200, r.content)
        ma = list(PhieuHoanTien.objects.values_list("ma_phieu_hoan", flat=True))
        self.assertEqual(len(set(ma)), 2)
        self.assertTrue(all(ma))

    def test_khach_khong_tu_huy_khi_dang_ngoi_ban(self):
        db = self._dat_ban(timedelta(minutes=5), trang_thai="khach_da_den")
        p = DichVuPhienPhucVu.xep_ban_va_bat_dau(nguoi_dung=self.admin, dat_ban_id=db.id, ban_an_id=self.b1.id)
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.status_code, 400, r.content)
        db.refresh_from_db()
        p.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.KHACH_DA_DEN)
        self.assertEqual(p.trang_thai, PhienPhucVu.TrangThai.DANG_PHUC_VU)

    def test_khong_chuyen_phieu_da_huy_ve_da_xac_nhan(self):
        db = self._co_coc(timedelta(days=1), trang_thai="da_huy")
        r = self.api_ad.patch(f"/api/dat-ban/{db.id}/trang_thai/", {"status": "da_xac_nhan"}, format="json")
        self.assertEqual(r.status_code, 400, r.content)
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.DA_HUY)

    def test_phieu_cho_thanh_toan_khong_duoc_xac_nhan_tay(self):
        db = self._co_coc(timedelta(days=1), trang_thai="cho_thanh_toan")
        r = self.api_ad.patch(f"/api/dat-ban/{db.id}/trang_thai/", {"status": "da_xac_nhan"}, format="json")
        self.assertEqual(r.status_code, 400, r.content)

    def test_chuyen_trang_thai_hop_le_van_chay(self):
        db = self._dat_ban(timedelta(days=1), trang_thai="cho_xac_nhan")
        r = self.api_ad.patch(f"/api/dat-ban/{db.id}/trang_thai/", {"status": "da_xac_nhan"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        r = self.api_ad.patch(f"/api/dat-ban/{db.id}/trang_thai/", {"status": "khach_khong_den"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
