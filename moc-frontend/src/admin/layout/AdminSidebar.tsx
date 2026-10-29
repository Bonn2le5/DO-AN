import { Link, NavLink } from "react-router-dom";
import {
  LayoutDashboard, ShoppingBag, CalendarDays, Armchair, MessageCircle, UtensilsCrossed, Tag, Package, Percent,
  Newspaper, Star, CreditCard, Landmark, MapPin, Users, ShieldCheck, Sparkles, Settings, X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCan } from "../permissions";
import type { Module } from "../types";

type Item = { to: string; label: string; icon: typeof Tag; module: Module; end?: boolean };
const GROUPS: { title: string; items: Item[] }[] = [
  { title: "Vận hành", items: [
    { to: "/admin", label: "Tổng quan", icon: LayoutDashboard, module: "dashboard", end: true },
    { to: "/admin/orders", label: "Đơn hàng", icon: ShoppingBag, module: "orders" },
    { to: "/admin/reservations", label: "Đặt bàn", icon: CalendarDays, module: "reservations" },
    { to: "/admin/tables", label: "Sơ đồ bàn", icon: Armchair, module: "tables" },
    { to: "/admin/chat", label: "Chat khách hàng", icon: MessageCircle, module: "chat" },
  ] },
  { title: "Thực đơn", items: [
    { to: "/admin/menu", label: "Món ăn", icon: UtensilsCrossed, module: "foods" },
    { to: "/admin/categories", label: "Danh mục & tag", icon: Tag, module: "categories" },
    { to: "/admin/ingredients", label: "Nguyên liệu & kho", icon: Package, module: "ingredients" },
  ] },
  { title: "Tiếp thị", items: [
    { to: "/admin/promotions", label: "Khuyến mãi", icon: Percent, module: "promotions" },
    { to: "/admin/posts", label: "Bài viết", icon: Newspaper, module: "posts" },
    { to: "/admin/reviews", label: "Đánh giá", icon: Star, module: "reviews" },
  ] },
  { title: "Tài chính", items: [
    { to: "/admin/payments", label: "Thanh toán & hoàn cọc", icon: CreditCard, module: "payments" },
    { to: "/admin/deposit-policy", label: "Chính sách cọc", icon: Landmark, module: "deposit" },
  ] },
  { title: "Hệ thống", items: [
    { to: "/admin/branches", label: "Chi nhánh", icon: MapPin, module: "branches" },
    { to: "/admin/users", label: "Người dùng", icon: Users, module: "users" },
    { to: "/admin/roles", label: "Vai trò & quyền", icon: ShieldCheck, module: "roles" },
    { to: "/admin/ai", label: "AI gợi ý món", icon: Sparkles, module: "ai" },
    { to: "/admin/settings", label: "Cài đặt", icon: Settings, module: "settings" },
  ] },
];

export default function AdminSidebar({ open, collapsed, onClose }: { open: boolean; collapsed: boolean; onClose: () => void }) {
  const can = useCan();
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
                    <i.icon width={17} height={17} />{i.label}
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
