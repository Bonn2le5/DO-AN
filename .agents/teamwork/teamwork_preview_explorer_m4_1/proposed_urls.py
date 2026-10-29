"""
Proposed URL routing specifications for Recommendations & Interactions.
Ensures support for:
- /api/recommendations/ & /api/goi-y/ (GET list, POST refresh)
- /api/recommendations/tuong-tac/ & /api/recommendations/interactions/ (POST/GET interactions)
- /api/tuong-tac/ & /api/interactions/ (Canonical interaction endpoints)
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recommendations.views import RecommendationViewSet, InteractionViewSet

# Router registrations
# router.register("recommendations", RecommendationViewSet, basename="recommendation")
# router.register("goi-y", RecommendationViewSet, basename="goi-y")
# router.register("interactions", InteractionViewSet, basename="interaction")
# router.register("tuong-tac", InteractionViewSet, basename="tuong-tac")

recommendation_extra_urlpatterns = [
    # Explicit dual endpoints for /api/recommendations/tuong-tac/ requested in Section 7
    path(
        "recommendations/tuong-tac/",
        InteractionViewSet.as_view({"get": "list", "post": "create"}),
        name="recommendation-tuong-tac",
    ),
    path(
        "recommendations/interactions/",
        InteractionViewSet.as_view({"get": "list", "post": "create"}),
        name="recommendation-interactions",
    ),
    path(
        "goi-y/tuong-tac/",
        InteractionViewSet.as_view({"get": "list", "post": "create"}),
        name="goi-y-tuong-tac",
    ),
    path(
        "recommendations/lam-moi/",
        RecommendationViewSet.as_view({"get": "refresh", "post": "refresh"}),
        name="recommendations-lam-moi-explicit",
    ),
]
