from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Any, Union
from django.db import transaction
from rest_framework.exceptions import ValidationError
from .models import NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho, MonAn


class DichVuKho:
    @staticmethod
    @transaction.atomic
    def khau_tru_nguyen_lieu_bom(
        *,
        danh_sach_mon,
        loai_tham_chieu: str,
        id_tham_chieu: int,
        nguoi_dung=None,
        ghi_chu: str = ""
    ) -> List[LichSuXuatNhapKho]:
        """
        Khấu trừ tồn kho nguyên liệu theo định mức (BOM) với Khóa bi quan select_for_update().
        Áp dụng thuật toán Strict Global ID Ordering để triệt tiêu hoàn toàn nguy cơ Deadlock.
        """
        # 1. Kiểm tra tính Idempotent: nếu giao dịch này đã xuất kho rồi thì bỏ qua
        giao_dich_cu = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu=loai_tham_chieu,
            id_tham_chieu=id_tham_chieu,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT
        )
        if giao_dich_cu.exists():
            return list(giao_dich_cu)

        # 2. Chuẩn hóa danh sách món ăn & số lượng
        dish_qty_map = defaultdict(int)

        if isinstance(danh_sach_mon, dict):
            for k, v in danh_sach_mon.items():
                dish_id = k.id if hasattr(k, "id") else int(k)
                dish_qty_map[dish_id] += int(v)
        else:
            for item in danh_sach_mon:
                if isinstance(item, dict):
                    mon_an = item.get("mon_an")
                    dish_id = item.get("mon_an_id") or (mon_an.id if hasattr(mon_an, "id") else mon_an)
                    so_luong = item.get("so_luong") or item.get("quantity", 1)
                else:
                    mon_an = getattr(item, "mon_an", None)
                    dish_id = getattr(item, "mon_an_id", None) or (mon_an.id if hasattr(mon_an, "id") else mon_an)
                    so_luong = getattr(item, "so_luong", 1)

                if dish_id and so_luong > 0:
                    dish_qty_map[dish_id] += int(so_luong)

        if not dish_qty_map:
            return []

        # 3. Tổng hợp nhu cầu nguyên liệu từ bảng DinhMucNguyenLieu
        tong_nhu_cau = defaultdict(Decimal)
        dinh_muc_qs = DinhMucNguyenLieu.objects.filter(
            mon_an_id__in=dish_qty_map.keys()
        ).select_related("nguyen_lieu")

        for dm in dinh_muc_qs:
            so_luong_mon = dish_qty_map[dm.mon_an_id]
            tong_nhu_cau[dm.nguyen_lieu_id] += dm.so_luong_can * Decimal(str(so_luong_mon))

        if not tong_nhu_cau:
            return []

        # 4. STRICT RESOURCE ORDERING: Sắp xếp ID nguyên liệu tăng dần để tránh Deadlock
        sorted_ids = sorted(tong_nhu_cau.keys())

        # 5. Khóa bi quan các dòng nguyên liệu trong PostgreSQL theo thứ tự ID
        nguyen_lieu_locked = list(
            NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")
        )

        # 6. Kiểm tra tồn kho trước khi trừ
        danh_sach_loi = []
        for nl in nguyen_lieu_locked:
            can_dung = tong_nhu_cau[nl.id]
            if nl.ton_kho_hien_tai < can_dung:
                danh_sach_loi.append(
                    f"Nguyên liệu '{nl.ten}' không đủ tồn kho (còn: {nl.ton_kho_hien_tai} {nl.don_vi}, cần: {can_dung} {nl.don_vi})."
                )

        if danh_sach_loi:
            raise ValidationError({"kho": danh_sach_loi})

        user_obj = nguoi_dung if (nguoi_dung and getattr(nguoi_dung, "is_authenticated", False)) else None

        # 7. Thực hiện trừ kho và ghi lịch sử giao dịch
        danh_sach_giao_dich = []
        for nl in nguyen_lieu_locked:
            so_luong_xuat = tong_nhu_cau[nl.id]
            ton_truoc = nl.ton_kho_hien_tai
            ton_sau = ton_truoc - so_luong_xuat

            nl.ton_kho_hien_tai = ton_sau
            nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

            giao_dich = LichSuXuatNhapKho.objects.create(
                nguyen_lieu=nl,
                loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT,
                so_luong=so_luong_xuat,
                ton_kho_truoc=ton_truoc,
                ton_kho_sau=ton_sau,
                loai_tham_chieu=loai_tham_chieu,
                id_tham_chieu=id_tham_chieu,
                ghi_chu=ghi_chu or f"Xuất kho nguyên liệu tự động cho {loai_tham_chieu} #{id_tham_chieu}",
                tao_boi=user_obj
            )
            danh_sach_giao_dich.append(giao_dich)

        return danh_sach_giao_dich

    @staticmethod
    @transaction.atomic
    def hoan_tra_nguyen_lieu_bom(
        *,
        loai_tham_chieu: str,
        id_tham_chieu: int,
        nguoi_dung=None,
        ghi_chu: str = ""
    ) -> List[LichSuXuatNhapKho]:
        """
        Hoàn trả tồn kho khi đơn hàng hoặc đặt bàn bị hủy sau khi đã trừ kho.
        """
        giao_dich_xuat = LichSuXuatNhapKho.objects.filter(
            loai_tham_chieu=loai_tham_chieu,
            id_tham_chieu=id_tham_chieu,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT
        ).select_related("nguyen_lieu")

        if not giao_dich_xuat.exists():
            return []

        sorted_ids = sorted([gd.nguyen_lieu_id for gd in giao_dich_xuat])
        nl_map = {
            nl.id: nl for nl in NguyenLieu.objects.select_for_update().filter(id__in=sorted_ids).order_by("id")
        }

        user_obj = nguoi_dung if (nguoi_dung and getattr(nguoi_dung, "is_authenticated", False)) else None
        danh_sach_hoan = []

        for gd in giao_dich_xuat:
            nl = nl_map[gd.nguyen_lieu_id]
            ton_truoc = nl.ton_kho_hien_tai
            ton_sau = ton_truoc + gd.so_luong

            nl.ton_kho_hien_tai = ton_sau
            nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])

            giao_dich_nhap = LichSuXuatNhapKho.objects.create(
                nguyen_lieu=nl,
                loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
                so_luong=gd.so_luong,
                ton_kho_truoc=ton_truoc,
                ton_kho_sau=ton_sau,
                loai_tham_chieu=loai_tham_chieu,
                id_tham_chieu=id_tham_chieu,
                ghi_chu=ghi_chu or f"Hoàn kho nguyên liệu do hủy {loai_tham_chieu} #{id_tham_chieu}",
                tao_boi=user_obj
            )
            danh_sach_hoan.append(giao_dich_nhap)

        return danh_sach_hoan


# Backward-compatible service aliases
InventoryService = DichVuKho
WarehouseService = DichVuKho
