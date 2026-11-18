"""
Tạo dữ liệu giả: khách demo + đơn hoàn tất + đánh giá + tương tác, để thấy rõ
gợi ý TF-IDF (theo khẩu vị) và cold-start (theo lượt đánh giá / điểm) hoạt động.

Mỗi khách demo có một "khẩu vị" (bò, hải sản, heo, rau-nấm, cay, lẩu, gỏi): khách gọi
chủ yếu món hợp vị và chấm cao, thỉnh thoảng gọi món lệch vị và chấm thấp.

    python manage.py seed_danh_gia_gia            # tạo lại (xoá dữ liệu demo cũ trước)
    python manage.py seed_danh_gia_gia --xoa      # chỉ xoá dữ liệu demo
    python manage.py seed_danh_gia_gia --so-khach-moi-vi 6

Mọi tài khoản demo có email *@demo.moc.vn, mật khẩu MocRestaurant@2026.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import VaiTro
from branches.models import ChiNhanh
from foods.models import MonAn
from orders.models import ChiTietDonHang, DonHang
from recommendations.models import GoiYMonAn, TuongTacMonAn
from recommendations.services import (
    DichVuGoiY, dong_bo_tuong_tac_danh_gia, ghi_nhan_dat_mon,
)
from reviews.models import DanhGia, DanhGiaBuaAn
from reviews.services import cap_nhat_diem_mon

NguoiDung = get_user_model()

DUOI_EMAIL = "@demo.moc.vn"
MAT_KHAU = "MocRestaurant@2026"


def _ten_co(*cum):
    """Nhận diện món hợp vị qua TÊN món (nguyên liệu phụ như "ba chỉ bò" trong set lẩu không tính)."""
    return lambda mon: any(c in mon.ten.lower() for c in cum)


def _danh_muc(ten):
    return lambda mon: bool(mon.danh_muc and mon.danh_muc.ten == ten)


# khóa → (tên hiển thị, hàm nhận diện món hợp vị)
KHAU_VI = {
    "bo": ("Mê thịt bò", _ten_co("bò")),
    "hai_san": ("Mê hải sản", _ten_co("tôm", "mực", "bạch tuộc", "cá ", "cá hồi", "sứa", "hải sản")),
    "heo": ("Mê thịt heo", _ten_co("heo", "phèo", "thủ linh", "nọng", "nạc dăm", "chẳng dừng", "tóp mỡ")),
    "rau_nam": ("Thích rau, nấm, món chay", lambda m: m.la_mon_chay or (
        not _danh_muc("Lẩu")(m) and _ten_co("rau", "nấm", "cà tím", "khổ qua", "bắp", "đậu")(m))),
    "cay": ("Ghiền cay", lambda m: m.do_cay > 0 or _ten_co("mala", "muối ớt", "sa tế", "tomyum")(m)),
    "lau": ("Mê lẩu", _danh_muc("Lẩu")),
    "goi": ("Thích gỏi, món nhẹ", _danh_muc("Gỏi")),
}

HO = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Đặng", "Bùi", "Đỗ", "Phan"]
TEN = ["An", "Bình", "Chi", "Dũng", "Giang", "Hà", "Khánh", "Linh", "Minh", "Nam",
       "Ngọc", "Phúc", "Quân", "Thảo", "Trang", "Tuấn", "Uyên", "Vy", "Yến", "Long"]

NHAN_XET = {
    5: ["Ngon xuất sắc, lần sau gọi tiếp!", "Đúng vị mình thích, rất đáng tiền.",
        "Món ruột luôn, cả bàn khen.", "Nêm nếm vừa miệng, phục vụ nhanh."],
    4: ["Ngon, phần ăn hơi ít.", "Khá ổn, sẽ quay lại.", "Vị ngon, trình bày đẹp."],
    3: ["Bình thường, không có gì đặc biệt.", "Ăn được, hơi nhạt so với mình."],
    2: ["Không hợp khẩu vị lắm.", "Hơi mặn, chưa thích lắm."],
    1: ["Không hợp với mình chút nào.", "Không gọi lại món này."],
}


class Command(BaseCommand):
    help = "Tạo khách demo + đơn + đánh giá + tương tác giả để minh hoạ gợi ý TF-IDF"

    def add_arguments(self, parser):
        parser.add_argument("--xoa", action="store_true", help="Chỉ xoá dữ liệu demo rồi thoát")
        parser.add_argument("--so-khach-moi-vi", type=int, default=4)
        parser.add_argument("--seed", type=int, default=2026, help="Hạt giống ngẫu nhiên (cố định = lặp lại được)")

    def handle(self, *args, **opt):
        with transaction.atomic():
            self._xoa_du_lieu_demo()
            if opt["xoa"]:
                self.stdout.write(self.style.SUCCESS("Đã xoá dữ liệu demo."))
                return
            self._tao(opt["so_khach_moi_vi"], random.Random(opt["seed"]))
        self._in_minh_hoa()

    # ------------------------------------------------------------------
    def _xoa_du_lieu_demo(self):
        users = NguoiDung.objects.filter(thu_dien_tu__endswith=DUOI_EMAIL)
        mon_ids = set(DanhGia.objects.filter(nguoi_dung__in=users).values_list("mon_an_id", flat=True))
        DonHang.objects.filter(khach_hang__in=users).delete()  # kéo theo chi tiết + đánh giá
        so, _ = users.delete()  # kéo theo tương tác + cache gợi ý
        for mon in MonAn.objects.filter(id__in=mon_ids):
            cap_nhat_diem_mon(mon)
        if so:
            self.stdout.write(f"Đã xoá dữ liệu demo cũ ({so} bản ghi liên quan).")

    def _tao(self, so_khach_moi_vi, rng):
        ds_mon = list(
            MonAn.objects.filter(con_hang=True, hien_thi=True)
            .select_related("danh_muc").prefetch_related("nguyen_lieu", "the_mon_an")
        )
        if not ds_mon:
            self.stderr.write("Chưa có món nào, hãy chạy seed_data trước.")
            return
        chi_nhanh = list(ChiNhanh.objects.all()) or [None]
        vai_tro_khach = VaiTro.objects.filter(ten="khach_hang").first()

        # Mỗi món có "chất lượng" ngầm khác nhau → điểm TB và lượt đánh giá chênh lệch rõ
        chat_luong = {m.id: rng.choice([-1, 0, 0, 0, 1, 1]) for m in ds_mon}
        hop_vi = {k: [m for m in ds_mon if f(m)] for k, (_, f) in KHAU_VI.items()}

        bay_gio = timezone.now()
        dem = {"khach": 0, "don": 0, "danh_gia": 0}
        stt = 0
        for khoa, (ten_vi, _) in KHAU_VI.items():
            mon_hop = hop_vi[khoa]
            if len(mon_hop) < 2:
                self.stdout.write(f"  Bỏ khẩu vị '{ten_vi}': chỉ có {len(mon_hop)} món hợp vị.")
                continue
            mon_lech = [m for m in ds_mon if m not in mon_hop]
            for i in range(so_khach_moi_vi):
                stt += 1
                ho, ten = rng.choice(HO), rng.choice(TEN)
                user = NguoiDung.objects.create_user(
                    username=f"demo_{khoa}_{i + 1}",
                    thu_dien_tu=f"{khoa}{i + 1}{DUOI_EMAIL}",
                    email=f"{khoa}{i + 1}{DUOI_EMAIL}",
                    password=MAT_KHAU,
                    first_name=ho, last_name=f"{ten} ({ten_vi})",
                    so_dien_thoai=f"0900{stt:06d}",
                )
                if vai_tro_khach:
                    user.danh_sach_vai_tro.add(vai_tro_khach)
                dem["khach"] += 1

                da_danh_gia = set()
                for _ in range(rng.randint(3, 5)):
                    so_hop = min(len(mon_hop), rng.randint(2, 3))
                    chon = rng.sample(mon_hop, so_hop)
                    # Thỉnh thoảng gọi thử món lệch vị (thường chấm thấp → kéo khẩu vị ra xa)
                    if mon_lech and rng.random() < 0.35:
                        chon.append(rng.choice(mon_lech))
                    dem["danh_gia"] += self._tao_don(
                        user, chon, rng, rng.choice(chi_nhanh), mon_hop, chat_luong,
                        bay_gio - timedelta(days=rng.randint(1, 90), hours=rng.randint(0, 12)),
                        da_danh_gia,
                    )
                    dem["don"] += 1

                ghi_nhan_dat_mon(user, list(da_danh_gia))
                for mid in da_danh_gia:
                    dong_bo_tuong_tac_danh_gia(user.id, mid)
                # Thêm vài lượt "xem" / "yêu thích" món hợp vị
                TuongTacMonAn.objects.bulk_create([
                    TuongTacMonAn(
                        nguoi_dung=user, mon_an=m,
                        loai_tuong_tac=rng.choice(["xem", "xem", "yeu_thich"]),
                    )
                    for m in rng.sample(mon_hop, min(2, len(mon_hop)))
                ])
                GoiYMonAn.objects.filter(nguoi_dung=user).delete()

        for mon in ds_mon:
            cap_nhat_diem_mon(mon)

        self.stdout.write(self.style.SUCCESS(
            f"Đã tạo {dem['khach']} khách demo, {dem['don']} đơn hoàn tất, {dem['danh_gia']} đánh giá món."
        ))

    def _tao_don(self, user, ds_mon, rng, chi_nhanh, mon_hop, chat_luong, luc, da_danh_gia):
        don = DonHang.objects.create(
            khach_hang=user, chi_nhanh=chi_nhanh, trang_thai=DonHang.TrangThai.HOAN_TAT,
            ten_khach=user.get_full_name(), sdt_khach=user.so_dien_thoai,
        )
        tong = Decimal(0)
        so_danh_gia = 0
        for mon in ds_mon:
            sl = rng.randint(1, 2)
            dong = ChiTietDonHang.objects.create(
                don_hang=don, mon_an=mon, so_luong=sl,
                don_gia_luc_dat=mon.don_gia, thanh_tien=mon.don_gia * sl,
            )
            tong += dong.thanh_tien
            # Món đã chấm rồi thì lần gọi lại không chấm nữa (giống khách thật)
            if mon.id in da_danh_gia:
                continue
            if mon in mon_hop:
                sao = rng.choice([4, 5, 5, 5])
            else:
                sao = rng.choice([1, 2, 2, 3])
            sao = max(1, min(5, sao + chat_luong[mon.id]))
            DanhGia.objects.create(
                nguoi_dung=user, mon_an=mon, don_hang=don, chi_tiet_don_hang=dong,
                diem_danh_gia=sao, nhan_xet=rng.choice(NHAN_XET[sao]),
            )
            da_danh_gia.add(mon.id)
            so_danh_gia += 1

        DanhGiaBuaAn.objects.create(
            nguoi_dung=user, don_hang=don,
            diem_phuc_vu=rng.choice([4, 5, 5]), diem_khong_gian=rng.choice([3, 4, 5]),
        )
        don.tien_hang = don.tong_tien = tong
        don.save(update_fields=["tien_hang", "tong_tien"])
        # tao_luc là auto_now_add → lùi ngày bằng update()
        DonHang.objects.filter(id=don.id).update(tao_luc=luc)
        ChiTietDonHang.objects.filter(don_hang=don).update(tao_luc=luc)
        DanhGia.objects.filter(don_hang=don).update(tao_luc=luc + timedelta(hours=2))
        return so_danh_gia

    # ------------------------------------------------------------------
    def _in_minh_hoa(self):
        self.stdout.write(self.style.NOTICE("\n=== Cold-start (khách mới): xếp theo lượt đánh giá + điểm ==="))
        for g in DichVuGoiY.lay_goi_y_khach_vang_lai(5):
            m = g.mon_an
            self.stdout.write(
                f"  {g.diem_tuong_dong:.3f}  {m.ten}  ({m.so_luot_danh_gia} lượt, {m.diem_danh_gia}★)"
            )

        for khoa, (ten_vi, _) in KHAU_VI.items():
            user = NguoiDung.objects.filter(thu_dien_tu=f"{khoa}1{DUOI_EMAIL}").first()
            if not user:
                continue
            self.stdout.write(self.style.NOTICE(f"\n=== {user.thu_dien_tu} — {ten_vi} (TF-IDF) ==="))
            for g in DichVuGoiY.cap_nhat_goi_y(user, 5):
                self.stdout.write(f"  {g.diem_tuong_dong:.3f}  {g.mon_an.ten}  — {g.ly_do_goi_y}")

        self.stdout.write(self.style.SUCCESS(f"\nĐăng nhập thử: <khẩu vị>1{DUOI_EMAIL} / {MAT_KHAU}"))
