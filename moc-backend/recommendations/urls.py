from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecommendationViewSet, InteractionViewSet

router = DefaultRouter()
router.register("recommendations", RecommendationViewSet, basename="recommendation")
router.register("goi-y", RecommendationViewSet, basename="goi-y")
router.register("interactions", InteractionViewSet, basename="interaction")
router.register("tuong-tac", InteractionViewSet, basename="tuong-tac")

urlpatterns = [
    path("recommendations/tuong-tac/", InteractionViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-tuong-tac"),
    path("recommendations/interactions/", InteractionViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-interactions"),
    path("goi-y/tuong-tac/", InteractionViewSet.as_view({"get": "list", "post": "create"}), name="goi-y-tuong-tac"),
    path("recommendations/lam-moi/", RecommendationViewSet.as_view({"get": "refresh", "post": "refresh"}), name="recommendations-lam-moi-explicit"),
    path("goi-y/lam-moi/", RecommendationViewSet.as_view({"get": "refresh", "post": "refresh"}), name="goi-y-lam-moi-explicit"),
    path("", include(router.urls)),
]
