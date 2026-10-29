from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import health_check
from accounts.views import (
    XacThucViewSet,
    NguoiDungViewSet,
    VaiTroViewSet,
    QuyenHanViewSet,
    DangNhapTokenView,
)
from foods.views import DanhMucViewSet, NguyenLieuViewSet, MonAnViewSet, TheMonAnViewSet, LichSuKhoViewSet
from orders.views import DonHangViewSet
from reservations.views import BanAnViewSet, DatBanViewSet
from promotions.views import PromotionViewSet, PromotionCodeViewSet, PromotionUsageViewSet
from posts.views import PostViewSet, PostCategoryViewSet
from reviews.views import ReviewViewSet
from recommendations.views import InteractionViewSet, RecommendationViewSet
from chat.views import ChatRoomViewSet
from analytics.views import NotificationViewSet, DashboardViewSet
from branches.views import BranchViewSet
from payments.views import PaymentViewSet, PhieuHoanTienViewSet
from carts.views import CartViewSet


router = DefaultRouter()

# 1. Accounts
router.register("auth", XacThucViewSet, basename="auth")
router.register("xac-thuc", XacThucViewSet, basename="xac-thuc")
router.register("users", NguoiDungViewSet, basename="user")
router.register("nguoi-dung", NguoiDungViewSet, basename="nguoi-dung")
router.register("roles", VaiTroViewSet, basename="role")
router.register("vai-tro", VaiTroViewSet, basename="vai-tro")
router.register("permissions", QuyenHanViewSet, basename="permission")

# 2. Foods
router.register("foods", MonAnViewSet, basename="food")
router.register("mon-an", MonAnViewSet, basename="mon-an")
router.register("categories", DanhMucViewSet, basename="category")
router.register("danh-muc", DanhMucViewSet, basename="danh-muc")
router.register("tags", TheMonAnViewSet, basename="tag")
router.register("the-mon-an", TheMonAnViewSet, basename="the-mon-an")
router.register("ingredients", NguyenLieuViewSet, basename="ingredient")
router.register("nguyen-lieu", NguyenLieuViewSet, basename="nguyen-lieu")
router.register("inventory-transactions", LichSuKhoViewSet, basename="inventory-transaction")
router.register("kho", LichSuKhoViewSet, basename="kho")

# 3. Branches
router.register("branches", BranchViewSet, basename="branch")
router.register("chi-nhanh", BranchViewSet, basename="chi-nhanh")

# 4. Tables & Reservations
router.register("tables", BanAnViewSet, basename="table")
router.register("ban-an", BanAnViewSet, basename="ban-an")
router.register("reservations", DatBanViewSet, basename="reservation")
router.register("dat-ban", DatBanViewSet, basename="dat-ban")

# 5. Orders
router.register("orders", DonHangViewSet, basename="order")
router.register("don-hang", DonHangViewSet, basename="don-hang")

# 6. Payments
router.register("payments", PaymentViewSet, basename="payment")
router.register("thanh-toan", PaymentViewSet, basename="thanh-toan")
router.register("refund-receipts", PhieuHoanTienViewSet, basename="refund-receipt")
router.register("phieu-hoan-tien", PhieuHoanTienViewSet, basename="phieu-hoan-tien")

# 7. Promotions
router.register("promotions", PromotionViewSet, basename="promotion")
router.register("khuyen-mai", PromotionViewSet, basename="khuyen-mai")
router.register("promotion-codes", PromotionCodeViewSet, basename="promotion-code")
router.register("promotion-usages", PromotionUsageViewSet, basename="promotion-usage")

# 8. Carts
router.register("cart", CartViewSet, basename="cart")
router.register("gio-hang", CartViewSet, basename="gio-hang")

# 9. Reviews
router.register("reviews", ReviewViewSet, basename="review")
router.register("danh-gia", ReviewViewSet, basename="danh-gia")

# 10. Posts
router.register("posts", PostViewSet, basename="post")
router.register("bai-viet", PostViewSet, basename="bai-viet")
router.register("post-categories", PostCategoryViewSet, basename="post-category")
router.register("danh-muc-bai-viet", PostCategoryViewSet, basename="danh-muc-bai-viet")

# 11. Chat
router.register("chat/rooms", ChatRoomViewSet, basename="chat-room")
router.register("chat/conversations", ChatRoomViewSet, basename="chat-conversation")
router.register("hoi-thoai", ChatRoomViewSet, basename="hoi-thoai")

# 12. Recommendations
router.register("recommendations", RecommendationViewSet, basename="recommendation")
router.register("goi-y", RecommendationViewSet, basename="goi-y")
router.register("interactions", InteractionViewSet, basename="interaction")
router.register("tuong-tac", InteractionViewSet, basename="tuong-tac")

# 13. Analytics & Notifications
router.register("notifications", NotificationViewSet, basename="notification")
router.register("thong-bao", NotificationViewSet, basename="thong-bao")
router.register("analytics/dashboard", DashboardViewSet, basename="dashboard")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/login/", DangNhapTokenView.as_view(), name="token-obtain-pair"),
    path("auth/dang-nhap/", DangNhapTokenView.as_view(), name="token-obtain-pair-vn"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/lam-moi/", TokenRefreshView.as_view(), name="token-refresh-vn"),
    path("analytics/ai/", DashboardViewSet.as_view({"get": "ai"}), name="analytics-ai"),
    path("analytics/settings/", DashboardViewSet.as_view({"get": "restaurant_settings", "put": "restaurant_settings"}), name="analytics-settings"),

    # Explicit VNPay dual endpoints
    path("payments/vnpay/create/", PaymentViewSet.as_view({"post": "vnpay_create"}), name="vnpay-create-en"),
    path("thanh-toan/vnpay/create/", PaymentViewSet.as_view({"post": "vnpay_create"}), name="vnpay-create-vn"),
    path("payments/vnpay/tao-phien/", PaymentViewSet.as_view({"post": "vnpay_tao_phien"}), name="vnpay-tao-phien-en"),
    path("thanh-toan/vnpay/tao-phien/", PaymentViewSet.as_view({"post": "vnpay_tao_phien"}), name="vnpay-tao-phien-vn"),
    path("payments/vnpay/return/", PaymentViewSet.as_view({"get": "vnpay_return"}), name="vnpay-return-en"),
    path("thanh-toan/vnpay/return/", PaymentViewSet.as_view({"get": "vnpay_return"}), name="vnpay-return-vn"),
    path("payments/vnpay/ipn/", PaymentViewSet.as_view({"get": "vnpay_ipn"}), name="vnpay-ipn-en"),
    path("thanh-toan/vnpay/ipn/", PaymentViewSet.as_view({"get": "vnpay_ipn"}), name="vnpay-ipn-vn"),

    # Explicit Table Concurrency dual endpoints
    path("tables/<int:pk>/giu_ban/", BanAnViewSet.as_view({"post": "giu_ban"}), name="table-giu-ban-en"),
    path("ban-an/<int:pk>/giu_ban/", BanAnViewSet.as_view({"post": "giu_ban"}), name="table-giu-ban-vn"),
    path("tables/<int:pk>/giu-ban/", BanAnViewSet.as_view({"post": "giu_ban"}), name="table-giu-ban-hyphen-en"),
    path("ban-an/<int:pk>/giu-ban/", BanAnViewSet.as_view({"post": "giu_ban"}), name="table-giu-ban-hyphen-vn"),
    path("dat-ban/giu-ban/", DatBanViewSet.as_view({"post": "giu_ban_frontend"}), name="dat-ban-giu-ban-list-vn"),
    path("reservations/giu-ban/", DatBanViewSet.as_view({"post": "giu_ban_frontend"}), name="dat-ban-giu-ban-list-en"),
    path("dat-ban/giu_ban/", DatBanViewSet.as_view({"post": "giu_ban_frontend"}), name="dat-ban-giu-ban-list-underscore-vn"),
    path("reservations/giu_ban/", DatBanViewSet.as_view({"post": "giu_ban_frontend"}), name="dat-ban-giu-ban-list-underscore-en"),

    # Explicit Recommendation dual endpoints
    path("recommendations/tuong-tac/", InteractionViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-tuong-tac"),
    path("recommendations/interactions/", InteractionViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-interactions"),
    path("goi-y/tuong-tac/", InteractionViewSet.as_view({"get": "list", "post": "create"}), name="goi-y-tuong-tac"),
    path("recommendations/lam-moi/", RecommendationViewSet.as_view({"get": "refresh", "post": "refresh"}), name="recommendations-lam-moi-explicit"),
    path("goi-y/lam-moi/", RecommendationViewSet.as_view({"get": "refresh", "post": "refresh"}), name="goi-y-lam-moi-explicit"),

    path("", include(router.urls)),
]

