from rest_framework.permissions import BasePermission, SAFE_METHODS


class LaNhanVienNhaHang(BasePermission):
    """Role-based API allowlist for restaurant employees and branch managers."""

    # Nhóm quyền theo đoạn đầu của đường dẫn sau /api/ (tên tiếng Anh cũ và tên tiếng Việt).
    # Khớp nguyên đoạn thay vì tìm chuỗi con, để "chat/rooms" không bị hiểu là bàn
    # và route mới quên khai báo sẽ bị chặn (test đối chiếu sẽ báo).
    SEGMENTS = {
        "orders": "orders", "don-hang": "orders",
        "reservations": "reservations", "dat-ban": "reservations",
        "dining-sessions": "dining_sessions", "phien-phuc-vu": "dining_sessions",
        "tables": "tables", "ban-an": "tables", "rooms": "tables", "phong-rieng": "tables",
        "foods": "foods", "mon-an": "foods", "tags": "foods", "the-mon-an": "foods",
        "categories": "categories", "danh-muc": "categories",
        "ingredients": "ingredients", "nguyen-lieu": "ingredients", "kho": "ingredients",
        "inventory-transactions": "ingredients", "dinh-muc-nguyen-lieu": "ingredients", "ton-kho": "ingredients",
        "promotions": "promotions", "khuyen-mai": "promotions", "promotion-codes": "promotions",
        "ma-khuyen-mai": "promotions", "promotion-usages": "promotions", "lich-su-khuyen-mai": "promotions",
        "posts": "posts", "bai-viet": "posts", "post-categories": "posts", "danh-muc-bai-viet": "posts",
        "reviews": "reviews", "danh-gia": "reviews",
        "payments": "payments", "thanh-toan": "payments", "refund-receipts": "payments", "phieu-hoan-tien": "payments",
        "chat": "chat", "hoi-thoai": "chat",
        # Báo món tạm hết theo chi nhánh: việc vận hành trong ca của nhân viên và quản lý.
        "tinh-trang-mon": "food_status",
        "branches": "branches", "chi-nhanh": "branches",
        "users": "users", "nguoi-dung": "users",
        "roles": "roles", "vai-tro": "roles", "permissions": "roles", "quyen-han": "roles",
    }
    # Hai đoạn đầu cho nhóm thống kê.
    SUB_SEGMENTS = {
        ("analytics", "dashboard"): "dashboard", ("thong-ke", "tong-quan"): "dashboard",
        ("analytics", "ai"): "ai", ("thong-ke", "ai"): "ai",
        ("analytics", "settings"): "settings", ("thong-ke", "cai-dat"): "settings",
    }
    REFUND_RECEIPTS = ("refund-receipts", "phieu-hoan-tien")
    RECORD_REFUND = ("record-refund", "ghi-nhan-hoan-tien")

    @classmethod
    def module_for(cls, path):
        parts = [p for p in path.lower().split("/") if p]
        if parts and parts[0] == "api":
            parts = parts[1:]
        if not parts:
            return None
        if any(p in cls.RECORD_REFUND for p in parts):
            return "payments"
        if any(p in ("chinh_sach_coc", "chinh-sach-coc") for p in parts):
            return "deposit"
        if len(parts) > 1 and (parts[0], parts[1]) in cls.SUB_SEGMENTS:
            return cls.SUB_SEGMENTS[(parts[0], parts[1])]
        return cls.SEGMENTS.get(parts[0])

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not getattr(user, "la_nhan_vien_nha_hang", False):
            return False
        if user.is_superuser or getattr(user, "la_quan_tri_vien", False):
            return True

        path = request.path_info.lower()
        module = self.module_for(path)
        if not module:
            return False

        is_manager = bool(getattr(user, "la_quan_ly_chi_nhanh", False))
        if any(f in path for f in self.REFUND_RECEIPTS) and not is_manager:
            return False
        # foods/categories/promotions chỉ đọc: cần để gọi món trong phiên phục vụ.
        # ingredients chỉ đọc với nhân viên: để thấy cảnh báo nguyên liệu sắp hết.
        # chat: nhân viên và quản lý trả lời khách của chi nhánh mình (lọc theo chi nhánh trong view).
        allowed = {"orders", "reservations", "dining_sessions", "payments", "branches", "foods", "categories", "promotions", "ingredients", "food_status", "chat"}
        if is_manager:
            # Quản lý chi nhánh: sơ đồ bàn/phòng, tổng quan, kho nguyên liệu và nhân viên chi nhánh mình.
            allowed.update({"dashboard", "tables", "users"})
        if module not in allowed:
            return False
        if module in {"branches", "foods", "categories", "promotions"}:
            return request.method in SAFE_METHODS
        if module == "ingredients":
            if request.method in SAFE_METHODS:
                return True
            # Danh mục nguyên liệu và định mức món dùng chung: chỉ quản trị viên sửa.
            # Tồn kho tách theo chi nhánh: quản lý chi nhánh lập phiếu nhập/xuất/kiểm kê, chuyển kho
            # và sửa mức tối thiểu — view kiểm tra đúng chi nhánh được phân công.
            phan_dau = [p for p in path.split("/") if p and p != "api"][:1]
            if not is_manager:
                return False
            if request.method == "POST":
                return phan_dau in (["kho"], ["inventory-transactions"])
            return request.method == "PATCH" and phan_dau == ["ton-kho"]
        if module == "dashboard":
            return is_manager and request.method in SAFE_METHODS

        if request.method in SAFE_METHODS:
            return True
        if any(f in path for f in self.RECORD_REFUND) or path.rstrip("/").endswith(("/mark_success", "/xac_nhan_thanh_cong")):
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
