"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def home_view(request):
    return JsonResponse(
        {
            "project": "Web App Quản lý Nhà hàng Mộc (Mộc Restaurant API)",
            "version": "1.0.0",
            "status": "online",
            "message": "Backend API đang hoạt động bình thường! Để xem giao diện người dùng & đặt món, hãy mở terminal chạy 'npm run dev' tại thư mục moc-frontend và truy cập http://localhost:5173",
            "frontend_url": "http://localhost:5173",
            "endpoints": {
                "admin": request.build_absolute_uri("/admin/"),
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


urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]
