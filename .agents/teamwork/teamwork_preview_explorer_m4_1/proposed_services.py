# Dịch vụ gợi ý món ăn (AI Recommender System)
# Kiến trúc: Content-Based Filtering + TF-IDF + Cosine Similarity (Pure Python)
# Hỗ trợ: Weighted User Interactions, Cold-Start Popularity Fallback, Explainable Tags
import math
import re
from collections import Counter
from decimal import Decimal
from typing import Dict, List, Any, Optional

from foods.models import MonAn
from .models import TuongTacMonAn, GoiYMonAn

# ==============================================================================
# 1. Trọng số tương tác chuẩn hóa theo thiết kế & tài liệu đặc tả
# ==============================================================================
# Feature 20: xem=1, thích=2, giỏ=3, đặt=4, đánh giá=5
TRONG_SO_TUONG_TAC = {
    "xem": 1,
    "yeu_thich": 2,
    "them_gio_hang": 3,
    "dat_mon": 4,
    "danh_gia": 5,
}

# Bảng bí danh hỗ trợ request từ frontend tiếng Anh hoặc biến thể tên
ALIAS_TRONG_SO = {
    "view": 1,
    "thich": 2,
    "favorite": 2,
    "like": 2,
    "gio_hang": 3,
    "cart": 3,
    "add_cart": 3,
    "dat_hang": 4,
    "order": 4,
    "review": 5,
    "rating": 5,
}

MODEL_VERSION_CONTENT_BASED = "cb_tfidf_v1"
MODEL_VERSION_COLD_START = "cold_start_v1"


def lay_trong_so_tuong_tac(loai: str) -> int:
    """Lấy trọng số số nguyên tương ứng cho loại tương tác."""
    k = str(loai).lower().strip()
    return TRONG_SO_TUONG_TAC.get(k, ALIAS_TRONG_SO.get(k, 1))


def tach_tu_khoa_mon_an(mon_an: MonAn) -> List[str]:
    """
    Tách từ khóa từ các trường đặc trưng của món ăn để xây dựng corpus TF-IDF.
    Tận dụng prefetch cache (không gọi .values_list() để tránh N+1 queries).
    """
    # Lấy tên nguyên liệu từ prefetch cache nếu có
    if hasattr(mon_an, "_prefetched_objects_cache") and "nguyen_lieu" in mon_an._prefetched_objects_cache:
        ds_nguyen_lieu = " ".join([nl.ten for nl in mon_an.nguyen_lieu.all()])
    else:
        ds_nguyen_lieu = " ".join(mon_an.nguyen_lieu.values_list("ten", flat=True))

    # Lấy tên thẻ món ăn từ prefetch cache nếu có
    if hasattr(mon_an, "_prefetched_objects_cache") and "the_mon_an" in mon_an._prefetched_objects_cache:
        ds_the = " ".join([t.ten for t in mon_an.the_mon_an.all()])
    else:
        ds_the = " ".join(mon_an.the_mon_an.values_list("ten", flat=True))

    ten_danh_muc = mon_an.danh_muc.ten if mon_an.danh_muc else ""
    mo_ta_ngan = mon_an.mo_ta_ngan or ""
    mo_ta_chi_tiet = mon_an.mo_ta_chi_tiet or ""

    # Bổ sung từ khóa ngữ cảnh đặc thù
    dac_trung_phu = []
    if mon_an.la_mon_chay:
        dac_trung_phu.append("món chay ăn chay thanh đạm")
    if mon_an.do_cay > 0:
        dac_trung_phu.append("món cay vị cay sa tế")
        if mon_an.do_cay >= 2:
            dac_trung_phu.append("rất cay nồng")

    van_ban_gop = (
        f"{mon_an.ten} {ten_danh_muc} {mo_ta_ngan} {mo_ta_chi_tiet} "
        f"{ds_nguyen_lieu} {ds_the} {' '.join(dac_trung_phu)}"
    ).lower()

    return re.findall(r"[\wÀ-ỹ]+", van_ban_gop)


def tao_ly_do_goi_y(mon_an: MonAn, user_vector: Optional[Dict[str, float]] = None) -> str:
    """
    Tạo nhãn giải thích khuyến nghị (Explainable Recommendation Tags).
    Đáp ứng các tiêu chí phân loại món ăn (lẩu, cay, nướng, chay, hải sản).
    """
    corpus = f"{mon_an.ten} {mon_an.danh_muc.ten if mon_an.danh_muc else ''} {mon_an.mo_ta_ngan or ''}".lower()
    
    if "lẩu" in corpus or "hotpot" in corpus:
        return "Gợi ý vì bạn yêu thích các món lẩu ấm cúng"
    elif mon_an.do_cay > 0 or "cay" in corpus or "sa tế" in corpus:
        return "Phù hợp với khẩu vị thích món cay nồng của bạn"
    elif "nướng" in corpus or "bbq" in corpus or "hải sản" in corpus:
        return "Được gợi ý dựa trên sở thích món nướng & hải sản của bạn"
    elif mon_an.la_mon_chay or "chay" in corpus:
        return "Lựa chọn thanh đạm phù hợp với sở thích ăn chay của bạn"
    return "Phù hợp với khẩu vị và các món bạn thường chọn"


class DichVuGoiY:
    @classmethod
    def tinh_goi_y_cold_start(cls, danh_sach_mon: List[MonAn], gioi_han: int = 6) -> List[tuple]:
        """
        Chiến lược Cold-Start Popularity Fallback cho người dùng chưa có tương tác hoặc khách vãng lai.
        Công thức điểm tổng hợp:
          score = 0.6 * (so_luot_danh_gia / max_reviews) + 0.4 * (diem_danh_gia / 5.0)
        Đảm bảo 0.0 <= score <= 1.0, an toàn tuyệt đối với CHECK constraint trong PostgreSQL.
        """
        if not danh_sach_mon:
            return []

        max_reviews = max([m.so_luot_danh_gia for m in danh_sach_mon] or [1])
        if max_reviews <= 0:
            max_reviews = 1

        danh_sach_diem = []
        for mon in danh_sach_mon:
            reviews = mon.so_luot_danh_gia or 0
            rating = float(mon.diem_danh_gia or 4.5)
            cold_score = 0.6 * (reviews / max_reviews) + 0.4 * (rating / 5.0)
            cold_score = min(1.0, max(0.0, cold_score))
            danh_sach_diem.append((mon, round(cold_score, 4), "Phổ biến hôm nay", True))

        danh_sach_diem.sort(key=lambda x: x[1], reverse=True)
        return danh_sach_diem[:gioi_han]

    @classmethod
    def lay_goi_y_khach_vang_lai(cls, gioi_han: int = 6) -> List[GoiYMonAn]:
        """Trả về đối tượng gợi ý không lưu DB cho khách chưa đăng nhập."""
        danh_sach_mon = list(
            MonAn.objects.filter(con_hang=True, hien_thi=True)
            .select_related("danh_muc")
            .prefetch_related("nguyen_lieu", "the_mon_an")
        )
        ket_qua = cls.tinh_goi_y_cold_start(danh_sach_mon, gioi_han=gioi_han)
        return [
            GoiYMonAn(
                id=idx + 1,
                mon_an=mon,
                diem_tuong_dong=Decimal(str(diem)),
                ly_do_goi_y=ly_do,
                phien_ban_model=MODEL_VERSION_COLD_START,
            )
            for idx, (mon, diem, ly_do, _) in enumerate(ket_qua)
        ]

    @classmethod
    def cap_nhat_goi_y(cls, nguoi_dung, gioi_han: int = 6) -> List[GoiYMonAn]:
        """
        Tính toán lại gợi ý cho người dùng:
        1. Người dùng mới (0 tương tác): Cold-Start Popularity Fallback.
        2. Người dùng có tương tác: TF-IDF + Cosine Similarity với vector khẩu vị có trọng số.
        3. Lưu kết quả vào bảng goi_y_mon_an làm cache.
        """
        danh_sach_mon = list(
            MonAn.objects.filter(con_hang=True, hien_thi=True)
            .select_related("danh_muc")
            .prefetch_related("nguyen_lieu", "the_mon_an")
        )
        if not danh_sach_mon:
            return []

        # Lấy lịch sử tương tác của người dùng
        tuong_tac_qs = TuongTacMonAn.objects.filter(nguoi_dung=nguoi_dung).select_related("mon_an")
        ds_tuong_tac = list(tuong_tac_qs)

        # Trường hợp 1: Chưa có tương tác nào -> Kích hoạt Cold-Start Popularity
        if not ds_tuong_tac:
            ket_qua = cls.tinh_goi_y_cold_start(danh_sach_mon, gioi_han=gioi_han)
        else:
            # Trường hợp 2: Có tương tác -> Thuật toán TF-IDF & Cosine Similarity Pure-Python
            corpus_tu_khoa = [tach_tu_khoa_mon_an(m) for m in danh_sach_mon]
            mon_id_to_index = {m.id: idx for idx, m in enumerate(danh_sach_mon)}

            # Tính Document Frequency (DF)
            doc_freq = Counter(
                tu for tai_lieu in corpus_tu_khoa for tu in set(tai_lieu)
            )
            tong_so_tai_lieu = len(danh_sach_mon)

            # Tính vector TF-IDF chuẩn hóa L2 cho từng món ăn
            vector_mon_an = []
            for doc in corpus_tu_khoa:
                tf = Counter(doc)
                vec = {}
                norm_sq = 0.0
                for tu, so_lan in tf.items():
                    # Smoothed IDF: ln((N + 1) / (DF + 1)) + 1
                    # Sublinear TF: 1 + ln(so_lan)
                    idf = math.log((tong_so_tai_lieu + 1) / (doc_freq[tu] + 1)) + 1.0
                    val = (1.0 + math.log(so_lan)) * idf
                    vec[tu] = val
                    norm_sq += val * val
                norm = math.sqrt(norm_sq) or 1.0
                vector_mon_an.append({tu: v / norm for tu, v in vec.items()})

            # Xây dựng Vector Khẩu vị Người dùng (User Preference Profile)
            vector_khau_vi = Counter()
            co_tuong_tac_hop_le = False

            for tt in ds_tuong_tac:
                m_id = tt.mon_an_id
                if m_id not in mon_id_to_index:
                    continue
                co_tuong_tac_hop_le = True
                trong_so = float(tt.trong_so) if tt.trong_so else lay_trong_so_tuong_tac(tt.loai_tuong_tac)
                vec_mon = vector_mon_an[mon_id_to_index[m_id]]
                for tu, val in vec_mon.items():
                    vector_khau_vi[tu] += val * trong_so

            if not co_tuong_tac_hop_le or not vector_khau_vi:
                ket_qua = cls.tinh_goi_y_cold_start(danh_sach_mon, gioi_han=gioi_han)
            else:
                # Chuẩn hóa L2 cho User Profile Vector
                norm_user_sq = sum(v * v for v in vector_khau_vi.values())
                norm_user = math.sqrt(norm_user_sq) or 1.0
                norm_user_vec = {tu: v / norm_user for tu, v in vector_khau_vi.items()}

                # Tính Cosine Similarity = Dot Product giữa 2 vector đơn vị
                danh_sach_diem = []
                for mon, vec in zip(danh_sach_mon, vector_mon_an):
                    score = sum(norm_user_vec.get(tu, 0.0) * vec.get(tu, 0.0) for tu in vec)
                    score = min(1.0, max(0.0, score))
                    ly_do = tao_ly_do_goi_y(mon, norm_user_vec)
                    danh_sach_diem.append((mon, round(score, 4), ly_do, False))

                danh_sach_diem.sort(key=lambda x: x[1], reverse=True)
                ket_qua = danh_sach_diem[:gioi_han]

        # Ghi đè vào bảng goi_y_mon_an để làm cache cho các truy vấn tiếp theo
        GoiYMonAn.objects.filter(nguoi_dung=nguoi_dung).delete()
        danh_sach_tao = [
            GoiYMonAn(
                nguoi_dung=nguoi_dung,
                mon_an=mon,
                diem_tuong_dong=Decimal(str(diem)),
                ly_do_goi_y=ly_do,
                phien_ban_model=MODEL_VERSION_COLD_START if is_cold else MODEL_VERSION_CONTENT_BASED,
            )
            for mon, diem, ly_do, is_cold in ket_qua
        ]
        GoiYMonAn.objects.bulk_create(danh_sach_tao)

        return list(
            GoiYMonAn.objects.filter(nguoi_dung=nguoi_dung)
            .select_related("mon_an")
            .order_by("-diem_tuong_dong")
        )


# Backward-compatible adapter method and aliases
def _refresh_for(cls, user, limit=6):
    return cls.cap_nhat_goi_y(user, gioi_han=limit)


DichVuGoiY.refresh_for = classmethod(_refresh_for)
RecommendationService = DichVuGoiY
