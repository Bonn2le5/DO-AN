import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.cache import cache, caches
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from rest_framework.exceptions import ValidationError
from .models import DatBan, MonAnTrongDatBan, BanAn, ChinhSachDatCoc


def _safe_cache():
    try:
        cache.get("_probe_")
        return cache
    except Exception:
        try:
            return caches["locmem"]
        except Exception:
            return cache


class DichVuDatBan:
    HOLD_TIMEOUT_SECONDS = 600  # 10 phút

    @staticmethod
    def _chuan_hoa_thoi_gian(ngay, gio):
        ngay_str = str(ngay).strip()
        gio_str = str(gio).strip()
        if len(gio_str) > 5:
            gio_str = gio_str[:5]  # Chuẩn hóa HH:MM
        return ngay_str, gio_str

    @staticmethod
    def _tao_khoa_giu_ban(id_ban, ngay, gio):
        ngay_str, gio_str = DichVuDatBan._chuan_hoa_thoi_gian(ngay, gio)
        return f"table_hold:{id_ban}:{ngay_str}:{gio_str}"

    @staticmethod
    def _tao_khoa_phu(id_ban, ngay, gio):
        ngay_str, gio_str = DichVuDatBan._chuan_hoa_thoi_gian(ngay, gio)
        return f"giu-ban:{id_ban}:{ngay_str}:{gio_str}"

    @classmethod
    def giu_ban_tam_thoi(cls, *, ban_id, ngay, gio, so_khach, user_id=None):
        """
        Phase 1: Giữ bàn tạm thời với Redis SET NX EX 600
        """
        ngay_str, gio_str = cls._chuan_hoa_thoi_gian(ngay, gio)
        ngay_dat = parse_date(ngay_str)
        gio_dat = parse_time(gio_str)
        if not ngay_dat or not gio_dat:
            raise ValidationError({"detail": "Ngày hoặc giờ đặt bàn không hợp lệ."})
        thoi_diem_dat = timezone.make_aware(
            datetime.combine(ngay_dat, gio_dat), timezone.get_current_timezone()
        )
        if thoi_diem_dat <= timezone.now():
            raise ValidationError({"detail": "Không thể giữ bàn ở thời điểm đã qua."})
        c = _safe_cache()

        # 1. Kiểm tra bàn ăn
        try:
            ban = BanAn.objects.select_related("chi_nhanh").get(id=ban_id)
        except BanAn.DoesNotExist:
            raise ValidationError({"ban_an": "Bàn ăn không tồn tại."})

        if ban.trang_thai == BanAn.TrangThai.BAO_TRI:
            raise ValidationError({"ban_an": "Bàn đang trong trạng thái bảo trì."})

        if ban.suc_chua < int(so_khach):
            raise ValidationError({"so_luong_khach": f"Bàn chỉ có sức chứa tối đa {ban.suc_chua} khách."})

        # 2. Kiểm tra bàn đã được chốt trong CSDL chưa
        da_dat_db = DatBan.objects.filter(
            ban_an=ban,
            ngay_dat=ngay_str,
            gio_bat_dau__startswith=gio_str,
            trang_thai__in=[
                DatBan.TrangThai.CHO_XAC_NHAN,
                DatBan.TrangThai.CHO_THANH_TOAN,
                DatBan.TrangThai.DA_XAC_NHAN,
                DatBan.TrangThai.KHACH_DA_DEN
            ]
        ).exists()

        if da_dat_db:
            return False, {
                "detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt",
                "chi_tiet": "Bàn này đã được đặt trong khung giờ đã chọn.",
                "code": "BAN_DANG_BAN",
                "error_code": "TABLE_ALREADY_BOOKED",
                "status": "conflict",
                "message": "Bàn ăn này đã được chốt đặt trong khung giờ này.",
                "ban_an_id": ban.id,
                "ngay_dat": ngay_str,
                "gio_bat_dau": gio_str,
            }

        # 3. Thực hiện khóa Redis SET NX EX 600
        khoa_redis = cls._tao_khoa_giu_ban(ban.id, ngay_str, gio_str)
        khoa_phu = cls._tao_khoa_phu(ban.id, ngay_str, gio_str)
        token_giu_ban = f"HOLD_{uuid.uuid4().hex}"

        # cache.add thực thi Redis SET NX EX
        khoa_thanh_cong = c.add(khoa_redis, token_giu_ban, timeout=cls.HOLD_TIMEOUT_SECONDS)

        if not khoa_thanh_cong:
            return False, {
                "detail": "Bàn này đang được người khác giữ chỗ hoặc đã được đặt",
                "chi_tiet": "Bàn này đang được người khác giữ chỗ tạm thời.",
                "code": "BAN_DANG_BAN",
                "error_code": "TABLE_CURRENTLY_HELD",
                "status": "conflict",
                "message": "Bàn ăn này đang được khách hàng khác giữ chỗ trong 10 phút. Vui lòng chọn bàn khác hoặc thử lại sau.",
                "ban_an_id": ban.id,
                "ngay_dat": ngay_str,
                "gio_bat_dau": gio_str,
                "retry_after_seconds": cls.HOLD_TIMEOUT_SECONDS,
            }

        # Đồng bộ hóa khóa phụ
        try:
            c.set(khoa_phu, token_giu_ban, timeout=cls.HOLD_TIMEOUT_SECONDS)
        except Exception:
            pass

        thoi_han = timezone.now() + timedelta(seconds=cls.HOLD_TIMEOUT_SECONDS)
        return True, {
            "status": "success",
            "id_giu_ban": token_giu_ban,
            "thoi_han_giu_cho": thoi_han.isoformat(),
            "thoi_gian_con_lai_giay": cls.HOLD_TIMEOUT_SECONDS,
            "ban_an_id": ban.id,
            "ngay_dat": ngay_str,
            "gio_bat_dau": gio_str,
        }

    @classmethod
    @transaction.atomic
    def tao_dat_ban(cls, *, nguoi_dung, du_lieu):
        """
        Phase 2: Chốt đặt bàn với Khóa bi quan select_for_update() và xác minh token Redis.
        Toàn bộ logic thực thi trong 1 Database Transaction nguyên tử duy nhất.
        Hỗ trợ: có ban_an cụ thể (flow cũ) hoặc chỉ có chi_nhanh (auto-assign bàn).
        """
        danh_sach_item = du_lieu.pop("danh_sach_mon", None) or du_lieu.pop("food_items", [])

        id_giu_ban = du_lieu.pop("id_giu_ban", None)
        du_lieu.pop("expected_version", None)

        ban = du_lieu.get("ban_an")
        ngay = du_lieu["ngay_dat"]
        gio = du_lieu["gio_bat_dau"]
        so_khach = du_lieu["so_luong_khach"]
        chi_nhanh = du_lieu.get("chi_nhanh") or (ban.chi_nhanh if ban else None)

        if not chi_nhanh:
            raise ValidationError({"chi_nhanh": "Cần cung cấp chi_nhanh hoặc ban_an."})

        du_lieu["chi_nhanh"] = chi_nhanh
        ngay_str, gio_str = cls._chuan_hoa_thoi_gian(ngay, gio)
        c = _safe_cache()

        if ban:
            # --- Flow cũ: khách chọn bàn cụ thể ---
            # 1. KHÓA BI QUAN ROW BÀN ĂN (Mutex để serialize các request cùng bàn)
            ban_locked = BanAn.objects.select_for_update().get(id=ban.id)

            if ban_locked.trang_thai == BanAn.TrangThai.BAO_TRI:
                raise ValidationError({"ban_an": "Bàn đang trong trạng thái bảo trì."})
            if so_khach > ban_locked.suc_chua:
                raise ValidationError({"so_luong_khach": f"Bàn chỉ có sức chứa tối đa {ban_locked.suc_chua} khách."})
            if ban_locked.chi_nhanh_id != chi_nhanh.id:
                raise ValidationError({"ban_an": "Bàn không thuộc chi nhánh đã chọn."})

            # 2. Kiểm tra xung đột đặt bàn trong CSDL với khóa bi quan
            tranh_chap = DatBan.objects.select_for_update().filter(
                ban_an=ban_locked,
                ngay_dat=ngay,
                gio_bat_dau__startswith=gio_str,
                trang_thai__in=[
                    DatBan.TrangThai.CHO_XAC_NHAN,
                    DatBan.TrangThai.CHO_THANH_TOAN,
                    DatBan.TrangThai.DA_XAC_NHAN,
                    DatBan.TrangThai.KHACH_DA_DEN
                ]
            )
            if tranh_chap.exists():
                raise ValidationError({"ban_an": "Bàn đã có người đặt trong khung giờ này."})

            # 3. Đối soát Token giữ bàn trên Redis
            khoa_redis = cls._tao_khoa_giu_ban(ban_locked.id, ngay_str, gio_str)
            khoa_phu = cls._tao_khoa_phu(ban_locked.id, ngay_str, gio_str)
            token_hien_tai = c.get(khoa_redis) or c.get(khoa_phu)

            if id_giu_ban:
                if token_hien_tai != str(id_giu_ban):
                    raise ValidationError({"id_giu_ban": "Phiên giữ bàn đã hết hạn hoặc không hợp lệ."})
            else:
                if token_hien_tai is not None:
                    raise ValidationError({"ban_an": "Bàn hiện đang được giữ chỗ tạm thời bởi khách hàng khác."})

            du_lieu["ban_an"] = ban_locked

            def _xoa_khoa_redis():
                try:
                    c.delete(khoa_redis)
                    c.delete(khoa_phu)
                    c.delete(f"giu-ban:{ban_locked.id}:{ngay_str}:{gio}")
                except Exception:
                    pass
            transaction.on_commit(_xoa_khoa_redis)

        else:
            # --- Flow mới: staff tự gán bàn, khách chỉ chọn chi nhánh + ngày + giờ ---
            # Tự động tìm bàn phù hợp còn trống
            ban_da_dat = DatBan.objects.filter(
                chi_nhanh=chi_nhanh,
                ngay_dat=ngay,
                gio_bat_dau__startswith=gio_str,
                trang_thai__in=[
                    DatBan.TrangThai.CHO_XAC_NHAN,
                    DatBan.TrangThai.CHO_THANH_TOAN,
                    DatBan.TrangThai.DA_XAC_NHAN,
                    DatBan.TrangThai.KHACH_DA_DEN
                ]
            ).values_list("ban_an_id", flat=True)

            ban_phu_hop = (
                BanAn.objects
                .select_for_update()
                .filter(chi_nhanh=chi_nhanh, suc_chua__gte=so_khach)
                .exclude(trang_thai=BanAn.TrangThai.BAO_TRI)
                .exclude(id__in=ban_da_dat)
                .order_by("suc_chua")
                .first()
            )
            # Ghi nhận bàn tự gán (có thể None — staff gán sau)
            du_lieu["ban_an"] = ban_phu_hop
            ban_locked = ban_phu_hop

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

        # 2. Khấu trừ tồn kho BOM (cho phép ValidationError nổi bọt để rollback khi thiếu hàng)
        if trang_thai_moi in [DatBan.TrangThai.DA_XAC_NHAN, DatBan.TrangThai.KHACH_DA_DEN]:
            from foods.services import DichVuKho
            items = db_locked.danh_sach_mon.all()
            has_items = items.exists() if hasattr(items, "exists") else bool(items)
            if has_items:
                DichVuKho.khau_tru_nguyen_lieu_bom(
                    danh_sach_mon=items,
                    loai_tham_chieu="dat_ban",
                    id_tham_chieu=db_locked.id,
                    nguoi_dung=nguoi_dung,
                    ghi_chu=f"Xuất kho cho đặt bàn {db_locked.ma_dat_ban}"
                )
        # 3. Hoàn trả tồn kho BOM khi hủy đặt bàn
        elif trang_thai_moi == DatBan.TrangThai.DA_HUY and trang_thai_cu in [DatBan.TrangThai.DA_XAC_NHAN, DatBan.TrangThai.KHACH_DA_DEN]:
            from foods.services import DichVuKho
            DichVuKho.hoan_tra_nguyen_lieu_bom(
                loai_tham_chieu="dat_ban",
                id_tham_chieu=db_locked.id,
                nguoi_dung=nguoi_dung,
                ghi_chu=f"Hoàn kho do hủy đặt bàn {db_locked.ma_dat_ban}"
            )

        dat_ban.trang_thai = db_locked.trang_thai
        dat_ban.phien_ban = db_locked.phien_ban
        dat_ban.cap_nhat_luc = db_locked.cap_nhat_luc
        return dat_ban


# Backward-compatible service alias
ReservationService = DichVuDatBan
