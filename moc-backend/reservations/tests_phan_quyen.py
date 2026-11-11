from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from branches.models import ChiNhanh
from foods.models import DanhMuc, MonAn
from orders.models import DonHang
from reservations.models import BanAn, DatBan, PhienPhucVu


def make_user(username, role, branch=None):
    user = NguoiDung.objects.create_user(username=username, thu_dien_tu=f"{username}@x.vn", email=f"{username}@x.vn", password="Passw0rd!x")
    user.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten=role)[0])
    user.chi_nhanh_quan_ly = branch
    user.save()
    return user


def client_for(user):
    c = APIClient()
    c.force_authenticate(user)
    return c


class PhanQuyenQuanLyNhanVienTest(TestCase):
    def setUp(self):
        self.branch = ChiNhanh.objects.create(ten="CN1", dia_chi="a")
        self.other = ChiNhanh.objects.create(ten="CN2", dia_chi="b")
        self.table = BanAn.objects.create(chi_nhanh=self.branch, so_ban="T1", khu_vuc="Trong nhà", suc_chua=4)
        cat = DanhMuc.objects.create(ten="Món", duong_dan="mon")
        self.food = MonAn.objects.create(danh_muc=cat, ten="Cơm", duong_dan="com", don_gia=Decimal("50000"), con_hang=True, hien_thi=True)
        self.staff = make_user("nv", "nhan_vien_ban_hang", self.branch)
        self.manager = make_user("ql", "quan_ly_chi_nhanh", self.branch)
        self.staff_other = make_user("nv2", "nhan_vien_ban_hang", self.other)
        self.nv = client_for(self.staff)
        self.ql = client_for(self.manager)

    # --- Hoá đơn chỉ sinh ra khi có món ---
    def _open(self):
        r = self.nv.post("/api/dining-sessions/walk-in/", {"ban_an": self.table.id, "so_luong_khach": 2}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["id"]

    def _set_items(self, client, session_id, qty):
        return client.put(f"/api/dining-sessions/{session_id}/items/", {"danh_sach_mon": [{"mon_an_id": self.food.id, "so_luong": qty}] if qty else []}, format="json")

    def _send_to_kitchen(self, session_id):
        order = DonHang.objects.get(phien_phuc_vu_id=session_id)
        r = self.nv.patch(f"/api/orders/{order.id}/status/", {"status": "da_xac_nhan"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        return order

    def test_mo_ban_khong_tao_hoa_don(self):
        sid = self._open()
        self.assertFalse(DonHang.objects.filter(phien_phuc_vu_id=sid).exists())
        self.assertEqual(self._set_items(self.nv, sid, 2).status_code, 200)
        self.assertEqual(DonHang.objects.get(phien_phuc_vu_id=sid).tong_tien, Decimal("100000"))
        # Xoá hết món khi chưa gửi bếp thì hoá đơn nháp cũng bị xoá.
        self.assertEqual(self._set_items(self.nv, sid, 0).status_code, 200)
        self.assertFalse(DonHang.objects.filter(phien_phuc_vu_id=sid).exists())

    def test_checkout_ban_chua_goi_mon_bi_tu_choi(self):
        sid = self._open()
        r = self.nv.post(f"/api/dining-sessions/{sid}/checkout/", {"phuong_thuc": "tien_mat"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_nhan_vien_huy_ban_chua_gui_bep(self):
        sid = self._open()
        self._set_items(self.nv, sid, 1)
        r = self.nv.post(f"/api/dining-sessions/{sid}/cancel/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(PhienPhucVu.objects.get(pk=sid).trang_thai, PhienPhucVu.TrangThai.DA_DONG)
        self.assertFalse(DonHang.objects.filter(phien_phuc_vu_id=sid).exists())
        self.table.refresh_from_db()
        self.assertEqual(self.table.trang_thai, BanAn.TrangThai.TRONG)

    def test_mon_da_gui_bep_chi_quan_ly_duoc_bot_hoac_huy(self):
        sid = self._open()
        self._set_items(self.nv, sid, 2)
        order = self._send_to_kitchen(sid)
        self.assertEqual(self._set_items(self.nv, sid, 3).status_code, 200)   # gọi thêm: được
        self.assertEqual(self._set_items(self.nv, sid, 1).status_code, 403)   # bớt món đã gửi: không
        self.assertEqual(self.nv.post(f"/api/dining-sessions/{sid}/cancel/", {}, format="json").status_code, 403)
        self.assertEqual(self.nv.patch(f"/api/orders/{order.id}/status/", {"status": "da_huy"}, format="json").status_code, 403)
        self.assertEqual(self._set_items(self.ql, sid, 1).status_code, 200)   # quản lý bớt được
        r = self.ql.post(f"/api/dining-sessions/{sid}/cancel/", {"ly_do": "Khách đổi ý"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        order.refresh_from_db()
        self.assertEqual(order.trang_thai, DonHang.TrangThai.DA_HUY)

    # --- Đặt bàn ---
    def test_huy_dat_ban_va_khong_den_chi_quan_ly(self):
        r = DatBan.objects.create(
            chi_nhanh=self.branch, ngay_dat=timezone.localdate(), gio_bat_dau=time(19, 0), so_luong_khach=2,
            hinh_thuc=DatBan.HinhThuc.CHI_GIU_CHO, trang_thai=DatBan.TrangThai.DA_XAC_NHAN, ten_khach="K", sdt_khach="09",
        )
        self.assertEqual(self.nv.patch(f"/api/reservations/{r.id}/trang_thai/", {"status": "khach_khong_den", "version": r.phien_ban}, format="json").status_code, 403)
        self.assertEqual(self.nv.patch(f"/api/reservations/{r.id}/trang_thai/", {"status": "da_huy", "version": r.phien_ban}, format="json").status_code, 403)
        self.assertEqual(self.nv.post(f"/api/reservations/{r.id}/cancel/", {}, format="json").status_code, 403)
        self.assertEqual(self.ql.patch(f"/api/reservations/{r.id}/trang_thai/", {"status": "da_huy", "version": r.phien_ban}, format="json").status_code, 200)

    # --- Kho và nhân viên ---
    def test_kho_nhan_vien_chi_xem_quan_ly_chi_lap_phieu(self):
        # Nguyên liệu dùng chung mọi chi nhánh: chỉ quản trị viên thêm/sửa (chi tiết: api/tests_permission_routes).
        self.assertEqual(self.nv.get("/api/ingredients/").status_code, 200)
        self.assertEqual(self.nv.post("/api/ingredients/", {"ten": "Muối", "don_vi": "kg"}, format="json").status_code, 403)
        self.assertEqual(self.ql.post("/api/ingredients/", {"ten": "Muối", "don_vi": "kg"}, format="json").status_code, 403)
        self.assertEqual(self.nv.get("/api/dining-sessions/canh-bao-kho/").status_code, 200)

    def test_quan_ly_chi_quan_ly_nhan_vien_chi_nhanh_minh(self):
        self.assertEqual(self.nv.get("/api/users/").status_code, 403)
        r = self.ql.get("/api/users/")
        self.assertEqual(r.status_code, 200)
        rows = r.json()["results"] if isinstance(r.json(), dict) else r.json()
        self.assertEqual({row["id"] for row in rows}, {self.staff.id})
        # Tạo nhân viên: luôn là nhân viên bán hàng của chi nhánh mình, dù gửi role khác.
        r = self.ql.post("/api/users/admin_create/", {"email": "moi@x.vn", "password": "Passw0rd!x", "name": "Mới", "role": "admin", "branch_id": self.other.id}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        created = NguoiDung.objects.get(thu_dien_tu="moi@x.vn")
        self.assertEqual(created.chi_nhanh_quan_ly_id, self.branch.id)
        self.assertEqual(created.ten_vai_tro, {"nhan_vien_ban_hang"})
        # Khoá tài khoản nhân viên mình: được. Đổi vai trò: không. Nhân viên chi nhánh khác: không thấy.
        self.assertEqual(self.ql.patch(f"/api/users/{self.staff.id}/admin_update/", {"active": False}, format="json").status_code, 200)
        self.assertEqual(self.ql.patch(f"/api/users/{self.staff.id}/admin_update/", {"role": "branch_manager"}, format="json").status_code, 403)
        self.assertEqual(self.ql.patch(f"/api/users/{self.staff.id}/admin_update/", {"name": "NV Một", "role": "staff", "branch_id": self.branch.id}, format="json").status_code, 200)
        self.assertEqual(self.ql.patch(f"/api/users/{self.staff.id}/admin_update/", {"branch_id": self.other.id}, format="json").status_code, 403)
        self.assertEqual(self.ql.patch(f"/api/users/{self.staff_other.id}/admin_update/", {"active": False}, format="json").status_code, 404)
        self.assertEqual(self.ql.delete(f"/api/users/{self.staff.id}/").status_code, 403)


    def test_huy_ban_khi_hoa_don_da_bi_huy(self):
        """Bàn có hoá đơn đã bị huỷ ở nơi khác vẫn phải giải phóng được."""
        sid = self._open()
        self._set_items(self.nv, sid, 1)
        order = DonHang.objects.get(phien_phuc_vu_id=sid)
        self.assertEqual(self.nv.patch(f"/api/orders/{order.id}/status/", {"status": "da_huy"}, format="json").status_code, 200)
        r = self.nv.post(f"/api/dining-sessions/{sid}/cancel/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.table.refresh_from_db()
        self.assertEqual(self.table.trang_thai, BanAn.TrangThai.TRONG)
