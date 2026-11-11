import json
import os
from decimal import Decimal
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from foods.models import DanhMuc, MonAn, NguyenLieu
from recommendations.models import TuongTacMonAn
from recommendations.tro_ly import loai_dam, so_mon_can

NguoiDung = get_user_model()

BUA_AN = ["lau", "nuong", "goi", "nham-nhi"]


class DuLieuThucDonMau:
    def setUp(self):
        cache.clear()  # bộ đếm giới hạn tần suất nằm trong cache, không tự xoá giữa các test
        self.client = APIClient()
        dm = {
            k: DanhMuc.objects.create(ten=t, duong_dan=k)
            for k, t in [("lau", "Lẩu"), ("nuong", "Nướng"), ("goi", "Gỏi"), ("nham-nhi", "Nhâm nhi")]
        }
        ot = NguyenLieu.objects.create(ten="Ớt", don_vi="g")

        def mon(k, ten, gia, mo_ta="", reviews=10, cay=False):
            m = MonAn.objects.create(
                danh_muc=dm[k], ten=ten, duong_dan=ten.lower().replace(" ", "-").replace("(", "").replace(")", ""),
                mo_ta_ngan=mo_ta, don_gia=Decimal(gia), so_luot_danh_gia=reviews,
                diem_danh_gia=Decimal("4.5"), con_hang=True, hien_thi=True,
            )
            if cay:
                m.nguyen_lieu.add(ot, through_defaults={"so_luong_can": Decimal("1")})
            return m

        self.lau_mala = mon("lau", "Set Lẩu MaLa", 149000, "lẩu cay tứ xuyên", reviews=50, cay=True)
        self.lau_nam = mon("lau", "Set Lẩu Nấm", 149000, "nấm thiên nhiên thanh ngọt", reviews=20)
        self.lau_to = mon("lau", "Set Lẩu Thái (3-5 người)", 369000, "lẩu thái hải sản")
        self.bo = mon("nuong", "Ba Chỉ Bò Nướng", 159000, "ba chỉ bò sốt bbq")
        self.heo = mon("nuong", "Nạc Dăm Heo Nướng", 99000, "nạc dăm heo")
        self.tom = mon("nuong", "Tôm Nướng", 99000, "tôm sú nướng muối ớt", cay=True)
        self.muc = mon("nuong", "Mực Nướng", 159000, "mực tươi")
        self.rau = mon("nuong", "Rau Củ Nướng", 29000, "rau củ")
        self.goi = mon("goi", "Gỏi Ngó Sen", 149000, "gỏi tôm thịt")
        self.goi_re = mon("goi", "Gỏi Xoài", 89000, "gỏi xoài xanh")
        self.nn1 = mon("nham-nhi", "Khoai Tây Chiên", 49000, "khoai chiên")
        self.nn2 = mon("nham-nhi", "Cà Tím Mỡ Hành", 39000, "cà tím")
        self.ca = mon("nuong", "Cá Tầm Nướng", 149000, "cá tầm")
        self.luoi = mon("nuong", "Lưỡi Bò Nướng", 129000, "lưỡi bò")
        self.ga = mon("nuong", "Má Đùi Gà", 89000, "gà")
        self.goi3 = mon("goi", "Gỏi Bò", 129000, "gỏi bò")
        self.nn3 = mon("nham-nhi", "Nấm Chiên", 59000, "nấm chiên giòn")


@override_settings(TRO_LY_DUNG_LLM=True)
@mock.patch.dict(os.environ, {"OPENAI_API_KEY": "khoa-gia-cho-test", "OPENAI_MODEL": "model-test",
                              "OPENAI_BASE_URL": "https://cong-test/v1"})
class KiemThuTroLyGoiMon(DuLieuThucDonMau, TestCase):
    """AI (giả lập) chỉ trả JSON ý định; backend chọn món từ database."""

    def _ai(self, loi=None, van_ban=None, **kw):
        y = {"intent": "recommend_food", "categories": ["lau", "nuong"], "occasion": None, "flavors": [],
             "preferences": [], "constraints": [], "people": None, "budget": None, "chi_nhom": False,
             "original_query": ""}
        y.update(kw)
        tra_ve = mock.Mock()
        tra_ve.raise_for_status.side_effect = loi
        noi_dung = van_ban if van_ban is not None else "```json\n" + json.dumps(y, ensure_ascii=False) + "\n```"
        tra_ve.json.return_value = {"output": [
            {"type": "reasoning"},
            {"type": "message", "content": [{"type": "output_text", "text": noi_dung}]},
        ]}
        return mock.patch("recommendations.tro_ly.requests.post", return_value=tra_ve)

    def _hoi(self, **body):
        return self.client.post("/api/goi-y/tro-ly/", body, format="json")

    def _mon(self, r):
        return {m["mon_an"]["id"]: m for g in r.data["nhom_mon"] for m in g["mon"]}

    def _so_mon(self, r):
        return {g["khoa"]: len(g["mon"]) for g in r.data["nhom_mon"]}

    def test_so_mon_theo_so_nguoi(self):
        self.assertEqual(so_mon_can(4, BUA_AN), {"lau": 1, "nuong": 4, "goi": 1, "nham-nhi": 1})
        self.assertEqual(so_mon_can(8, BUA_AN), {"lau": 2, "nuong": 8, "goi": 2, "nham-nhi": 2})
        self.assertEqual(so_mon_can(2, BUA_AN), {"lau": 1, "nuong": 2, "goi": 1, "nham-nhi": 1})
        self.assertEqual(so_mon_can(4, ["nuong"]), {"nuong": 5})

    def test_loai_dam(self):
        self.assertEqual(loai_dam(self.luoi), "noi_tang")  # lưỡi bò là nội tạng, không phải bò
        self.assertEqual(loai_dam(self.bo), "bo")
        self.assertEqual(loai_dam(self.tom), "tom")
        self.assertEqual(loai_dam(self.ca), "ca")

    def test_4_nguoi_du_nhom_moi_mon_1_phan(self):
        with self._ai(people=4) as post:
            r = self._hoi(yeu_cau="lẩu nướng 4 người", dieu_chinh=["thêm gỏi"])
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["phien_ban_model"], "tro_ly_llm_db_v3")
        self.assertEqual(self._so_mon(r), {"goi": 1, "nham-nhi": 1, "lau": 1, "nuong": 4})
        mon = self._mon(r)
        self.assertTrue(all(m["so_luong"] == 1 for m in mon.values()))
        self.assertTrue(all("ly_do" not in m for m in mon.values()))
        self.assertEqual(r.data["tong_tien"], sum(m["thanh_tien"] for m in mon.values()))
        # AI chỉ nhận tin nhắn, không nhận thực đơn → nhanh
        gui = post.call_args.kwargs["json"]
        self.assertEqual(post.call_args.args[0], "https://cong-test/v1/responses")
        self.assertNotIn("Set Lẩu", gui["input"])
        self.assertIn("Điều chỉnh 1: thêm gỏi", gui["input"])
        self.assertFalse(gui["store"])

    def test_nuong_da_dang_loai_dam(self):
        with self._ai(people=4):
            r = self._hoi(yeu_cau="lẩu nướng 4 người")
        nuong = [MonAn.objects.get(id=m["mon_an"]["id"]) for g in r.data["nhom_mon"] if g["khoa"] == "nuong"
                 for m in g["mon"]]
        self.assertEqual(len({loai_dam(m) for m in nuong}), 4)  # 4 món, 4 loại đạm khác nhau

    def test_rau_nuong_xep_sau_dam(self):
        with self._ai(people=2):
            r = self._hoi(yeu_cau="lẩu nướng 2 người")
        self.assertNotIn(self.rau.id, self._mon(r))
        with self._ai(people=2, preferences=["chay"], categories=["nuong"], chi_nhom=True):
            r = self._hoi(yeu_cau="chỉ nướng, ăn chay")
        self.assertIn(self.rau.id, self._mon(r))

    def test_so_khach_dat_ban_la_khung_co_dinh(self):
        # Lỗi thật: đặt 10 khách, khách gõ "gia đình", AI trả people=4 → thực đơn 4 người
        with self._ai(people=4, occasion="gia_dinh"):
            r = self._hoi(yeu_cau="Bữa gia đình", so_nguoi=10)
        self.assertEqual(r.data["phan_tich"]["so_nguoi"], 10)
        self.assertEqual(self._so_mon(r)["lau"], 2)
        self.assertTrue(any("10 khách của đơn đặt bàn" in g for g in r.data["ghi_chu"]))
        with self._ai(people=6):  # không có đơn đặt bàn → dùng số khách nói
            r = self._hoi(yeu_cau="lẩu nướng 6 người")
        self.assertEqual(r.data["phan_tich"]["so_nguoi"], 6)

    def test_8_nguoi_them_mon_khac(self):
        with self._ai(people=8):
            r = self._hoi(yeu_cau="lẩu nướng 8 người")
        self.assertEqual(self._so_mon(r), {"goi": 2, "nham-nhi": 2, "lau": 2, "nuong": 8})

    def test_nhom_dong_uu_tien_set_lau_lon(self):
        with self._ai(people=5):
            r = self._hoi(yeu_cau="lẩu nướng 5 người")
        lau = [m["mon_an"]["id"] for g in r.data["nhom_mon"] if g["khoa"] == "lau" for m in g["mon"]]
        self.assertEqual(lau, [self.lau_to.id])

    def test_ban_2_nguoi_khong_goi_set_lon(self):
        for _ in range(5):
            r = self._hoi(yeu_cau="Nhiều thịt", so_nguoi=2, goi_y_nhanh="nhieu_thit")
            self.assertNotIn(self.lau_to.id, self._mon(r))

    def test_gu_cay_uu_tien_mon_cay(self):
        with self._ai(people=2, flavors=["cay"]):
            r = self._hoi(yeu_cau="lẩu nướng cay 2 người")
        self.assertIn(self.lau_mala.id, self._mon(r))
        self.assertEqual(r.data["phan_tich"]["khau_vi"], ["cay"])

    def test_rang_buoc_va_di_ung(self):
        with self._ai(people=6, constraints=["khong_cay", "di_ung_tom", "khong_noi_tang"]):
            r = self._hoi(yeu_cau="6 người không cay, bé dị ứng tôm, không ăn nội tạng")
        mon = self._mon(r)
        for bi_loai in (self.lau_mala, self.tom, self.goi, self.luoi):  # gỏi ngó sen có tôm trong mô tả
            self.assertNotIn(bi_loai.id, mon)
        self.assertEqual(r.data["phan_tich"]["tranh"], ["cay", "tôm", "nội tạng"])
        self.assertTrue(any("dị ứng" in g for g in r.data["ghi_chu"]))

    def test_chi_nhom(self):
        with self._ai(people=2, categories=["nuong"], chi_nhom=True):
            r = self._hoi(yeu_cau="chỉ ăn nướng 2 người")
        self.assertEqual(self._so_mon(r), {"nuong": 3})

    def test_ngan_sach(self):
        with self._ai(people=4, budget=600_000):
            r = self._hoi(yeu_cau="lẩu nướng 4 người 600k")
        self.assertLessEqual(r.data["tong_tien"], 600_000)
        self.assertIn("lau", self._so_mon(r))
        self.assertIn("nuong", self._so_mon(r))

    def test_toi_da_1_mon_quen(self):
        user = NguoiDung.objects.create_user(
            username="khach_quen", email="khach_quen@moc.vn", so_dien_thoai="0901112225", password="MatKhau@123"
        )
        quen = [self.lau_to, self.lau_nam, self.lau_mala, self.goi, self.goi_re, self.bo, self.heo, self.nn1]
        for m in quen:
            TuongTacMonAn.objects.create(nguoi_dung=user, mon_an=m, loai_tuong_tac="yeu_thich", trong_so=2)
        self.client.force_authenticate(user)
        with self._ai(people=4):
            r = self._hoi(yeu_cau="lẩu nướng 4 người")
        mon = self._mon(r)
        self.assertLessEqual(len(set(mon) & {m.id for m in quen}), 1)
        self.assertEqual(self._so_mon(r)["goi"], 1)  # vẫn đủ món nhờ món chưa gọi

    def test_goi_y_nhanh_khong_goi_ai(self):
        for khoa in ("lau_nuong", "gia_dinh", "tiet_kiem", "nhieu_thit", "hai_san", "lai_rai"):
            with self._ai() as post:
                r = self._hoi(yeu_cau="Gợi ý nhanh", so_nguoi=4, goi_y_nhanh=khoa)
            post.assert_not_called()
            self.assertEqual(r.status_code, 200, khoa)
            self.assertEqual(r.data["phan_tich"]["so_nguoi"], 4)
            self.assertEqual(self._so_mon(r)["lau"], 1)

    @mock.patch.dict(os.environ, {"OPENAI_MODEL": ""})
    def test_goi_y_nhanh_chay_ca_khi_chua_cau_hinh_ai(self):
        r = self._hoi(yeu_cau="Lẩu nướng cho 4 người", so_nguoi=4, goi_y_nhanh="lau_nuong")
        self.assertEqual(r.status_code, 200)

    def test_goi_y_nhanh_noi_dung(self):
        r = self._hoi(yeu_cau="Bữa gia đình", so_nguoi=4, goi_y_nhanh="gia_dinh")
        self.assertEqual(r.data["phan_tich"]["tranh"], ["cay"])
        self.assertNotIn(self.lau_mala.id, self._mon(r))
        r = self._hoi(yeu_cau="Tiết kiệm", so_nguoi=2, goi_y_nhanh="tiet_kiem")
        self.assertEqual(r.data["ngan_sach"], 300_000)  # 150k × 2 người
        self.assertLessEqual(r.data["tong_tien"], 300_000)
        r = self._hoi(yeu_cau="Nhiều thịt", so_nguoi=4, goi_y_nhanh="nhieu_thit")
        self.assertEqual(r.data["phan_tich"]["khau_vi"], ["nhiều thịt"])

    def test_goi_y_nhanh_roi_dieu_chinh_thi_hoi_ai(self):
        with self._ai(people=None, constraints=["khong_cay"]) as post:
            r = self._hoi(yeu_cau="Lẩu nướng cho 4 người", dieu_chinh=["không cay"], so_nguoi=4,
                          goi_y_nhanh="lau_nuong")
        post.assert_called_once()
        self.assertEqual(r.data["phan_tich"]["tranh"], ["cay"])

    def test_goi_y_nhanh_sai_ma(self):
        r = self._hoi(yeu_cau="x", goi_y_nhanh="khong_co")
        self.assertEqual(r.status_code, 400)

    def test_ai_bia_mon_va_gia_bi_loc_bo(self):
        # AI tự thêm danh sách món bịa, giá, giá trị ngoài danh sách cho phép, số người/ngân sách vô lý
        with self._ai(people=4, mon=[{"ten": "Tôm hùm 1 đồng", "gia": 1}], gia="1đ", loi_nhan="Khuyến mãi 90%",
                      flavors=["cay", "sieu_cay"], constraints=["khong_cay", "khong_vang"], occasion="sinh_nhat",
                      budget=5, original_query="AI tự viết"):
            r = self._hoi(yeu_cau="lẩu nướng 4 người")
        y = r.data["y_dinh"]
        self.assertEqual(set(y), {"intent", "categories", "occasion", "flavors", "preferences", "constraints",
                                  "people", "budget", "chi_nhom", "original_query"})
        self.assertEqual(y["flavors"], ["cay"])
        self.assertEqual(y["constraints"], ["khong_cay"])
        self.assertIsNone(y["occasion"])
        self.assertIsNone(y["budget"])
        self.assertEqual(y["original_query"], "lẩu nướng 4 người")
        self.assertNotIn("Tôm hùm", str(r.data))
        self.assertNotIn("Khuyến mãi", str(r.data))
        ids = {m.id for m in MonAn.objects.all()}
        for g in r.data["nhom_mon"]:
            for m in g["mon"]:  # mọi món và giá đều từ database
                self.assertIn(m["mon_an"]["id"], ids)
                self.assertEqual(m["don_gia"], int(MonAn.objects.get(id=m["mon_an"]["id"]).don_gia_hien_tai))

    def test_an_chay_loai_mon_dong_vat(self):
        with self._ai(people=4, preferences=["chay"]):
            r = self._hoi(yeu_cau="4 người ăn chay")
        ten = {m["mon_an"]["ten"] for g in r.data["nhom_mon"] for m in g["mon"]}
        self.assertTrue(ten)
        self.assertTrue(ten <= {"Set Lẩu Nấm", "Rau Củ Nướng", "Gỏi Xoài", "Khoai Tây Chiên", "Cà Tím Mỡ Hành",
                                "Nấm Chiên"}, ten)

    def test_cau_khong_lien_quan(self):
        with self._ai(intent="other"):
            r = self._hoi(yeu_cau="thời tiết hôm nay thế nào")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["nhom_mon"], [])
        self.assertIn("gợi ý món", r.data["loi_nhan"])

    def test_ai_loi_tra_503(self):
        with self._ai(loi=requests.HTTPError("401")):
            r = self._hoi(yeu_cau="lẩu nướng 4 người")
        self.assertEqual(r.status_code, 503)

    def test_ai_tra_chu_khong_phai_json_tra_503(self):
        with self._ai(van_ban="Dạ em gợi ý lẩu nấm ạ"):
            r = self._hoi(yeu_cau="lẩu nướng 2 người")
        self.assertEqual(r.status_code, 503)

    @mock.patch.dict(os.environ, {"OPENAI_MODEL": ""})
    def test_chua_cau_hinh_tra_503(self):
        with self._ai() as post:
            r = self._hoi(yeu_cau="lẩu nướng 2 người")
        post.assert_not_called()
        self.assertEqual(r.status_code, 503)

    @mock.patch.dict(os.environ, {"OPENAI_BASE_URL": ""})
    def test_base_url_bo_trong_dung_cong_openai(self):
        with self._ai(people=2) as post:
            r = self._hoi(yeu_cau="lẩu nướng 2 người")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/responses")

    def test_ai_tra_so_vo_cuc_khong_sap(self):
        with self._ai(van_ban='{"intent": "recommend_food", "people": 1e999, "budget": 1e999}'):
            r = self._hoi(yeu_cau="lẩu nướng")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["phan_tich"]["so_nguoi"], 2)
        self.assertIsNone(r.data["ngan_sach"])

    def test_cong_tra_json_sai_khuon_tra_503(self):
        for sai in (["không phải object"], {"output": ["không phải object"]}, {"output": 5}):
            tra_ve = mock.Mock()
            tra_ve.raise_for_status.return_value = None
            tra_ve.json.return_value = sai
            with mock.patch("recommendations.tro_ly.requests.post", return_value=tra_ve):
                r = self._hoi(yeu_cau="lẩu nướng 2 người")
            self.assertEqual(r.status_code, 503, sai)

    def test_gioi_han_tan_suat(self):
        ma = [self._hoi(yeu_cau="Lẩu nướng", so_nguoi=2, goi_y_nhanh="lau_nuong").status_code for _ in range(21)]
        self.assertEqual(ma[:20], [200] * 20)
        self.assertEqual(ma[20], 429)

    def test_tu_choi_yeu_cau_rong(self):
        r = self._hoi(yeu_cau="")
        self.assertEqual(r.status_code, 400)
