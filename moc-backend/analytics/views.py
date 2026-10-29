from datetime import timedelta
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
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
        now = timezone.now()
        start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        don_hang = DonHang.objects.filter(tao_luc__gte=start).exclude(trang_thai=DonHang.TrangThai.DA_HUY)
        doanh_thu = don_hang.filter(trang_thai=DonHang.TrangThai.HOAN_TAT).aggregate(val=Sum("tong_tien"))["val"] or 0
        so_don = don_hang.count()
        so_dat_ban = DatBan.objects.count()
        from django.contrib.auth import get_user_model
        from orders.models import ChiTietDonHang
        from foods.models import NguyenLieu
        from chat.models import TinNhan
        User = get_user_model()
        so_khach = User.objects.filter(date_joined__gte=start).count()
        phan_bo_trang_thai = list(don_hang.values("trang_thai").annotate(count=Count("id")))
        daily = list(don_hang.filter(trang_thai=DonHang.TrangThai.HOAN_TAT).annotate(day=TruncDate("tao_luc")).values("day").annotate(value=Sum("tong_tien")).order_by("day"))
        daily_map = {row["day"]: float(row["value"] or 0) for row in daily}
        revenue_by_day = [{"label": f"{(start.date() + timedelta(days=i)).day}/{(start.date() + timedelta(days=i)).month}", "value": daily_map.get(start.date() + timedelta(days=i), 0)} for i in range(days)]
        top_foods = list(ChiTietDonHang.objects.filter(don_hang__tao_luc__gte=start, don_hang__trang_thai=DonHang.TrangThai.HOAN_TAT).values("mon_an__ten").annotate(qty=Sum("so_luong")).order_by("-qty")[:5])
        today = timezone.localdate()
        pending_orders = DonHang.objects.filter(trang_thai=DonHang.TrangThai.CHO_TIEP_NHAN).count()
        pending_deposits = DatBan.objects.filter(
            yeu_cau_dat_coc=True,
            trang_thai_coc__in=[DatBan.TrangThaiCoc.CHUA_THANH_TOAN, DatBan.TrangThaiCoc.DANG_XU_LY, DatBan.TrangThaiCoc.THAT_BAI],
            trang_thai__in=[DatBan.TrangThai.CHO_XAC_NHAN, DatBan.TrangThai.CHO_THANH_TOAN],
        ).count()
        refund_queue = DatBan.objects.filter(trang_thai__in=[DatBan.TrangThai.DA_HUY, DatBan.TrangThai.KHACH_KHONG_DEN], trang_thai_coc=DatBan.TrangThaiCoc.THANH_CONG).count()
        low_stock = NguyenLieu.objects.filter(con_hoat_dong=True, ton_kho_hien_tai__lt=F("ton_kho_toi_thieu")).count()
        unread = TinNhan.objects.filter(da_doc=False, nguoi_gui__is_staff=False).exclude(nguoi_gui__danh_sach_vai_tro__ten__in=["nhan_vien", "quan_tri_vien"]).distinct().count()

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
            "reservations_today": DatBan.objects.filter(ngay_dat=today).count(),
            "new_customers": so_khach,
            "revenue_by_day": revenue_by_day,
            "top_foods": [[row["mon_an__ten"], row["qty"]] for row in top_foods],
            "tasks": {"pendingOrders": pending_orders, "pendingDeposits": pending_deposits, "refundQueue": refund_queue, "lowStock": low_stock, "unreadChats": unread},
        })

    def ai(self, request):
        from recommendations.models import TuongTacMonAn, GoiYMonAn
        base = TuongTacMonAn.objects.all()
        viewed = list(base.filter(loai_tuong_tac="xem").values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])
        ordered = list(base.filter(loai_tuong_tac="dat_mon").values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])
        favorited = list(base.filter(loai_tuong_tac="yeu_thich").values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])
        recommended = list(GoiYMonAn.objects.values("mon_an__ten").annotate(n=Count("id")).order_by("-n")[:5])
        shown = GoiYMonAn.objects.count()
        click_count = base.filter(loai_tuong_tac__in=["xem", "dat_mon", "yeu_thich"]).count()
        order_count = base.filter(loai_tuong_tac="dat_mon").count()
        return Response({
            "overview": {"suggested": shown, "ctr": round(click_count * 100 / shown, 1) if shown else 0, "conversion": round(order_count * 100 / click_count, 1) if click_count else 0},
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
