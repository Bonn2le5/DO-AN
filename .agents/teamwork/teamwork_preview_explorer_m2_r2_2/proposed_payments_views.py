from datetime import timedelta
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from api.permissions import LaNhanVienNhaHang, IsRestaurantStaff
from reservations.models import DatBan
from orders.models import DonHang
from .models import ThanhToan, Payment, PhieuHoanTien, RefundReceipt
from .serializers import (
    ThanhToanSerializer, PaymentSerializer,
    PhieuHoanTienSerializer, RefundReceiptSerializer,
    VNPayCreatePaymentSerializer
)
from .services import VNPayService, RefundService


class ThanhToanViewSet(viewsets.ModelViewSet):
    serializer_class = ThanhToanSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Public webhook & return callbacks must allow anonymous access from VNPay and client redirects.
        Administrative confirmations require restaurant staff role.
        """
        if self.action in {"vnpay_create", "vnpay_tao_phien", "vnpay_return", "vnpay_ipn"}:
            return [AllowAny()]
        if self.action in {"xac_nhan_thanh_cong", "mark_success"}:
            return [LaNhanVienNhaHang()]
        return super().get_permissions()

    def get_queryset(self):
        q = ThanhToan.objects.select_related("don_hang", "dat_ban", "nguoi_dung").order_by("-tao_luc")
        user = self.request.user
        return q if getattr(user, "la_nhan_vien_nha_hang", False) else q.filter(nguoi_dung=user)

    def perform_create(self, serializer):
        serializer.save(nguoi_dung=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[LaNhanVienNhaHang])
    def xac_nhan_thanh_cong(self, request, pk=None):
        tt = self.get_object()
        tt.trang_thai = ThanhToan.TrangThai.THANH_CONG
        tt.thanh_toan_luc = timezone.now()
        tt.save(update_fields=["trang_thai", "thanh_toan_luc", "cap_nhat_luc"])

        if tt.loai_thanh_toan == ThanhToan.LoaiThanhToan.TIEN_COC and tt.dat_ban:
            db = tt.dat_ban
            db.trang_thai_coc = "thanh_cong"
            db.thanh_toan_coc_luc = tt.thanh_toan_luc
            db.trang_thai = "da_xac_nhan"
            db.phien_ban += 1
            db.save(update_fields=["trang_thai_coc", "thanh_toan_coc_luc", "trang_thai", "phien_ban", "cap_nhat_luc"])
        return Response(self.get_serializer(tt).data)

    @action(detail=True, methods=["post"], permission_classes=[LaNhanVienNhaHang])
    def mark_success(self, request, pk=None):
        return self.xac_nhan_thanh_cong(request, pk=pk)

    @action(detail=False, methods=["post"], url_path="vnpay/create", permission_classes=[AllowAny])
    def vnpay_create(self, request):
        ser = VNPayCreatePaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user if (request.user and request.user.is_authenticated) else None
        loai = data["loai_thanh_toan"]
        dat_ban = don_hang = None

        if loai == "tien_coc":
            dat_ban = get_object_or_404(DatBan, id=data["dat_ban_id"])
            if not user:
                user = dat_ban.nguoi_dung
            so_tien = data.get("so_tien") or dat_ban.so_tien_coc
        else:
            don_hang = get_object_or_404(DonHang, id=data["don_hang_id"])
            if not user:
                user = don_hang.khach_hang
            so_tien = data.get("so_tien") or don_hang.tong_tien

        if not user:
            from django.contrib.auth import get_user_model
            user = get_user_model().objects.filter(is_active=True).first()

        thanh_toan, _ = ThanhToan.objects.get_or_create(
            dat_ban=dat_ban,
            don_hang=don_hang,
            loai_thanh_toan=loai,
            phuong_thuc="vnpay",
            trang_thai=ThanhToan.TrangThai.CHO_XU_LY,
            defaults={"so_tien": so_tien, "nguoi_dung": user}
        )
        if thanh_toan.so_tien != so_tien:
            thanh_toan.so_tien = so_tien
            thanh_toan.save(update_fields=["so_tien", "cap_nhat_luc"])

        client_ip = data.get("ip_addr") or VNPayService.get_client_ip(request)
        payment_url, params = VNPayService.create_payment_url(
            thanh_toan=thanh_toan,
            ip_addr=client_ip,
            order_info=data.get("order_info")
        )

        expires_at = (timezone.now() + timedelta(minutes=15)).isoformat()
        return Response({
            "payment_url": payment_url,
            "duong_dan_thanh_toan": payment_url,
            "txn_ref": thanh_toan.ma_giao_dich,
            "ma_giao_dich": thanh_toan.ma_giao_dich,
            "amount": float(thanh_toan.so_tien),
            "so_tien": float(thanh_toan.so_tien),
            "expires_at": expires_at,
            "het_han_luc": expires_at,
            "thanh_toan_id": thanh_toan.id,
        })

    @action(detail=False, methods=["post"], url_path="vnpay/tao-phien", permission_classes=[AllowAny])
    def vnpay_tao_phien(self, request):
        return self.vnpay_create(request)

    @action(detail=False, methods=["get"], url_path="vnpay/return", permission_classes=[AllowAny])
    def vnpay_return(self, request):
        if hasattr(request.query_params, "dict"):
            raw_dict = request.query_params.dict()
        else:
            raw_dict = dict(request.query_params)
        params = {
            k: (v[0] if isinstance(v, list) and len(v) > 0 else v)
            for k, v in raw_dict.items()
        }

        hash_secret = getattr(settings, "VNPAY_HASH_SECRET", "VNPAYSECRETKEY2026MOCRESTAURANT")
        vnp_secure_hash = params.pop("vnp_SecureHash", None)
        params.pop("vnp_SecureHashType", None)

        is_valid = VNPayService.verify_signature(params, vnp_secure_hash, hash_secret)
        rsp_code = params.get("vnp_ResponseCode", "")
        is_success = is_valid and rsp_code == "00"
        raw_amount = params.get("vnp_Amount", 0)
        amount_vnd = float(raw_amount) / 100.0 if raw_amount else 0.0

        return Response({
            "status": "success" if is_success else "failed",
            "ma_giao_dich": params.get("vnp_TxnRef", ""),
            "txn_ref": params.get("vnp_TxnRef", ""),
            "ma_phan_hoi": rsp_code,
            "response_code": rsp_code,
            "so_tien": amount_vnd,
            "amount": amount_vnd,
            "message": "Giao dịch thành công" if is_success else "Giao dịch không thành công hoặc chữ ký không hợp lệ"
        })

    @action(detail=False, methods=["get"], url_path="vnpay/ipn", permission_classes=[AllowAny])
    def vnpay_ipn(self, request):
        rsp_code, message = VNPayService.process_ipn(request.query_params)
        return Response({"RspCode": rsp_code, "Message": message})


class PhieuHoanTienViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PhieuHoanTienSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        q = PhieuHoanTien.objects.select_related("dat_ban", "thanh_toan").order_by("-tao_luc")
        user = self.request.user
        return q if getattr(user, "la_nhan_vien_nha_hang", False) else q.filter(dat_ban__nguoi_dung=user)


# Backward-compatible viewset aliases
PaymentViewSet = ThanhToanViewSet
RefundReceiptViewSet = PhieuHoanTienViewSet
