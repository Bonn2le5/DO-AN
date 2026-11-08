"""
Tạo nguyên liệu thật và định mức (BOM) cho các món đang có trong thực đơn.

Định mức tính cho 1 phần món. Chỉ ghi nguyên liệu chính (đạm, rau củ, nước lẩu,
sốt đặc trưng); gia vị chung (muối, đường, dầu ăn...) không theo dõi.

Chạy lại an toàn: nguyên liệu đã có được giữ nguyên tồn kho, định mức được cập nhật.
    python manage.py seed_nguyen_lieu
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from foods.models import DinhMucNguyenLieu, LichSuXuatNhapKho, MonAn, NguyenLieu

# (tên, đơn vị, tồn đầu kỳ, tồn tối thiểu)
NGUYEN_LIEU = [
    # Bò
    ("Ba chỉ bò", "kg", 15, 4),
    ("Thăn bò tươi", "kg", 15, 4),
    ("Dẻ sườn bò", "kg", 6, 2),
    ("Lõi vai bò Mỹ", "kg", 8, 2),
    ("U hoa bò", "kg", 6, 2),
    # Heo
    ("Ba chỉ heo", "kg", 10, 3),
    ("Chẳng dừng heo", "kg", 5, 1.5),
    ("Nạc dăm heo", "kg", 6, 2),
    ("Nạc nọng heo", "kg", 5, 1.5),
    ("Lưỡi heo", "kg", 5, 1.5),
    ("Phèo heo", "kg", 5, 1.5),
    ("Thủ linh heo", "kg", 5, 1.5),
    ("Tai heo", "kg", 3, 1),
    ("Sụn heo", "kg", 3, 1),
    ("Tóp mỡ", "kg", 2, 0.5),
    ("Chà bông", "kg", 2, 0.5),
    # Gà
    ("Má đùi gà", "kg", 8, 2),
    # Hải sản
    ("Tôm sú", "kg", 10, 3),
    ("Mực lá", "kg", 8, 2),
    ("Bạch tuộc", "kg", 5, 1.5),
    ("Cá hồi", "kg", 5, 1.5),
    ("Cá tầm", "kg", 6, 2),
    ("Sứa", "kg", 3, 1),
    ("Riêu cua đồng", "kg", 8, 2),
    ("Cá viên", "kg", 3, 1),
    ("Tép khô", "kg", 1, 0.3),
    ("Trứng muối", "quả", 60, 15),
    ("Đậu hũ", "miếng", 40, 10),
    # Rau củ, nấm
    ("Rau nấm lẩu", "kg", 15, 4),
    ("Nấm kim châm", "kg", 3, 1),
    ("Nấm tổng hợp", "kg", 4, 1),
    ("Xoài xanh", "kg", 6, 2),
    ("Đu đủ xanh", "kg", 6, 2),
    ("Ngó sen", "kg", 3, 1),
    ("Cà tím", "kg", 5, 1.5),
    ("Cà pháo", "kg", 2, 0.5),
    ("Bơ Đà Lạt", "kg", 4, 1),
    ("Rau muống", "kg", 6, 2),
    ("Khổ qua", "kg", 4, 1),
    ("Bắp nếp", "trái", 30, 8),
    ("Khoai tây", "kg", 8, 2),
    ("Rau luộc tổng hợp", "kg", 5, 1.5),
    ("Rau củ nướng tổng hợp", "kg", 5, 1.5),
    ("Đậu bắp", "kg", 3, 1),
    # Tinh bột
    ("Bún tươi", "kg", 10, 3),
    ("Miến", "kg", 3, 1),
    ("Mì Milket", "gói", 60, 15),
    ("Cơm trắng", "kg", 10, 3),
    ("Cơm cháy", "kg", 2, 0.5),
    ("Phô mai", "kg", 2, 0.5),
    # Nước lẩu
    ("Nước lẩu MaLa", "lít", 30, 8),
    ("Nước lẩu Thái Tomyum", "lít", 30, 8),
    ("Nước lẩu nấm", "lít", 20, 5),
    ("Nước lẩu riêu cua", "lít", 20, 5),
    # Sốt đặc trưng
    ("Mỡ hành", "kg", 2, 0.5),
    ("Mắm nhĩ", "lít", 3, 1),
    ("Sốt muối ớt", "lít", 4, 1),
    ("Sa tế", "lít", 2, 0.5),
    ("Sốt BBQ", "lít", 4, 1),
    ("Sả băm", "kg", 2, 0.5),
    ("Kho quẹt", "kg", 2, 0.5),
    ("Mắm chẻo", "lít", 2, 0.5),
]

_SET_LAU_CO_BAN = [("Thăn bò tươi", 0.1), ("Rau nấm lẩu", 0.3), ("Mì Milket", 1)]

# tên món -> [(tên nguyên liệu, lượng cho 1 phần)]
DINH_MUC = {
    # Gỏi
    "Bò Cà Kéo Pháo": [("Thăn bò tươi", 0.12), ("Cà pháo", 0.08)],
    "Cá Hồi Om Bơ Đà Lạt": [("Cá hồi", 0.12), ("Bơ Đà Lạt", 0.15)],
    "Gỏi Ngó Sen Tôm Thịt": [("Ngó sen", 0.1), ("Tôm sú", 0.08), ("Ba chỉ heo", 0.05)],
    "Gỏi Sứa Đại Dương Chấm Chẻo": [("Sứa", 0.12), ("Mắm chẻo", 0.05)],
    "Gỏi Xoài Xanh Cá Hồi": [("Xoài xanh", 0.15), ("Cá hồi", 0.12)],
    "Gỏi Xoài Xanh Hải Sản Đặc Biệt": [("Xoài xanh", 0.15), ("Tôm sú", 0.08), ("Mực lá", 0.06)],
    "Gỏi Xoài Xanh Tai Heo": [("Xoài xanh", 0.15), ("Tai heo", 0.1)],
    "Gỏi Đu Đủ Cá Hồi": [("Đu đủ xanh", 0.15), ("Cá hồi", 0.12)],
    "Gỏi Đu Đủ Hải Sản Đặc Biệt": [("Đu đủ xanh", 0.15), ("Tôm sú", 0.08), ("Mực lá", 0.06)],
    # Lẩu
    "Set Lẩu 2 Ngăn (MaLa Tứ Xuyên/Nấm/Riêu/Thái Tomyum)": _SET_LAU_CO_BAN + [("Nước lẩu MaLa", 0.75), ("Nước lẩu Thái Tomyum", 0.75)],
    "Set Lẩu 2 Ngăn Có MaLa Trứng Muối": _SET_LAU_CO_BAN + [("Nước lẩu MaLa", 0.75), ("Nước lẩu Thái Tomyum", 0.75), ("Trứng muối", 2)],
    "Set Lẩu MaLa Trứng Muối": _SET_LAU_CO_BAN + [("Nước lẩu MaLa", 1.5), ("Trứng muối", 2)],
    "Set Lẩu MaLa Tứ Xuyên Húp Được Nước": _SET_LAU_CO_BAN + [("Nước lẩu MaLa", 1.5)],
    "Set Lẩu Nấm Thiên Nhiên": _SET_LAU_CO_BAN + [("Nước lẩu nấm", 1.5), ("Nấm tổng hợp", 0.1)],
    "Set Lẩu Riêu": _SET_LAU_CO_BAN + [("Nước lẩu riêu cua", 1.5), ("Riêu cua đồng", 0.15), ("Đậu hũ", 1)],
    "Set Lẩu Riêu Cua Bắc Bộ": [("Nước lẩu riêu cua", 1.5), ("Riêu cua đồng", 0.2), ("Rau nấm lẩu", 0.3), ("Bún tươi", 0.3), ("Đậu hũ", 1)],
    "Set Lẩu Riêu Cua Bắc Bộ (3-5 người)": [
        ("Nước lẩu riêu cua", 2.5), ("Riêu cua đồng", 0.5), ("Rau nấm lẩu", 0.3), ("Bún tươi", 0.6),
        ("Sụn heo", 0.15), ("Thăn bò tươi", 0.15), ("Đậu hũ", 1), ("Tôm sú", 0.15),
    ],
    "Set Lẩu Thái Tomyum": _SET_LAU_CO_BAN + [("Nước lẩu Thái Tomyum", 1.5)],
    "Set Lẩu Thái Tomyum (3-5 người)": [
        ("Nước lẩu Thái Tomyum", 2.5), ("Rau nấm lẩu", 0.3), ("Bún tươi", 0.6),
        ("Ba chỉ bò", 0.15), ("Cá viên", 0.15), ("Mực lá", 0.15), ("Tôm sú", 0.15),
    ],
    # Nhâm nhi
    "Bắp Nếp Xào Tép Khô Mỡ Hành": [("Bắp nếp", 2), ("Tép khô", 0.02), ("Mỡ hành", 0.03)],
    "Cà Tím Nướng Mắm Hành": [("Cà tím", 0.25), ("Mỡ hành", 0.03)],
    "Cơm Chiên Tomyum Hải Sản": [("Cơm trắng", 0.25), ("Tôm sú", 0.08), ("Mực lá", 0.05)],
    "Cơm Cháy Chà Bông Mỡ Hành": [("Cơm cháy", 0.1), ("Chà bông", 0.03), ("Mỡ hành", 0.03)],
    "Khoai Tây Chiên": [("Khoai tây", 0.25)],
    "Khổ Qua Chà Bông": [("Khổ qua", 0.25), ("Chà bông", 0.03)],
    "Miến Om Tôm": [("Miến", 0.1), ("Tôm sú", 0.15)],
    "Nấm Chiên Phô Mai": [("Nấm tổng hợp", 0.15), ("Phô mai", 0.05)],
    "Rau Luộc Kho Quẹt": [("Rau luộc tổng hợp", 0.4), ("Kho quẹt", 0.1)],
    "Rau Muống Xào Tóp Mỡ": [("Rau muống", 0.3), ("Tóp mỡ", 0.05)],
    "Súp Tomyum Hải Sản + Bún": [("Nước lẩu Thái Tomyum", 0.8), ("Tôm sú", 0.1), ("Mực lá", 0.08), ("Bún tươi", 0.3)],
    # Nướng
    "Ba Chỉ Bò Cuộn Kim Châm BBQ": [("Ba chỉ bò", 0.15), ("Nấm kim châm", 0.1), ("Sốt BBQ", 0.05)],
    "Ba Chỉ Bò Tảng Sốt Muối Ớt": [("Ba chỉ bò", 0.2), ("Sốt muối ớt", 0.05)],
    "Ba Chỉ Bò Tảng Sốt Sả": [("Ba chỉ bò", 0.2), ("Sả băm", 0.03)],
    "Ba Chỉ Heo": [("Ba chỉ heo", 0.2)],
    "Bò Tươi Tùng Xẻo Nhà Mộc": [("Thăn bò tươi", 0.15)],
    "Bạch Tuộc Sốt Muối Ớt": [("Bạch tuộc", 0.2), ("Sốt muối ớt", 0.05)],
    "Bạch Tuộc Sốt Sa Tế": [("Bạch tuộc", 0.2), ("Sa tế", 0.04)],
    "Chẳng Dừng Tươi": [("Chẳng dừng heo", 0.2)],
    "Cá Tầm Tươi": [("Cá tầm", 0.4)],
    "Dẻ Sườn Bò Obe": [("Dẻ sườn bò", 0.25)],
    "Lõi Vai Bò Mỹ": [("Lõi vai bò Mỹ", 0.2)],
    "Lõi Vai Bò Mỹ Sốt Trứng Muối": [("Lõi vai bò Mỹ", 0.2), ("Trứng muối", 1)],
    "Lưỡi Heo Sốt Mắm Nhĩ": [("Lưỡi heo", 0.2), ("Mắm nhĩ", 0.03)],
    "Lưỡi Heo Sốt Truyền Thống": [("Lưỡi heo", 0.2)],
    "Má Đùi Gà": [("Má đùi gà", 0.25)],
    "Mực (200g)": [("Mực lá", 0.2)],
    "Nạc Dăm Nướng": [("Nạc dăm heo", 0.2)],
    "Nạc Nọng Má Giòn Tươi": [("Nạc nọng heo", 0.2)],
    "Phèo Sốt Mắm Nhĩ": [("Phèo heo", 0.2), ("Mắm nhĩ", 0.03)],
    "Phèo Sốt Truyền Thống": [("Phèo heo", 0.2)],
    "Rau Củ": [("Rau củ nướng tổng hợp", 0.25)],
    "Thăn Bò Tươi Nhà Mộc": [("Thăn bò tươi", 0.15)],
    "Thủ Linh Sốt Mắm Nhĩ": [("Thủ linh heo", 0.2), ("Mắm nhĩ", 0.03)],
    "Thủ Linh Sốt Truyền Thống": [("Thủ linh heo", 0.2)],
    "Tôm Tươi": [("Tôm sú", 0.2)],
    "U Hoa Bò Sốt BBQ": [("U hoa bò", 0.2), ("Sốt BBQ", 0.05)],
    "U Hoa Bò Sốt Muối Ớt": [("U hoa bò", 0.2), ("Sốt muối ớt", 0.05)],
    "ba chỉ cuốn": [("Ba chỉ heo", 0.2)],
    "Đậu Bắp": [("Đậu bắp", 0.15)],
}


def _d(value):
    return Decimal(str(value))


class Command(BaseCommand):
    help = "Tạo nguyên liệu thật và định mức nguyên liệu cho các món trong thực đơn."

    @transaction.atomic
    def handle(self, *args, **options):
        nl_map, tao_moi = {}, 0
        for ten, don_vi, ton_dau, toi_thieu in NGUYEN_LIEU:
            nl, created = NguyenLieu.objects.get_or_create(
                ten=ten,
                defaults={"don_vi": don_vi, "ton_kho_hien_tai": _d(ton_dau), "ton_kho_toi_thieu": _d(toi_thieu)},
            )
            if created:
                tao_moi += 1
                LichSuXuatNhapKho.objects.create(
                    nguyen_lieu=nl, loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
                    so_luong=_d(ton_dau), ton_kho_truoc=0, ton_kho_sau=_d(ton_dau),
                    loai_tham_chieu="ton_dau_ky", ghi_chu="Tồn đầu kỳ khi khởi tạo nguyên liệu",
                )
            nl_map[ten] = nl

        mon_map = {m.ten: m for m in MonAn.objects.filter(ten__in=DINH_MUC.keys())}
        thieu_mon = sorted(set(DINH_MUC) - set(mon_map))
        so_dinh_muc = 0
        for ten_mon, items in DINH_MUC.items():
            mon = mon_map.get(ten_mon)
            if not mon:
                continue
            for ten_nl, qty in items:
                DinhMucNguyenLieu.objects.update_or_create(
                    mon_an=mon, nguyen_lieu=nl_map[ten_nl], defaults={"so_luong_can": _d(qty)},
                )
                so_dinh_muc += 1

        khong_dinh_muc = list(MonAn.objects.exclude(dinhmucnguyenlieu__isnull=False).values_list("ten", flat=True))
        self.stdout.write(self.style.SUCCESS(
            f"Nguyên liệu: {len(NGUYEN_LIEU)} ({tao_moi} tạo mới). Định mức: {so_dinh_muc} dòng cho {len(mon_map)} món."
        ))
        if thieu_mon:
            self.stdout.write(self.style.WARNING(f"Không tìm thấy món: {', '.join(thieu_mon)}"))
        if khong_dinh_muc:
            self.stdout.write(self.style.WARNING(f"Món chưa có định mức: {', '.join(khong_dinh_muc)}"))
