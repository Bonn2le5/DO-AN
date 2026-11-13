"""Tách tồn kho nguyên liệu theo chi nhánh (2/3): chép dữ liệu.

Trước khi tách, mọi chi nhánh dùng chung một kho, nên đơn của chi nhánh nào cũng trừ vào số tồn chung.
Để mỗi chi nhánh có số tồn khớp với lịch sử của chính nó:
- Lịch sử cũ gắn với đơn hàng -> chi nhánh của đơn; phiếu khác -> chi nhánh đầu tiên (kho gốc).
- Các chi nhánh còn lại nhận một phiếu "Tồn đầu kỳ" bằng tồn đầu kỳ gốc của nguyên liệu,
  đặt cùng thời điểm với phiếu gốc.
- Chạy lại lịch sử của từng chi nhánh theo thời gian để tính lại tồn trước/sau và tồn hiện tại.
Mức tồn tối thiểu được chép nguyên cho mọi chi nhánh.
"""
from collections import defaultdict
from decimal import Decimal

from django.db import migrations

GHI_CHU_TACH = "Tồn đầu kỳ khi tách kho theo chi nhánh"


def _chay_lai(rows):
    """Tính lại tồn trước/sau theo thứ tự thời gian; trả về tồn cuối."""
    ton = Decimal("0")
    for ls in sorted(rows, key=lambda r: (r.tao_luc, r.id)):
        truoc = ton
        if ls.loai_giao_dich == "nhap":
            ton = ton + ls.so_luong
        elif ls.loai_giao_dich == "xuat":
            ton = ton - ls.so_luong
        else:  # dieu_chinh: so_luong là tồn thực tế sau kiểm kê
            ton = ls.so_luong
        if (ls.ton_kho_truoc, ls.ton_kho_sau) != (truoc, ton):
            ls.ton_kho_truoc, ls.ton_kho_sau = truoc, ton
            ls.save(update_fields=["ton_kho_truoc", "ton_kho_sau"])
    return ton


def tach_kho(apps, schema_editor):
    NguyenLieu = apps.get_model("foods", "NguyenLieu")
    TonKho = apps.get_model("foods", "TonKhoChiNhanh")
    LichSu = apps.get_model("foods", "LichSuXuatNhapKho")
    ChiNhanh = apps.get_model("branches", "ChiNhanh")
    DonHang = apps.get_model("orders", "DonHang")

    chi_nhanh_ids = list(ChiNhanh.objects.order_by("id").values_list("id", flat=True))
    if not chi_nhanh_ids:
        return
    goc = chi_nhanh_ids[0]

    don_ids = set(LichSu.objects.filter(loai_tham_chieu="don_hang").values_list("id_tham_chieu", flat=True))
    don_cn = {}
    for d in DonHang.objects.filter(id__in=don_ids).select_related("phien_phuc_vu", "dat_ban"):
        don_cn[d.id] = (
            d.chi_nhanh_id
            or (d.phien_phuc_vu.chi_nhanh_id if d.phien_phuc_vu_id else None)
            or (d.dat_ban.chi_nhanh_id if d.dat_ban_id else None)
        )
    for ls in LichSu.objects.filter(chi_nhanh__isnull=True):
        cn = don_cn.get(ls.id_tham_chieu) if ls.loai_tham_chieu == "don_hang" else None
        ls.chi_nhanh_id = cn or goc
        ls.save(update_fields=["chi_nhanh"])

    for nl in NguyenLieu.objects.all():
        dau_ky = LichSu.objects.filter(nguyen_lieu=nl, loai_tham_chieu="ton_dau_ky").order_by("tao_luc", "id").first()
        for cn in chi_nhanh_ids[1:]:
            if dau_ky and dau_ky.so_luong > 0:
                moi = LichSu.objects.create(
                    nguyen_lieu=nl, chi_nhanh_id=cn, loai_giao_dich="nhap", so_luong=dau_ky.so_luong,
                    ton_kho_truoc=0, ton_kho_sau=dau_ky.so_luong, loai_tham_chieu="ton_dau_ky", ghi_chu=GHI_CHU_TACH,
                )
                # Đặt cùng thời điểm phiếu gốc để đứng trước các đơn cũ khi chạy lại lịch sử.
                LichSu.objects.filter(id=moi.id).update(tao_luc=dau_ky.tao_luc)

        theo_cn = defaultdict(list)
        for ls in LichSu.objects.filter(nguyen_lieu=nl):
            theo_cn[ls.chi_nhanh_id].append(ls)
        for cn in chi_nhanh_ids:
            if theo_cn.get(cn):
                ton = _chay_lai(theo_cn[cn])
            else:
                # Không có lịch sử nào (tồn được nhập tay ngoài phiếu): giữ số tồn chung.
                ton = nl.ton_kho_hien_tai
            TonKho.objects.create(
                nguyen_lieu=nl, chi_nhanh_id=cn, ton_kho_hien_tai=ton, ton_kho_toi_thieu=nl.ton_kho_toi_thieu,
            )


def gop_kho(apps, schema_editor):
    """Quay lại kho chung: bỏ phiếu tồn đầu kỳ do tách kho, chạy lại toàn bộ lịch sử thành một dòng tồn."""
    TonKho = apps.get_model("foods", "TonKhoChiNhanh")
    NguyenLieu = apps.get_model("foods", "NguyenLieu")
    LichSu = apps.get_model("foods", "LichSuXuatNhapKho")
    LichSu.objects.filter(loai_tham_chieu="ton_dau_ky", ghi_chu=GHI_CHU_TACH).delete()
    for nl in NguyenLieu.objects.all():
        rows = list(LichSu.objects.filter(nguyen_lieu=nl))
        tk = TonKho.objects.filter(nguyen_lieu=nl).order_by("chi_nhanh_id").first()
        nl.ton_kho_hien_tai = _chay_lai(rows) if rows else (tk.ton_kho_hien_tai if tk else 0)
        if tk:
            nl.ton_kho_toi_thieu = tk.ton_kho_toi_thieu
        nl.save(update_fields=["ton_kho_hien_tai", "ton_kho_toi_thieu"])
    LichSu.objects.update(chi_nhanh=None)
    TonKho.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("foods", "0002_ton_kho_chi_nhanh"),
        ("orders", "0005_gan_khach_don_tai_cho"),
        ("reservations", "0010_tat_chinh_sach_coc_chung_trung"),
    ]

    operations = [
        migrations.RunPython(tach_kho, gop_kho),
    ]
