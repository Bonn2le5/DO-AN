from rest_framework.permissions import BasePermission, SAFE_METHODS


class LaNhanVienNhaHang(BasePermission):
    """Role-based API allowlist for restaurant employees and branch managers."""

    MODULES = (
        ("orders", ("orders", "don-hang")),
        ("reservations", ("reservations", "dat-ban")),
        ("dining_sessions", ("dining-sessions", "phien-phuc-vu")),
        ("tables", ("tables", "ban-an", "rooms")),
        ("foods", ("foods", "mon-an")),
        ("categories", ("categories", "danh-muc")),
        ("ingredients", ("ingredients", "nguyen-lieu", "kho", "inventory-transactions")),
        ("promotions", ("promotions", "khuyen-mai")),
        ("posts", ("posts", "bai-viet")),
        ("reviews", ("reviews", "danh-gia")),
        ("payments", ("payments", "thanh-toan", "refund-receipts")),
        ("chat", ("chat", "hoi-thoai")),
        ("branches", ("branches", "chi-nhanh")),
        ("users", ("users", "nguoi-dung")),
        ("roles", ("roles", "vai-tro")),
        ("dashboard", ("analytics/dashboard",)),
        ("ai", ("analytics/ai",)),
        ("settings", ("analytics/settings",)),
    )

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not getattr(user, "la_nhan_vien_nha_hang", False):
            return False
        if user.is_superuser or getattr(user, "la_quan_tri_vien", False):
            return True

        path = request.path_info.lower()
        if "record-refund" in path:
            module = "payments"
        elif "chinh_sach_coc" in path or "chinh-sach-coc" in path:
            module = "deposit"
        else:
            module = next((name for name, fragments in self.MODULES if any(fragment in path for fragment in fragments)), None)
        if not module:
            return False

        is_manager = bool(getattr(user, "la_quan_ly_chi_nhanh", False))
        if "refund-receipts" in path and not is_manager:
            return False
        # foods/categories/promotions chỉ đọc: cần để gọi món trong phiên phục vụ.
        allowed = {"orders", "reservations", "dining_sessions", "payments", "branches", "foods", "categories", "promotions"}
        if is_manager:
            # Quản lý chi nhánh được cấu hình sơ đồ bàn/phòng của chi nhánh mình;
            # nhân viên chỉ vận hành phiên phục vụ và đơn tại bàn.
            allowed.update({"dashboard", "tables"})
        if module not in allowed:
            return False
        if module in {"branches", "foods", "categories", "promotions"}:
            return request.method in SAFE_METHODS
        if module == "dashboard":
            return is_manager and request.method in SAFE_METHODS

        if request.method in SAFE_METHODS:
            return True
        if "record-refund" in path or path.rstrip("/").endswith(("/mark_success", "/xac_nhan_thanh_cong")):
            action = "update"
        elif request.method == "POST":
            action = "create"
        else:
            action = "update" if request.method in {"PUT", "PATCH"} else "delete" if request.method == "DELETE" else "view"

        if module == "payments" and not is_manager:
            return action in {"view", "create"} or (
                action == "update" and path.rstrip("/").endswith(("/mark_success", "/xac_nhan_thanh_cong"))
            )
        if module == "tables" and is_manager:
            return action in {"view", "create", "update", "delete"}
        return action in {"view", "create", "update"}


class LaNhanVienHoacChiDoc(LaNhanVienNhaHang):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            user = request.user
            if not (user and user.is_authenticated and getattr(user, "la_nhan_vien_nha_hang", False)):
                return True
        return super().has_permission(request, view)


# Backward-compatible permission aliases
IsRestaurantStaff = LaNhanVienNhaHang
IsStaffOrReadOnly = LaNhanVienHoacChiDoc
