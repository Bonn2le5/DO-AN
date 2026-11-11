export * from "./auth";

// Category types
export type MaDanhMuc = "main" | "appetizer" | "drink" | "dessert" | "combo" | string;
export type DanhMucMonAn = "mon_chinh" | "khai_vi" | "do_uong" | "trang_mieng" | "combo" | MaDanhMuc;
export type LoaiMonAn = string;

export interface MucDanhMuc {
  id: string;
  idSo?: number;
  ten: string;
  duongDan?: string;
  bieuTuong?: string;
  hinhAnh?: string;
  moTa?: string;
  conHoatDong?: boolean;
}

// Food types
export interface MonAn {
  id: string;
  tenMon: string;
  duongDan: string;
  danhMuc: MaDanhMuc | DanhMucMonAn | string;
  tenDanhMuc?: string;
  donGia: number;
  duongDanAnh?: string;
  moTaNgan: string;
  moTaChiTiet?: string;
  nguyenLieu: string[];
  theMonAn: string[];
  doCay: 0 | 1 | 2 | 3;
  laMonChay: boolean;
  diemDanhGia: number;
  soLuotDanhGia: number;
  conHang: boolean;
  tonKho: number;
  nhanHienThi?: "Bán chạy" | "Mới" | "AI gợi ý" | "" | string;
  phongCachHienThi: 1 | 2 | 3 | 4 | 5 | 6;
  taoLuc?: string;
}


// Combo types
export interface ComboMonAn {
  id: string;
  tenCombo: string;
  duongDan?: string;
  donGia: number;
  giaNiemYet?: number;
  giaGoc: number;
  nhanHienThi?: string;
  danhSachMon: string[];
  phongCachHienThi: 1 | 2 | 3 | 4 | 5 | 6;
  taoLuc?: string;
}


// Review types
/** Một dòng món trong bữa ăn đã hoàn tất, kèm đánh giá nếu khách đã chấm. */
export interface MonTrongBuaAn {
  idChiTiet: string;
  idMonAn: string;
  duongDanMon: string;
  tenMon: string;
  duongDanAnh?: string;
  soLuong: number;
  danhGia: { diemDanhGia: number; nhanXet: string } | null;
}

/** Bữa ăn (đơn tại bàn đã hoàn tất) còn phần chưa đánh giá. */
export interface BuaAnChoDanhGia {
  id: string;
  maDonHang: string;
  taoLuc: string;
  chiNhanh: string;
  mon: MonTrongBuaAn[];
  danhGiaChung: { diemPhucVu: number; diemKhongGian: number; nhanXet: string } | null;
}

export interface DanhGiaMonAn {
  id: string;
  idMonAn: string;
  duongDanMon?: string;
  tenMonAn?: string;
  tacGia: string;
  diemDanhGia: number;
  nhanXet: string;
  taoLuc: string;
}


// Table types
export type TrangThaiBan =
  | "available"
  | "held"
  | "reserved"
  | "occupied"
  | "maintenance";

export type TrangThaiBanAn = TrangThaiBan | "trong" | "dang_giu" | "da_dat" | "dang_phuc_vu" | "bao_tri";

export interface BanAn {
  id: string;
  soBan: string;
  sucChua: number;
  trangThai: TrangThaiBan;
  khuVuc: string;
}


// Reservation types
export type HinhThucDatBan =
  | "table_only"
  | "table_and_food"
  | "table_and_food_editable"
  | "chi_giu_cho"
  | "dat_ban_va_goi_mon"
  | "dat_ban_goi_mon_chinh_sua";


export type TrangThaiDatBan =
  | "cho_xac_nhan"
  | "awaiting_payment"
  | "confirmed"
  | "seated"
  | "completed"
  | "cancelled"
  | "no_show"
  | "cho_thanh_toan"
  | "da_xac_nhan"
  | "khach_da_den"
  | "hoan_tat"
  | "da_huy"
  | "khach_khong_den";


export type TrangThaiThanhToanCoc =
  | "unpaid"
  | "processing"
  | "success"
  | "failed"
  | "refunded"
  | "partially_refunded"
  | "chua_thanh_toan"
  | "dang_xu_ly"
  | "thanh_cong"
  | "that_bai"
  | "da_hoan_tien"
  | "hoan_tien_mot_phan";


export type MocHuyDatBan = "truoc_24h" | "tu_6_den_24h" | "trong_6h" | "khach_khong_den" | string;

export interface QuyTacHuyCoc {
  mocThoiGian?: MocHuyDatBan;
  phanTramHoanTien: number;
}

export interface ChinhSachDatCoc {
  phanTramCoc: number;
  quyTacHuyBan: QuyTacHuyCoc[];
  thoiGianGiuChoPhut: number;
  hanThanhToanPhut: number;
}


export interface MonAnDatBan {
  monAn: MonAn;
  soLuong: number;
}


export interface ThongTinDatBan {
  id: string;
  maDatBan?: string;
  tenChiNhanh?: string;
  idBanAn: string;
  tenBanAn?: string;
  ngayDat: string;
  gioDat: string;
  soLuongKhach: number;
  ghiChu?: string;
  tenKhachHang: string;
  soDienThoai: string;
  hinhThuc: HinhThucDatBan;
  danhSachMonAn: MonAnDatBan[];
  tienMonAn: number;
  soTienCoc: number;
  trangThai: TrangThaiDatBan;
  trangThaiThanhToanCoc: TrangThaiThanhToanCoc;
  taoLuc: string;

  thoiHanGiuCho?: string;
}


// Phiên thanh toán PayOS
export interface PhienThanhToanPayOS {
  duongDanThanhToan: string;
  maGiaoDich: string;
  soTien: number;
  hetHanLuc: string;
}


// Promotion types
export interface KhuyenMai {
  id: string;
  maGiamGia: string;
  tieuDe: string;
  moTa: string;
  nhanGiamGia?: string;
  kieuGiamGia: "percent" | "percentage" | "fixed" | "phan_tram" | "so_tien_co_dinh";
  giaTriGiam: number;
  nhanMucGiam?: string;
  donHangToiThieu?: number;
  ketThucLuc?: string;
  hetHanLuc?: string;
}


// Blog types
export interface BaiVietBlog {
  id: string;
  duongDan: string;
  tieuDe: string;
  tomTat: string;
  noiDung: string;
  theBaiViet: string;
  tacGia: string;
  taoLuc: string;
  thoiGianDocPhut: number;
  phongCachHienThi: 1 | 2 | 3 | 4 | 5 | 6;
}


// Recommendation types
export interface GoiYMonAn {
  monAn: MonAn;
  diemTuongDong: number;
  lyDoGoiY: string;
  phienBanMoHinh?: string;
  laKhoiDauLanh?: boolean;
}


// Trợ lý gọi món AI
export interface MonTrongThucDon {
  monAn: MonAn;
  soLuong: number;
  thanhTien: number;
}

export interface NhomMonThucDon {
  khoa: string;
  ten: string;
  soMon: number;
  mon: MonTrongThucDon[];
}

export interface ThucDonTroLy {
  phanTich: { soNguoi: number; nganSach: number | null; tietKiem: boolean; nhom: string[]; tranh: string[]; khauVi: string[] };
  nhomMon: NhomMonThucDon[];
  tongTien: number;
  nganSach: number | null;
  vuotNganSach: boolean;
  ghiChu: string[];
  phienBanMoHinh: string;
  loiNhan: string;
}

// Branch / GIS types
export interface ChiNhanh {
  id: string;
  tenChiNhanh: string;
  diaChi: string;
  soDienThoai: string;
  viDo: number;
  kinhDo: number;
  gioMoCua: string;
  laChiNhanhChinh?: boolean;
}


export interface ThongTinTuyenDuong {
  khoangCachKm: number;
  thoiGianPhut: number;
  toaDoTuyenDuong: [number, number][];
}


// Inventory types
export interface NguyenLieu {
  id: string;
  ten: string;
  donVi: string;
  tonKhoHienTai: number;
  tonKhoToiThieu: number;
  conHoatDong: boolean;
}

export interface LichSuKho {
  id: string;
  idNguyenLieu: string;
  tenNguyenLieu?: string;
  loaiGiaoDich: "nhap" | "xuat" | "dieu_chinh" | "tru_tu_dong";
  soLuong: number;
  tonKhoTruoc: number;
  tonKhoSau: number;
  lyDo?: string;
  nguoiTao?: string;
  taoLuc: string;
}

// Refund Receipt types
export interface PhieuHoanTien {
  id: string;
  maPhieuHoan: string;
  idDatBan: string;
  idThanhToan: string;
  soTienCocGoc: number;
  phanTramHoan: number;
  soTienHoan: number;
  soTienPhat: number;
  mocThoiGian: string;
  soGioTruocGioHen: number;
  lyDoHuy: string;
  trangThai: "cho_xu_ly" | "da_hoan_tien" | "tu_choi";
  phuongThucHoan: "payos" | "chuyen_khoan" | "tien_mat";
  taoLuc: string;
}

// Chat types
export interface TinNhan {
  id: number | string;
  idHoiThoai: number | string;
  idNguoiGui: number | string;
  tenNguoiGui: string;
  vaiTroNguoiGui?: string;
  laNhanVien: boolean;
  noiDung: string;
  loaiTinNhan: "van_ban" | "hinh_anh" | "he_thong";
  daDoc: boolean;
  taoLuc: string;
}

export interface HoiThoai {
  id: number | string;
  idKhachHang: number | string;
  tenKhachHang?: string;
  idNhanVien?: number | string | null;
  tenNhanVien?: string | null;
  trangThai: "mo" | "dong";
  tinNhanCuoiLuc?: string;
  danhSachTinNhan: TinNhan[];
}

