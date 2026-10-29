import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export default function AdminGuard() {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/dang-nhap" replace />;
  }

  const isStaff =
    Boolean(user?.isStaff) ||
    Boolean(user?.laNhanVien) ||
    Boolean((user as any)?.is_superuser) ||
    Boolean((user as any)?.is_restaurant_staff) ||
    user?.roles?.some((role: string) =>
      ["admin", "staff", "nhan_vien", "quan_tri_vien", "QUAN_LY", "ADMIN", "BEP", "PHUC_VU"].includes(String(role).toLowerCase())
    ) ||
    user?.danhSachVaiTro?.some((role: string) =>
      ["admin", "staff", "nhan_vien", "quan_tri_vien", "QUAN_LY", "ADMIN", "BEP", "PHUC_VU"].includes(String(role).toLowerCase())
    );

  if (!isStaff) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-100">
        <div className="text-center bg-white p-8 rounded-lg shadow">
          <h1 className="text-4xl font-bold text-red-500 mb-4">403</h1>
          <h2 className="text-xl font-semibold mb-2">Truy cập bị từ chối</h2>
          <p className="text-gray-600 mb-6">
            Bạn không có quyền truy cập vào khu vực này.
          </p>
          <a
            href="/"
            className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 transition-colors"
          >
            Về trang chủ
          </a>
        </div>
      </div>
    );
  }

  return <Outlet />;
}
