"""Trang tài khoản → Lịch sử đặt bàn: danh sách ?mine=1 và khách tự huỷ."""
from datetime import time, timedelta
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung
from branches.models import ChiNhanh
from payments.models import PhieuHoanTien
from reservations.models import DatBan


class LichSuDatBanTest(TestCase):
    def setUp(self):
        self.branch = ChiNhanh.objects.create(ten="CN1", dia_chi="a")
        self.user = NguoiDung.objects.create_user(
            username="kh", thu_dien_tu="kh@x.vn", email="kh@x.vn", password="Passw0rd!x"
        )
        self.other = NguoiDung.objects.create_user(
            username="kh2", thu_dien_tu="kh2@x.vn", email="kh2@x.vn", password="Passw0rd!x"
        )
        self.c = APIClient()
        self.c.force_authenticate(self.user)

    def dat_ban(self, user=None, **kw):
        kw.setdefault("trang_thai", DatBan.TrangThai.DA_XAC_NHAN)
        return DatBan.objects.create(
            nguoi_dung=user or self.user, chi_nhanh=self.branch,
            ngay_dat=timezone.localdate() + timedelta(days=3), gio_bat_dau=time(18),
            so_luong_khach=2, **kw,
        )

    def test_chi_thay_phieu_cua_minh(self):
        mine = self.dat_ban()
        self.dat_ban(user=self.other)
        r = self.c.get("/api/dat-ban/", {"mine": 1})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([d["id"] for d in r.json()], [mine.id])

    def test_so_query_khong_tang_theo_so_phieu(self):
        def dem():
            with CaptureQueriesContext(connection) as ctx:
                self.assertEqual(self.c.get("/api/dat-ban/", {"mine": 1}).status_code, 200)
            return len(ctx)

        for _ in range(2):
            self.dat_ban()
        it = dem()
        for _ in range(8):
            self.dat_ban()
        self.assertEqual(dem(), it)

    def test_refund_record_lay_phieu_moi_nhat(self):
        db = self.dat_ban(trang_thai=DatBan.TrangThai.DA_HUY, so_tien_coc=Decimal("100000"))
        for pct, tien in (("50", "50000"), ("100", "100000")):
            PhieuHoanTien.objects.create(
                dat_ban=db, so_tien_coc_goc=Decimal("100000"), phan_tram_hoan=Decimal(pct),
                so_tien_hoan=Decimal(tien), so_tien_phat=Decimal("0"),
                moc_thoi_gian="truoc_24h", so_gio_truoc_gio_hen=Decimal("48"),
            )
        rec = self.c.get("/api/dat-ban/", {"mine": 1}).json()[0]["refund_record"]
        self.assertEqual(rec["amount"], 100000.0)

    def test_khach_tu_huy_truoc_check_in(self):
        db = self.dat_ban()
        r = self.c.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {"ly_do": "Bận"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(db.ly_do_huy, "Bận")

    def test_khong_huy_duoc_khi_dang_dung_bua(self):
        db = self.dat_ban(trang_thai=DatBan.TrangThai.KHACH_DA_DEN)
        r = self.c.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.status_code, 400)
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.KHACH_DA_DEN)

    def test_khong_huy_phieu_nguoi_khac(self):
        db = self.dat_ban(user=self.other)
        r = self.c.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.status_code, 404)

    def test_thanh_toan_coc_qua_han_bao_da_huy(self):
        db = self.dat_ban(
            trang_thai=DatBan.TrangThai.CHO_THANH_TOAN, so_tien_coc=Decimal("200000"),
            trang_thai_coc=DatBan.TrangThaiCoc.CHUA_THANH_TOAN,
        )
        DatBan.objects.filter(pk=db.pk).update(tao_luc=timezone.now() - timedelta(hours=2))
        r = self.c.post(
            "/api/thanh-toan/payos/tao-phien/",
            {"loai_thanh_toan": "tien_coc", "dat_ban_id": db.id}, format="json",
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("đã bị huỷ do quá hạn", str(r.json()["dat_ban_id"]))
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.DA_HUY)
