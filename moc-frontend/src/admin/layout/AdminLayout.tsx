import { Suspense, useEffect, useRef, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { ExternalLink, LogOut, Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useAuthStore } from "@/store/authStore";
import AdminSidebar from "./AdminSidebar";
import { Toaster, useToast } from "../components/toast";
import { PREVIEW, usePreviewRole, useRole } from "../permissions";
import { inputCls } from "../components/primitives";
import { chatStore } from "../api/admin.api";
import type { RoleName } from "../types";

export default function AdminLayout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { pathname } = useLocation();
  const { user, logout } = useAuthStore();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const pushToast = useToast((s) => s.push);
  const seenChatMessageIds = useRef<Set<string> | null>(null);
  const chatPollInFlight = useRef(false);
  const role = useRole();
  const { role: previewRole, setRole } = usePreviewRole();

  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let mounted = true;
    const poll = async () => {
      if (chatPollInFlight.current) return;
      chatPollInFlight.current = true;
      try {
        const rooms = await chatStore.list();
        if (!mounted) return;
        const previousIds = seenChatMessageIds.current;
        const nextIds = new Set<string>();
        const newMessages: { customer: string; text: string }[] = [];
        for (const room of rooms) {
          for (const message of room.messages) {
            const id = String(message.id);
            nextIds.add(id);
            if (previousIds && !previousIds.has(id) && message.from === "customer") {
              newMessages.push({ customer: room.customer, text: message.text });
            }
          }
        }
        seenChatMessageIds.current = nextIds;
        newMessages.slice(-3).forEach(({ customer, text }) => {
          const preview = text.length > 70 ? `${text.slice(0, 67)}…` : text;
          const notice = `${customer} vừa nhắn: ${preview}`;
          pushToast(notice);
          if (document.visibilityState === "hidden" && "Notification" in window && Notification.permission === "granted") {
            new Notification("Tin nhắn khách hàng mới", { body: notice });
          }
        });
        if (newMessages.length > 3) pushToast(`Có thêm ${newMessages.length - 3} tin nhắn mới từ khách hàng.`);
      } catch (error) {
        console.error("Không thể kiểm tra tin nhắn mới:", error);
      } finally {
        chatPollInFlight.current = false;
      }
    };

    void poll();
    const timer = window.setInterval(() => void poll(), 3000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [isAuthenticated, pushToast]);

  return (
    <div className="admin-ui min-h-screen flex bg-bg">
      <AdminSidebar open={menuOpen} collapsed={sidebarCollapsed} onClose={() => setMenuOpen(false)} />
      <div className="flex-1 min-w-0 flex flex-col">
        <header className="sticky top-0 z-40 h-16 px-4 md:px-8 flex items-center gap-3 bg-bg/90 backdrop-blur border-b border-black/[0.07]">
          <button className="lg:hidden icon-btn" onClick={() => setMenuOpen(true)} aria-label="Mở menu"><Menu width={20} height={20} /></button>
          <button className="hidden lg:inline-flex icon-btn" onClick={() => setSidebarCollapsed((collapsed) => !collapsed)} aria-label={sidebarCollapsed ? "Hiện thanh điều hướng" : "Ẩn thanh điều hướng"} title={sidebarCollapsed ? "Hiện thanh điều hướng" : "Ẩn thanh điều hướng"}>
            {sidebarCollapsed ? <PanelLeftOpen width={19} height={19} /> : <PanelLeftClose width={19} height={19} />}
          </button>
          <div className="ml-auto flex items-center gap-3">
            {PREVIEW && (
              <label className="flex items-center gap-2 text-[13px] text-muted">
                Xem với vai trò
                <select value={previewRole} onChange={(e) => setRole(e.target.value as RoleName)} className={`${inputCls} w-auto! py-1.5!`}>
                  <option value="admin">Quản trị viên</option>
                  <option value="staff">Nhân viên</option>
                </select>
              </label>
            )}
            <Link to="/" className="hidden sm:flex items-center gap-1.5 text-sm text-muted hover:text-primary"><ExternalLink width={14} height={14} />Xem website</Link>
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">{user?.avatarInitial ?? (role === "admin" ? "A" : "N")}</span>
              <div className="hidden md:block leading-tight">
                <div className="text-sm font-semibold">{user?.name ?? (role === "admin" ? "Quản trị viên" : "Nhân viên")}</div>
                <div className="text-xs text-muted">{role === "admin" ? "Quản trị viên" : "Nhân viên"}</div>
              </div>
              {!PREVIEW && <button className="icon-btn" onClick={logout} aria-label="Đăng xuất"><LogOut width={17} height={17} /></button>}
            </div>
          </div>
        </header>
        <main className="flex-1 px-4 md:px-8 py-8 max-w-[1280px] w-full">
          <Suspense fallback={<div className="text-muted text-sm py-20 text-center">Đang tải…</div>}>
            <Outlet />
          </Suspense>
        </main>
      </div>
      <Toaster />
    </div>
  );
}
