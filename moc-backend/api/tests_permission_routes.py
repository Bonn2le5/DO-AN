import re
from datetime import time
from pathlib import Path

from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from api import urls as api_urls
from api.permissions import LaNhanVienNhaHang as Perm
from branches.models import ChiNhanh
from reservations.models import DatBan

# Route không cần nhóm quyền nhân viên (công khai, đăng nhập, hoặc tự kiểm tra quyền riêng).
PUBLIC_PREFIXES = {
    "auth", "xac-thuc", "health", "notifications", "thong-bao",
    "recommendations", "goi-y", "interactions", "tuong-tac",
}


def all_prefixes():
    prefixes = [prefix for prefix, _, _ in api_urls.router.registry]
    prefixes += re.findall(r'path\("([^"]+)"', Path(api_urls.__file__).read_text(encoding="utf-8"))
    return [p.strip("/") for p in prefixes if p.strip("/")]


class RouteModuleMappingTest(SimpleTestCase):
    def test_moi_route_deu_thuoc_mot_nhom_quyen(self):
        missing = [p for p in all_prefixes() if p.split("/")[0] not in PUBLIC_PREFIXES and Perm.module_for(f"/api/{p}/") is None]
        self.assertEqual(missing, [], "Route mới chưa khai báo nhóm quyền trong api/permissions.py")

    def test_ten_tieng_viet_cung_nhom_voi_ten_cu(self):
        pairs = [
            ("analytics/dashboard", "thong-ke/tong-quan"), ("analytics/ai", "thong-ke/ai"), ("analytics/settings", "thong-ke/cai-dat"),
            ("rooms", "phong-rieng"), ("refund-receipts", "phieu-hoan-tien"), ("orders", "don-hang"),
            ("reservations", "dat-ban"), ("dining-sessions", "phien-phuc-vu"), ("tables", "ban-an"),
            ("ingredients", "nguyen-lieu"), ("users", "nguoi-dung"), ("payments", "thanh-toan"),
        ]
        for old, new in pairs:
            self.assertEqual(Perm.module_for(f"/api/{old}/1/"), Perm.module_for(f"/api/{new}/1/"), (old, new))

    def test_khong_khop_nham_chuoi_con(self):
        self.assertEqual(Perm.module_for("/api/chat/rooms/"), "chat")
        self.assertEqual(Perm.module_for("/api/dining-sessions/canh-bao-kho/"), "dining_sessions")
        self.assertEqual(Perm.module_for("/api/dat-ban/5/ghi-nhan-hoan-tien/"), "payments")


class TongQuanTheoVaiTroTest(TestCase):
    def setUp(self):
        self.branch = ChiNhanh.objects.create(ten="CN1", dia_chi="a")

    def _client(self, username, role):
        user = NguoiDung.objects.create_user(username=username, thu_dien_tu=f"{username}@x.vn", email=f"{username}@x.vn", password="Passw0rd!x")
        user.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten=role)[0])
        user.chi_nhanh_quan_ly = self.branch
        user.save()
        c = APIClient()
        c.force_authenticate(user)
        return c

    def test_quan_ly_xem_tong_quan_nhan_vien_khong(self):
        ql = self._client("ql", "quan_ly_chi_nhanh")
        nv = self._client("nv", "nhan_vien_ban_hang")
        for path in ("/api/thong-ke/tong-quan/?days=7", "/api/analytics/dashboard/?days=7"):
            r = ql.get(path)
            self.assertEqual(r.status_code, 200, (path, r.content[:200]))
            self.assertEqual([b["id"] for b in r.json()["live"]], [self.branch.id])
            self.assertEqual(nv.get(path).status_code, 403, path)
        self.assertEqual(ql.get("/api/chat/rooms/").status_code, 403)

    def test_quan_ly_xem_khoan_hut_chi_nhanh_minh(self):
        from decimal import Decimal
        from orders.models import DonHang
        other = ChiNhanh.objects.create(ten="CN2", dia_chi="b")
        DonHang.objects.create(chi_nhanh=self.branch, trang_thai=DonHang.TrangThai.DA_HUY, ten_khach="A", tien_hang=Decimal("100000"), tong_tien=Decimal("100000"))
        DonHang.objects.create(chi_nhanh=other, trang_thai=DonHang.TrangThai.DA_HUY, ten_khach="B", tien_hang=Decimal("500000"), tong_tien=Decimal("500000"))
        leaks = self._client("ql", "quan_ly_chi_nhanh").get("/api/thong-ke/tong-quan/?days=7").json()["leaks"]
        self.assertEqual((leaks["cancelled"]["count"], leaks["cancelled"]["value"]), (1, 100000.0))
        self.assertIsNone(leaks["cancelled"]["worst_branch"])

    def test_nhan_vien_khong_ghi_nhan_hoan_tien_bang_ten_moi(self):
        nv = self._client("nv", "nhan_vien_ban_hang")
        r = DatBan.objects.create(
            chi_nhanh=self.branch, ngay_dat=timezone.localdate(), gio_bat_dau=time(19, 0), so_luong_khach=2,
            hinh_thuc=DatBan.HinhThuc.CHI_GIU_CHO, trang_thai=DatBan.TrangThai.DA_HUY, ten_khach="K", sdt_khach="09",
        )
        for path in (f"/api/reservations/{r.id}/record-refund/", f"/api/dat-ban/{r.id}/ghi-nhan-hoan-tien/"):
            self.assertEqual(nv.post(path, {}, format="json").status_code, 403, path)


class QuyenKhoNguyenLieuTest(TongQuanTheoVaiTroTest):
    """Nguyên liệu, định mức và tồn kho dùng chung mọi chi nhánh: quản lý chi nhánh chỉ lập phiếu kho."""

    test_quan_ly_xem_tong_quan_nhan_vien_khong = None  # không chạy lại test của lớp cha

    def setUp(self):
        super().setUp()
        from decimal import Decimal
        from foods.models import DanhMuc, DinhMucNguyenLieu, MonAn, NguyenLieu
        self.nl = NguyenLieu.objects.create(ten="Tôm", don_vi="kg", ton_kho_hien_tai=Decimal("10"), ton_kho_toi_thieu=Decimal("1"))
        mon = MonAn.objects.create(danh_muc=DanhMuc.objects.create(ten="Lẩu", duong_dan="lau"), ten="Lẩu", duong_dan="lau", don_gia=100000)
        self.mon = mon
        self.dm = DinhMucNguyenLieu.objects.create(mon_an=mon, nguyen_lieu=self.nl, so_luong_can=Decimal("0.2"))

    def _ghi(self, c):
        """Mã trạng thái của mọi thao tác ghi lên nguyên liệu / định mức / phiếu kho."""
        return {
            "tao_nguyen_lieu": c.post("/api/nguyen-lieu/", {"ten": "Mực", "don_vi": "kg"}, format="json").status_code,
            "sua_nguyen_lieu": c.patch(f"/api/nguyen-lieu/{self.nl.id}/", {"ten": "Tôm sú"}, format="json").status_code,
            "xoa_nguyen_lieu": c.delete(f"/api/ingredients/{self.nl.id}/").status_code,
            "tao_dinh_muc": c.post("/api/dinh-muc-nguyen-lieu/", {"mon_an": self.mon.id, "nguyen_lieu": self.nl.id, "so_luong_can": "1"}, format="json").status_code,
            "sua_dinh_muc": c.patch(f"/api/dinh-muc-nguyen-lieu/{self.dm.id}/", {"so_luong_can": "5"}, format="json").status_code,
            "xoa_dinh_muc": c.delete(f"/api/dinh-muc-nguyen-lieu/{self.dm.id}/").status_code,
        }

    def test_quan_ly_chi_nhanh_chi_xem_va_lap_phieu_kho(self):
        ql = self._client("ql", "quan_ly_chi_nhanh")
        for path in ("/api/nguyen-lieu/", "/api/kho/", "/api/dinh-muc-nguyen-lieu/"):
            self.assertEqual(ql.get(path).status_code, 200, path)
        r = ql.post("/api/kho/", {"nguyen_lieu": self.nl.id, "loai_giao_dich": "nhap", "so_luong": "2"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(ql.post("/api/inventory-transactions/", {"nguyen_lieu": self.nl.id, "loai_giao_dich": "xuat", "so_luong": "1"}, format="json").status_code, 201)
        self.assertEqual(set(self._ghi(ql).values()), {403}, self._ghi(ql))

    def test_nhan_vien_chi_xem(self):
        nv = self._client("nv", "nhan_vien_ban_hang")
        self.assertEqual(nv.get("/api/nguyen-lieu/").status_code, 200)
        self.assertEqual(nv.post("/api/kho/", {"nguyen_lieu": self.nl.id, "loai_giao_dich": "nhap", "so_luong": "2"}, format="json").status_code, 403)
        self.assertEqual(set(self._ghi(nv).values()), {403})

    def test_quan_tri_vien_van_toan_quyen(self):
        qt = self._client("qt", "quan_tri_vien")
        kq = self._ghi(qt)
        self.assertNotIn(403, kq.values(), kq)  # 400 ở đây là kiểm tra dữ liệu (trùng định mức, nguyên liệu đang dùng)
