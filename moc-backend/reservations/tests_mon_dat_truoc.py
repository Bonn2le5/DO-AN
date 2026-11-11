from datetime import time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from branches.models import ChiNhanh
from foods.models import DanhMuc, MonAn
from orders.models import ChiTietDonHang
from reservations.models import BanAn, DatBan, MonAnTrongDatBan


def _ngay_mai_vn():
    """Ngày mai theo giờ Việt Nam — cùng mốc với code khi xét \"đặt trong ngày\".
    Dùng ngày UTC thì từ 0h đến 7h sáng, \"ngày mai\" của test lại là hôm nay của code."""
    return timezone.localdate(timezone=ZoneInfo("Asia/Ho_Chi_Minh")) + timedelta(days=1)


class MonDatTruocTest(TestCase):
    """Món đặt trước giữ giá lúc đặt và không chặn việc xếp bàn khi hết món."""

    def setUp(self):
        self.branch = ChiNhanh.objects.create(ten="CN test", dia_chi="a")
        self.table = BanAn.objects.create(chi_nhanh=self.branch, so_ban="T1", suc_chua=4)
        category = DanhMuc.objects.create(ten="Món chính", duong_dan="mon-chinh")
        self.bo = MonAn.objects.create(danh_muc=category, ten="Bò", duong_dan="bo", don_gia=Decimal("100000"), con_hang=True, hien_thi=True)
        self.ga = MonAn.objects.create(danh_muc=category, ten="Gà", duong_dan="ga", don_gia=Decimal("80000"), con_hang=True, hien_thi=True)
        staff = NguoiDung.objects.create_user(username="nv", thu_dien_tu="nv@x.vn", email="nv@x.vn", password="Passw0rd!x")
        staff.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten="nhan_vien_ban_hang")[0])
        staff.chi_nhanh_quan_ly = self.branch
        staff.save()
        self.staff = APIClient()
        self.staff.force_authenticate(staff)
        khach = NguoiDung.objects.create_user(username="kh", thu_dien_tu="kh@x.vn", email="kh@x.vn", password="Passw0rd!x")
        self.khach = APIClient()
        self.khach.force_authenticate(khach)

    def _dat_ban_da_den(self, items):
        dat_ban = DatBan.objects.create(
            chi_nhanh=self.branch, ngay_dat=timezone.localdate(), gio_bat_dau=time(18, 0), so_luong_khach=2,
            hinh_thuc=DatBan.HinhThuc.DAT_BAN_VA_GOI_MON, trang_thai=DatBan.TrangThai.KHACH_DA_DEN,
            ten_khach="Khách", sdt_khach="0900000000",
        )
        for mon, so_luong, gia in items:
            MonAnTrongDatBan.objects.create(dat_ban=dat_ban, mon_an=mon, so_luong=so_luong, don_gia_luc_dat=gia)
        return dat_ban

    def _xep_ban(self, dat_ban):
        return self.staff.post(f"/api/dat-ban/{dat_ban.id}/xep-ban/", {"ban_an": self.table.id}, format="json")

    def test_hoa_don_giu_gia_luc_dat(self):
        dat_ban = self._dat_ban_da_den([(self.bo, 2, Decimal("90000"))])  # giá đã tăng lên 100.000 sau khi đặt
        r = self._xep_ban(dat_ban)
        self.assertEqual(r.status_code, 201, r.content)
        line = ChiTietDonHang.objects.get(don_hang__phien_phuc_vu_id=r.data["id"])
        self.assertEqual(line.don_gia_luc_dat, Decimal("90000"))
        self.assertEqual(line.thanh_tien, Decimal("180000"))

        # Sửa giỏ (PUT) vẫn giữ giá đã chốt cho món cũ, món mới lấy giá hiện tại.
        r = self.staff.put(f"/api/phien-phuc-vu/{r.data['id']}/mon/", {"danh_sach_mon": [
            {"mon_an_id": self.bo.id, "so_luong": 3}, {"mon_an_id": self.ga.id, "so_luong": 1},
        ]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        gia = dict(ChiTietDonHang.objects.filter(don_hang__phien_phuc_vu_id=r.data["id"]).values_list("mon_an_id", "don_gia_luc_dat"))
        self.assertEqual(gia, {self.bo.id: Decimal("90000"), self.ga.id: Decimal("80000")})

    def test_het_mon_van_xep_ban_va_bao_mon_thieu(self):
        self.bo.ton_kho_cache = 1
        self.bo.save()
        dat_ban = self._dat_ban_da_den([(self.bo, 2, Decimal("100000")), (self.ga, 1, Decimal("80000"))])
        r = self._xep_ban(dat_ban)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["mon_khong_du"], [{"mon_an_id": self.bo.id, "ten": "Bò", "so_luong": 2}])
        lines = ChiTietDonHang.objects.filter(don_hang__phien_phuc_vu_id=r.data["id"])
        self.assertEqual(list(lines.values_list("mon_an_id", flat=True)), [self.ga.id])
        self.bo.refresh_from_db()
        self.assertEqual(self.bo.ton_kho_cache, 1)

    def test_tat_ca_mon_het_van_mo_ban_khong_tao_hoa_don(self):
        self.bo.con_hang = False
        self.bo.save()
        r = self._xep_ban(self._dat_ban_da_den([(self.bo, 1, Decimal("100000"))]))
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(len(r.data["mon_khong_du"]), 1)
        self.assertFalse(ChiTietDonHang.objects.filter(don_hang__phien_phuc_vu_id=r.data["id"]).exists())

    def _dat_online(self, ngay, so_luong):
        return self.khach.post("/api/dat-ban/", {
            "chi_nhanh": self.branch.id, "ngay_dat": ngay.isoformat(), "gio_bat_dau": "21:59",
            "so_luong_khach": 2, "ten_khach": "Khách", "sdt_khach": "0900000000",
            "hinh_thuc": "dat_ban_va_goi_mon", "danh_sach_mon": [{"mon_an_id": self.bo.id, "so_luong": so_luong}],
        }, format="json")

    def test_dat_ban_tu_choi_mon_an_khong_hien_thi(self):
        self.bo.hien_thi = False
        self.bo.save()
        r = self._dat_online(_ngay_mai_vn(), 1)
        self.assertEqual(r.status_code, 400)
        self.assertIn("danh_sach_mon", r.data)

    def test_ton_kho_chi_kiem_tra_khi_dat_trong_ngay(self):
        self.bo.ton_kho_cache = 1
        self.bo.save()
        self.assertEqual(self._dat_online(_ngay_mai_vn(), 3).status_code, 201)
