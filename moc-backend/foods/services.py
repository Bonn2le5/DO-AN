from decimal import Decimal
from collections import defaultdict
from typing import List, Dict, Any, Iterable, Optional
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from .models import DinhMucNguyenLieu, LichSuXuatNhapKho, TonKhoChiNhanh


def _nguoi(nguoi_dung):
    return nguoi_dung if (nguoi_dung and getattr(nguoi_dung, "is_authenticated", False)) else None


class DichVuKho:
    """
    Kho nguyên liệu tách theo chi nhánh: danh mục nguyên liệu và định mức món dùng chung,
    tồn kho (TonKhoChiNhanh) và lịch sử xuất nhập ghi riêng cho từng chi nhánh.
    """
    LOAI_DON_HANG = "don_hang"
    LOAI_CHUYEN_KHO = "chuyen_kho"

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

    # ---------- Tồn kho theo chi nhánh ----------
    @staticmethod
    def chi_nhanh_cua_don(don_hang) -> int:
        """Chi nhánh trừ kho của một đơn: chi nhánh của đơn, nếu thiếu thì lấy từ phiên phục vụ / đặt bàn."""
        cn = getattr(don_hang, "chi_nhanh_id", None)
        if not cn and getattr(don_hang, "phien_phuc_vu_id", None):
            cn = don_hang.phien_phuc_vu.chi_nhanh_id
        if not cn and getattr(don_hang, "dat_ban_id", None):
            cn = don_hang.dat_ban.chi_nhanh_id
        if not cn:
            raise ValidationError({"chi_nhanh": "Đơn hàng chưa gắn chi nhánh nên không biết trừ kho ở đâu."})
        return cn

    @staticmethod
    def dam_bao_ton_kho(nguyen_lieu_ids: Iterable[int], chi_nhanh_ids: Iterable[int], ton_kho_toi_thieu=None):
        """Tạo dòng tồn (bằng 0) còn thiếu cho các cặp nguyên liệu – chi nhánh."""
        nl_ids, cn_ids = set(nguyen_lieu_ids), set(chi_nhanh_ids)
        if not nl_ids or not cn_ids:
            return
        co_san = set(
            TonKhoChiNhanh.objects.filter(nguyen_lieu_id__in=nl_ids, chi_nhanh_id__in=cn_ids)
            .values_list("nguyen_lieu_id", "chi_nhanh_id")
        )
        moi = [
            TonKhoChiNhanh(
                nguyen_lieu_id=nl, chi_nhanh_id=cn,
                ton_kho_toi_thieu=ton_kho_toi_thieu if ton_kho_toi_thieu is not None else Decimal("0"),
            )
            for nl in nl_ids for cn in cn_ids if (nl, cn) not in co_san
        ]
        if moi:
            TonKhoChiNhanh.objects.bulk_create(moi, ignore_conflicts=True)

    @staticmethod
    def _khoa_ton(chi_nhanh_id: int, nguyen_lieu_ids: Iterable[int]) -> Dict[int, TonKhoChiNhanh]:
        """Khoá dòng tồn của chi nhánh theo thứ tự nguyên liệu tăng dần để tránh deadlock."""
        ids = sorted(set(nguyen_lieu_ids))
        DichVuKho.dam_bao_ton_kho(ids, [chi_nhanh_id])
        rows = (
            TonKhoChiNhanh.objects.select_for_update()
            .select_related("nguyen_lieu")
            .filter(chi_nhanh_id=chi_nhanh_id, nguyen_lieu_id__in=ids)
            .order_by("nguyen_lieu_id")
        )
        return {tk.nguyen_lieu_id: tk for tk in rows}

    @staticmethod
    def _ghi_bien_dong(tk: TonKhoChiNhanh, so_luong_xuat: Decimal, loai_tham_chieu, id_tham_chieu, user_obj, ghi_chu,
                       loai_giao_dich=None, ton_sau=None):
        """
        Đổi tồn của một dòng TonKhoChiNhanh đang bị khoá và ghi lịch sử.
        so_luong_xuat > 0: xuất; < 0: nhập. Kiểm kê truyền loai_giao_dich + ton_sau.
        """
        ton_truoc = tk.ton_kho_hien_tai
        if ton_sau is None:
            ton_sau = ton_truoc - so_luong_xuat
        if loai_giao_dich is None:
            loai_giao_dich = LichSuXuatNhapKho.LoaiGiaoDich.XUAT if so_luong_xuat > 0 else LichSuXuatNhapKho.LoaiGiaoDich.NHAP
        tk.ton_kho_hien_tai = ton_sau
        tk.save(update_fields=["ton_kho_hien_tai", "cap_nhat_luc"])
        return LichSuXuatNhapKho.objects.create(
            nguyen_lieu_id=tk.nguyen_lieu_id,
            chi_nhanh_id=tk.chi_nhanh_id,
            loai_giao_dich=loai_giao_dich,
            so_luong=abs(so_luong_xuat) if loai_giao_dich != LichSuXuatNhapKho.LoaiGiaoDich.DIEU_CHINH else ton_sau,
            ton_kho_truoc=ton_truoc,
            ton_kho_sau=ton_sau,
            loai_tham_chieu=loai_tham_chieu,
            id_tham_chieu=id_tham_chieu,
            ghi_chu=ghi_chu,
            tao_boi=user_obj,
        )

    @staticmethod
    def _da_xuat_rong(loai_tham_chieu: str, id_tham_chieu: int) -> Dict[tuple, Decimal]:
        """Lượng đã xuất ròng (xuất - hoàn) của một chứng từ, theo (nguyên liệu, chi nhánh)."""
        rong = defaultdict(Decimal)
        rows = (
            LichSuXuatNhapKho.objects.filter(loai_tham_chieu=loai_tham_chieu, id_tham_chieu=id_tham_chieu)
            .values("nguyen_lieu_id", "chi_nhanh_id", "loai_giao_dich")
            .annotate(tong=Sum("so_luong"))
        )
        for row in rows:
            key = (row["nguyen_lieu_id"], row["chi_nhanh_id"])
            if row["loai_giao_dich"] == LichSuXuatNhapKho.LoaiGiaoDich.XUAT:
                rong[key] += row["tong"]
            elif row["loai_giao_dich"] == LichSuXuatNhapKho.LoaiGiaoDich.NHAP:
                rong[key] -= row["tong"]
        return rong

    # ---------- Gửi bếp / huỷ đơn ----------
    @staticmethod
    @transaction.atomic
    def dong_bo_nguyen_lieu_don(*, don_hang, nguoi_dung=None, ghi_chu: str = "") -> List[LichSuXuatNhapKho]:
        """
        Đối soát kho của chi nhánh phục vụ đơn theo các món hiện có trong đơn: chỉ xuất thêm phần
        món mới gửi bếp (hoặc hoàn lại phần món bị bớt). Gọi lại nhiều lần vẫn an toàn.
        """
        loai, ref_id = DichVuKho.LOAI_DON_HANG, don_hang.id
        dish_qty_map = DichVuKho._gom_so_luong_mon(don_hang.danh_sach_mon.all())

        can_dung = defaultdict(Decimal)
        for dm in DinhMucNguyenLieu.objects.filter(mon_an_id__in=dish_qty_map.keys()):
            can_dung[dm.nguyen_lieu_id] += dm.so_luong_can * Decimal(dish_qty_map[dm.mon_an_id])

        da_xuat = DichVuKho._da_xuat_rong(loai, ref_id)
        if not can_dung and not da_xuat:
            return []
        cn = DichVuKho.chi_nhanh_cua_don(don_hang)
        da_xuat_cn = {nl: v for (nl, c), v in da_xuat.items() if c == cn}
        chenh_lech = {
            nl_id: can_dung.get(nl_id, Decimal("0")) - da_xuat_cn.get(nl_id, Decimal("0"))
            for nl_id in set(can_dung) | set(da_xuat_cn)
        }
        chenh_lech = {k: v for k, v in chenh_lech.items() if v != 0}
        if not chenh_lech:
            return []

        locked = DichVuKho._khoa_ton(cn, chenh_lech.keys())
        loi = [
            f"Nguyên liệu '{tk.nguyen_lieu.ten}' ở chi nhánh này không đủ tồn kho "
            f"(còn: {tk.ton_kho_hien_tai} {tk.nguyen_lieu.don_vi}, cần thêm: {chenh_lech[nl_id]} {tk.nguyen_lieu.don_vi})."
            for nl_id, tk in locked.items()
            if chenh_lech[nl_id] > 0 and tk.ton_kho_hien_tai < chenh_lech[nl_id]
        ]
        if loi:
            raise ValidationError({"kho": loi})

        user_obj = _nguoi(nguoi_dung)
        ma = getattr(don_hang, "ma_don_hang", ref_id)
        return [
            DichVuKho._ghi_bien_dong(
                tk, chenh_lech[nl_id], loai, ref_id, user_obj,
                ghi_chu or (f"Xuất kho khi gửi bếp đơn {ma}" if chenh_lech[nl_id] > 0 else f"Hoàn kho do bớt món đơn {ma}"),
            )
            for nl_id, tk in locked.items()
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
        """Hoàn trả toàn bộ lượng đã xuất ròng, về đúng kho chi nhánh đã bị trừ."""
        da_xuat = {k: v for k, v in DichVuKho._da_xuat_rong(loai_tham_chieu, id_tham_chieu).items() if v > 0 and k[1]}
        if not da_xuat:
            return []
        user_obj = _nguoi(nguoi_dung)
        ket_qua = []
        for cn in sorted({c for _, c in da_xuat}):
            locked = DichVuKho._khoa_ton(cn, [nl for nl, c in da_xuat if c == cn])
            for nl_id, tk in locked.items():
                ket_qua.append(DichVuKho._ghi_bien_dong(
                    tk, -da_xuat[(nl_id, cn)], loai_tham_chieu, id_tham_chieu, user_obj,
                    ghi_chu or f"Hoàn kho nguyên liệu do hủy {loai_tham_chieu} #{id_tham_chieu}",
                ))
        return ket_qua

    # ---------- Phiếu kho thủ công ----------
    @staticmethod
    @transaction.atomic
    def lap_phieu(*, nguyen_lieu_id: int, chi_nhanh_id: int, loai_giao_dich: str, so_luong,
                  ghi_chu: str = "", nguoi_dung=None) -> LichSuXuatNhapKho:
        """Nhập / xuất / kiểm kê. so_luong của kiểm kê là tồn thực tế sau khi kiểm."""
        so_luong = Decimal(str(so_luong))
        tk = DichVuKho._khoa_ton(chi_nhanh_id, [nguyen_lieu_id])[nguyen_lieu_id]
        L = LichSuXuatNhapKho.LoaiGiaoDich
        if loai_giao_dich == L.NHAP:
            xuat, ton_sau = -so_luong, None
        elif loai_giao_dich == L.XUAT:
            if tk.ton_kho_hien_tai < so_luong:
                raise ValidationError({"so_luong": (
                    f"Tồn kho hiện tại ({tk.ton_kho_hien_tai} {tk.nguyen_lieu.don_vi}) "
                    f"không đủ để xuất {so_luong} {tk.nguyen_lieu.don_vi}."
                )})
            xuat, ton_sau = so_luong, None
        elif loai_giao_dich == L.DIEU_CHINH:
            xuat, ton_sau = tk.ton_kho_hien_tai - so_luong, so_luong
        else:
            raise ValidationError({"loai_giao_dich": f"Loại giao dịch '{loai_giao_dich}' không hợp lệ."})
        return DichVuKho._ghi_bien_dong(
            tk, xuat, "thu_cong", None, _nguoi(nguoi_dung), ghi_chu,
            loai_giao_dich=loai_giao_dich, ton_sau=ton_sau,
        )

    @staticmethod
    @transaction.atomic
    def chuyen_kho(*, nguyen_lieu_id: int, tu_chi_nhanh_id: int, den_chi_nhanh_id: int, so_luong,
                   ghi_chu: str = "", nguoi_dung=None):
        """Chuyển nguyên liệu giữa hai chi nhánh: một phiếu xuất ở kho gửi và một phiếu nhập ở kho nhận."""
        so_luong = Decimal(str(so_luong))
        tu, den = int(tu_chi_nhanh_id), int(den_chi_nhanh_id)
        if so_luong <= 0:
            raise ValidationError({"so_luong": "Số lượng chuyển phải lớn hơn 0."})
        if tu == den:
            raise ValidationError({"den_chi_nhanh": "Chi nhánh nhận phải khác chi nhánh gửi."})
        from branches.models import ChiNhanh
        ten = dict(ChiNhanh.objects.filter(id__in=[tu, den]).values_list("id", "ten"))
        if len(ten) != 2:
            raise ValidationError({"chi_nhanh": "Không tìm thấy chi nhánh."})
        DichVuKho.dam_bao_ton_kho([nguyen_lieu_id], [tu, den])
        # Khoá hai dòng theo id tăng dần để hai lượt chuyển ngược chiều không deadlock.
        rows = {
            tk.chi_nhanh_id: tk for tk in TonKhoChiNhanh.objects.select_for_update().select_related("nguyen_lieu")
            .filter(nguyen_lieu_id=nguyen_lieu_id, chi_nhanh_id__in=[tu, den]).order_by("id")
        }
        gui, nhan = rows[tu], rows[den]
        if gui.ton_kho_hien_tai < so_luong:
            raise ValidationError({"so_luong": (
                f"Kho gửi chỉ còn {gui.ton_kho_hien_tai} {gui.nguyen_lieu.don_vi}, không đủ để chuyển {so_luong}."
            )})
        user_obj = _nguoi(nguoi_dung)
        note = (ghi_chu or "").strip()
        phieu_xuat = DichVuKho._ghi_bien_dong(
            gui, so_luong, DichVuKho.LOAI_CHUYEN_KHO, None, user_obj,
            f"Chuyển sang {ten[den]}" + (f" — {note}" if note else ""),
        )
        phieu_nhap = DichVuKho._ghi_bien_dong(
            nhan, -so_luong, DichVuKho.LOAI_CHUYEN_KHO, phieu_xuat.id, user_obj,
            f"Nhận từ {ten[tu]}" + (f" — {note}" if note else ""),
        )
        # Hai phiếu trỏ vào nhau để tra được cặp chuyển kho.
        phieu_xuat.id_tham_chieu = phieu_nhap.id
        phieu_xuat.save(update_fields=["id_tham_chieu", "cap_nhat_luc"])
        return phieu_xuat, phieu_nhap

    # ---------- Cảnh báo ----------
    @staticmethod
    def canh_bao_sap_het(mon_an_ids, chi_nhanh_id: Optional[int]) -> List[Dict[str, Any]]:
        """Nguyên liệu của các món đang ở mức <= tồn tối thiểu (hoặc hết) tại một chi nhánh."""
        if not chi_nhanh_id:
            return []
        dinh_muc = list(
            DinhMucNguyenLieu.objects.filter(mon_an_id__in=set(mon_an_ids), nguyen_lieu__con_hoat_dong=True)
            .select_related("nguyen_lieu", "mon_an")
            .order_by("nguyen_lieu_id", "mon_an__ten")
        )
        ton = {
            tk.nguyen_lieu_id: tk for tk in TonKhoChiNhanh.objects.filter(
                chi_nhanh_id=chi_nhanh_id, nguyen_lieu_id__in={dm.nguyen_lieu_id for dm in dinh_muc}
            )
        }
        mon_theo_nl, nl_map = defaultdict(list), {}
        for dm in dinh_muc:
            tk = ton.get(dm.nguyen_lieu_id)
            hien_tai = tk.ton_kho_hien_tai if tk else Decimal("0")
            toi_thieu = tk.ton_kho_toi_thieu if tk else Decimal("0")
            if hien_tai <= 0 or (toi_thieu > 0 and hien_tai <= toi_thieu):
                nl_map[dm.nguyen_lieu_id] = (dm.nguyen_lieu, hien_tai, toi_thieu)
                mon_theo_nl[dm.nguyen_lieu_id].append(dm.mon_an.ten)
        return [
            {
                "nguyen_lieu_id": nl.id,
                "chi_nhanh_id": int(chi_nhanh_id),
                "ten": nl.ten,
                "don_vi": nl.don_vi,
                "ton_kho_hien_tai": float(hien_tai),
                "ton_kho_toi_thieu": float(toi_thieu),
                "mon_an": mon_theo_nl[nl.id],
            }
            for nl, hien_tai, toi_thieu in nl_map.values()
        ]


def hom_nay_vn():
    from zoneinfo import ZoneInfo
    from django.utils import timezone
    return timezone.localdate(timezone=ZoneInfo("Asia/Ho_Chi_Minh"))


def mon_tam_het_ids(chi_nhanh_id, ngay=None):
    """ID các món đang tạm hết tại chi nhánh trong ngày (mặc định hôm nay)."""
    from .models import MonAnTamHet
    if not chi_nhanh_id:
        return set()
    return set(MonAnTamHet.objects.filter(chi_nhanh_id=chi_nhanh_id, ngay=ngay or hom_nay_vn()).values_list("mon_an_id", flat=True))
