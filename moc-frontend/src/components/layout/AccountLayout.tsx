import { NavLink, Outlet, Navigate, Link } from "react-router-dom";
import { User, Package, Heart, LogOut, ShieldCheck } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";

const TABS = [
  { to: "/tai-khoan", label: "Hồ sơ", icon: User, end: true },
  { to: "/tai-khoan/don-hang", label: "Đơn hàng", icon: Package, end: false },
  { to: "/tai-khoan/yeu-thich", label: "Yêu thích", icon: Heart, end: false },
];

export default function AccountLayout() {
  const { isAuthenticated, user, logout } = useAuthStore();

  if (!isAuthenticated) return <Navigate to="/dang-nhap" replace />;

  return (
    <div className="max-w-275 mx-auto px-5 md:px-8 py-12">
      <div className="flex items-center gap-4 mb-10">
        <div className="w-14 h-14 rounded-full bg-primary text-white font-display text-xl flex items-center justify-center">
          {user?.avatarInitial}
        </div>
        <div>
          <h1 className="font-display text-2xl">{user?.name}</h1>
          <p className="text-sm text-muted">{user?.email}</p>
        </div>
      </div>

      <div className="grid md:grid-cols-[220px_1fr] gap-10">
        <aside className="space-y-1.5">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors",
                  isActive ? "bg-dark text-white" : "hover:bg-black/5",
                )
              }
            >
              <tab.icon width={16} height={16} />
              {tab.label}
            </NavLink>
          ))}
          {user?.isStaff && (
            <Link
              to="/admin"
              className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold text-primary bg-primary/10 hover:bg-primary/20 transition-colors mt-2"
            >
              <ShieldCheck width={16} height={16} />
              Quản Trị Nhà Hàng
            </Link>
          )}
          <button
            onClick={logout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-primary hover:bg-primary/5 w-full mt-4"
          >
            <LogOut width={16} height={16} />
            Đăng xuất
          </button>
        </aside>
        <div>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
