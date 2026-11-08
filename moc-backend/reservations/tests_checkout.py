from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from branches.models import ChiNhanh
from foods.models import DanhMuc, MonAn
from payments.models import ThanhToan
from reservations.models import BanAn, DatBan, PhienPhucVu


class LuongDatBanCheckInCheckOutTest(TestCase):
    """Đặt bàn đã cọc: check-in → xếp bàn → gọi món → check-out phải trừ tiền cọc."""

    def setUp(self):
        self.branch = ChiNhanh.objects.create(ten="CN test", dia_chi="a")
        self.table = BanAn.objects.create(chi_nhanh=self.branch, so_ban="T1", khu_vuc="Trong nhà", suc_chua=4)
        category = DanhMuc.objects.create(ten="Món chính", duong_dan="mon-chinh")
        self.food = MonAn.objects.create(danh_muc=category, ten="Bò lúc lắc", duong_dan="bo-luc-lac", don_gia=Decimal("100000"), con_hang=True, hien_thi=True)
        staff = NguoiDung.objects.create_user(username="nv", thu_dien_tu="nv@x.vn", email="nv@x.vn", password="Passw0rd!x")
        staff.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten="nhan_vien_ban_hang")[0])
        staff.chi_nhanh_quan_ly = self.branch
        staff.save()
        self.client = APIClient()
        self.client.force_authenticate(staff)

    def _reservation(self, deposit, deposit_status=DatBan.TrangThaiCoc.THANH_CONG):
        return DatBan.objects.create(
            chi_nhanh=self.branch, ngay_dat=timezone.localdate(), gio_bat_dau=time(18, 0), so_luong_khach=3,
            hinh_thuc=DatBan.HinhThuc.DAT_BAN_VA_GOI_MON, trang_thai=DatBan.TrangThai.DA_XAC_NHAN,
            so_tien_coc=Decimal(deposit), trang_thai_coc=deposit_status, ten_khach="Khách", sdt_khach="0900000000",
        )

    def _run_flow(self, reservation, qty):
        r = self.client.post(f"/api/reservations/{reservation.id}/check-in/", {"version": reservation.phien_ban}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        r = self.client.post(f"/api/reservations/{reservation.id}/seat/", {"ban_an": self.table.id}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        session_id = r.json()["id"]
        r = self.client.put(f"/api/dining-sessions/{session_id}/items/", {"danh_sach_mon": [{"mon_an_id": self.food.id, "so_luong": qty}]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        r = self.client.get(f"/api/dining-sessions/{session_id}/")
        self.assertEqual(Decimal(str(r.json()["tien_coc_da_tra"])), reservation.so_tien_coc if reservation.trang_thai_coc == DatBan.TrangThaiCoc.THANH_CONG else Decimal("0"))
        r = self.client.post(f"/api/dining-sessions/{session_id}/checkout/", {"phuong_thuc": "tien_mat"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        return PhienPhucVu.objects.get(pk=session_id)

    def test_checkout_tru_tien_coc_da_tra(self):
        reservation = self._reservation("50000")
        session = self._run_flow(reservation, qty=2)  # hoá đơn 200.000
        payment = ThanhToan.objects.get(don_hang=session.don_hang)
        self.assertEqual(payment.so_tien, Decimal("150000"))
        self.assertEqual(payment.trang_thai, ThanhToan.TrangThai.THANH_CONG)
        reservation.refresh_from_db(); self.table.refresh_from_db()
        self.assertEqual(reservation.trang_thai, DatBan.TrangThai.HOAN_TAT)
        self.assertEqual(self.table.trang_thai, BanAn.TrangThai.TRONG)
        self.assertEqual(session.trang_thai, PhienPhucVu.TrangThai.DA_DONG)

    def test_coc_lon_hon_hoa_don_thi_khong_thu_them(self):
        reservation = self._reservation("300000")
        session = self._run_flow(reservation, qty=1)  # hoá đơn 100.000
        self.assertFalse(ThanhToan.objects.filter(don_hang=session.don_hang).exists())

    def test_coc_chua_thanh_toan_thi_thu_du(self):
        reservation = self._reservation("50000", DatBan.TrangThaiCoc.CHUA_THANH_TOAN)
        session = self._run_flow(reservation, qty=2)
        self.assertEqual(ThanhToan.objects.get(don_hang=session.don_hang).so_tien, Decimal("200000"))
