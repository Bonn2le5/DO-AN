import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

export default function AdminLayout() {
  const { user, logout } = useAuthStore();
  const location = useLocation();

  const navItems = [
    { name: "Tổng quan", path: "/admin", icon: "📊" },
    { name: "Đơn hàng", path: "/admin/orders", icon: "🛍️" },
    { name: "Đặt bàn", path: "/admin/reservations", icon: "📅" },
    { name: "Thực đơn & Kho", path: "/admin/menu", icon: "🍲" },
    { name: "Đánh giá", path: "/admin/reviews", icon: "⭐" },
    { name: "Hỗ trợ khách", path: "/admin/chat", icon: "💬" },
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r flex flex-col hidden md:flex">
        <div className="p-6 border-b">
          <Link to="/" className="text-xl font-bold text-primary flex items-center gap-2">
            <span>Mộc Quán</span>
            <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">Admin</span>
          </Link>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path || 
              (item.path !== "/admin" && location.pathname.startsWith(item.path));
              
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                  isActive 
                    ? "bg-primary/10 text-primary font-medium" 
                    : "text-gray-600 hover:bg-gray-100"
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
              {user?.avatarInitial || "A"}
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <span>🚪</span> Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden bg-white border-b p-4 flex justify-between items-center">
          <span className="font-bold">Mộc Quán Admin</span>
          <button className="text-gray-500">☰</button>
        </header>
        
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}