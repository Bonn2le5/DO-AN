from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import NguoiDung, VaiTro
from branches.models import ChiNhanh
from chat.models import HoiThoai
from foods.models import DanhMuc, MonAn, MonAnTamHet
from foods.services import hom_nay_vn
from reservations.models import BanAn, DatBan


def make_user(username, role=None, branch=None):
    user = NguoiDung.objects.create_user(username=username, thu_dien_tu=f"{username}@x.vn", email=f"{username}@x.vn", password="Passw0rd!x")
    if role:
        user.danh_sach_vai_tro.add(VaiTro.objects.get_or_create(ten=role)[0])
    user.chi_nhanh_quan_ly = branch
    user.save()
    return user


def client_for(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


class MonTamHetTheoChiNhanhTest(TestCase):
    def setUp(self):
        self.a = ChiNhanh.objects.create(ten="A", dia_chi="a")
        self.b = ChiNhanh.objects.create(ten="B", dia_chi="b")
        self.table = BanAn.objects.create(chi_nhanh=self.a, so_ban="T1", khu_vuc="Trong nhà", suc_chua=4)
        cat = DanhMuc.objects.create(ten="Món", duong_dan="mon")
        self.ca = MonAn.objects.create(danh_muc=cat, ten="Cá hồi", duong_dan="ca-hoi", don_gia=Decimal("100000"), con_hang=True, hien_thi=True)
        self.com = MonAn.objects.create(danh_muc=cat, ten="Cơm", duong_dan="com", don_gia=Decimal("20000"), con_hang=True, hien_thi=True)
        self.nv = client_for(make_user("nv", "nhan_vien_ban_hang", self.a))

    def _set(self, sid, items):
        return self.nv.put(f"/api/dining-sessions/{sid}/items/", {"danh_sach_mon": [{"mon_an_id": f.id, "so_luong": q} for f, q in items]}, format="json")

    def test_bao_het_chan_goi_mon_o_chi_nhanh_do(self):
        sid = self.nv.post("/api/dining-sessions/walk-in/", {"ban_an": self.table.id, "so_luong_khach": 2}, format="json").json()["id"]
        self.assertEqual(self._set(sid, [(self.ca, 1)]).status_code, 200)  # gọi khi còn hàng

        r = self.nv.post("/api/tinh-trang-mon/", {"mon_an": self.ca.id, "het": True}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["mon_an"], [self.ca.id])
        self.assertEqual(self.nv.post("/api/tinh-trang-mon/", {"mon_an": self.ca.id, "het": True, "chi_nhanh": self.b.id}, format="json").status_code, 403)

        self.assertEqual(self._set(sid, [(self.ca, 1), (self.com, 1)]).status_code, 200)  # phần đã gọi vẫn giữ
        self.assertEqual(self._set(sid, [(self.ca, 2)]).status_code, 400)                 # gọi thêm món hết: chặn
        # Chi nhánh khác không bị ảnh hưởng; khách xem được không cần đăng nhập.
        self.assertEqual(client_for().get(f"/api/tinh-trang-mon/?chi_nhanh={self.b.id}").json()["mon_an"], [])

        self.nv.post("/api/tinh-trang-mon/", {"mon_an": self.ca.id, "het": False}, format="json")
        self.assertEqual(self._set(sid, [(self.ca, 2)]).status_code, 200)

    def test_nhan_vien_chua_gan_chi_nhanh_khong_bao_het_duoc(self):
        nv = client_for(make_user("nv0", "nhan_vien_ban_hang"))
        r = nv.post("/api/tinh-trang-mon/", {"mon_an": self.ca.id, "het": True, "chi_nhanh": self.b.id}, format="json")
        self.assertEqual(r.status_code, 403)
        self.assertFalse(MonAnTamHet.objects.exists())
        self.assertEqual(client_for().get("/api/tinh-trang-mon/?chi_nhanh=abc").status_code, 400)

    def test_bao_het_chi_co_hieu_luc_trong_ngay(self):
        MonAnTamHet.objects.create(mon_an=self.ca, chi_nhanh=self.a, ngay=hom_nay_vn() - timedelta(days=1))
        self.assertEqual(self.nv.get("/api/tinh-trang-mon/").json()["mon_an"], [])


class ChatTheoChiNhanhTest(TestCase):
    def setUp(self):
        self.a = ChiNhanh.objects.create(ten="A", dia_chi="a")
        self.b = ChiNhanh.objects.create(ten="B", dia_chi="b")
        self.khach = make_user("khach")
        DatBan.objects.create(
            nguoi_dung=self.khach, chi_nhanh=self.a, ngay_dat=hom_nay_vn() + timedelta(days=1), gio_bat_dau="19:00",
            so_luong_khach=2, hinh_thuc=DatBan.HinhThuc.CHI_GIU_CHO, trang_thai=DatBan.TrangThai.DA_XAC_NHAN, ten_khach="K", sdt_khach="09",
        )
        self.nv_a = client_for(make_user("nva", "nhan_vien_ban_hang", self.a))
        self.ql_b = client_for(make_user("qlb", "quan_ly_chi_nhanh", self.b))
        self.admin = client_for(make_user("ad", "quan_tri_vien"))

    def _ids(self, client):
        data = client.get("/api/hoi-thoai/").json()
        return [row["id"] for row in (data["results"] if isinstance(data, dict) else data)]

    def test_hoi_thoai_gan_chi_nhanh_va_loc_theo_chi_nhanh(self):
        room = client_for(self.khach).get("/api/hoi-thoai/dang-mo/").json()
        self.assertEqual(room["chi_nhanh"], self.a.id)  # theo lượt đặt bàn sắp tới
        self.assertEqual(self._ids(self.nv_a), [room["id"]])
        self.assertEqual(self._ids(self.ql_b), [])
        self.assertEqual(self.ql_b.get(f"/api/hoi-thoai/{room['id']}/tin-nhan/").status_code, 404)

        r = self.nv_a.post(f"/api/hoi-thoai/{room['id']}/tin-nhan/", {"noi_dung": "Chào anh, bàn đã giữ."}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.json()["is_staff"])

        # Chỉ admin chuyển hội thoại sang chi nhánh khác.
        self.assertEqual(self.nv_a.post(f"/api/hoi-thoai/{room['id']}/chuyen-chi-nhanh/", {"chi_nhanh": self.b.id}, format="json").status_code, 403)
        self.assertEqual(self.admin.post(f"/api/hoi-thoai/{room['id']}/chuyen-chi-nhanh/", {"chi_nhanh": self.b.id}, format="json").status_code, 200)
        self.assertEqual(self._ids(self.nv_a), [])
        self.assertEqual(self._ids(self.ql_b), [room["id"]])

    def test_tham_so_chi_nhanh_sai_khong_gay_loi(self):
        r = client_for(self.khach).get("/api/hoi-thoai/dang-mo/?chi_nhanh=abc")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["chi_nhanh"], self.a.id)

    def test_nhan_vien_chat_voi_tu_cach_khach(self):
        nv_b = make_user("nvb", "nhan_vien_ban_hang", self.b)
        room = HoiThoai.objects.create(khach_hang=nv_b, chi_nhanh=self.a)
        self.assertIn(room.id, self._ids(client_for(nv_b)))

    def test_hoi_thoai_chua_gan_chi_nhanh_chi_admin_thay(self):
        room = HoiThoai.objects.create(khach_hang=make_user("khach2"))
        self.assertIn(room.id, self._ids(self.admin))
        self.assertNotIn(room.id, self._ids(self.nv_a))
        self.assertNotIn(room.id, self._ids(self.ql_b))


class HopThuRealtimeTheoChiNhanhTest(TestCase):
    """Tin nhắn realtime chỉ được phát tới hộp thư admin và hộp thư của đúng chi nhánh."""

    def test_nhom_websocket_va_quyen_vao_phong(self):
        from chat.services import STAFF_GROUP, branch_group, can_access_room, inbox_groups
        a = ChiNhanh.objects.create(ten="A", dia_chi="a")
        b = ChiNhanh.objects.create(ten="B", dia_chi="b")
        khach = make_user("khach")
        room = HoiThoai.objects.create(khach_hang=khach, chi_nhanh=a)
        groups = inbox_groups(room)
        self.assertIn(STAFF_GROUP, groups)
        self.assertIn(branch_group(a.id), groups)
        self.assertNotIn(branch_group(b.id), groups)
        self.assertTrue(can_access_room(make_user("nva", "nhan_vien_ban_hang", a), room))
        self.assertFalse(can_access_room(make_user("nvb", "nhan_vien_ban_hang", b), room))
        self.assertTrue(can_access_room(khach, room))
        self.assertFalse(can_access_room(make_user("khac"), room))
