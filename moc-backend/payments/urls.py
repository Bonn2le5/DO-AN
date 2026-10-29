from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ThanhToanViewSet, PhieuHoanTienViewSet

router = DefaultRouter()
router.register("payments", ThanhToanViewSet, basename="payment")
router.register("thanh-toan", ThanhToanViewSet, basename="thanh-toan")
router.register("refund-receipts", PhieuHoanTienViewSet, basename="refund-receipt")
router.register("phieu-hoan-tien", PhieuHoanTienViewSet, basename="phieu-hoan-tien")

urlpatterns = [
    # Explicit dual routes for VNPay
    path("vnpay/create/", ThanhToanViewSet.as_view({"post": "vnpay_create"}), name="vnpay-create"),
    path("vnpay/tao-phien/", ThanhToanViewSet.as_view({"post": "vnpay_tao_phien"}), name="vnpay-tao-phien"),
    path("vnpay/return/", ThanhToanViewSet.as_view({"get": "vnpay_return"}), name="vnpay-return"),
    path("vnpay/ipn/", ThanhToanViewSet.as_view({"get": "vnpay_ipn"}), name="vnpay-ipn"),
    path("", include(router.urls)),
]
