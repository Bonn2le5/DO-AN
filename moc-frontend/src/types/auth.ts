export type UserRole = "customer" | "staff" | "branch_manager" | "admin" | "khach_hang" | "nhan_vien" | "nhan_vien_ban_hang" | "quan_ly_chi_nhanh" | "quan_tri_vien";

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  avatarInitial: string;
  roles?: UserRole[];
  isStaff?: boolean;
  isAdmin?: boolean;
  branchId?: string;

  // Vietnamese aliases
  hoTen?: string;
  thuDienTu?: string;
  soDienThoai?: string;
  kyTuDaiDien?: string;
  danhSachVaiTro?: UserRole[];
  laNhanVien?: boolean;
}

export type NguoiDung = User;
