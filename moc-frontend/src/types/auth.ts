export type VaiTroNguoiDung = "customer" | "staff" | "branch_manager" | "admin" | "khach_hang" | "nhan_vien" | "nhan_vien_ban_hang" | "quan_ly_chi_nhanh" | "quan_tri_vien";

export interface NguoiDung {
  id: string;
  hoTen: string;
  thuDienTu: string;
  soDienThoai?: string;
  kyTuDaiDien: string;
  danhSachVaiTro?: VaiTroNguoiDung[];
  laNhanVien?: boolean;
  laQuanTri?: boolean;
  idChiNhanh?: string;
}

