from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Any, Union
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from .models import NguyenLieu, DinhMucNguyenLieu, LichSuXuatNhapKho, MonAn


class DichVuKho:
    LOAI_DON_HANG = "don_hang"

    @staticmethod
    def _gom_so_luong_mon(danh_sach_mon) -> Dict[int, int]:
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
                    so_luong = item.get("so_luong") or 1
                else:
                    mon_an = getattr(item, "mon_an", None)
                    dish_id = getattr(item, "mon_an_id", None) or (mon_an.id if hasattr(mon_an, "id") else mon_an)
                    so_luong = getattr(item, "so_luong", 1)

                if dish_id and so_luong > 0:
                    dish_qty_map[dish_id] += int(so_luong)
        return dish_qty_map

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
        dish_qty_map = DichVuKho._gom_so_luong_mon(danh_sach_mon)

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
    def _da_xuat_rong(loai_tham_chieu: str, id_tham_chieu: int) -> Dict[int, Decimal]:
        """Lượng nguyên liệu đã xuất ròng (xuất - hoàn) cho một chứng từ."""
        rong = defaultdict(Decimal)
        rows = (
            LichSuXuatNhapKho.objects.filter(loai_tham_chieu=loai_tham_chieu, id_tham_chieu=id_tham_chieu)
            .values("nguyen_lieu_id", "loai_giao_dich")
            .annotate(tong=Sum("so_luong"))
        )
        for row in rows:
            if row["loai_giao_dich"] == LichSuXuatNhapKho.LoaiGiaoDich.XUAT:
                rong[row["nguyen_lieu_id"]] += row["tong"]
            elif row["loai_giao_dich"] == LichSuXuatNhapKho.LoaiGiaoDich.NHAP:
                rong[row["nguyen_lieu_id"]] -= row["tong"]
        return rong

    @staticmethod
    def _ghi_bien_dong(nl, so_luong: Decimal, loai_tham_chieu, id_tham_chieu, user_obj, ghi_chu):
        """so_luong > 0: xuất kho; < 0: hoàn kho. nl phải đang bị khóa."""
        ton_truoc = nl.ton_kho_hien_tai
        ton_sau = ton_truoc - so_luong
        nl.ton_kho_hien_tai = ton_sau
        nl.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])
        return LichSuXuatNhapKho.objects.create(
            nguyen_lieu=nl,
            loai_giao_dich=LichSuXuatNhapKho.LoaiGiaoDich.XUAT if so_luong > 0 else LichSuXuatNhapKho.LoaiGiaoDich.NHAP,
            so_luong=abs(so_luong),
            ton_kho_truoc=ton_truoc,
            ton_kho_sau=ton_sau,
            loai_tham_chieu=loai_tham_chieu,
            id_tham_chieu=id_tham_chieu,
            ghi_chu=ghi_chu,
            tao_boi=user_obj,
        )

    @staticmethod
    @transaction.atomic
    def dong_bo_nguyen_lieu_don(*, don_hang, nguoi_dung=None, ghi_chu: str = "") -> List[LichSuXuatNhapKho]:
        """
        Đối soát kho theo các món hiện có trong đơn: chỉ xuất thêm phần món mới gửi bếp
        (hoặc hoàn lại phần món bị bớt). Gọi lại nhiều lần vẫn an toàn.
        """
        loai, ref_id = DichVuKho.LOAI_DON_HANG, don_hang.id
        dish_qty_map = DichVuKho._gom_so_luong_mon(don_hang.danh_sach_mon.all())

        can_dung = defaultdict(Decimal)
        for dm in DinhMucNguyenLieu.objects.filter(mon_an_id__in=dish_qty_map.keys()):
            can_dung[dm.nguyen_lieu_id] += dm.so_luong_can * Decimal(dish_qty_map[dm.mon_an_id])

        da_xuat = DichVuKho._da_xuat_rong(loai, ref_id)
        chenh_lech = {
            nl_id: can_dung.get(nl_id, Decimal("0")) - da_xuat.get(nl_id, Decimal("0"))
            for nl_id in set(can_dung) | set(da_xuat)
        }
        chenh_lech = {k: v for k, v in chenh_lech.items() if v != 0}
        if not chenh_lech:
            return []

        # Khóa theo thứ tự ID tăng dần để tránh deadlock
        locked = list(NguyenLieu.objects.select_for_update().filter(id__in=chenh_lech.keys()).order_by("id"))
        loi = [
            f"Nguyên liệu '{nl.ten}' không đủ tồn kho (còn: {nl.ton_kho_hien_tai} {nl.don_vi}, cần thêm: {chenh_lech[nl.id]} {nl.don_vi})."
            for nl in locked
            if chenh_lech[nl.id] > 0 and nl.ton_kho_hien_tai < chenh_lech[nl.id]
        ]
        if loi:
            raise ValidationError({"kho": loi})

        user_obj = nguoi_dung if (nguoi_dung and getattr(nguoi_dung, "is_authenticated", False)) else None
        ma = getattr(don_hang, "ma_don_hang", ref_id)
        return [
            DichVuKho._ghi_bien_dong(
                nl, chenh_lech[nl.id], loai, ref_id, user_obj,
                ghi_chu or (f"Xuất kho khi gửi bếp đơn {ma}" if chenh_lech[nl.id] > 0 else f"Hoàn kho do bớt món đơn {ma}"),
            )
            for nl in locked
        ]

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
        Hoàn trả toàn bộ lượng đã xuất ròng khi đơn hàng hoặc đặt bàn bị hủy.
        """
        da_xuat = {k: v for k, v in DichVuKho._da_xuat_rong(loai_tham_chieu, id_tham_chieu).items() if v > 0}
        if not da_xuat:
            return []
        user_obj = nguoi_dung if (nguoi_dung and getattr(nguoi_dung, "is_authenticated", False)) else None
        locked = NguyenLieu.objects.select_for_update().filter(id__in=da_xuat.keys()).order_by("id")
        return [
            DichVuKho._ghi_bien_dong(
                nl, -da_xuat[nl.id], loai_tham_chieu, id_tham_chieu, user_obj,
                ghi_chu or f"Hoàn kho nguyên liệu do hủy {loai_tham_chieu} #{id_tham_chieu}",
            )
            for nl in locked
        ]

    @staticmethod
    def canh_bao_sap_het(mon_an_ids) -> List[Dict[str, Any]]:
        """Nguyên liệu của các món đã gọi đang ở mức <= tồn tối thiểu (hoặc hết)."""
        mon_theo_nl = defaultdict(list)
        dinh_muc = (
            DinhMucNguyenLieu.objects.filter(mon_an_id__in=set(mon_an_ids), nguyen_lieu__con_hoat_dong=True)
            .select_related("nguyen_lieu", "mon_an")
            .order_by("nguyen_lieu_id", "mon_an__ten")
        )
        nl_map = {}
        for dm in dinh_muc:
            nl = dm.nguyen_lieu
            if nl.ton_kho_hien_tai <= 0 or (nl.ton_kho_toi_thieu > 0 and nl.ton_kho_hien_tai <= nl.ton_kho_toi_thieu):
                nl_map[nl.id] = nl
                mon_theo_nl[nl.id].append(dm.mon_an.ten)
        return [
            {
                "nguyen_lieu_id": nl.id,
                "ten": nl.ten,
                "don_vi": nl.don_vi,
                "ton_kho_hien_tai": float(nl.ton_kho_hien_tai),
                "ton_kho_toi_thieu": float(nl.ton_kho_toi_thieu),
                "mon_an": mon_theo_nl[nl.id],
            }
            for nl in nl_map.values()
        ]
