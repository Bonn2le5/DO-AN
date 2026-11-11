from datetime import time, timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung
from branches.models import ChiNhanh
from foods.models import DanhMuc, MonAn
from payments.models import ThanhToan
from payments.services import DichVuPayOS
from reservations.models import BanAn, ChinhSachDatCoc, DatBan
from reservations.services import lay_chinh_sach_coc

HASH_SECRET = "test-secret"


@override_settings(PAYOS_CLIENT_ID="TEST", PAYOS_API_KEY="TEST", PAYOS_CHECKSUM_KEY=HASH_SECRET)
class GiuChoChoCocTest(TestCase):
    """Phiếu cần cọc chỉ giữ ghế trong hạn thanh toán."""

    def setUp(self):
        # Không gọi PayOS thật: giả lập API tạo link.
        patcher = mock.patch.object(
            DichVuPayOS, "_goi_api", return_value={"checkoutUrl": "https://pay.payos.vn/web/test", "status": "PENDING"}
        )
        self.goi_api = patcher.start()
        self.addCleanup(patcher.stop)
        self.branch = ChiNhanh.objects.create(ten="CN test", dia_chi="a")
        BanAn.objects.create(chi_nhanh=self.branch, so_ban="T1", suc_chua=4)
        ChinhSachDatCoc.objects.create(chi_nhanh=self.branch, phan_tram_coc=Decimal("20"), han_thanh_toan_phut=15)
        category = DanhMuc.objects.create(ten="Món chính", duong_dan="mon-chinh")
        self.food = MonAn.objects.create(
            danh_muc=category, ten="Bò", duong_dan="bo", don_gia=Decimal("100000"), con_hang=True, hien_thi=True
        )
        self.user = NguoiDung.objects.create_user(
            username="kh", thu_dien_tu="kh@x.vn", email="kh@x.vn", password="Passw0rd!x"
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.ngay = (timezone.localdate() + timedelta(days=1)).isoformat()

    def _dat_ban(self, so_khach=4, mon=True):
        payload = {
            "chi_nhanh": self.branch.id, "ngay_dat": self.ngay, "gio_bat_dau": "18:00",
            "so_luong_khach": so_khach, "ten_khach": "Khách", "sdt_khach": "0900000000",
            "hinh_thuc": "dat_ban_va_goi_mon" if mon else "chi_giu_cho",
        }
        if mon:
            payload["danh_sach_mon"] = [{"mon_an_id": self.food.id, "so_luong": 2}]
        return self.client.post("/api/dat-ban/", payload, format="json")

    def _qua_han(self, dat_ban_id, phut=21):
        DatBan.objects.filter(pk=dat_ban_id).update(tao_luc=timezone.now() - timedelta(minutes=phut))

    def _webhook(self, thanh_toan, chu_ky=None):
        data = {
            "orderCode": int(thanh_toan.ma_giao_dich),
            "amount": int(thanh_toan.so_tien),
            "description": "test",
            "code": "00",
            "desc": "success",
        }
        body = {"code": "00", "desc": "success", "success": True, "data": data,
                "signature": chu_ky or DichVuPayOS.ky(data, HASH_SECRET)}
        return APIClient().post("/api/thanh-toan/payos/webhook/", body, format="json")

    def _tao_thanh_toan(self, dat_ban_id):
        r = self.client.post(
            "/api/thanh-toan/payos/tao-phien/", {"loai_thanh_toan": "tien_coc", "dat_ban_id": dat_ban_id}, format="json"
        )
        return r

    def test_phieu_can_coc_tao_o_trang_thai_cho_thanh_toan(self):
        r = self._dat_ban()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["trang_thai"], DatBan.TrangThai.CHO_THANH_TOAN)
        self.assertEqual(Decimal(r.data["so_tien_coc"]), Decimal("40000"))

    def test_chi_giu_cho_van_cho_xac_nhan(self):
        r = self._dat_ban(mon=False)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["trang_thai"], DatBan.TrangThai.CHO_XAC_NHAN)

    def test_qua_han_coc_tra_lai_ghe(self):
        dat_ban_id = self._dat_ban().data["id"]
        self.assertEqual(self._dat_ban().status_code, 400)  # chi nhánh chỉ có 4 ghế

        self._qua_han(dat_ban_id)
        self.assertEqual(self._dat_ban().status_code, 201)
        dat_ban = DatBan.objects.get(pk=dat_ban_id)
        self.assertEqual(dat_ban.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(dat_ban.ly_do_huy, "Quá hạn thanh toán cọc")

    def test_khung_gio_trong_huy_phieu_qua_han(self):
        dat_ban_id = self._dat_ban().data["id"]
        self._qua_han(dat_ban_id)
        r = self.client.get("/api/dat-ban/khung-gio-trong/", {"chi_nhanh_id": self.branch.id, "ngay": self.ngay, "so_khach": 4})
        slot = next(s for s in r.data["slots"] if s["khung_gio"] == "18:00")
        self.assertTrue(slot["con_trong"])

    def test_trong_thoi_gian_cho_ipn_chua_huy(self):
        dat_ban_id = self._dat_ban().data["id"]
        self._qua_han(dat_ban_id, phut=17)  # quá 15 phút nhưng chưa hết 5 phút chờ IPN
        self.client.get("/api/dat-ban/")
        self.assertEqual(DatBan.objects.get(pk=dat_ban_id).trang_thai, DatBan.TrangThai.CHO_THANH_TOAN)
        r = self._tao_thanh_toan(dat_ban_id)
        self.assertEqual(r.status_code, 400)  # không mở phiên PayOS mới sau hạn

    def test_ipn_thanh_cong_chuyen_cho_xac_nhan(self):
        dat_ban_id = self._dat_ban().data["id"]
        r = self._tao_thanh_toan(dat_ban_id)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["duong_dan_thanh_toan"], "https://pay.payos.vn/web/test")
        body = self.goi_api.call_args.args[2]
        self.assertEqual(body["amount"], 40000)
        self.assertIn("expiredAt", body)
        self.assertEqual(self._webhook(ThanhToan.objects.get(pk=r.data["thanh_toan_id"])).status_code, 200)
        dat_ban = DatBan.objects.get(pk=dat_ban_id)
        self.assertEqual(dat_ban.trang_thai, DatBan.TrangThai.CHO_XAC_NHAN)
        self.assertEqual(dat_ban.trang_thai_coc, DatBan.TrangThaiCoc.THANH_CONG)

    def test_ipn_den_sau_khi_huy_giu_nguyen_da_huy(self):
        dat_ban_id = self._dat_ban().data["id"]
        thanh_toan = ThanhToan.objects.get(pk=self._tao_thanh_toan(dat_ban_id).data["thanh_toan_id"])
        self._qua_han(dat_ban_id)
        self.client.get("/api/dat-ban/")
        self._webhook(thanh_toan)
        dat_ban = DatBan.objects.get(pk=dat_ban_id)
        self.assertEqual(dat_ban.trang_thai, DatBan.TrangThai.DA_HUY)
        self.assertEqual(dat_ban.trang_thai_coc, DatBan.TrangThaiCoc.THANH_CONG)  # nhân viên hoàn cọc

    def test_webhook_sai_chu_ky_khong_xac_nhan(self):
        dat_ban_id = self._dat_ban().data["id"]
        thanh_toan = ThanhToan.objects.get(pk=self._tao_thanh_toan(dat_ban_id).data["thanh_toan_id"])
        r = self._webhook(thanh_toan, chu_ky="0" * 64)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["success"])
        self.assertEqual(DatBan.objects.get(pk=dat_ban_id).trang_thai_coc, DatBan.TrangThaiCoc.CHUA_THANH_TOAN)

    def test_return_hoi_lai_payos_truoc_khi_xac_nhan(self):
        dat_ban_id = self._dat_ban().data["id"]
        thanh_toan = ThanhToan.objects.get(pk=self._tao_thanh_toan(dat_ban_id).data["thanh_toan_id"])
        url = f"/api/thanh-toan/payos/return/?orderCode={thanh_toan.ma_giao_dich}&status=PAID"
        # PayOS nói vẫn đang chờ: tham số status=PAID trên URL không được tin.
        self.goi_api.return_value = {"status": "PENDING", "amount": 40000}
        self.assertIn("status=failed", self.client.get(url)["Location"])
        self.goi_api.return_value = {"status": "PAID", "amount": 40000}
        self.assertIn("status=success", self.client.get(url)["Location"])
        self.assertEqual(DatBan.objects.get(pk=dat_ban_id).trang_thai, DatBan.TrangThai.CHO_XAC_NHAN)

    def test_chinh_sach_chung_va_rieng(self):
        ChinhSachDatCoc.objects.create(chi_nhanh=None, phan_tram_coc=Decimal("30"))
        self.assertEqual(lay_chinh_sach_coc(self.branch.id).phan_tram_coc, Decimal("20"))
        khac = ChiNhanh.objects.create(ten="CN khác", dia_chi="b")
        self.assertEqual(lay_chinh_sach_coc(khac.id).phan_tram_coc, Decimal("30"))
