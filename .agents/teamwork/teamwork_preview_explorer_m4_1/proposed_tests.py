from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from foods.models import DanhMuc, MonAn, TheMonAn, NguyenLieu
from recommendations.models import TuongTacMonAn, GoiYMonAn
from recommendations.services import (
    DichVuGoiY,
    TRONG_SO_TUONG_TAC,
    MODEL_VERSION_COLD_START,
    MODEL_VERSION_CONTENT_BASED,
)

NguoiDung = get_user_model()


class KiemThuHeThongGoiYMonAn(TestCase):
    """
    Bộ kiểm thử tự động cho hệ sinh thái AI Gợi ý món ăn (Milestone 4 - Features 19-22):
    1. Feature 19: Content-Based TF-IDF & Cosine Similarity
    2. Feature 20: Weighted User Interactions
    3. Feature 21: Cold-Start Popularity Fallback
    4. Feature 22: Explainable Recommendation Tags & Cache Strategy
    """

    def setUp(self):
        self.client = APIClient()

        # Tạo danh mục
        self.dm_lau = DanhMuc.objects.create(ten="Lẩu", duong_dan="lau")
        self.dm_nuong = DanhMuc.objects.create(ten="Món Nướng", duong_dan="mon-nuong")
        self.dm_chay = DanhMuc.objects.create(ten="Món Chay", duong_dan="mon-chay")

        # Tạo thẻ món ăn
        self.the_cay = TheMonAn.objects.create(ten="Cay nồng", duong_dan="cay-nong")
        self.the_thanh_dam = TheMonAn.objects.create(ten="Thanh đạm", duong_dan="thanh-dam")

        # Tạo nguyên liệu
        self.nl_bo = NguyenLieu.objects.create(ten="Thịt bò", don_vi="kg")
        self.nl_hai_san = NguyenLieu.objects.create(ten="Hải sản", don_vi="kg")
        self.nl_sa_te = NguyenLieu.objects.create(ten="Sa tế", don_vi="g")

        # Tạo danh sách món ăn đa dạng
        self.mon_lau_thai = MonAn.objects.create(
            danh_muc=self.dm_lau,
            ten="Lẩu Thái Chua Cay",
            duong_dan="lau-thai-chua-cay",
            mo_ta_ngan="Lẩu hải sản chua cay thơm nồng vị sa tế",
            don_gia=Decimal("250000"),
            do_cay=2,
            diem_danh_gia=Decimal("4.8"),
            so_luot_danh_gia=85,
            con_hang=True,
            hien_thi=True,
        )
        self.mon_lau_thai.the_mon_an.add(self.the_cay)
        self.mon_lau_thai.nguyen_lieu.add(self.nl_hai_san, self.nl_sa_te)

        self.mon_bo_nuong = MonAn.objects.create(
            danh_muc=self.dm_nuong,
            ten="Bò Nướng Sa Tế",
            duong_dan="bo-nuong-sa-te",
            mo_ta_ngan="Bò tơ nướng sa tế thơm lừng",
            don_gia=Decimal("180000"),
            do_cay=1,
            diem_danh_gia=Decimal("4.6"),
            so_luot_danh_gia=40,
            con_hang=True,
            hien_thi=True,
        )
        self.mon_bo_nuong.the_mon_an.add(self.the_cay)
        self.mon_bo_nuong.nguyen_lieu.add(self.nl_bo, self.nl_sa_te)

        self.mon_chay = MonAn.objects.create(
            danh_muc=self.dm_chay,
            ten="Nấm Hầm Đậu Hũ Chay",
            duong_dan="nam-ham-dau-hu-chay",
            mo_ta_ngan="Món chay thanh nhẹ bổ dưỡng",
            don_gia=Decimal("95000"),
            la_mon_chay=True,
            do_cay=0,
            diem_danh_gia=Decimal("4.2"),
            so_luot_danh_gia=15,
            con_hang=True,
            hien_thi=True,
        )
        self.mon_chay.the_mon_an.add(self.the_thanh_dam)

        # Tạo user thử nghiệm
        self.user = NguoiDung.objects.create_user(
            so_dien_thoai="0901234567",
            mat_khau="MatKhau@123",
            ho_ten="Khách Thử Nghiệm",
        )

    def test_feature_20_interaction_weights(self):
        """Kiểm tra bảng trọng số tương tác: xem=1, thich=2, gio_hang=3, dat_hang=4, danh_gia=5."""
        self.assertEqual(TRONG_SO_TUONG_TAC["xem"], 1)
        self.assertEqual(TRONG_SO_TUONG_TAC["yeu_thich"], 2)
        self.assertEqual(TRONG_SO_TUONG_TAC["them_gio_hang"], 3)
        self.assertEqual(TRONG_SO_TUONG_TAC["dat_mon"], 4)
        self.assertEqual(TRONG_SO_TUONG_TAC["danh_gia"], 5)

    def test_feature_21_cold_start_fallback(self):
        """Khách mới 0 tương tác nhận danh sách món xếp theo độ phổ biến chuẩn hóa [0, 1]."""
        recs = DichVuGoiY.cap_nhat_goi_y(self.user, gioi_han=3)
        self.assertEqual(len(recs), 3)

        top_rec = recs[0]
        # Món có lượt đánh giá cao nhất (85 reviews, 4.8 sao) là Lẩu Thái
        self.assertEqual(top_rec.mon_an.id, self.mon_lau_thai.id)
        self.assertEqual(top_rec.phien_ban_model, MODEL_VERSION_COLD_START)
        self.assertEqual(top_rec.ly_do_goi_y, "Phổ biến hôm nay")
        self.assertTrue(0.0 <= float(top_rec.diem_tuong_dong) <= 1.0)

    def test_feature_19_tfidf_cosine_personalized(self):
        """Người dùng có tương tác nhận gợi ý món tương đồng cao nhất theo TF-IDF."""
        # User đặt món Lẩu Thái (weight 4) và đánh giá (weight 5)
        TuongTacMonAn.objects.create(
            nguoi_dung=self.user,
            mon_an=self.mon_lau_thai,
            loai_tuong_tac="dat_mon",
            trong_so=4,
        )
        TuongTacMonAn.objects.create(
            nguoi_dung=self.user,
            mon_an=self.mon_lau_thai,
            loai_tuong_tac="danh_gia",
            trong_so=5,
        )

        recs = DichVuGoiY.cap_nhat_goi_y(self.user, gioi_han=3)
        self.assertEqual(len(recs), 3)
        self.assertEqual(recs[0].mon_an.id, self.mon_lau_thai.id)
        self.assertEqual(recs[0].phien_ban_model, MODEL_VERSION_CONTENT_BASED)
        self.assertTrue(0.0 <= float(recs[0].diem_tuong_dong) <= 1.0)

    def test_feature_22_explainable_tags(self):
        """Kiểm tra tag giải thích khuyến nghị theo đặc trưng món ăn."""
        # Món lẩu
        TuongTacMonAn.objects.create(
            nguoi_dung=self.user,
            mon_an=self.mon_lau_thai,
            loai_tuong_tac="yeu_thich",
            trong_so=2,
        )
        recs = DichVuGoiY.cap_nhat_goi_y(self.user, gioi_han=2)
        top_rec = recs[0]
        self.assertIn("lẩu", top_rec.ly_do_goi_y.lower())

    def test_cache_strategy_and_refresh_action(self):
        """Kiểm tra cơ chế lưu cache GoiYMonAn và xóa cache khi có tương tác mới."""
        # Lần đầu tính toán -> Tạo cache DB
        DichVuGoiY.cap_nhat_goi_y(self.user, gioi_han=3)
        count_before = GoiYMonAn.objects.filter(nguoi_dung=self.user).count()
        self.assertEqual(count_before, 3)

        # Thêm tương tác qua API -> Kiểm tra xóa cache
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/tuong-tac/",
            {"mon_an": self.mon_bo_nuong.id, "loai_tuong_tac": "yeu_thich"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(GoiYMonAn.objects.filter(nguoi_dung=self.user).count(), 0)

        # Gọi lại API recommendations -> Tự động tính toán lại
        resp_recs = self.client.get("/api/recommendations/")
        self.assertEqual(resp_recs.status_code, 200)
        self.assertGreater(len(resp_recs.data), 0)
        self.assertIn("is_cold_start", resp_recs.data[0])
