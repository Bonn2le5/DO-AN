from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GoiYMonAnViewSet, TuongTacMonAnViewSet

router = DefaultRouter()
router.register("recommendations", GoiYMonAnViewSet, basename="recommendation")
router.register("goi-y", GoiYMonAnViewSet, basename="goi-y")
router.register("interactions", TuongTacMonAnViewSet, basename="interaction")
router.register("tuong-tac", TuongTacMonAnViewSet, basename="tuong-tac")

urlpatterns = [
    path("recommendations/tuong-tac/", TuongTacMonAnViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-tuong-tac"),
    path("recommendations/interactions/", TuongTacMonAnViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-interactions"),
    path("goi-y/tuong-tac/", TuongTacMonAnViewSet.as_view({"get": "list", "post": "create"}), name="goi-y-tuong-tac"),
    path("recommendations/lam-moi/", GoiYMonAnViewSet.as_view({"get": "refresh", "post": "refresh"}), name="recommendations-lam-moi-explicit"),
    path("goi-y/lam-moi/", GoiYMonAnViewSet.as_view({"get": "refresh", "post": "refresh"}), name="goi-y-lam-moi-explicit"),
    path("", include(router.urls)),
]
