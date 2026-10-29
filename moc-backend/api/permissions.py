from rest_framework.permissions import BasePermission, SAFE_METHODS


class LaNhanVienNhaHang(BasePermission):
    MODULES = (
        ("orders", "orders"), ("orders", "don-hang"),
        ("reservations", "reservations"), ("reservations", "dat-ban"),
        ("tables", "tables"), ("tables", "ban-an"),
        ("foods", "foods"), ("foods", "mon-an"),
        ("categories", "categories"), ("categories", "danh-muc"),
        ("ingredients", "ingredients"), ("ingredients", "nguyen-lieu"), ("ingredients", "kho"), ("ingredients", "inventory-transactions"),
        ("promotions", "promotions"), ("promotions", "khuyen-mai"),
        ("posts", "posts"), ("posts", "bai-viet"),
        ("reviews", "reviews"), ("reviews", "danh-gia"),
        ("payments", "payments"), ("payments", "thanh-toan"), ("payments", "refund-receipts"),
        ("chat", "chat"), ("chat", "hoi-thoai"),
        ("branches", "branches"), ("branches", "chi-nhanh"),
        ("users", "users"), ("users", "nguoi-dung"),
        ("roles", "roles"), ("roles", "vai-tro"),
        ("dashboard", "analytics/dashboard"), ("ai", "analytics/ai"), ("settings", "analytics/settings"),
    )

    def has_permission(self, request, view):
        user = request.user
        is_staff = bool(user and user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False)))
        if not is_staff:
            return False
        if user.is_superuser or getattr(user, "la_quan_tri_vien", False):
            return True

        path = request.path_info.lower()
        if "record-refund" in path:
            module = "payments"
        elif "chinh_sach_coc" in path or "chinh-sach-coc" in path:
            module = "deposit"
        else:
            module = next((name for name, fragment in self.MODULES if fragment in path), None)
        if not module:
            return True
        if module in {"dashboard", "ai"} or (module == "settings" and request.method == "GET"):
            action = "view"
        elif module == "deposit":
            action = "view" if request.method == "GET" else "update"
        elif request.method in {"GET", "HEAD", "OPTIONS"}:
            action = "view"
        elif "record-refund" in path:
            action = "update"
        elif request.method == "POST" and path.rstrip("/").endswith(("/messages", "/mark_read", "/mark_success")):
            action = "create" if path.rstrip("/").endswith("/messages") else "update"
        else:
            action = {"POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}.get(request.method, "view")

        role_ids = list(user.danh_sach_vai_tro.values_list("id", flat=True))
        if not role_ids:
            return True
        from accounts.models import VaiTroQuyenHan
        explicit = VaiTroQuyenHan.objects.filter(vai_tro_id__in=role_ids, quyen_han__ma_quyen__startswith=f"{module}.")
        if not explicit.exists():
            return True
        return explicit.filter(quyen_han__ma_quyen=f"{module}.{action}").exists()


class LaNhanVienHoacChiDoc(LaNhanVienNhaHang):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            user = request.user
            if not (user and user.is_authenticated and (user.is_staff or getattr(user, "la_nhan_vien_nha_hang", False))):
                return True
        return super().has_permission(request, view)


# Backward-compatible permission aliases
IsRestaurantStaff = LaNhanVienNhaHang
IsStaffOrReadOnly = LaNhanVienHoacChiDoc
