import { Suspense, useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import {
  ExternalLink,
  LogOut,
  Menu,
} from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import { useChatInbox } from "@/hooks/useChatInbox";
import AdminSidebar from "./AdminSidebar";
import { Toaster, useToast } from "../components/toast";
import { PREVIEW, usePreviewRole, useRole } from "../permissions";
import { inputCls } from "../components/primitives";
import type { RoleName } from "../types";

export default function AdminLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { pathname } = useLocation();
  const { nguoiDung: user, dangXuat: logout } = useAuthStore();
  const isAuthenticated = useAuthStore((s) => s.daDangNhap);
  const pushToast = useToast((s) => s.push);
  const role = useRole();
  const { role: previewRole, setRole } = usePreviewRole();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);

  // Một kết nối WebSocket duy nhất cho toàn khu admin (thay cho polling 3s).
  const inbox = useChatInbox(isAuthenticated && role === "admin", (item, message) => {
    if (/\/chat\/?$/.test(window.location.pathname)) return; // đang ở trang chat thì không toast
    const text = String(message.content ?? "");
    const preview = text.length > 70 ? `${text.slice(0, 67)}…` : text;
    const notice = `${item.customerName} vừa nhắn: ${preview}`;
    pushToast(notice);
    if (
      document.visibilityState === "hidden" &&
      "Notification" in window &&
      Notification.permission === "granted"
    ) {
      new Notification("Tin nhắn khách hàng mới", { body: notice });
    }
  });

  return (
    <div className="admin-ui min-h-screen flex bg-bg">
      <AdminSidebar
        open={menuOpen}
        collapsed={sidebarCollapsed}
        onClose={() => setMenuOpen(false)}
      />
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-40 h-16 px-4 md:px-8 flex items-center gap-3 bg-bg/90 backdrop-blur border-b border-black/[0.07]">
          {/* Một nút duy nhất: desktop ẩn/hiện sidebar, mobile mở sidebar dạng ngăn kéo. */}
          <button
            className="icon-btn"
            onClick={() => {
              if (window.matchMedia("(min-width: 1024px)").matches) setSidebarCollapsed((c) => !c);
              else setMenuOpen(true);
            }}
            aria-label="Menu điều hướng"
            title={sidebarCollapsed ? "Hiện thanh điều hướng" : "Ẩn thanh điều hướng"}
          >
            <Menu width={20} height={20} />
          </button>
          <div className="ml-auto flex items-center gap-3">
            {PREVIEW && (
              <label className="flex items-center gap-2 text-[13px] text-muted">
                Xem với vai trò
                <select
                  value={previewRole}
                  onChange={(e) => setRole(e.target.value as RoleName)}
                  className={`${inputCls} w-auto! py-1.5!`}
                >
                  <option value="admin">Quản trị viên</option>
                  <option value="branch_manager">Quản lý chi nhánh</option>
                  <option value="staff">Nhân viên</option>
                </select>
              </label>
            )}
            <Link
              to="/"
              className="hidden sm:flex items-center gap-1.5 text-sm text-muted hover:text-primary"
            >
              <ExternalLink width={14} height={14} />
              Xem website
            </Link>
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                {user?.kyTuDaiDien ?? (role === "admin" ? "A" : "N")}
              </span>
              <div className="hidden md:block leading-tight">
                <div className="text-sm font-semibold">
                  {user?.hoTen ??
                    (role === "admin" ? "Quản trị viên" : "Nhân viên")}
                </div>
                <div className="text-xs text-muted">
                  {role === "admin" ? "Quản trị viên" : role === "branch_manager" ? "Quản lý chi nhánh" : "Nhân viên"}
                </div>
              </div>
              {!PREVIEW && (
                <button
                  className="icon-btn"
                  onClick={logout}
                  aria-label="Đăng xuất"
                >
                  <LogOut width={17} height={17} />
                </button>
              )}
            </div>
          </div>
        </header>
        <main className="flex-1 px-4 md:px-8 py-8 max-w-[1280px] w-full">
          <Suspense
            fallback={
              <div className="text-muted text-sm py-20 text-center">
                Đang tải…
              </div>
            }
          >
            <Outlet context={inbox} />
          </Suspense>
        </main>
      </div>
      <Toaster />
    </div>
  );
}
