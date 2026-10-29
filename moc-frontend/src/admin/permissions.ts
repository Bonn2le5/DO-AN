import { create } from "zustand";
import { useAuthStore } from "@/store/authStore";
import type { Action, Module, RoleName } from "./types";

/** Bật VITE_ADMIN_PREVIEW=true để xem giao diện admin mà không cần đăng nhập (chỉ dùng khi phát triển). */
export const PREVIEW = import.meta.env.VITE_ADMIN_PREVIEW === "true";
const EMPTY_ROLES: string[] = [];

export const MODULES: { key: Module; label: string }[] = [
  { key: "dashboard", label: "Tổng quan" },
  { key: "orders", label: "Đơn hàng" },
  { key: "reservations", label: "Đặt bàn" },
  { key: "tables", label: "Bàn" },
  { key: "chat", label: "Chat" },
  { key: "foods", label: "Món ăn" },
  { key: "categories", label: "Danh mục & tag" },
  { key: "ingredients", label: "Nguyên liệu" },
  { key: "promotions", label: "Khuyến mãi" },
  { key: "posts", label: "Bài viết" },
  { key: "reviews", label: "Đánh giá" },
  { key: "payments", label: "Thanh toán" },
  { key: "deposit", label: "Chính sách cọc" },
  { key: "branches", label: "Chi nhánh" },
  { key: "users", label: "Người dùng" },
  { key: "roles", label: "Vai trò" },
  { key: "ai", label: "AI gợi ý" },
  { key: "settings", label: "Cài đặt" },
];

export const ACTIONS: { key: Action; label: string }[] = [
  { key: "view", label: "Xem" },
  { key: "create", label: "Tạo" },
  { key: "update", label: "Sửa" },
  { key: "delete", label: "Xoá" },
];

const ALL: Action[] = ["view", "create", "update", "delete"];

/**
 * Chỉ để ẩn/hiện giao diện. Quyền thật phải do backend kiểm tra
 * (HasPermission theo codename trong bảng role_permissions).
 */
export const MATRIX: Record<RoleName, Partial<Record<Module, Action[]>>> = {
  admin: Object.fromEntries(MODULES.map((m) => [m.key, ALL])),
  staff: {
    dashboard: ["view"],
    orders: ["view", "update"],
    reservations: ["view", "update"],
    tables: ["view", "update"],
    chat: ["view", "create", "update"],
    foods: ["view", "update"],
    categories: ["view"],
    ingredients: ["view", "create", "update"],
    promotions: ["view"],
    posts: ["view", "create", "update"],
    reviews: ["view", "update"],
    payments: ["view", "update"],
    deposit: ["view"],
    branches: ["view"],
    settings: ["view", "update"],
  },
};

export const usePreviewRole = create<{ role: RoleName; setRole: (r: RoleName) => void }>((set) => ({
  role: "admin",
  setRole: (role) => set({ role }),
}));

export function useRole(): RoleName | null {
  const previewRole = usePreviewRole((s) => s.role);
  const roles = useAuthStore((s) => s.user?.roles ?? EMPTY_ROLES);
  if (PREVIEW) return previewRole;
  if (roles.some((r) => ["admin", "quan_tri_vien"].includes(String(r).toLowerCase()))) return "admin";
  if (roles.some((r) => ["staff", "nhan_vien"].includes(String(r).toLowerCase()))) return "staff";
  return null;
}

export function useCan() {
  const role = useRole();
  return (module: Module, action: Action = "view") => !!role && !!MATRIX[role][module]?.includes(action);
}
