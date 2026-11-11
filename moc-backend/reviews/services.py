"""Nghiệp vụ đánh giá: đánh giá từng món theo dòng đơn và đánh giá chung cho cả bữa ăn."""
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Prefetch
from rest_framework.exceptions import ValidationError

from foods.models import HinhAnhMonAn
from orders.models import ChiTietDonHang, DonHang
from recommendations.services import dong_bo_tuong_tac_danh_gia
from .models import DanhGia, DanhGiaBuaAn

# Chỉ xét các đơn hoàn tất gần nhất để danh sách "chờ đánh giá" không phình theo thời gian
SO_DON_GAN_NHAT = 20


def cap_nhat_diem_mon(mon_an):
    ket_qua = mon_an.danh_sach_danh_gia.filter(hien_thi=True).aggregate(
        rating=Avg("diem_danh_gia"), count=Count("id")
    )
    mon_an.diem_danh_gia = ket_qua["rating"] or 0
    mon_an.so_luot_danh_gia = ket_qua["count"] or 0
    mon_an.save(update_fields=["diem_danh_gia", "so_luot_danh_gia", "cap_nhat_luc"])


def _anh_chinh(mon_an):
    ds = list(mon_an.hinh_anh.all())
    anh = next((h for h in ds if h.la_anh_chinh), ds[0] if ds else None)
    return anh.anh.url if anh and anh.anh else ""


def _danh_gia_cua(obj, ten_quan_he):
    """Đọc quan hệ OneToOne ngược; trả None nếu chưa có (thay vì ném DoesNotExist)."""
    try:
        return getattr(obj, ten_quan_he)
    except ObjectDoesNotExist:
        return None


def don_cho_danh_gia(nguoi_dung):
    """Các đơn tại bàn đã hoàn tất mà khách còn món hoặc phần đánh giá chung chưa chấm."""
    don_ds = (
        DonHang.objects.filter(khach_hang=nguoi_dung, trang_thai=DonHang.TrangThai.HOAN_TAT)
        .select_related("chi_nhanh", "danh_gia_bua_an")
        .prefetch_related(
            Prefetch(
                "danh_sach_mon",
                queryset=ChiTietDonHang.objects.select_related("mon_an", "danh_gia").prefetch_related(
                    Prefetch("mon_an__hinh_anh", queryset=HinhAnhMonAn.objects.order_by("-la_anh_chinh", "id"))
                ).order_by("id"),
            )
        )
        .order_by("-tao_luc")[:SO_DON_GAN_NHAT]
    )

    ket_qua = []
    for don in don_ds:
        mon = []
        for dong in don.danh_sach_mon.all():
            dg = _danh_gia_cua(dong, "danh_gia")
            mon.append({
                "chi_tiet_don_hang": dong.id,
                "mon_an": dong.mon_an_id,
                "ten_mon": dong.mon_an.ten,
                "duong_dan_mon": dong.mon_an.duong_dan,
                "anh": _anh_chinh(dong.mon_an),
                "so_luong": dong.so_luong,
                "danh_gia": {"diem_danh_gia": dg.diem_danh_gia, "nhan_xet": dg.nhan_xet} if dg else None,
            })
        bua_an = _danh_gia_cua(don, "danh_gia_bua_an")
        con_thieu = bua_an is None or any(m["danh_gia"] is None for m in mon)
        if not mon or not con_thieu:
            continue
        ket_qua.append({
            "id": don.id,
            "ma_don_hang": don.ma_don_hang,
            "tao_luc": don.tao_luc,
            "chi_nhanh": don.chi_nhanh.ten if don.chi_nhanh else "",
            "mon": mon,
            "danh_gia_bua_an": {
                "diem_phuc_vu": bua_an.diem_phuc_vu,
                "diem_khong_gian": bua_an.diem_khong_gian,
                "nhan_xet": bua_an.nhan_xet,
            } if bua_an else None,
        })
    return ket_qua


@transaction.atomic
def gui_danh_gia_bua_an(nguoi_dung, du_lieu):
    """
    Gửi một lần cho cả bữa: điểm từng món (theo dòng đơn) và/hoặc điểm chung.
    Dòng món đã đánh giá trước đó thì báo lỗi, không ghi đè.
    """
    # Khoá dòng đơn để hai lần bấm "Gửi" liên tiếp không tạo trùng
    don = (
        DonHang.objects.select_for_update()
        .filter(id=du_lieu["don_hang"], khach_hang=nguoi_dung)
        .first()
    )
    if don is None:
        raise ValidationError({"don_hang": "Không tìm thấy đơn của bạn."})
    if don.trang_thai != DonHang.TrangThai.HOAN_TAT:
        raise ValidationError({"don_hang": "Chỉ đánh giá được bữa ăn đã hoàn tất."})

    dong_theo_id = {
        d.id: d for d in ChiTietDonHang.objects.filter(don_hang=don).select_related("mon_an", "danh_gia")
    }
    mon_ds = du_lieu.get("mon") or []
    da_gap = set()
    for m in mon_ds:
        dong = dong_theo_id.get(m["chi_tiet_don_hang"])
        if dong is None:
            raise ValidationError({"mon": "Có món không thuộc đơn này."})
        if dong.id in da_gap or _danh_gia_cua(dong, "danh_gia") is not None:
            raise ValidationError({"mon": f"Món {dong.mon_an.ten} đã được đánh giá."})
        da_gap.add(dong.id)

    co_diem_chung = du_lieu.get("diem_phuc_vu") is not None
    if co_diem_chung and DanhGiaBuaAn.objects.filter(don_hang=don).exists():
        raise ValidationError({"diem_phuc_vu": "Bữa ăn này đã được đánh giá chung."})

    try:
        for m in mon_ds:
            dong = dong_theo_id[m["chi_tiet_don_hang"]]
            DanhGia.objects.create(
                nguoi_dung=nguoi_dung, mon_an=dong.mon_an, don_hang=don, chi_tiet_don_hang=dong,
                diem_danh_gia=m["diem_danh_gia"], nhan_xet=m.get("nhan_xet", ""),
            )
        if co_diem_chung:
            DanhGiaBuaAn.objects.create(
                nguoi_dung=nguoi_dung, don_hang=don,
                diem_phuc_vu=du_lieu["diem_phuc_vu"], diem_khong_gian=du_lieu["diem_khong_gian"],
                nhan_xet=du_lieu.get("nhan_xet", ""),
            )
    except IntegrityError:
        raise ValidationError({"detail": "Đánh giá đã được gửi trước đó."})

    for mon_an in {dong_theo_id[m["chi_tiet_don_hang"]].mon_an for m in mon_ds}:
        cap_nhat_diem_mon(mon_an)
        dong_bo_tuong_tac_danh_gia(nguoi_dung.id, mon_an.id)

    return {"so_mon_da_danh_gia": len(mon_ds), "da_danh_gia_chung": co_diem_chung}


def co_the_danh_gia_mon(nguoi_dung, mon_an_id) -> bool:
    return ChiTietDonHang.objects.filter(
        don_hang__khach_hang=nguoi_dung,
        don_hang__trang_thai=DonHang.TrangThai.HOAN_TAT,
        mon_an_id=mon_an_id,
        danh_gia__isnull=True,
    ).exists()
