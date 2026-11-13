from datetime import time
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from branches.models import ChiNhanh
from foods.models import DanhMuc, MonAn
from orders.models import DonHang
from payments.models import ThanhToan
from payments.services import DichVuPayOS
from reservations.models import BanAn, DatBan, PhienPhucVu


class PayOSGia:
    """Giả lập API PayOS: lưu trạng thái từng orderCode."""

    def __init__(self):
        self.trang_thai = {}
        self.so_tien = {}
        self.da_huy = []

    def __call__(self, method, path, body=None):
        if method == "POST" and path == "/v2/payment-requests":
            self.trang_thai[str(body["orderCode"])] = "PENDING"
            self.so_tien[str(body["orderCode"])] = body["amount"]
            return {"checkoutUrl": "https://pay.payos.vn/web/x", "qrCode": "QRDATA"}
        ma = path.split("/")[3]
        if path.endswith("/cancel"):
            self.da_huy.append(ma)
            self.trang_thai[ma] = "CANCELLED"
            return {}
        return {"status": self.trang_thai[ma], "amount": self.so_tien[ma]}


@override_settings(PAYOS_CLIENT_ID="id", PAYOS_API_KEY="key", PAYOS_CHECKSUM_KEY="checksum")
class PayOSTaiBanTest(TestCase):
    """Thu ngân thu tiền hoá đơn tại bàn bằng mã QR PayOS."""

    def setUp(self):
        self.payos = PayOSGia()
        patcher = mock.patch.object(DichVuPayOS, "_goi_api", side_effect=self.payos)
        patcher.start()
        self.addCleanup(patcher.stop)

        branch = ChiNhanh.objects.create(ten="CN test", dia_chi="a")
        table = BanAn.objects.create(chi_nhanh=branch, so_ban="T1", suc_chua=4)
        category = DanhMuc.objects.create(ten="Món chính", duong_dan="mon-chinh")
        food = MonAn.objects.create(danh_muc=category, ten="Bò", duong_dan="bo", don_gia=Decimal("100000"), con_hang=True, hien_thi=True)
        staff = NguoiDung.objects.create_user(username="nv", thu_dien_tu="nv@x.vn", email="nv@x.vn", password="Passw0rd!x")
        staff.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten="nhan_vien_ban_hang")[0])
        staff.chi_nhanh_quan_ly = branch
        staff.save()
        self.client = APIClient()
        self.client.force_authenticate(staff)

        dat_ban = DatBan.objects.create(
            chi_nhanh=branch, ngay_dat=timezone.localdate(), gio_bat_dau=time(18, 0), so_luong_khach=2,
            hinh_thuc=DatBan.HinhThuc.DAT_BAN_VA_GOI_MON, trang_thai=DatBan.TrangThai.KHACH_DA_DEN,
            so_tien_coc=Decimal("50000"), trang_thai_coc=DatBan.TrangThaiCoc.THANH_CONG,
            ten_khach="Khách", sdt_khach="0900000000",
        )
        r = self.client.post(f"/api/dat-ban/{dat_ban.id}/xep-ban/", {"ban_an": table.id}, format="json")
        self.phien_id = r.data["id"]
        r = self.client.put(f"/api/phien-phuc-vu/{self.phien_id}/mon/", {"danh_sach_mon": [{"mon_an_id": food.id, "so_luong": 2}]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.don_hang = DonHang.objects.get(phien_phuc_vu_id=self.phien_id)

    def _tao_qr(self, client=None):
        return (client or self.client).post(
            "/api/thanh-toan/payos/tao-phien/", {"loai_thanh_toan": "don_hang", "don_hang_id": self.don_hang.id}, format="json"
        )

    def _checkout(self, phuong_thuc):
        return self.client.post(f"/api/phien-phuc-vu/{self.phien_id}/checkout/", {"phuong_thuc": phuong_thuc}, format="json")

    def _sua_mon(self, so_luong):
        mon_an_id = self.don_hang.danh_sach_mon.first().mon_an_id
        return self.client.put(f"/api/phien-phuc-vu/{self.phien_id}/mon/", {"danh_sach_mon": [{"mon_an_id": mon_an_id, "so_luong": so_luong}]}, format="json")

    def test_da_tra_thi_khong_sua_mon_va_khong_tao_qr_moi(self):
        thanh_toan = ThanhToan.objects.get(pk=self._tao_qr().data["thanh_toan_id"])
        self.payos.trang_thai[thanh_toan.ma_giao_dich] = "PAID"
        self.client.get(f"/api/thanh-toan/{thanh_toan.id}/payos/trang-thai/")
        self.assertEqual(self._sua_mon(3).status_code, 400)
        self.assertEqual(self._tao_qr().status_code, 400)
        self.assertEqual(self._checkout("payos").status_code, 200)

    def test_sua_mon_thi_huy_ma_qr_dang_cho(self):
        thanh_toan = ThanhToan.objects.get(pk=self._tao_qr().data["thanh_toan_id"])
        self.assertEqual(self._sua_mon(3).status_code, 200)
        self.assertIn(thanh_toan.ma_giao_dich, self.payos.da_huy)
        self.assertEqual(self._tao_qr().data["so_tien"], 250000.0)

    def test_payos_mat_ket_noi_thi_van_ghi_nhan_tien_khach_quet_sau(self):
        thanh_toan = ThanhToan.objects.get(pk=self._tao_qr().data["thanh_toan_id"])
        with mock.patch.object(DichVuPayOS, "_goi_api", side_effect=DichVuPayOS.LoiCong()):
            self.assertEqual(self._sua_mon(3).status_code, 400)  # chưa huỷ được mã thì chưa cho đổi số tiền
            self.assertEqual(self._checkout("tien_mat").status_code, 200)
        self.assertEqual(DichVuPayOS.xac_nhan(thanh_toan.ma_giao_dich, 150000, thanh_cong=True), "thanh_cong")

    def test_tao_qr_thu_phan_con_lai_sau_coc(self):
        r = self._tao_qr()
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["so_tien"], 150000.0)  # 200.000 − cọc 50.000
        self.assertEqual(r.data["ma_qr"], "QRDATA")

    def test_khach_khong_tao_duoc_qr_tai_ban(self):
        khach = NguoiDung.objects.create_user(username="kh", thu_dien_tu="kh@x.vn", email="kh@x.vn", password="Passw0rd!x")
        client = APIClient()
        client.force_authenticate(khach)
        self.assertEqual(self._tao_qr(client).status_code, 403)

    def test_khach_quet_tra_roi_hoan_tat_ban(self):
        thanh_toan_id = self._tao_qr().data["thanh_toan_id"]
        r = self.client.get(f"/api/thanh-toan/{thanh_toan_id}/payos/trang-thai/")
        self.assertEqual(r.data["trang_thai"], ThanhToan.TrangThai.CHO_XU_LY)
        self.assertEqual(self._checkout("payos").status_code, 400)  # chưa trả thì chưa đóng bàn

        self.payos.trang_thai[ThanhToan.objects.get(pk=thanh_toan_id).ma_giao_dich] = "PAID"
        r = self.client.get(f"/api/thanh-toan/{thanh_toan_id}/payos/trang-thai/")
        self.assertEqual(r.data["trang_thai"], ThanhToan.TrangThai.THANH_CONG)
        self.don_hang.refresh_from_db()
        self.assertEqual(self.don_hang.trang_thai, DonHang.TrangThai.CHO_TIEP_NHAN)  # PayOS không tự đẩy trạng thái bếp

        r = self._checkout("payos")
        self.assertEqual(r.status_code, 200, r.content)
        self.don_hang.refresh_from_db()
        self.assertEqual(self.don_hang.trang_thai, DonHang.TrangThai.HOAN_TAT)
        self.assertEqual(PhienPhucVu.objects.get(pk=self.phien_id).trang_thai, PhienPhucVu.TrangThai.DA_DONG)
        self.assertEqual(ThanhToan.objects.filter(don_hang=self.don_hang).count(), 1)

    def test_doi_sang_tien_mat_thi_huy_ma_qr(self):
        thanh_toan = ThanhToan.objects.get(pk=self._tao_qr().data["thanh_toan_id"])
        r = self._checkout("tien_mat")
        self.assertEqual(r.status_code, 200, r.content)
        thanh_toan.refresh_from_db()
        self.assertEqual(thanh_toan.trang_thai, ThanhToan.TrangThai.THAT_BAI)
        self.assertIn(thanh_toan.ma_giao_dich, self.payos.da_huy)
        tien_mat = ThanhToan.objects.get(don_hang=self.don_hang, phuong_thuc="tien_mat")
        self.assertEqual((tien_mat.trang_thai, tien_mat.so_tien), (ThanhToan.TrangThai.THANH_CONG, Decimal("150000")))

    def test_da_tra_payos_thi_khong_thu_tien_mat_nua(self):
        thanh_toan = ThanhToan.objects.get(pk=self._tao_qr().data["thanh_toan_id"])
        self.payos.trang_thai[thanh_toan.ma_giao_dich] = "PAID"
        r = self._checkout("tien_mat")
        self.assertEqual(r.status_code, 400)
        self.assertIn("PayOS", str(r.data))
