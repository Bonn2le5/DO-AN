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


    # --- Khách huỷ phiếu đã cọc chờ nhân viên hoàn thật; xác nhận tay không lùi trạng thái phiếu ---
    def _coc_da_tra(self, sau, trang_thai="da_xac_nhan"):
        from payments.models import ThanhToan
        db = self._co_coc(sau, trang_thai=trang_thai, trang_thai_coc="thanh_cong")
        tt = ThanhToan.objects.create(dat_ban=db, loai_thanh_toan="tien_coc", phuong_thuc="payos",
                                      so_tien=db.so_tien_coc, nguoi_dung=self.kh, trang_thai="thanh_cong")
        return db, tt

    def test_khach_huy_co_tien_hoan_thi_cho_nhan_vien_chuyen_khoan(self):
        db, tt = self._coc_da_tra(timedelta(days=3))
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["so_tien_hoan"], 40000.0)
        self.assertEqual(r.data["trang_thai_hoan"], "cho_hoan")
        db.refresh_from_db(); tt.refresh_from_db()
        # Chưa ai chuyển tiền: không có phiếu hoàn, cọc và thanh toán vẫn "thành công" → hiện ở "cần hoàn cọc"
        self.assertEqual(db.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(db.trang_thai_coc, DatBan.TrangThaiCoc.THANH_CONG)
        self.assertEqual(tt.trang_thai, "thanh_cong")
        self.assertFalse(PhieuHoanTien.objects.filter(dat_ban=db).exists())

        r = self.api_ad.post(f"/api/dat-ban/{db.id}/ghi-nhan-hoan-tien/", {"percent": 100, "reference": "CK001"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        db.refresh_from_db(); tt.refresh_from_db()
        self.assertEqual(db.trang_thai_coc, DatBan.TrangThaiCoc.DA_HOAN_TIEN)
        self.assertEqual(tt.trang_thai, "da_hoan_tien")
        phieu = PhieuHoanTien.objects.get(dat_ban=db)
        self.assertEqual(phieu.so_tien_hoan, Decimal("40000"))
        self.assertEqual(phieu.du_lieu_chi_tiet["reference"], "CK001")

    def test_khach_huy_sat_gio_mat_coc_thi_dong_ngay(self):
        db, tt = self._coc_da_tra(timedelta(hours=2))
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.data["so_tien_hoan"], 0.0)
        self.assertEqual(r.data["trang_thai_hoan"], "khong_hoan")
        phieu = PhieuHoanTien.objects.get(dat_ban=db)
        self.assertEqual(phieu.trang_thai, "that_bai")
        self.assertEqual(phieu.so_tien_phat, Decimal("40000"))
        tt.refresh_from_db()
        self.assertEqual(tt.trang_thai, "thanh_cong")  # tiền giữ lại, không hoàn

    def test_xac_nhan_tay_khong_hoi_sinh_phieu_da_huy(self):
        from payments.models import ThanhToan
        db = self._co_coc(timedelta(days=1), trang_thai="da_huy")
        tt = ThanhToan.objects.create(dat_ban=db, loai_thanh_toan="tien_coc", phuong_thuc="chuyen_khoan",
                                      so_tien=db.so_tien_coc, nguoi_dung=self.kh)
        r = self.api_ad.post(f"/api/thanh-toan/{tt.id}/xac_nhan_thanh_cong/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(db.trang_thai_coc, DatBan.TrangThaiCoc.THANH_CONG)  # → hiện ở "cần hoàn cọc"

    def test_xac_nhan_tay_khong_lui_khach_dang_ngoi(self):
        from payments.models import ThanhToan
        db = self._co_coc(timedelta(minutes=30), trang_thai="khach_da_den")
        tt = ThanhToan.objects.create(dat_ban=db, loai_thanh_toan="tien_coc", phuong_thuc="chuyen_khoan",
                                      so_tien=db.so_tien_coc, nguoi_dung=self.kh)
        self.api_ad.post(f"/api/thanh-toan/{tt.id}/xac_nhan_thanh_cong/", {}, format="json")
        db.refresh_from_db()
        self.assertEqual(db.trang_thai, DatBan.TrangThai.KHACH_DA_DEN)

    def test_xac_nhan_tay_phieu_dang_cho_va_khong_xac_nhan_lai(self):
        from payments.models import ThanhToan
        db = self._co_coc(timedelta(days=1), trang_thai="cho_thanh_toan")
        tt = ThanhToan.objects.create(dat_ban=db, loai_thanh_toan="tien_coc", phuong_thuc="chuyen_khoan",
                                      so_tien=db.so_tien_coc, nguoi_dung=self.kh)
        r = self.api_ad.post(f"/api/thanh-toan/{tt.id}/xac_nhan_thanh_cong/", {}, format="json")
        db.refresh_from_db()
        self.assertEqual((r.status_code, db.trang_thai), (200, DatBan.TrangThai.DA_XAC_NHAN))
        r = self.api_ad.post(f"/api/thanh-toan/{tt.id}/xac_nhan_thanh_cong/", {}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_ty_le_hoan_theo_chinh_sach_coc_da_cau_hinh(self):
        from reservations.models import ChinhSachDatCoc, QuyTacHuyDatCoc
        chung = ChinhSachDatCoc.objects.create(phan_tram_coc=Decimal("20"))
        QuyTacHuyDatCoc.objects.create(chinh_sach=chung, moc_thoi_gian="truoc_24h", phan_tram_hoan_tien=Decimal("10"))
        rieng = ChinhSachDatCoc.objects.create(chi_nhanh=self.cn, phan_tram_coc=Decimal("20"))
        for moc, pct in (("truoc_24h", 80), ("tu_6_den_24h", 30), ("trong_6h", 10)):
            QuyTacHuyDatCoc.objects.create(chinh_sach=rieng, moc_thoi_gian=moc, phan_tram_hoan_tien=Decimal(pct))

        for sau, moc, hoan in ((timedelta(days=3), "truoc_24h", 32000.0),
                               (timedelta(hours=20), "tu_6_den_24h", 12000.0),
                               (timedelta(hours=2), "trong_6h", 4000.0)):
            db, _ = self._coc_da_tra(sau)
            r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
            self.assertEqual((r.data["moc_thoi_gian"], r.data["so_tien_hoan"]), (moc, hoan), sau)
            self.assertEqual(r.data["trang_thai_hoan"], "cho_hoan")  # có tiền hoàn → chờ nhân viên chuyển

    def test_quy_tac_hoan_0_phan_tram_thi_lap_phieu_mat_coc_dung_so(self):
        from reservations.models import ChinhSachDatCoc, QuyTacHuyDatCoc
        rieng = ChinhSachDatCoc.objects.create(chi_nhanh=self.cn, phan_tram_coc=Decimal("20"))
        QuyTacHuyDatCoc.objects.create(chinh_sach=rieng, moc_thoi_gian="tu_6_den_24h", phan_tram_hoan_tien=Decimal("0"))
        db, _ = self._coc_da_tra(timedelta(hours=20))
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual((r.data["so_tien_hoan"], r.data["trang_thai_hoan"]), (0.0, "khong_hoan"))
        phieu = PhieuHoanTien.objects.get(dat_ban=db)
        self.assertEqual((phieu.phan_tram_hoan, phieu.so_tien_phat), (Decimal("0"), Decimal("40000")))
        self.assertEqual(phieu.du_lieu_chi_tiet["chinh_sach_ap_dung"]["ty_le_hoan_phan_tram"], 0.0)

    # --- API chính sách cọc ---
    def test_xem_chinh_sach_coc_khong_tao_ban_moi(self):
        from reservations.models import ChinhSachDatCoc
        for _ in range(3):
            r = APIClient().get(f"/api/dat-ban/chinh_sach_coc/?branch={self.cn.id}")
            self.assertEqual(r.status_code, 200)
            APIClient().get("/api/dat-ban/chinh_sach_coc/")
        self.assertEqual(ChinhSachDatCoc.objects.count(), 1)  # chỉ bản chung mặc định, tạo một lần

    def test_admin_sua_chinh_sach_chung_thi_hoan_coc_theo_do(self):
        from reservations.models import ChinhSachDatCoc
        # Dữ liệu cũ đã có nhiều bản chung trùng: admin và hệ thống phải cùng dùng một bản.
        for _ in range(3):
            ChinhSachDatCoc.objects.create(phan_tram_coc=Decimal("20"))
        quy_tac = [{"moc_thoi_gian": "truoc_24h", "phan_tram_hoan_tien": 70},
                   {"moc_thoi_gian": "tu_6_den_24h", "phan_tram_hoan_tien": 25}]
        r = self.api_ad.put("/api/dat-ban/chinh_sach_coc/", {"quy_tac_huy": quy_tac}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        r = APIClient().get(f"/api/dat-ban/chinh_sach_coc/?branch={self.cn.id}")
        self.assertEqual({q["moc_thoi_gian"]: float(q["phan_tram_hoan_tien"]) for q in r.data["quy_tac_huy"]},
                         {"truoc_24h": 70.0, "tu_6_den_24h": 25.0})
        db, _ = self._coc_da_tra(timedelta(hours=20))
        r = self.api_kh.post(f"/api/dat-ban/{db.id}/huy_dat_ban/", {}, format="json")
        self.assertEqual(r.data["so_tien_hoan"], 10000.0)  # 25% của 40.000đ

    def test_sua_chinh_sach_coc_kiem_tra_quyen_va_du_lieu(self):
        nv = NguoiDung.objects.create_user(username="nv", thu_dien_tu="nv@moc.vn", email="nv@moc.vn",
                                           password="Passw0rd!x", is_staff=True)
        c = APIClient(); c.force_authenticate(nv)
        self.assertEqual(c.put("/api/dat-ban/chinh_sach_coc/", {"phan_tram_coc": 50}, format="json").status_code, 403)
        self.assertEqual(self.api_kh.put("/api/dat-ban/chinh_sach_coc/", {"phan_tram_coc": 50}, format="json").status_code, 403)
        sai = {"quy_tac_huy": [{"moc_thoi_gian": "truoc_24h", "phan_tram_hoan_tien": 150}]}
        self.assertEqual(self.api_ad.put("/api/dat-ban/chinh_sach_coc/", sai, format="json").status_code, 400)
        sai = {"quy_tac_huy": [{"moc_thoi_gian": "bat_ky", "phan_tram_hoan_tien": 10}]}
        self.assertEqual(self.api_ad.put("/api/dat-ban/chinh_sach_coc/", sai, format="json").status_code, 400)

    def test_chinh_sach_rieng_chi_nhanh(self):
        r = self.api_ad.put(f"/api/dat-ban/chinh_sach_coc/?branch={self.cn.id}", {"phan_tram_coc": 30}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["chi_nhanh"], self.cn.id)
        r = APIClient().get(f"/api/dat-ban/chinh_sach_coc/?branch={self.cn.id}")
        self.assertEqual(Decimal(r.data["phan_tram_coc"]), Decimal("30"))
        khac = ChiNhanh.objects.create(ten="CN khác", dia_chi="b")
        r = APIClient().get(f"/api/dat-ban/chinh_sach_coc/?branch={khac.id}")
        self.assertIsNone(r.data["chi_nhanh"])  # chi nhánh chưa có chính sách riêng → dùng chung
