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
from foods.views import DanhMucViewSet, NguyenLieuViewSet, MonAnViewSet, TheMonAnViewSet, LichSuKhoViewSet, DinhMucNguyenLieuViewSet
from orders.views import DonHangViewSet
from reservations.views import BanAnViewSet, DatBanViewSet, PhongRiengViewSet, PhienPhucVuViewSet
from promotions.views import KhuyenMaiViewSet, MaKhuyenMaiViewSet, LichSuDungKhuyenMaiViewSet
from posts.views import BaiVietViewSet, DanhMucBaiVietViewSet
from reviews.views import DanhGiaViewSet
from recommendations.views import TuongTacMonAnViewSet, GoiYMonAnViewSet
from chat.views import HoiThoaiViewSet
from analytics.views import ThongBaoViewSet, TongQuanViewSet
from branches.views import ChiNhanhViewSet
from payments.views import ThanhToanViewSet, PhieuHoanTienViewSet


router = DefaultRouter()

# 1. Accounts
router.register("auth", XacThucViewSet, basename="auth")
router.register("xac-thuc", XacThucViewSet, basename="xac-thuc")
router.register("users", NguoiDungViewSet, basename="user")
router.register("nguoi-dung", NguoiDungViewSet, basename="nguoi-dung")
router.register("roles", VaiTroViewSet, basename="role")
router.register("vai-tro", VaiTroViewSet, basename="vai-tro")
router.register("permissions", QuyenHanViewSet, basename="permission")
router.register("quyen-han", QuyenHanViewSet, basename="quyen-han")

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
router.register("dinh-muc-nguyen-lieu", DinhMucNguyenLieuViewSet, basename="dinh-muc-nguyen-lieu")

# 3. Branches
router.register("branches", ChiNhanhViewSet, basename="branch")
router.register("chi-nhanh", ChiNhanhViewSet, basename="chi-nhanh")

# 4. Tables & Reservations
router.register("tables", BanAnViewSet, basename="table")
router.register("rooms", PhongRiengViewSet, basename="room")
router.register("phong-rieng", PhongRiengViewSet, basename="phong-rieng")
router.register("ban-an", BanAnViewSet, basename="ban-an")
router.register("reservations", DatBanViewSet, basename="reservation")
router.register("dat-ban", DatBanViewSet, basename="dat-ban")
router.register("dining-sessions", PhienPhucVuViewSet, basename="dining-session")
router.register("phien-phuc-vu", PhienPhucVuViewSet, basename="phien-phuc-vu")

# 5. Orders
router.register("orders", DonHangViewSet, basename="order")
router.register("don-hang", DonHangViewSet, basename="don-hang")

# 6. Payments
router.register("payments", ThanhToanViewSet, basename="payment")
router.register("thanh-toan", ThanhToanViewSet, basename="thanh-toan")
router.register("refund-receipts", PhieuHoanTienViewSet, basename="refund-receipt")
router.register("phieu-hoan-tien", PhieuHoanTienViewSet, basename="phieu-hoan-tien")

# 7. Promotions
router.register("promotions", KhuyenMaiViewSet, basename="promotion")
router.register("khuyen-mai", KhuyenMaiViewSet, basename="khuyen-mai")
router.register("promotion-codes", MaKhuyenMaiViewSet, basename="promotion-code")
router.register("promotion-usages", LichSuDungKhuyenMaiViewSet, basename="promotion-usage")
router.register("ma-khuyen-mai", MaKhuyenMaiViewSet, basename="ma-khuyen-mai")
router.register("lich-su-khuyen-mai", LichSuDungKhuyenMaiViewSet, basename="lich-su-khuyen-mai")

# 9. Reviews
router.register("reviews", DanhGiaViewSet, basename="review")
router.register("danh-gia", DanhGiaViewSet, basename="danh-gia")

# 10. Posts
router.register("posts", BaiVietViewSet, basename="post")
router.register("bai-viet", BaiVietViewSet, basename="bai-viet")
router.register("post-categories", DanhMucBaiVietViewSet, basename="post-category")
router.register("danh-muc-bai-viet", DanhMucBaiVietViewSet, basename="danh-muc-bai-viet")

# 11. Chat
router.register("chat/rooms", HoiThoaiViewSet, basename="chat-room")
router.register("chat/conversations", HoiThoaiViewSet, basename="chat-conversation")
router.register("hoi-thoai", HoiThoaiViewSet, basename="hoi-thoai")

# 12. Recommendations
router.register("recommendations", GoiYMonAnViewSet, basename="recommendation")
router.register("goi-y", GoiYMonAnViewSet, basename="goi-y")
router.register("interactions", TuongTacMonAnViewSet, basename="interaction")
router.register("tuong-tac", TuongTacMonAnViewSet, basename="tuong-tac")

# 13. Analytics & Notifications
router.register("notifications", ThongBaoViewSet, basename="notification")
router.register("thong-bao", ThongBaoViewSet, basename="thong-bao")
router.register("analytics/dashboard", TongQuanViewSet, basename="dashboard")
router.register("thong-ke/tong-quan", TongQuanViewSet, basename="thong-ke-tong-quan")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("auth/login/", DangNhapTokenView.as_view(), name="token-obtain-pair"),
    path("auth/dang-nhap/", DangNhapTokenView.as_view(), name="token-obtain-pair-vn"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/lam-moi/", TokenRefreshView.as_view(), name="token-refresh-vn"),
    path("xac-thuc/dang-nhap/", DangNhapTokenView.as_view(), name="xac-thuc-dang-nhap"),
    path("xac-thuc/lam-moi/", TokenRefreshView.as_view(), name="xac-thuc-lam-moi"),
    path("analytics/ai/", TongQuanViewSet.as_view({"get": "ai"}), name="analytics-ai"),
    path("analytics/settings/", TongQuanViewSet.as_view({"get": "restaurant_settings", "put": "restaurant_settings"}), name="analytics-settings"),
    path("thong-ke/ai/", TongQuanViewSet.as_view({"get": "ai"}), name="thong-ke-ai"),
    path("thong-ke/cai-dat/", TongQuanViewSet.as_view({"get": "restaurant_settings", "put": "restaurant_settings"}), name="thong-ke-cai-dat"),

    # PayOS
    path("thanh-toan/payos/tao-phien/", ThanhToanViewSet.as_view({"post": "payos_tao_phien"}), name="payos-tao-phien-vn"),
    path("thanh-toan/payos/return/", ThanhToanViewSet.as_view({"get": "payos_return"}), name="payos-return-vn"),
    path("thanh-toan/payos/webhook/", ThanhToanViewSet.as_view({"post": "payos_webhook"}), name="payos-webhook-vn"),

    # Explicit Recommendation dual endpoints
    path("recommendations/tuong-tac/", TuongTacMonAnViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-tuong-tac"),
    path("recommendations/interactions/", TuongTacMonAnViewSet.as_view({"get": "list", "post": "create"}), name="recommendation-interactions"),
    path("goi-y/tuong-tac/", TuongTacMonAnViewSet.as_view({"get": "list", "post": "create"}), name="goi-y-tuong-tac"),
    path("recommendations/lam-moi/", GoiYMonAnViewSet.as_view({"get": "refresh", "post": "refresh"}), name="recommendations-lam-moi-explicit"),
    path("goi-y/lam-moi/", GoiYMonAnViewSet.as_view({"get": "refresh", "post": "refresh"}), name="goi-y-lam-moi-explicit"),

    path("", include(router.urls)),
]
