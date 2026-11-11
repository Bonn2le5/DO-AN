"""
URL configuration for config project.
"""
from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve as serve_media
from django.http import HttpResponse, JsonResponse


def home_view(request):
    return JsonResponse(
        {
            "project": "Web App Quản lý Nhà hàng Mộc (Mộc Restaurant API)",
            "version": "1.0.0",
            "status": "online",
            "message": "Backend API đang hoạt động bình thường! Để xem giao diện người dùng & đặt món, hãy mở terminal chạy 'npm run dev' tại thư mục moc-frontend và truy cập http://localhost:5173",
            "frontend_url": "http://localhost:5173",
            "endpoints": {
                "api_root": request.build_absolute_uri("/api/"),
                "health": request.build_absolute_uri("/api/health/"),
                "foods": request.build_absolute_uri("/api/foods/"),
                "tables": request.build_absolute_uri("/api/tables/"),
                "reservations": request.build_absolute_uri("/api/reservations/"),
                "orders": request.build_absolute_uri("/api/orders/"),
                "recommendations": request.build_absolute_uri("/api/recommendations/"),
            },
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


_dang_nhap_admin_goc = admin.site.login


def _dang_nhap_admin_co_gioi_han(request, extra_context=None):
    """Trang đăng nhập admin của Django không đi qua DRF nên tự áp giới hạn dò mật khẩu theo IP."""
    if request.method == "POST":
        from api.throttling import GioiHanDangNhapAdmin
        gioi_han = GioiHanDangNhapAdmin()
        if not gioi_han.allow_request(request, None):
            return HttpResponse(
                f"Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau {gioi_han.wait()} giây.",
                status=429, content_type="text/plain; charset=utf-8",
            )
    return _dang_nhap_admin_goc(request, extra_context)


admin.site.login = _dang_nhap_admin_co_gioi_han  # phải gán trước khi admin.site.urls được đọc

urlpatterns = [
    path("", home_view, name="home"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/", include("api.urls")),
    re_path(r"^media/(?P<path>.*)$", serve_media, {"document_root": settings.MEDIA_ROOT}),
]
