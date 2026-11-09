import re
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from django.db.models import Sum, Count, F, Min
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.permissions import LaNhanVienNhaHang, IsRestaurantStaff
from .models import ThongBao, Notification, AdminSetting
from .serializers import ThongBaoSerializer, NotificationSerializer
from orders.models import DonHang, Order
from reservations.models import DatBan, Reservation

VN = ZoneInfo("Asia/Ho_Chi_Minh")
BRANCH_OF_ORDER = Coalesce("chi_nhanh_id", "phien_phuc_vu__chi_nhanh_id")


class ThongBaoViewSet(viewsets.ModelViewSet):
    serializer_class = ThongBaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ThongBao.objects.filter(nguoi_dung=self.request.user)

    def perform_create(self, serializer):
        serializer.save(nguoi_dung=self.request.user)

    @action(detail=True, methods=["post"])
    def da_doc(self, request, pk=None):
        tb = self.get_object()
        tb.da_doc = True
        tb.doc_luc = timezone.now()
        tb.save(update_fields=["da_doc", "doc_luc", "cap_nhat_luc"])
        return Response(self.get_serializer(tb).data)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        return self.da_doc(request, pk=pk)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [LaNhanVienNhaHang]

    def list(self, request):
        days = min(90, max(1, int(request.query_params.get("days", 7))))
        user = request.user
        is_admin = user.is_superuser or getattr(user, "la_quan_tri_vien", False)
        branch_id = None if is_admin else getattr(user, "chi_nhanh_quan_ly_id", None)
        now = timezone.now()
        # Ngày làm việc tính theo giờ Việt Nam (server đang để TIME_ZONE = UTC).
        today_vn = timezone.localtime(now, VN).date()
        start = datetime.combine(today_vn - timedelta(days=days - 1), dtime.min, tzinfo=VN)
        # Hoá đơn cũ có thể chỉ gắn chi nhánh qua phiên phục vụ.
        don_hang = DonHang.objects.annotate(cn=BRANCH_OF_ORDER).filter(tao_luc__gte=start).exclude(trang_thai=DonHang.TrangThai.DA_HUY)
        dat_ban = DatBan.objects.all()
        if not is_admin:
            if branch_id:
                don_hang = don_hang.filter(cn=branch_id)
                dat_ban = dat_ban.filter(chi_nhanh_id=branch_id)
            else:
                don_hang = don_hang.none()
                dat_ban = dat_ban.none()
        doanh_thu = don_hang.filter(trang_thai=DonHang.TrangThai.HOAN_TAT).aggregate(val=Sum("tong_tien"))["val"] or 0
        so_don = don_hang.count()
        so_dat_ban = dat_ban.count()
        from django.contrib.auth import get_user_model
        from orders.models import ChiTietDonHang
        from foods.models import NguyenLieu
        from chat.models import TinNhan
        User = get_user_model()
        so_khach = User.objects.filter(date_joined__gte=start).count() if is_admin else 0
        phan_bo_trang_thai = list(don_hang.values("trang_thai").annotate(count=Count("id")))
        daily = list(don_hang.filter(trang_thai=DonHang.TrangThai.HOAN_TAT).annotate(day=TruncDate("tao_luc", tzinfo=VN)).values("day").annotate(value=Sum("tong_tien")).order_by("day"))
        daily_map = {row["day"]: float(row["value"] or 0) for row in daily}
        revenue_by_day = [{"label": f"{(start.date() + timedelta(days=i)).day}/{(start.date() + timedelta(days=i)).month}", "value": daily_map.get(start.date() + timedelta(days=i), 0)} for i in range(days)]
        top_food_query = ChiTietDonHang.objects.filter(don_hang__tao_luc__gte=start, don_hang__trang_thai=DonHang.TrangThai.HOAN_TAT)
        if not is_admin:
            top_food_query = top_food_query.filter(don_hang__in=don_hang) if branch_id else top_food_query.none()
        top_foods = list(top_food_query.values("mon_an__ten").annotate(qty=Sum("so_luong")).order_by("-qty")[:5])
        today = today_vn
        pending_orders_qs = DonHang.objects.filter(trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN)
        if not is_admin:
            pending_orders_qs = pending_orders_qs.filter(chi_nhanh_id=branch_id)
        pending_orders = pending_orders_qs.count()
        pending_deposits = dat_ban.filter(
            yeu_cau_dat_coc=True,
            trang_thai_coc__in=[DatBan.TrangThaiCoc.CHUA_THANH_TOAN, DatBan.TrangThaiCoc.DANG_XU_LY, DatBan.TrangThaiCoc.THAT_BAI],
            trang_thai__in=[DatBan.TrangThai.CHO_XAC_NHAN, DatBan.TrangThai.CHO_THANH_TOAN],
        ).count()
        refund_queue = dat_ban.filter(trang_thai__in=[DatBan.TrangThai.DA_HUY, DatBan.TrangThai.KHACH_KHONG_DEN], trang_thai_coc=DatBan.TrangThaiCoc.THANH_CONG).count()
        low_stock = NguyenLieu.objects.filter(con_hoat_dong=True, ton_kho_hien_tai__lt=F("ton_kho_toi_thieu")).count() if is_admin else 0
        unread = TinNhan.objects.filter(da_doc=False, nguoi_gui__is_staff=False).exclude(nguoi_gui__danh_sach_vai_tro__ten__in=["nhan_vien", "nhan_vien_ban_hang", "quan_ly_chi_nhanh", "quan_tri_vien"]).distinct().count() if is_admin else 0

        return Response({
            # Vietnamese standard keys
            "doanh_thu": doanh_thu,
            "so_don_hang": so_don,
            "so_dat_ban": so_dat_ban,
            "so_khach_hang": so_khach,
            "don_hang_theo_trang_thai": phan_bo_trang_thai,
            # English legacy compatibility keys
            "revenue": doanh_thu,
            "orders": so_don,
            "reservations": so_dat_ban,
            "customers": so_khach,
            "orders_by_status": phan_bo_trang_thai,
            "reservations_today": dat_ban.filter(ngay_dat=today).count(),
            "new_customers": so_khach,
            "revenue_by_day": revenue_by_day,
            "top_foods": [[row["mon_an__ten"], row["qty"]] for row in top_foods],
            "tasks": {
                "pendingOrders": pending_orders, "pendingDeposits": pending_deposits, "refundQueue": refund_queue,
                "lowStock": low_stock, "unreadChats": unread,
                "pendingConfirm": dat_ban.filter(trang_thai=DatBan.TrangThai.CHO_XAC_NHAN, ngay_dat__gte=today_vn).count(),
            },
            **self._overview(is_admin=is_admin, branch_id=branch_id, now=now, today_vn=today_vn, start=start),
        })

    @staticmethod
    def _overview(*, is_admin, branch_id, now, today_vn, start):
        """Số liệu cho trang Tổng quan mới: tình trạng bàn lúc này, hôm nay, so sánh chi nhánh, khách sắp đến."""
        from branches.models import ChiNhanh
        from reservations.models import BanAn, PhienPhucVu

        branches = ChiNhanh.objects.all().order_by("id") if is_admin else ChiNhanh.objects.filter(pk=branch_id)
        branch_ids = list(branches.values_list("id", flat=True))
        natural = lambda v: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", v or "")]

        open_sessions = {}
        for p in PhienPhucVu.objects.filter(
            chi_nhanh_id__in=branch_ids,
            trang_thai__in=[PhienPhucVu.TrangThai.DANG_PHUC_VU, PhienPhucVu.TrangThai.CHO_DON],
        ).select_related("don_hang"):
            open_sessions[p.ban_an_id] = p

        start_today = datetime.combine(today_vn, dtime.min, tzinfo=VN)
        done = DonHang.objects.annotate(cn=BRANCH_OF_ORDER).filter(cn__in=branch_ids, trang_thai=DonHang.TrangThai.HOAN_TAT)
        today_rows = {r["cn"]: r for r in done.filter(tao_luc__gte=start_today).values("cn").annotate(revenue=Sum("tong_tien"), bills=Count("id"))}
        last_week = done.filter(tao_luc__gte=start_today - timedelta(days=7), tao_luc__lte=now - timedelta(days=7)).aggregate(v=Sum("tong_tien"))["v"] or 0
        range_rows = {r["cn"]: r for r in done.filter(tao_luc__gte=start).values("cn").annotate(revenue=Sum("tong_tien"), bills=Count("id"))}
        guest_rows = {r["chi_nhanh_id"]: r["guests"] for r in PhienPhucVu.objects.filter(chi_nhanh_id__in=branch_ids, bat_dau_luc__gte=start).values("chi_nhanh_id").annotate(guests=Sum("so_luong_khach"))}

        live = []
        tables_by_branch = {}
        for t in BanAn.objects.filter(chi_nhanh_id__in=branch_ids, da_luu_tru=False):
            tables_by_branch.setdefault(t.chi_nhanh_id, []).append(t)
        for b in branches:
            tables = sorted(tables_by_branch.get(b.id, []), key=lambda t: natural(t.so_ban))
            cells, guests, open_total = [], 0, 0
            for t in tables:
                p = open_sessions.get(t.id)
                if p and p.trang_thai == PhienPhucVu.TrangThai.DANG_PHUC_VU:
                    state = "busy"; guests += p.so_luong_khach
                    open_total += float(getattr(getattr(p, "don_hang", None), "tong_tien", 0) or 0)
                elif (p and p.trang_thai == PhienPhucVu.TrangThai.CHO_DON) or t.trang_thai == BanAn.TrangThai.CHO_DON:
                    state = "cleaning"
                elif t.trang_thai == BanAn.TrangThai.BAO_TRI:
                    state = "maintenance"
                elif t.trang_thai == BanAn.TrangThai.TRONG:
                    state = "free"
                else:
                    state = "held"
                cells.append({"name": t.so_ban, "seats": t.suc_chua, "state": state})
            today = today_rows.get(b.id, {})
            rng = range_rows.get(b.id, {})
            live.append({
                "id": b.id, "name": b.ten, "tables": cells, "guests": guests, "open_total": open_total,
                "today_revenue": float(today.get("revenue") or 0), "today_bills": today.get("bills") or 0,
                "range_revenue": float(rng.get("revenue") or 0), "range_bills": rng.get("bills") or 0,
                "range_guests": guest_rows.get(b.id) or 0,
            })

        upcoming_qs = DatBan.objects.filter(
            chi_nhanh_id__in=branch_ids, ngay_dat=today_vn,
            trang_thai__in=[DatBan.TrangThai.CHO_XAC_NHAN, DatBan.TrangThai.CHO_THANH_TOAN, DatBan.TrangThai.DA_XAC_NHAN],
        ).select_related("chi_nhanh").order_by("gio_bat_dau")
        upcoming = [{
            "id": r.id, "time": r.gio_bat_dau.strftime("%H:%M"), "customer": r.ten_khach, "party": r.so_luong_khach,
            "status": r.trang_thai, "branch": r.chi_nhanh.ten, "preorder": r.hinh_thuc != DatBan.HinhThuc.CHI_GIU_CHO,
        } for r in upcoming_qs[:6]]

        unassigned = None
        leaks = None
        if is_admin:
            # Khoản hụt: những chỗ tiền lẽ ra vào túi nhưng không vào, chỉ chủ nhà hàng cần nhìn tổng.
            from reviews.models import DanhGia
            per_branch = lambda qs, key: {r["k"]: r for r in qs.values(k=F(key)).annotate(n=Count("id"), v=Sum("_v"))}
            orders = DonHang.objects.annotate(cn=BRANCH_OF_ORDER).filter(tao_luc__gte=start)
            discount = orders.filter(trang_thai=DonHang.TrangThai.HOAN_TAT, tien_giam__gt=0).annotate(_v=F("tien_giam"))
            cancelled = orders.filter(trang_thai=DonHang.TrangThai.DA_HUY).annotate(_v=F("tong_tien"))
            no_show = DatBan.objects.filter(trang_thai=DatBan.TrangThai.KHACH_KHONG_DEN, ngay_dat__gte=start.date(), ngay_dat__lte=today_vn).annotate(_v=F("so_luong_khach"))
            low = DanhGia.objects.filter(tao_luc__gte=start, diem_danh_gia__lte=2).annotate(cn=Coalesce("don_hang__chi_nhanh_id", "don_hang__phien_phuc_vu__chi_nhanh_id"), _v=F("diem_danh_gia"))
            names = {b.id: b.ten for b in branches}

            def pack(qs, key):
                rows = per_branch(qs, key)
                worst = max(rows.values(), key=lambda r: r["n"], default=None)
                return {
                    "count": sum(r["n"] for r in rows.values()), "value": float(sum((r["v"] or 0) for r in rows.values())),
                    "worst_branch": names.get(worst["k"]) if worst and len(rows) > 1 else None,
                }
            leaks = {"discount": pack(discount, "cn"), "cancelled": pack(cancelled, "cn"), "no_show": pack(no_show, "chi_nhanh_id"), "low_reviews": pack(low, "cn")}

            row = DonHang.objects.annotate(cn=BRANCH_OF_ORDER).filter(cn__isnull=True, trang_thai=DonHang.TrangThai.HOAN_TAT, tao_luc__gte=start).aggregate(revenue=Sum("tong_tien"), bills=Count("id"))
            if row["bills"]:
                unassigned = {"revenue": float(row["revenue"] or 0), "bills": row["bills"]}

        return {
            "leaks": leaks,
            "unassigned": unassigned,
            "now": timezone.localtime(now, VN).strftime("%H:%M"),
            "live": live,
            "today": {
                "revenue": sum(b["today_revenue"] for b in live), "bills": sum(b["today_bills"] for b in live),
                "last_week_same_time": float(last_week),
                "reservations": DatBan.objects.filter(chi_nhanh_id__in=branch_ids, ngay_dat=today_vn).exclude(trang_thai__in=[DatBan.TrangThai.DA_HUY]).count(),
                "upcoming_count": upcoming_qs.count(),
            },
            "upcoming": upcoming,
        }

    def ai(self, request):
        from recommendations.models import TuongTacMonAn, GoiYMonAn, SuKienGoiY
        base = TuongTacMonAn.objects.all()
        viewed = list(base.filter(loai_tuong_tac="xem").values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])
        ordered = list(base.filter(loai_tuong_tac="dat_mon").values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])
        favorited = list(base.filter(loai_tuong_tac="yeu_thich").values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])

        # CTR = lượt nhấp món gợi ý / lượt món gợi ý được hiển thị (nhật ký SuKienGoiY)
        hien_thi = SuKienGoiY.objects.filter(loai_su_kien=SuKienGoiY.LoaiSuKien.HIEN_THI)
        nhap = SuKienGoiY.objects.filter(loai_su_kien=SuKienGoiY.LoaiSuKien.NHAP)
        shown, click_count = hien_thi.count(), nhap.count()
        recommended = list(hien_thi.values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])

        # Conversion = cặp (khách, món) đã nhấp gợi ý rồi SAU ĐÓ đặt món đó / tổng cặp đã nhấp
        lan_nhap_dau = {
            (x["nguoi_dung_id"], x["mon_an_id"]): x["dau_tien"]
            for x in nhap.filter(nguoi_dung__isnull=False)
            .values("nguoi_dung_id", "mon_an_id").annotate(dau_tien=Min("tao_luc"))
        }
        da_dat = set()
        if lan_nhap_dau:
            for t in base.filter(
                loai_tuong_tac="dat_mon",
                nguoi_dung_id__in={u for u, _ in lan_nhap_dau},
                mon_an_id__in={m for _, m in lan_nhap_dau},
            ).values("nguoi_dung_id", "mon_an_id", "tao_luc"):
                key = (t["nguoi_dung_id"], t["mon_an_id"])
                if key in lan_nhap_dau and t["tao_luc"] >= lan_nhap_dau[key]:
                    da_dat.add(key)
        conversion = round(len(da_dat) * 100 / len(lan_nhap_dau), 1) if lan_nhap_dau else 0

        theo_vi_tri = []
        for value, label in SuKienGoiY.ViTri.choices:
            s, c = hien_thi.filter(vi_tri=value).count(), nhap.filter(vi_tri=value).count()
            theo_vi_tri.append({"key": value, "label": label, "shown": s, "clicks": c, "ctr": round(c * 100 / s, 1) if s else 0})

        return Response({
            "overview": {"suggested": shown, "clicks": click_count, "ctr": round(click_count * 100 / shown, 1) if shown else 0, "conversion": conversion},
            "positions": theo_vi_tri,
            "top": {"recommended": [[x["mon_an__ten"], x["n"]] for x in recommended], "viewed": [[x["mon_an__ten"], x["n"]] for x in viewed], "ordered": [[x["mon_an__ten"], x["n"]] for x in ordered], "favorited": [[x["mon_an__ten"], x["n"]] for x in favorited]},
            "recent": [{"user": x.nguoi_dung.get_full_name() or x.nguoi_dung.username, "food": x.mon_an.ten, "score": float(x.diem_tuong_dong), "reason": x.ly_do_goi_y} for x in GoiYMonAn.objects.select_related("nguoi_dung", "mon_an").order_by("-tao_luc")[:10]],
        })

    def restaurant_settings(self, request):
        entry, _ = AdminSetting.objects.get_or_create(key="restaurant", defaults={"value": {"name": "MỘC Kitchen", "email": "hello@moc-kitchen.vn", "weekday": "10:00 – 22:00", "weekend": "09:00 – 23:00"}})
        if request.method == "PUT":
            entry.value = {key: str(request.data.get(key, "")) for key in ("name", "email", "weekday", "weekend")}
            entry.save(update_fields=["value", "updated_at"])
        return Response(entry.value)


NotificationViewSet = ThongBaoViewSet
