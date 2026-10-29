export type UserRole = "customer" | "staff" | "admin" | "khach_hang" | "nhan_vien" | "quan_tri_vien";

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  avatarInitial: string;
  roles?: UserRole[];
  isStaff?: boolean;

  // Vietnamese aliases
  hoTen?: string;
  thuDienTu?: string;
  soDienThoai?: string;
  kyTuDaiDien?: string;
  danhSachVaiTro?: UserRole[];
  laNhanVien?: boolean;
}

export type NguoiDung = User;
