import { apiClient, setAccessToken, setRefreshToken } from "./client";

export interface LoginPayload {
  email: string;
  password: string;
}
export interface RegisterPayload extends LoginPayload {
  name: string;
  phone: string;
}
export interface AuthResult {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    name: string;
    email: string;
    phone?: string;
    avatarInitial: string;
    roles?: import("@/types").UserRole[];
    danhSachVaiTro?: import("@/types").UserRole[];
    isStaff?: boolean;
    laNhanVien?: boolean;
    is_superuser?: boolean;
    is_restaurant_staff?: boolean;
    isAdmin?: boolean;
    branchId?: string;
    chi_nhanh_quan_ly?: number | string | null;
  };
}

export async function login(payload: LoginPayload): Promise<AuthResult> {
  const { data: tokens } = await apiClient.post("/auth/login/", payload);
  setAccessToken(tokens.access); setRefreshToken(tokens.refresh);
  const { data: user } = await apiClient.get("/auth/profile/");
  return { accessToken: tokens.access, refreshToken: tokens.refresh, user: mapUser(user) };
}

export async function register(payload: RegisterPayload): Promise<{ email: string; message: string }> {
  const { data } = await apiClient.post("/auth/register/", payload);
  // Backend now returns { email, message } instead of tokens (email verification required)
  return { email: data.email ?? payload.email, message: data.message ?? "" };
}

export async function verifyEmail(params: {
  email: string;
  maXacThuc: string;
}): Promise<AuthResult> {
  const { data } = await apiClient.post("/auth/xac-thuc-email/", {
    email: params.email,
    ma_xac_thuc: params.maXacThuc,
  });
  setAccessToken(data.access);
  setRefreshToken(data.refresh);
  return {
    accessToken: data.access,
    refreshToken: data.refresh,
    user: mapUser(data.user ?? data.nguoi_dung),
  };
}

export async function resendVerificationEmail(email: string): Promise<void> {
  await apiClient.post("/auth/gui-ma-xac-thuc/", { email });
}

export async function updateProfile(payload: Record<string, string>): Promise<AuthResult["user"]> {
  const { data } = await apiClient.patch("/auth/profile/", payload);
  return mapUser(data);
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await apiClient.post("/auth/change-password/", { old_password: oldPassword, new_password: newPassword });
}

/** Lấy thông báo lỗi đầu tiên từ phản hồi DRF. */
export function apiErrorMessage(e: any, fallback: string): string {
  const data = e?.response?.data;
  if (!data || typeof data !== "object") return fallback;
  if (data.detail) return String(data.detail);
  const first = Object.values(data).flat()[0];
  return first ? String(first) : fallback;
}

function mapUser(raw: any): AuthResult["user"] {
  const name = raw.name || [raw.first_name, raw.last_name].filter(Boolean).join(" ") || raw.username || raw.email || raw.thu_dien_tu;
  const roles = raw.roles || raw.danh_sach_vai_tro || [];
  const isStaff = Boolean(raw.is_restaurant_staff || raw.la_nhan_vien_nha_hang || raw.is_superuser || roles.some((r: string) => ["admin", "staff", "branch_manager", "quan_tri_vien", "nhan_vien", "nhan_vien_ban_hang", "quan_ly_chi_nhanh"].includes(r)));
  return {
    id: String(raw.id),
    name,
    email: raw.email || raw.thu_dien_tu,
    phone: raw.phone || raw.so_dien_thoai || "",
    avatarInitial: (name || "U").charAt(0).toUpperCase(),
    roles,
    isStaff,
    laNhanVien: isStaff,
    danhSachVaiTro: roles,
    is_superuser: raw.is_superuser,
    is_restaurant_staff: isStaff,
    isAdmin: Boolean(raw.is_superuser || raw.roles?.some((r: string) => ["admin", "quan_tri_vien"].includes(r))),
    branchId: raw.chi_nhanh_quan_ly ? String(raw.chi_nhanh_quan_ly) : undefined,
  };
}
