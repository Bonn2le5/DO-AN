from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ThanhToanViewSet, PhieuHoanTienViewSet

router = DefaultRouter()
router.register("payments", ThanhToanViewSet, basename="payment")
router.register("thanh-toan", ThanhToanViewSet, basename="thanh-toan")
router.register("refund-receipts", PhieuHoanTienViewSet, basename="refund-receipt")
router.register("phieu-hoan-tien", PhieuHoanTienViewSet, basename="phieu-hoan-tien")

urlpatterns = [
    path("payos/tao-phien/", ThanhToanViewSet.as_view({"post": "payos_tao_phien"}), name="payos-tao-phien"),
    path("payos/return/", ThanhToanViewSet.as_view({"get": "payos_return"}), name="payos-return"),
    path("payos/webhook/", ThanhToanViewSet.as_view({"post": "payos_webhook"}), name="payos-webhook"),
    path("", include(router.urls)),
]
