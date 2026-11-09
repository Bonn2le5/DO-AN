from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from branches.models import ChiNhanh
from .models import DatBan, MonAnTrongDatBan, BanAn, ChinhSachDatCoc, PhienPhucVu


THOI_GIAN_PHUC_VU = timedelta(hours=2)
TRANG_THAI_DAT_BAN_DANG_GIU_CHO = [
    DatBan.TrangThai.CHO_XAC_NHAN,
    DatBan.TrangThai.CHO_THANH_TOAN,
    DatBan.TrangThai.DA_XAC_NHAN,
    DatBan.TrangThai.KHACH_DA_DEN,
]


def tinh_suc_chua_con_lai(chi_nhanh, ngay, gio):
    """Sức chứa ghế còn lại tại một thời điểm, tính theo lượt ăn kéo dài hai giờ."""
    tong_suc_chua = chi_nhanh.danh_sach_ban.filter(da_luu_tru=False).exclude(
        trang_thai=BanAn.TrangThai.BAO_TRI
    ).aggregate(tong=Sum("suc_chua"))["tong"] or 0
    bat_dau = datetime.combine(ngay, gio)
    ket_thuc = bat_dau + THOI_GIAN_PHUC_VU
    so_khach_da_dat = 0
    dat_ban_trong_ngay = DatBan.objects.filter(
        chi_nhanh=chi_nhanh,
        ngay_dat=ngay,
        trang_thai__in=TRANG_THAI_DAT_BAN_DANG_GIU_CHO,
    ).only("gio_bat_dau", "gio_ket_thuc", "so_luong_khach")
    for dat_ban in dat_ban_trong_ngay:
        bat_dau_khac = datetime.combine(ngay, dat_ban.gio_bat_dau)
        ket_thuc_khac = datetime.combine(ngay, dat_ban.gio_ket_thuc) if dat_ban.gio_ket_thuc else bat_dau_khac + THOI_GIAN_PHUC_VU
        if bat_dau_khac < ket_thuc and ket_thuc_khac > bat_dau:
            so_khach_da_dat += dat_ban.so_luong_khach
    return max(0, tong_suc_chua - so_khach_da_dat), so_khach_da_dat, tong_suc_chua

class DichVuDatBan:
    @classmethod
    @transaction.atomic
    def tao_dat_ban(cls, *, nguoi_dung, du_lieu):
        """
        Tạo đặt chỗ theo chi nhánh, ngày và giờ. Nhân viên xếp bàn khi khách đến.
        """
        danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])

        du_lieu.pop("expected_version", None)

        ban = du_lieu.get("ban_an")
        ngay = du_lieu["ngay_dat"]
        gio = du_lieu["gio_bat_dau"]
        so_khach = du_lieu["so_luong_khach"]
        if so_khach < 1 or so_khach > 12:
            raise ValidationError({"so_luong_khach": "Mỗi lượt đặt bàn tối đa 12 khách."})
        chi_nhanh = du_lieu.get("chi_nhanh") or (ban.chi_nhanh if ban else None)

        if not chi_nhanh:
            raise ValidationError({"chi_nhanh": "Cần cung cấp chi_nhanh hoặc ban_an."})

        du_lieu["chi_nhanh"] = chi_nhanh
        if ban:
            # Hỗ trợ dữ liệu nội bộ cũ có bàn được gán sẵn.
            ban_locked = BanAn.objects.select_for_update().get(id=ban.id)

            if ban_locked.trang_thai == BanAn.TrangThai.BAO_TRI:
                raise ValidationError({"ban_an": "Bàn đang trong trạng thái bảo trì."})
            if so_khach > ban_locked.suc_chua:
                raise ValidationError({"so_luong_khach": f"Bàn chỉ có sức chứa tối đa {ban_locked.suc_chua} khách."})
            if ban_locked.chi_nhanh_id != chi_nhanh.id:
                raise ValidationError({"ban_an": "Bàn không thuộc chi nhánh đã chọn."})

            tranh_chap = DatBan.objects.select_for_update().filter(
                ban_an=ban_locked,
                ngay_dat=ngay,
                gio_bat_dau=gio,
                trang_thai__in=[
                    DatBan.TrangThai.CHO_XAC_NHAN,
                    DatBan.TrangThai.CHO_THANH_TOAN,
                    DatBan.TrangThai.DA_XAC_NHAN,
                    DatBan.TrangThai.KHACH_DA_DEN
                ]
            )
            if tranh_chap.exists():
                raise ValidationError({"ban_an": "Bàn đã có người đặt trong khung giờ này."})

            du_lieu["ban_an"] = ban_locked

        else:
            # Khách chỉ đặt chỗ theo chi nhánh; nhân viên xếp bàn khi khách đến.
            chi_nhanh = ChiNhanh.objects.select_for_update().get(pk=chi_nhanh.pk)
            con_lai, da_dat, tong = tinh_suc_chua_con_lai(chi_nhanh, ngay, gio)
            if so_khach > con_lai:
                raise ValidationError({"gio_bat_dau": f"Khung giờ này chỉ còn {con_lai} chỗ (sức chứa {tong}, đã có {da_dat} khách đặt)."})
            du_lieu["chi_nhanh"] = chi_nhanh
            du_lieu["ban_an"] = None

        # 4. Tính toán tiền món ăn và tiền đặt cọc
        tien_mon_an = sum(
            (item["mon_an"].don_gia_hien_tai * item["so_luong"] for item in danh_sach_item),
            Decimal("0")
        )

        hinh_thuc = du_lieu.get("hinh_thuc")
        if not hinh_thuc:
            hinh_thuc = DatBan.HinhThuc.DAT_BAN_VA_GOI_MON if danh_sach_item else DatBan.HinhThuc.CHI_GIU_CHO
            du_lieu["hinh_thuc"] = hinh_thuc

        can_coc = hinh_thuc != DatBan.HinhThuc.CHI_GIU_CHO
        if can_coc and not danh_sach_item:
            raise ValidationError({"danh_sach_mon": "Đặt bàn kèm gọi món cần chọn ít nhất một món."})

        chinh_sach = ChinhSachDatCoc.objects.filter(
            con_ap_dung=True, chi_nhanh__in=[chi_nhanh, None]
        ).order_by("-chi_nhanh_id").first()

        so_tien_coc = Decimal("0")
        if can_coc:
            phan_tram_coc = chinh_sach.phan_tram_coc if chinh_sach else Decimal("20")
            so_tien_coc = (tien_mon_an * phan_tram_coc / Decimal("100")).quantize(Decimal("1"))

        user_obj = nguoi_dung if (nguoi_dung and nguoi_dung.is_authenticated) else None

        # 5. Tạo bản ghi DatBan
        dat_ban = DatBan.objects.create(
            nguoi_dung=user_obj,
            yeu_cau_dat_coc=can_coc,
            so_tien_coc=so_tien_coc,
            trang_thai_coc=DatBan.TrangThaiCoc.CHUA_THANH_TOAN,
            trang_thai=DatBan.TrangThai.CHO_XAC_NHAN,
            **du_lieu
        )

        # 6. Tạo các món ăn đính kèm
        for item in danh_sach_item:
            MonAnTrongDatBan.objects.create(
                dat_ban=dat_ban,
                mon_an=item["mon_an"],
                so_luong=item["so_luong"],
                don_gia_luc_dat=item["mon_an"].don_gia_hien_tai
            )

        # 7. Ghi tương tác "đặt món" cho mô hình gợi ý AI (món gọi trước)
        from recommendations.services import ghi_nhan_dat_mon
        ghi_nhan_dat_mon(user_obj, [item["mon_an"].id for item in danh_sach_item])

        return dat_ban

    @staticmethod
    @transaction.atomic
    def doi_trang_thai(dat_ban, trang_thai_moi, nguoi_dung):
        if trang_thai_moi not in DatBan.TrangThai.values:
            raise ValidationError({"status": "Trạng thái đặt bàn không hợp lệ."})

        # 1. Khóa bi quan dòng DatBan để ngăn chặn xung đột trạng thái
        db_locked = DatBan.objects.select_for_update().get(id=dat_ban.id)
        trang_thai_cu = db_locked.trang_thai
        db_locked.trang_thai = trang_thai_moi
        db_locked.phien_ban += 1
        db_locked.save(update_fields=["trang_thai", "phien_ban", "cap_nhat_luc"])

        dat_ban.trang_thai = db_locked.trang_thai
        dat_ban.phien_ban = db_locked.phien_ban
        dat_ban.cap_nhat_luc = db_locked.cap_nhat_luc
        return dat_ban


class DichVuPhienPhucVu:
    """Nghiệp vụ dùng chung cho khách walk-in và khách đặt bàn trước."""

    @staticmethod
    def _kiem_tra_ban(ban, so_khach, chi_nhanh_id=None):
        if ban.da_luu_tru:
            raise ValidationError({"ban_an": "Bàn đã được lưu trữ."})
        if chi_nhanh_id and ban.chi_nhanh_id != chi_nhanh_id:
            raise ValidationError({"ban_an": "Bàn không thuộc chi nhánh của đặt chỗ."})
        if ban.trang_thai != BanAn.TrangThai.TRONG:
            raise ValidationError({"ban_an": "Bàn hiện không còn trống để bắt đầu phục vụ."})
        if ban.suc_chua < so_khach:
            raise ValidationError({"ban_an": f"Bàn chỉ phục vụ tối đa {ban.suc_chua} khách."})
        if PhienPhucVu.objects.filter(
            ban_an=ban,
            trang_thai__in=[PhienPhucVu.TrangThai.DANG_PHUC_VU, PhienPhucVu.TrangThai.CHO_DON],
        ).exists():
            raise ValidationError({"ban_an": "Bàn đang có một phiên phục vụ khác."})

    @classmethod
    def _tao_phien(cls, *, nguoi_dung, ban, so_khach, dat_ban=None, ten_khach="", sdt_khach="", ghi_chu=""):
        phien = PhienPhucVu.objects.create(
            chi_nhanh=ban.chi_nhanh,
            ban_an=ban,
            dat_ban=dat_ban,
            so_luong_khach=so_khach,
            ten_khach=ten_khach or (dat_ban.ten_khach if dat_ban else ""),
            sdt_khach=sdt_khach or (dat_ban.sdt_khach if dat_ban else ""),
            ghi_chu=ghi_chu or (dat_ban.ghi_chu if dat_ban else ""),
            nguoi_bat_dau=nguoi_dung,
        )
        # Không tạo hoá đơn lúc mở bàn: hoá đơn chỉ sinh ra khi có món (tránh đơn 0 đ).
        ban.trang_thai = BanAn.TrangThai.DANG_PHUC_VU
        ban.save(update_fields=["trang_thai", "cap_nhat_luc"])
        return phien

    @staticmethod
    def la_quan_ly(nguoi_dung):
        return bool(nguoi_dung and (
            nguoi_dung.is_superuser
            or getattr(nguoi_dung, "la_quan_tri_vien", False)
            or getattr(nguoi_dung, "la_quan_ly_chi_nhanh", False)
        ))

    @staticmethod
    def _don_cua_phien(phien, nguoi_dung=None, tao_moi=False):
        """Hoá đơn của phiên (khoá dòng). Chỉ tạo mới khi được yêu cầu, tức là khi có món."""
        from orders.models import DonHang
        don = DonHang.objects.select_for_update().filter(phien_phuc_vu=phien).first()
        if don is None and tao_moi:
            from orders.services import DichVuDonHang
            don = DichVuDonHang.tao_don_tai_cho(
                nguoi_dung=nguoi_dung, phien_phuc_vu=phien,
                ten_khach=phien.ten_khach, sdt_khach=phien.sdt_khach, ghi_chu=phien.ghi_chu,
            )
        return don

    @staticmethod
    def _xoa_don_chua_gui_bep(don_hang):
        """Đơn chưa gửi bếp không có giá trị lưu trữ: trả lại tồn món rồi xoá."""
        for line in don_hang.danh_sach_mon.select_related("mon_an"):
            food = line.mon_an
            if food.ton_kho_cache is not None and not food.quan_ly_kho:
                food.ton_kho_cache += line.so_luong
                food.save(update_fields=["ton_kho_cache", "cap_nhat_luc"])
        don_hang.delete()

    @classmethod
    @transaction.atomic
    def tao_walk_in(cls, *, nguoi_dung, ban_an_id, so_luong_khach, ten_khach="", sdt_khach="", ghi_chu=""):
        ban = BanAn.objects.select_for_update(of=("self",)).select_related("chi_nhanh").get(pk=ban_an_id)
        cls._kiem_tra_ban(ban, so_luong_khach)
        return cls._tao_phien(
            nguoi_dung=nguoi_dung,
            ban=ban,
            so_khach=so_luong_khach,
            ten_khach=ten_khach,
            sdt_khach=sdt_khach,
            ghi_chu=ghi_chu,
        )

    @classmethod
    @transaction.atomic
    def check_in_dat_ban(cls, *, dat_ban, nguoi_dung):
        dat_ban = DatBan.objects.select_for_update().get(pk=dat_ban.pk)
        if dat_ban.trang_thai == DatBan.TrangThai.KHACH_DA_DEN:
            return dat_ban
        if dat_ban.trang_thai != DatBan.TrangThai.DA_XAC_NHAN:
            raise ValidationError({"status": "Chỉ đặt bàn đã xác nhận mới có thể check-in."})
        dat_ban.trang_thai = DatBan.TrangThai.KHACH_DA_DEN
        dat_ban.check_in_luc = timezone.now()
        dat_ban.phien_ban += 1
        dat_ban.save(update_fields=["trang_thai", "check_in_luc", "phien_ban", "cap_nhat_luc"])
        return dat_ban

    @classmethod
    @transaction.atomic
    def xep_ban_va_bat_dau(cls, *, nguoi_dung, dat_ban_id, ban_an_id):
        dat_ban = DatBan.objects.select_for_update(of=("self",)).select_related("chi_nhanh").get(pk=dat_ban_id)
        if dat_ban.trang_thai != DatBan.TrangThai.KHACH_DA_DEN:
            raise ValidationError({"status": "Khách cần check-in trước khi bắt đầu phục vụ."})
        if PhienPhucVu.objects.select_for_update().filter(dat_ban=dat_ban).exclude(trang_thai=PhienPhucVu.TrangThai.DA_DONG).exists():
            raise ValidationError({"reservation": "Đặt bàn này đã có phiên phục vụ."})
        ban = BanAn.objects.select_for_update(of=("self",)).select_related("chi_nhanh").get(pk=ban_an_id)
        cls._kiem_tra_ban(ban, dat_ban.so_luong_khach, dat_ban.chi_nhanh_id)

        dat_ban.ban_an = ban
        dat_ban.phien_ban += 1
        dat_ban.save(update_fields=["ban_an", "phien_ban", "cap_nhat_luc"])
        phien = cls._tao_phien(
            nguoi_dung=nguoi_dung,
            ban=ban,
            so_khach=dat_ban.so_luong_khach,
            dat_ban=dat_ban,
        )

        # Món khách chọn trước trở thành các dòng của hóa đơn chung khi phiên bắt đầu.
        dat_truoc = list(dat_ban.danh_sach_mon.select_related("mon_an").all())
        if dat_truoc:
            from orders.services import DichVuDonHang
            DichVuDonHang.them_mon_tai_cho(
                don_hang=cls._don_cua_phien(phien, nguoi_dung, tao_moi=True),
                danh_sach_item=[{
                    "mon_an": item.mon_an,
                    "so_luong": item.so_luong,
                    "ghi_chu": "Món khách chọn trước",
                } for item in dat_truoc],
                nguoi_dung=nguoi_dung,
            )
        return phien

    @classmethod
    @transaction.atomic
    def them_mon(cls, *, nguoi_dung, phien_id, danh_sach_item):
        phien = PhienPhucVu.objects.select_for_update().get(pk=phien_id)
        if phien.trang_thai != PhienPhucVu.TrangThai.DANG_PHUC_VU:
            raise ValidationError({"session": "Chỉ có thể thêm món khi phiên đang phục vụ."})
        if not danh_sach_item:
            return phien
        from orders.services import DichVuDonHang
        don_hang = cls._don_cua_phien(phien, nguoi_dung, tao_moi=True)
        DichVuDonHang.them_mon_tai_cho(don_hang=don_hang, danh_sach_item=danh_sach_item, nguoi_dung=nguoi_dung)
        cls._dong_bo_kho_neu_da_gui_bep(don_hang, nguoi_dung)
        return phien

    @staticmethod
    def _dong_bo_kho_neu_da_gui_bep(don_hang, nguoi_dung):
        """Đơn đã gửi bếp: món gọi thêm/bớt được trừ/hoàn kho nguyên liệu ngay."""
        from orders.models import DonHang
        from foods.services import DichVuKho
        don_hang.refresh_from_db(fields=["trang_thai"])
        if don_hang.trang_thai in {
            DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.SAN_SANG,
        }:
            DichVuKho.dong_bo_nguyen_lieu_don(don_hang=don_hang, nguoi_dung=nguoi_dung)

    @classmethod
    @transaction.atomic
    def cap_nhat_mon(cls, *, nguoi_dung, phien_id, danh_sach_item):
        """Thay nội dung giỏ món của phiên, giữ nguyên ghi chú và số lượng đã sửa."""
        from orders.services import DichVuDonHang

        from orders.models import DonHang

        phien = PhienPhucVu.objects.select_for_update().get(pk=phien_id)
        if phien.trang_thai != PhienPhucVu.TrangThai.DANG_PHUC_VU:
            raise ValidationError({"session": "Chỉ có thể sửa món khi phiên đang phục vụ."})
        don_hang = cls._don_cua_phien(phien)
        if don_hang is None:
            if not danh_sach_item:
                return phien
            don_hang = cls._don_cua_phien(phien, nguoi_dung, tao_moi=True)
        if don_hang.trang_thai in DichVuDonHang.TERMINAL_STATES:
            raise ValidationError({"session": "Hoá đơn đã kết thúc, không sửa món được nữa."})

        da_gui_bep = don_hang.trang_thai != DonHang.TrangThai.CHO_TIEP_NHAN
        if da_gui_bep and not cls.la_quan_ly(nguoi_dung):
            # Nhân viên chỉ được gọi thêm; bớt món bếp đã nhận cần quản lý chi nhánh.
            cu, moi = {}, {}
            for line in don_hang.danh_sach_mon.all():
                cu[line.mon_an_id] = cu.get(line.mon_an_id, 0) + line.so_luong
            for item in danh_sach_item:
                moi[item["mon_an"].id] = moi.get(item["mon_an"].id, 0) + item["so_luong"]
            if any(moi.get(mon_id, 0) < so_luong for mon_id, so_luong in cu.items()):
                raise PermissionDenied("Món đã gửi bếp chỉ quản lý chi nhánh mới bớt được.")
        if not danh_sach_item and not da_gui_bep:
            cls._xoa_don_chua_gui_bep(don_hang)
            return phien

        # Restore the stock reserved by the current cart before applying its replacement.
        for line in don_hang.danh_sach_mon.select_related("mon_an"):
            food = line.mon_an
            if food.ton_kho_cache is not None and not food.quan_ly_kho:
                food.ton_kho_cache += line.so_luong
                food.save(update_fields=["ton_kho_cache", "cap_nhat_luc"])
        don_hang.danh_sach_mon.all().delete()

        if danh_sach_item:
            DichVuDonHang.them_mon_tai_cho(
                don_hang=don_hang,
                danh_sach_item=danh_sach_item,
                nguoi_dung=nguoi_dung,
            )
        else:
            don_hang.tien_hang = 0
            don_hang.tong_tien = 0
            don_hang.save(update_fields=["tien_hang", "tong_tien", "cap_nhat_luc"])
        cls._dong_bo_kho_neu_da_gui_bep(don_hang, nguoi_dung)
        return phien

    @classmethod
    @transaction.atomic
    def chuyen_ban(cls, *, nguoi_dung, phien_id, ban_an_moi_id):
        phien = PhienPhucVu.objects.select_for_update(of=("self",)).select_related("ban_an", "dat_ban").get(pk=phien_id)
        if phien.trang_thai != PhienPhucVu.TrangThai.DANG_PHUC_VU:
            raise ValidationError({"session": "Chỉ chuyển bàn khi phiên đang phục vụ."})
        if phien.ban_an_id == ban_an_moi_id:
            raise ValidationError({"ban_an": "Khách đang ở bàn này."})
        tables = list(BanAn.objects.select_for_update(of=("self",)).select_related("chi_nhanh").filter(
            id__in=[phien.ban_an_id, ban_an_moi_id]
        ).order_by("id"))
        if len(tables) != 2:
            raise ValidationError({"ban_an": "Không tìm thấy bàn cần chuyển."})
        ban_cu = next(table for table in tables if table.id == phien.ban_an_id)
        ban_moi = next(table for table in tables if table.id == ban_an_moi_id)
        cls._kiem_tra_ban(ban_moi, phien.so_luong_khach, phien.chi_nhanh_id)

        phien.ban_an = ban_moi
        phien.save(update_fields=["ban_an", "cap_nhat_luc"])
        ban_cu.trang_thai = BanAn.TrangThai.TRONG
        ban_cu.save(update_fields=["trang_thai", "cap_nhat_luc"])
        ban_moi.trang_thai = BanAn.TrangThai.DANG_PHUC_VU
        ban_moi.save(update_fields=["trang_thai", "cap_nhat_luc"])
        if phien.dat_ban_id:
            DatBan.objects.filter(pk=phien.dat_ban_id).update(ban_an=ban_moi, cap_nhat_luc=timezone.now())
        return phien

    @staticmethod
    def tien_coc_da_tra(phien, don_hang=None):
        """Tiền cọc đã thu thành công của đặt bàn gắn với phiên, không vượt tổng hoá đơn."""
        from decimal import Decimal
        dat_ban = phien.dat_ban if phien.dat_ban_id else None
        if not dat_ban or dat_ban.trang_thai_coc != DatBan.TrangThaiCoc.THANH_CONG:
            return Decimal("0")
        coc = dat_ban.so_tien_coc or Decimal("0")
        if don_hang is None:
            return coc
        return min(coc, don_hang.tong_tien)

    @classmethod
    @transaction.atomic
    def check_out(cls, *, nguoi_dung, phien_id, phuong_thuc="tien_mat", ma_tham_chieu=""):
        from orders.models import DonHang
        from orders.services import DichVuDonHang
        from payments.models import ThanhToan

        phien = PhienPhucVu.objects.select_for_update(of=("self",)).select_related("ban_an", "dat_ban").get(pk=phien_id)
        if phien.trang_thai != PhienPhucVu.TrangThai.DANG_PHUC_VU:
            raise ValidationError({"session": "Phiên này không còn ở trạng thái phục vụ."})
        don_hang = cls._don_cua_phien(phien)
        if don_hang is None or not don_hang.danh_sach_mon.exists():
            raise ValidationError({"order": "Bàn chưa gọi món nào. Dùng “Huỷ bàn” nếu khách không dùng bữa."})
        # Checkout is the cashier's final action. Advance the order through its
        # normal kitchen states so the existing inventory and history hooks run.
        next_states = {
            DonHang.TrangThai.CHO_TIEP_NHAN: DonHang.TrangThai.DA_XAC_NHAN,
            DonHang.TrangThai.DA_XAC_NHAN: DonHang.TrangThai.DANG_CHE_BIEN,
            DonHang.TrangThai.DANG_CHE_BIEN: DonHang.TrangThai.SAN_SANG,
            DonHang.TrangThai.SAN_SANG: DonHang.TrangThai.HOAN_TAT,
        }
        while don_hang.trang_thai in next_states:
            target = next_states[don_hang.trang_thai]
            DichVuDonHang.doi_trang_thai(don_hang, target, nguoi_dung, "Hoàn tất tại quầy")
            don_hang.refresh_from_db()
        if don_hang.trang_thai != DonHang.TrangThai.HOAN_TAT:
            raise ValidationError({"order": "Hóa đơn đã kết thúc và không thể checkout."})

        # Tiền cọc khách đã trả khi đặt bàn được trừ vào hoá đơn, chỉ thu phần còn lại.
        can_thu = don_hang.tong_tien - cls.tien_coc_da_tra(phien, don_hang)
        payment = ThanhToan.objects.select_for_update().filter(
            don_hang=don_hang, trang_thai=ThanhToan.TrangThai.THANH_CONG
        ).first()
        if payment and payment.so_tien != can_thu:
            raise ValidationError({"payment": "Khoản thanh toán thành công không khớp số tiền cần thu."})
        if not payment and can_thu:
            if phuong_thuc not in {"tien_mat", "chuyen_khoan"}:
                raise ValidationError({"payment": "Thanh toán VNPay cần được xác nhận thành công trước khi checkout."})
            payment = ThanhToan.objects.select_for_update().filter(
                don_hang=don_hang, trang_thai=ThanhToan.TrangThai.CHO_XU_LY
            ).first()
            if payment and payment.so_tien != can_thu:
                raise ValidationError({"payment": "Hóa đơn thanh toán đang chờ có số tiền không khớp."})
            if not payment:
                payment = ThanhToan.objects.create(
                    nguoi_dung=nguoi_dung,
                    don_hang=don_hang,
                    loai_thanh_toan=ThanhToan.LoaiThanhToan.DON_HANG,
                    phuong_thuc=phuong_thuc,
                    so_tien=can_thu,
                    ma_giao_dich=ma_tham_chieu,
                )
            payment.trang_thai = ThanhToan.TrangThai.THANH_CONG
            payment.thanh_toan_luc = timezone.now()
            payment.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])

        now = timezone.now()
        phien.trang_thai = PhienPhucVu.TrangThai.DA_DONG
        phien.check_out_luc = now
        phien.da_don_luc = now
        phien.nguoi_check_out = nguoi_dung
        phien.nguoi_xac_nhan_don = nguoi_dung
        phien.save(update_fields=["trang_thai", "check_out_luc", "da_don_luc", "nguoi_check_out", "nguoi_xac_nhan_don", "cap_nhat_luc"])
        phien.ban_an.trang_thai = BanAn.TrangThai.TRONG
        phien.ban_an.save(update_fields=["trang_thai", "cap_nhat_luc"])
        if phien.dat_ban_id:
            dat_ban = phien.dat_ban
            dat_ban.trang_thai = DatBan.TrangThai.HOAN_TAT
            dat_ban.gio_ket_thuc = now.time()
            dat_ban.phien_ban += 1
            dat_ban.save(update_fields=["trang_thai", "gio_ket_thuc", "phien_ban", "cap_nhat_luc"])
        return phien

    @classmethod
    @transaction.atomic
    def huy_phien(cls, *, nguoi_dung, phien_id, ly_do=""):
        """Huỷ bàn đang mở. Chưa gửi bếp: nhân viên được huỷ, hoá đơn nháp bị xoá.
        Đã gửi bếp: chỉ quản lý được huỷ, hoá đơn chuyển "Đã huỷ" và hoàn kho."""
        from orders.models import DonHang
        from orders.services import DichVuDonHang

        phien = PhienPhucVu.objects.select_for_update(of=("self",)).select_related("ban_an", "dat_ban").get(pk=phien_id)
        if phien.trang_thai != PhienPhucVu.TrangThai.DANG_PHUC_VU:
            raise ValidationError({"session": "Phiên này không còn ở trạng thái phục vụ."})
        don_hang = cls._don_cua_phien(phien)
        if don_hang is not None:
            if don_hang.trang_thai == DonHang.TrangThai.DA_HUY:
                pass  # Hoá đơn đã bị huỷ ở nơi khác: chỉ cần đóng phiên, giải phóng bàn.
            elif don_hang.trang_thai in DichVuDonHang.TERMINAL_STATES:
                raise ValidationError({"order": "Hoá đơn đã hoàn tất, dùng thanh toán để đóng bàn."})
            elif don_hang.trang_thai == DonHang.TrangThai.CHO_TIEP_NHAN:
                cls._xoa_don_chua_gui_bep(don_hang)
            else:
                if not cls.la_quan_ly(nguoi_dung):
                    raise PermissionDenied("Hoá đơn đã gửi bếp, chỉ quản lý chi nhánh mới huỷ được.")
                DichVuDonHang.doi_trang_thai(don_hang, DonHang.TrangThai.DA_HUY, nguoi_dung, (ly_do or "Quản lý huỷ hoá đơn tại bàn")[:255])

        now = timezone.now()
        phien.trang_thai = PhienPhucVu.TrangThai.DA_DONG
        phien.check_out_luc = now
        phien.da_don_luc = now
        phien.nguoi_check_out = nguoi_dung
        phien.save(update_fields=["trang_thai", "check_out_luc", "da_don_luc", "nguoi_check_out", "cap_nhat_luc"])
        phien.ban_an.trang_thai = BanAn.TrangThai.TRONG
        phien.ban_an.save(update_fields=["trang_thai", "cap_nhat_luc"])
        if phien.dat_ban_id:
            # Khách đặt bàn vẫn ở trạng thái đã đến, có thể xếp lại bàn khác.
            DatBan.objects.filter(pk=phien.dat_ban_id).update(ban_an=None, cap_nhat_luc=now)
        return phien

    @classmethod
    @transaction.atomic
    def xac_nhan_da_don(cls, *, nguoi_dung, phien_id):
        phien = PhienPhucVu.objects.select_for_update(of=("self",)).select_related("ban_an").get(pk=phien_id)
        if phien.trang_thai != PhienPhucVu.TrangThai.CHO_DON:
            raise ValidationError({"session": "Chỉ xác nhận dọn bàn sau khi checkout."})
        now = timezone.now()
        phien.trang_thai = PhienPhucVu.TrangThai.DA_DONG
        phien.da_don_luc = now
        phien.nguoi_xac_nhan_don = nguoi_dung
        phien.save(update_fields=["trang_thai", "da_don_luc", "nguoi_xac_nhan_don", "cap_nhat_luc"])
        phien.ban_an.trang_thai = BanAn.TrangThai.TRONG
        phien.ban_an.save(update_fields=["trang_thai", "cap_nhat_luc"])
        return phien


# Backward-compatible service alias
ReservationService = DichVuDatBan
