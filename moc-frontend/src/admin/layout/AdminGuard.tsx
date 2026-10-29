import { Link, Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { PREVIEW, useRole } from "../permissions";

/** Chặn truy cập /quan-tri nếu chưa đăng nhập hoặc không phải staff/admin. Quyền thật vẫn do backend kiểm tra. */
export default function AdminGuard() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const role = useRole();

  if (PREVIEW) return <Outlet />;
  if (!isAuthenticated) return <Navigate to="/dang-nhap" replace />;
  if (!role) {
    return (
      <div className="max-w-md mx-auto px-5 py-28 text-center">
        <h1 className="font-display text-2xl mb-3">Bạn chưa có quyền truy cập</h1>
        <p className="text-muted mb-8">Khu vực này chỉ dành cho nhân viên và quản trị viên của MỘC.</p>
        <Link to="/" className="btn btn-primary">Về trang chủ</Link>
      </div>
    );
  }
  return <Outlet />;
}
