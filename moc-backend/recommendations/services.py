# Dịch vụ gợi ý món ăn (AI Recommender System)
# Kiến trúc: Content-Based Filtering + TF-IDF + Cosine Similarity (Pure Python)
# Hỗ trợ: Weighted User Interactions, Cold-Start Popularity Fallback,
#         Explainable Recommendation (lý do dựa trên món khách đã tương tác),
#         Item-to-Item "món tương tự".
import math
import re
from collections import Counter
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Tuple

from foods.models import MonAn
from .models import TuongTacMonAn, GoiYMonAn

# ==============================================================================
# 1. Trọng số tương tác chuẩn hóa theo thiết kế & tài liệu đặc tả
# ==============================================================================
# xem=1, yêu thích=2, đặt món=4, đánh giá=5
TRONG_SO_TUONG_TAC = {
    "xem": 1,
    "yeu_thich": 2,
    "dat_mon": 4,
    "danh_gia": 5,
}

# Bảng bí danh hỗ trợ request từ frontend tiếng Anh hoặc biến thể tên
ALIAS_TRONG_SO = {
    "view": 1,
    "thich": 2,
    "favorite": 2,
    "like": 2,
    "dat_hang": 4,
    "order": 4,
    "review": 5,
    "rating": 5,
}

# Động từ dùng khi sinh câu giải thích
DONG_TU_TUONG_TAC = {
    "xem": "đã xem",
    "yeu_thich": "đã thích",
    "dat_mon": "đã đặt",
    "danh_gia": "đã đánh giá",
}

MODEL_VERSION_CONTENT_BASED = "cb_tfidf_v1"
MODEL_VERSION_COLD_START = "cold_start_v1"
MODEL_VERSION_ITEM_ITEM = "item_tfidf_v1"

LY_DO_COLD_START = "Phổ biến hôm nay"


# Loại tương tác client được phép tự gửi; dat_mon / danh_gia do server ghi.
LOAI_TUONG_TAC_TU_CLIENT = ("xem", "yeu_thich")


def trong_so_danh_gia(so_sao: int) -> float:
    """5★ → +5, 4★ → +2.5, 3★ → 0, 2★ → −2.5, 1★ → −5 (đánh giá thấp kéo khẩu vị ra xa)."""
    return (int(so_sao) - 3) * 2.5


def lay_trong_so_tuong_tac(loai: str) -> int:
    """Lấy trọng số số nguyên tương ứng cho loại tương tác."""
    k = str(loai).lower().strip()
    return TRONG_SO_TUONG_TAC.get(k, ALIAS_TRONG_SO.get(k, 1))


def _ds_ten(mon_an: MonAn, quan_he: str) -> List[str]:
    """Đọc tên từ quan hệ M2M, ưu tiên prefetch cache (tránh N+1 queries)."""
    cache = getattr(mon_an, "_prefetched_objects_cache", {})
    if quan_he in cache:
        return [x.ten for x in getattr(mon_an, quan_he).all()]
    return list(getattr(mon_an, quan_he).values_list("ten", flat=True))


def tach_tu_khoa_mon_an(mon_an: MonAn) -> List[str]:
    """Tách từ khóa từ các trường đặc trưng của món ăn để xây dựng corpus TF-IDF."""
    ten_danh_muc = mon_an.danh_muc.ten if mon_an.danh_muc else ""

    # Bổ sung từ khóa ngữ cảnh đặc thù
    dac_trung_phu = []
    if mon_an.la_mon_chay:
        dac_trung_phu.append("món chay ăn chay thanh đạm")
    if mon_an.do_cay > 0:
        dac_trung_phu.append("món cay vị cay sa tế")
        if mon_an.do_cay >= 2:
            dac_trung_phu.append("rất cay nồng")

    van_ban_gop = (
        f"{mon_an.ten} {ten_danh_muc} {mon_an.mo_ta_ngan or ''} {mon_an.mo_ta_chi_tiet or ''} "
        f"{' '.join(_ds_ten(mon_an, 'nguyen_lieu'))} {' '.join(_ds_ten(mon_an, 'the_mon_an'))} "
        f"{' '.join(dac_trung_phu)}"
    ).lower()

    return re.findall(r"[\wÀ-ỹ]+", van_ban_gop)


def dac_trung_hien_thi(mon_an: MonAn) -> set:
    """
    Tập đặc trưng "đọc được" của món (nguyên liệu, thẻ, danh mục, vị cay, món chay)
    — dùng để giải thích lý do gợi ý bằng ngôn ngữ tự nhiên.
    """
    ds = {x.strip().lower() for x in _ds_ten(mon_an, "nguyen_lieu") + _ds_ten(mon_an, "the_mon_an")}
    if mon_an.danh_muc:
        ds.add(mon_an.danh_muc.ten.strip().lower())
    if mon_an.do_cay > 0:
        ds.add("vị cay")
    if mon_an.la_mon_chay:
        ds.add("món chay")
    return {x for x in ds if x}


class MoHinhTFIDF:
    """Ma trận TF-IDF (chuẩn hóa L2) trên toàn bộ món đang bán."""

    def __init__(self, danh_sach_mon: List[MonAn]):
        self.danh_sach_mon = danh_sach_mon
        self.chi_so = {m.id: i for i, m in enumerate(danh_sach_mon)}
        corpus = [tach_tu_khoa_mon_an(m) for m in danh_sach_mon]
        self.doc_freq = Counter(tu for doc in corpus for tu in set(doc))
        self.n = len(danh_sach_mon)
        self.vectors = [self._vector_hoa(doc) for doc in corpus]

    def _vector_hoa(self, tokens: Iterable[str]) -> Dict[str, float]:
        tf = Counter(tokens)
        vec = {}
        for tu, so_lan in tf.items():
            # Smoothed IDF: ln((N + 1) / (DF + 1)) + 1 ; Sublinear TF: 1 + ln(tf)
            idf = math.log((self.n + 1) / (self.doc_freq.get(tu, 0) + 1)) + 1.0
            vec[tu] = (1.0 + math.log(so_lan)) * idf
        return chuan_hoa_l2(vec)

    def vector_cua(self, mon_an: MonAn) -> Dict[str, float]:
        idx = self.chi_so.get(mon_an.id)
        if idx is not None:
            return self.vectors[idx]
        return self._vector_hoa(tach_tu_khoa_mon_an(mon_an))


def chuan_hoa_l2(vec: Dict[str, float]) -> Dict[str, float]:
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {k: v / norm for k, v in vec.items()}


def cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Cosine Similarity giữa 2 vector đã chuẩn hóa L2 = tích vô hướng."""
    if len(a) > len(b):
        a, b = b, a
    return min(1.0, max(0.0, sum(v * b.get(k, 0.0) for k, v in a.items())))


def _noi_dac_trung(chung: set, toi_da: int = 2) -> str:
    return ", ".join(sorted(chung)[:toi_da])


def tao_ly_do_goi_y(
    mon_an: MonAn,
    mon_lien_quan: Optional[MonAn] = None,
    loai_tuong_tac: str = "",
) -> str:
    """
    Explainable Recommendation: giải thích bằng món mà khách đã tương tác
    có độ tương đồng cao nhất với món được gợi ý, kèm các đặc trưng chung.
    """
    if mon_lien_quan is None:
        return "Phù hợp với khẩu vị và các món bạn thường chọn"
    if mon_lien_quan.id == mon_an.id:
        return f"Bạn {DONG_TU_TUONG_TAC.get(loai_tuong_tac, 'đã chọn')} món này, gọi lại nhé"
    dong_tu = DONG_TU_TUONG_TAC.get(loai_tuong_tac, "đã chọn")
    chung = dac_trung_hien_thi(mon_an) & dac_trung_hien_thi(mon_lien_quan)
    if chung:
        return f"Vì bạn {dong_tu} {mon_lien_quan.ten}: cùng {_noi_dac_trung(chung)}"
    return f"Tương tự {mon_lien_quan.ten} mà bạn {dong_tu}"


def _lay_mon_dang_ban() -> List[MonAn]:
    return list(
        MonAn.objects.filter(con_hang=True, hien_thi=True)
        .select_related("danh_muc")
        .prefetch_related("nguyen_lieu", "the_mon_an")
    )


class DichVuGoiY:
    @classmethod
    def tinh_goi_y_cold_start(cls, danh_sach_mon: List[MonAn], gioi_han: int = 6) -> List[tuple]:
        """
        Chiến lược Cold-Start Popularity Fallback cho người dùng chưa có tương tác hoặc khách vãng lai.
          score = 0.6 * (so_luot_danh_gia / max_reviews) + 0.4 * (diem_danh_gia / 5.0)
        """
        if not danh_sach_mon:
            return []

        max_reviews = max([m.so_luot_danh_gia for m in danh_sach_mon] or [1]) or 1

        danh_sach_diem = []
        for mon in danh_sach_mon:
            reviews = mon.so_luot_danh_gia or 0
            rating = float(mon.diem_danh_gia or 4.5)
            cold_score = 0.6 * (reviews / max_reviews) + 0.4 * (rating / 5.0)
            cold_score = min(1.0, max(0.0, cold_score))
            danh_sach_diem.append((mon, round(cold_score, 4), LY_DO_COLD_START, True))

        danh_sach_diem.sort(key=lambda x: x[1], reverse=True)
        return danh_sach_diem[:gioi_han]

    @classmethod
    def lay_goi_y_khach_vang_lai(cls, gioi_han: int = 6) -> List[GoiYMonAn]:
        """Trả về đối tượng gợi ý không lưu DB cho khách chưa đăng nhập."""
        ket_qua = cls.tinh_goi_y_cold_start(_lay_mon_dang_ban(), gioi_han=gioi_han)
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
    def tinh_goi_y_ca_nhan(
        cls, ds_tuong_tac: List[TuongTacMonAn], danh_sach_mon: List[MonAn], gioi_han: int
    ) -> List[tuple]:
        """
        TF-IDF + Cosine Similarity giữa vector khẩu vị (tổng có trọng số các món đã
        tương tác) và vector từng món. Món khách CHƯA tương tác được xếp trước để
        gợi ý khám phá món mới; món đã tương tác chỉ dùng để lấp đầy Top-N.
        """
        mo_hinh = MoHinhTFIDF(danh_sach_mon)

        # Gộp tương tác theo món: tổng trọng số + loại tương tác mạnh nhất (để giải thích)
        trong_so_theo_mon: Dict[int, float] = Counter()
        loai_manh_nhat: Dict[int, Tuple[float, str]] = {}
        mon_theo_id: Dict[int, MonAn] = {}
        for tt in ds_tuong_tac:
            if not tt.mon_an_id or tt.mon_an is None:
                continue
            # trong_so có thể âm (đánh giá 1–2★) hoặc 0 (3★): không được coi 0 là "chưa có"
            w = float(tt.trong_so) if tt.trong_so is not None else lay_trong_so_tuong_tac(tt.loai_tuong_tac)
            trong_so_theo_mon[tt.mon_an_id] += w
            mon_theo_id[tt.mon_an_id] = tt.mon_an
            if tt.mon_an_id not in loai_manh_nhat or w > loai_manh_nhat[tt.mon_an_id][0]:
                loai_manh_nhat[tt.mon_an_id] = (w, tt.loai_tuong_tac)

        # Chỉ món có tổng trọng số dương mới được dùng làm "lý do" giải thích
        mon_duong = {mid for mid, w in trong_so_theo_mon.items() if w > 0}
        if not mon_duong:
            return []

        vector_mon_da_tuong_tac = {mid: mo_hinh.vector_cua(m) for mid, m in mon_theo_id.items()}

        # Vector khẩu vị người dùng (User Preference Profile, kiểu Rocchio:
        # món thích cộng vào, món chê trừ ra)
        vector_khau_vi: Dict[str, float] = Counter()
        for mid, w in trong_so_theo_mon.items():
            for tu, val in vector_mon_da_tuong_tac[mid].items():
                vector_khau_vi[tu] += val * w
        vector_khau_vi = chuan_hoa_l2(vector_khau_vi)

        mon_moi, mon_cu = [], []
        for mon, vec in zip(danh_sach_mon, mo_hinh.vectors):
            score = round(cosine(vector_khau_vi, vec), 4)
            if mon.id in trong_so_theo_mon:
                if mon.id not in mon_duong:
                    continue  # khách đã chê món này → không gợi ý lại
                ly_do = tao_ly_do_goi_y(mon, mon, loai_manh_nhat[mon.id][1])
                mon_cu.append((mon, score, ly_do, False))
                continue
            # Giải thích: món đã tương tác đóng góp nhiều nhất (cosine × trọng số)
            mid_lien_quan = max(
                mon_duong,
                key=lambda mid: cosine(vector_mon_da_tuong_tac[mid], vec) * trong_so_theo_mon[mid],
            )
            ly_do = tao_ly_do_goi_y(mon, mon_theo_id[mid_lien_quan], loai_manh_nhat[mid_lien_quan][1])
            mon_moi.append((mon, score, ly_do, False))

        mon_moi.sort(key=lambda x: x[1], reverse=True)
        mon_cu.sort(key=lambda x: x[1], reverse=True)
        return (mon_moi + mon_cu)[:gioi_han]

    @classmethod
    def cap_nhat_goi_y(cls, nguoi_dung, gioi_han: int = 6) -> List[GoiYMonAn]:
        """
        Tính toán lại gợi ý cho người dùng:
        1. Người dùng mới (0 tương tác): Cold-Start Popularity Fallback.
        2. Người dùng có tương tác: TF-IDF + Cosine Similarity với vector khẩu vị có trọng số.
        3. Lưu kết quả vào bảng goi_y_mon_an làm cache.
        """
        danh_sach_mon = _lay_mon_dang_ban()
        if not danh_sach_mon:
            return []

        ds_tuong_tac = list(
            TuongTacMonAn.objects.filter(nguoi_dung=nguoi_dung)
            .select_related("mon_an", "mon_an__danh_muc")
            .prefetch_related("mon_an__nguyen_lieu", "mon_an__the_mon_an")
        )

        ket_qua = cls.tinh_goi_y_ca_nhan(ds_tuong_tac, danh_sach_mon, gioi_han) if ds_tuong_tac else []
        if not ket_qua:
            ket_qua = cls.tinh_goi_y_cold_start(danh_sach_mon, gioi_han=gioi_han)

        # Ghi đè vào bảng goi_y_mon_an để làm cache cho các truy vấn tiếp theo
        GoiYMonAn.objects.filter(nguoi_dung=nguoi_dung).delete()
        GoiYMonAn.objects.bulk_create([
            GoiYMonAn(
                nguoi_dung=nguoi_dung,
                mon_an=mon,
                diem_tuong_dong=Decimal(str(diem)),
                ly_do_goi_y=ly_do,
                phien_ban_model=MODEL_VERSION_COLD_START if is_cold else MODEL_VERSION_CONTENT_BASED,
                thu_hang=idx,
            )
            for idx, (mon, diem, ly_do, is_cold) in enumerate(ket_qua)
        ])

        return list(
            GoiYMonAn.objects.filter(nguoi_dung=nguoi_dung)
            .select_related("mon_an")
            .order_by("thu_hang", "-diem_tuong_dong")
        )

    @classmethod
    def mon_tuong_tu(cls, mon_an_id: int, gioi_han: int = 3) -> List[GoiYMonAn]:
        """
        Item-to-Item: các món có vector TF-IDF gần nhất với một món cho trước.
        Dùng ở trang chi tiết món; không cần lịch sử của khách nên chạy được cả cho khách mới.
        """
        danh_sach_mon = _lay_mon_dang_ban()
        goc = next((m for m in danh_sach_mon if m.id == mon_an_id), None)
        if goc is None:
            goc = (
                MonAn.objects.select_related("danh_muc")
                .prefetch_related("nguyen_lieu", "the_mon_an")
                .filter(id=mon_an_id).first()
            )
            if goc is None:
                return []

        mo_hinh = MoHinhTFIDF(danh_sach_mon)
        vec_goc = mo_hinh.vector_cua(goc)
        dac_trung_goc = dac_trung_hien_thi(goc)

        ket_qua = []
        for mon, vec in zip(danh_sach_mon, mo_hinh.vectors):
            if mon.id == goc.id:
                continue
            score = round(cosine(vec_goc, vec), 4)
            chung = dac_trung_hien_thi(mon) & dac_trung_goc
            ly_do = f"Cùng {_noi_dac_trung(chung)}" if chung else f"Hợp vị với {goc.ten}"
            ket_qua.append((mon, score, ly_do))
        ket_qua.sort(key=lambda x: x[1], reverse=True)

        return [
            GoiYMonAn(
                id=idx + 1,
                mon_an=mon,
                diem_tuong_dong=Decimal(str(score)),
                ly_do_goi_y=ly_do,
                phien_ban_model=MODEL_VERSION_ITEM_ITEM,
            )
            for idx, (mon, score, ly_do) in enumerate(ket_qua[:gioi_han])
        ]


def ghi_nhan_dat_mon(nguoi_dung, mon_an_ids: Iterable[int]) -> int:
    """
    Ghi tương tác 'dat_mon' (trọng số 4) cho mỗi món khác nhau mà khách đã đặt.
    Bỏ qua khách vãng lai. Trả về số tương tác đã tạo.
    """
    if not nguoi_dung or not getattr(nguoi_dung, "is_authenticated", False):
        return 0
    ids = {i for i in mon_an_ids if i}
    if not ids:
        return 0
    TuongTacMonAn.objects.bulk_create([
        TuongTacMonAn(
            nguoi_dung=nguoi_dung,
            mon_an_id=mid,
            loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DAT_MON,
            trong_so=TRONG_SO_TUONG_TAC["dat_mon"],
        )
        for mid in ids
    ])
    # bulk_create không bắn post_save → tự vô hiệu hóa cache gợi ý
    GoiYMonAn.objects.filter(nguoi_dung=nguoi_dung).delete()
    return len(ids)


def dong_bo_tuong_tac_danh_gia(nguoi_dung_id: int, mon_an_id: int) -> None:
    """
    Đồng bộ tương tác 'danh_gia' của khách với một món theo các đánh giá hiện có
    (gọi sau khi tạo / sửa / xoá đánh giá). Trọng số tính theo số sao, 3★ bỏ qua.
    """
    from reviews.models import DanhGia

    TuongTacMonAn.objects.filter(
        nguoi_dung_id=nguoi_dung_id, mon_an_id=mon_an_id,
        loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DANH_GIA,
    ).delete()
    so_sao = DanhGia.objects.filter(
        nguoi_dung_id=nguoi_dung_id, mon_an_id=mon_an_id
    ).values_list("diem_danh_gia", flat=True)
    TuongTacMonAn.objects.bulk_create([
        TuongTacMonAn(
            nguoi_dung_id=nguoi_dung_id,
            mon_an_id=mon_an_id,
            loai_tuong_tac=TuongTacMonAn.LoaiTuongTac.DANH_GIA,
            trong_so=Decimal(str(trong_so_danh_gia(sao))),
        )
        for sao in so_sao
        if trong_so_danh_gia(sao) != 0
    ])
    GoiYMonAn.objects.filter(nguoi_dung_id=nguoi_dung_id).delete()


# Backward-compatible adapter method and aliases
def _refresh_for(cls, user, limit=6):
    return cls.cap_nhat_goi_y(user, gioi_han=limit)


DichVuGoiY.refresh_for = classmethod(_refresh_for)
