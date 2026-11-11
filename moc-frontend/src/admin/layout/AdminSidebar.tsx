import { Link, NavLink } from "react-router-dom";
import {
  LayoutDashboard, ShoppingBag, CalendarDays, Armchair, MessageCircle, UtensilsCrossed, Tag, Package, Percent,
  Newspaper, Star, CreditCard, Landmark, MapPin, Users, ShieldCheck, Sparkles, Settings, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCan, useRole } from "../permissions";
import type { Module } from "../types";

type Item = { to: string; label: string; icon: typeof Tag; module: Module; end?: boolean };
const GROUPS: { title: string; items: Item[] }[] = [
  { title: "Vận hành", items: [
    { to: "/admin", label: "Tổng quan", icon: LayoutDashboard, module: "dashboard", end: true },
    { to: "/admin/don-hang", label: "Đơn hàng", icon: ShoppingBag, module: "orders" },
    { to: "/admin/dat-ban", label: "Đặt bàn", icon: CalendarDays, module: "reservations" },
    { to: "/admin/ban-an", label: "Sơ đồ bàn", icon: Armchair, module: "tables" },
    { to: "/admin/hoi-thoai", label: "Chat khách hàng", icon: MessageCircle, module: "chat" },
  ] },
  { title: "Thực đơn", items: [
    { to: "/admin/mon-an", label: "Món ăn", icon: UtensilsCrossed, module: "foods" },
    { to: "/admin/danh-muc", label: "Danh mục & tag", icon: Tag, module: "categories" },
    { to: "/admin/nguyen-lieu", label: "Nguyên liệu & kho", icon: Package, module: "ingredients" },
  ] },
  { title: "Tiếp thị", items: [
    { to: "/admin/khuyen-mai", label: "Khuyến mãi", icon: Percent, module: "promotions" },
    { to: "/admin/bai-viet", label: "Bài viết", icon: Newspaper, module: "posts" },
    { to: "/admin/danh-gia", label: "Đánh giá", icon: Star, module: "reviews" },
  ] },
  { title: "Tài chính", items: [
    { to: "/admin/thanh-toan", label: "Hóa đơn & thanh toán", icon: CreditCard, module: "payments" },
    { to: "/admin/chinh-sach-coc", label: "Chính sách cọc", icon: Landmark, module: "deposit" },
  ] },
  { title: "Hệ thống", items: [
    { to: "/admin/chi-nhanh", label: "Chi nhánh", icon: MapPin, module: "branches" },
    { to: "/admin/nguoi-dung", label: "Người dùng", icon: Users, module: "users" },
    { to: "/admin/vai-tro", label: "Vai trò & quyền", icon: ShieldCheck, module: "roles" },
    { to: "/admin/ai", label: "AI gợi ý món", icon: Sparkles, module: "ai" },
    { to: "/admin/cai-dat", label: "Cài đặt", icon: Settings, module: "settings" },
  ] },
];

export default function AdminSidebar({ open, collapsed, unreadChatCount = 0, onClose }: { open: boolean; collapsed: boolean; unreadChatCount?: number; onClose: () => void }) {
  const can = useCan();
  const isManager = useRole() === "branch_manager";
  return (
    <>
      <div className={cn("lg:hidden fixed inset-0 z-50 bg-dark/50 transition-opacity", open ? "opacity-100" : "opacity-0 pointer-events-none")} onClick={onClose} />
      <aside
        aria-label="Menu quản trị"
        className={cn(
          "fixed lg:sticky top-0 left-0 z-51 h-screen w-64 shrink-0 bg-dark text-white/75 flex flex-col transition-transform duration-300",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0",
          collapsed && "lg:hidden",
        )}
      >
        <div className="h-16 px-5 flex items-center justify-between border-b border-white/10 shrink-0">
        <Link to="/" className="font-display text-xl text-white">MỘC <span className="text-xs font-body text-white/50 ml-1">Quản trị</span></Link>
          <button className="lg:hidden text-white/70" onClick={onClose} aria-label="Đóng menu"><X width={20} height={20} /></button>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
          {GROUPS.map((g) => {
            const items = g.items.filter((i) => can(i.module));
            if (!items.length) return null;
            return (
              <div key={g.title}>
                <div className="px-3 mb-1.5 text-[12px] text-white/40">{g.title}</div>
                {items.map((i) => (
                  <NavLink
                    key={i.to} to={i.to} end={i.end} onClick={onClose}
                    className={({ isActive }) => cn("flex items-center gap-3 px-3 py-2.5 rounded-lg text-[14px] transition-colors", isActive ? "bg-primary text-white" : "hover:bg-white/8 hover:text-white")}
                  >
                    <i.icon width={17} height={17} />{isManager && i.module === "users" ? "Nhân viên chi nhánh" : i.label}{i.module === "chat" && unreadChatCount > 0 && <span className="ml-auto min-w-5 h-5 px-1 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center">{unreadChatCount}</span>}
                  </NavLink>
                ))}
              </div>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
