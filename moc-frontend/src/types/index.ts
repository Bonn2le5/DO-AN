export * from "./auth";

// Category types
export type CategoryId = "main" | "appetizer" | "drink" | "dessert" | "combo";
export type DanhMucMonAn = "mon_chinh" | "khai_vi" | "do_uong" | "trang_mieng" | "combo" | CategoryId;
export type FoodCategory = CategoryId;

// Food types
export interface Food {
  id: string;
  name: string;
  slug: string;
  category: CategoryId | DanhMucMonAn | string;
  categoryLabel?: string;
  price: number;
  imageUrl?: string;
  description: string;
  longDescription?: string;
  ingredients: string[];
  tags: string[];
  spicyLevel: 0 | 1 | 2 | 3;
  isVegetarian: boolean;
  rating: number;
  reviewCount: number;
  available: boolean;
  stock: number;
  badge?: "Bán chạy" | "Mới" | "AI gợi ý" | "" | string;
  placeholderTone: 1 | 2 | 3 | 4 | 5 | 6;
  createdAt?: string;

  // Vietnamese aliases
  tenMon?: string;
  duongDan?: string;
  danhMuc?: any;
  tenDanhMuc?: string;
  donGia?: number;
  moTaNgan?: string;
  moTaChiTiet?: string;
  nguyenLieu?: string[];
  theMonAn?: string[];
  doCay?: 0 | 1 | 2 | 3;
  laMonChay?: boolean;
  diemDanhGia?: number;
  soLuotDanhGia?: number;
  conHang?: boolean;
  tonKho?: number;
  nhanHienThi?: string;
  phongCachHienThi?: 1 | 2 | 3 | 4 | 5 | 6;
  taoLuc?: string;
}

export type MonAn = Food;

// Combo types
export interface ComboItem {
  id: string;
  name: string;
  slug?: string;
  price: number;
  originalPrice?: number;
  oldPrice: number;
  badge?: string;
  items: string[];
  placeholderTone: 1 | 2 | 3 | 4 | 5 | 6;
  createdAt?: string;

  // Vietnamese aliases
  tenCombo?: string;
  danhSachMon?: string[];
  donGia?: number;
  giaGoc?: number;
  phongCachHienThi?: 1 | 2 | 3 | 4 | 5 | 6;
}

export type ComboMonAn = ComboItem;

// Review types
export interface Review {
  id: string;
  foodId: string;
  author: string;
  rating: number;
  comment: string;
  createdAt: string;

  // Vietnamese aliases
  idMonAn?: string;
  tacGia?: string;
  diemDanhGia?: number;
  nhanXet?: string;
  taoLuc?: string;
}

export type DanhGiaMonAn = Review;

// Cart types
export interface CartItem {
  food: Food;
  quantity: number;
  note?: string;

  // Vietnamese aliases
  monAn?: Food;
  soLuong?: number;
  ghiChu?: string;
}

export type ChiTietGioHang = CartItem;

// Order types
export type OrderStatus =
  | "pending"
  | "confirmed"
  | "preparing"
  | "ready"
  | "serving"
  | "completed"
  | "cancelled"
  | "cho_tiep_nhan"
  | "da_xac_nhan"
  | "dang_che_bien"
  | "san_sang"
  | "hoan_tat"
  | "da_huy";

export type TrangThaiDonHang = OrderStatus;

export interface Order {
  id: string;
  items: CartItem[];
  subtotal: number;
  discount: number;
  total: number;
  status: OrderStatus;
  createdAt: string;
  customerName: string;
  customerPhone: string;
  address?: string;
  note?: string;
  promoCode?: string;

  // Vietnamese aliases
  danhSachMon?: CartItem[];
  tienHang?: number;
  tienGiam?: number;
  tongTien?: number;
  trangThai?: TrangThaiDonHang;
  taoLuc?: string;
  tenKhachHang?: string;
  soDienThoai?: string;
  ghiChu?: string;
  maKhuyenMai?: string;
}

export type DonHang = Order;

// Table types
export type TableStatus =
  | "available"
  | "held"
  | "reserved"
  | "occupied"
  | "maintenance";

export type TrangThaiBanAn = TableStatus | "trong" | "dang_giu" | "da_dat" | "dang_phuc_vu" | "bao_tri";

export interface RestaurantTable {
  id: string;
  label: string;
  capacity: number;
  status: TableStatus;
  zone: string;

  // Vietnamese aliases
  soBan?: string;
  sucChua?: number;
  trangThai?: any;
  khuVuc?: string;
}

export type BanAn = RestaurantTable;

// Reservation types
export type ReservationOption =
  | "table_only"
  | "table_and_food"
  | "table_and_food_editable"
  | "chi_giu_cho"
  | "dat_ban_va_goi_mon"
  | "dat_ban_goi_mon_chinh_sua";

export type HinhThucDatBan = ReservationOption;

export type ReservationStatus =
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

export type TrangThaiDatBan = ReservationStatus;

export type DepositStatus =
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

export type TrangThaiThanhToanCoc = DepositStatus;

export type MocHuyDatBan = "truoc_24h" | "tu_6_den_24h" | "trong_6h" | "khach_khong_den" | string;

export interface CancellationRule {
  timeBucket?: MocHuyDatBan;
  refundPercentage: number;
  mocThoiGian?: MocHuyDatBan;
  phanTramHoanTien?: number;
}

export interface DepositPolicy {
  depositPercentage: number;
  cancellationRules: CancellationRule[];
  holdMinutes: number;
  paymentExpiryMinutes: number;

  // Vietnamese aliases
  phanTramCoc?: number;
  quyTacHuyBan?: { mocThoiGian: MocHuyDatBan; phanTramHoanTien: number }[];
  thoiGianGiuChoPhut?: number;
  hanThanhToanPhut?: number;
}

export type ChinhSachDatCoc = DepositPolicy;

export interface ReservationFoodItem {
  food: Food;
  quantity: number;

  // Vietnamese aliases
  monAn?: Food;
  soLuong?: number;
}

export type MonAnDatBan = ReservationFoodItem;

export interface Reservation {
  id: string;
  tableId: string;
  tableLabel?: string;
  date: string;
  time: string;
  partySize: number;
  note?: string;
  customerName: string;
  customerPhone: string;
  option: ReservationOption;
  foodItems: ReservationFoodItem[];
  foodSubtotal: number;
  depositAmount: number;
  status: ReservationStatus;
  depositStatus: DepositStatus;
  holdExpiresAt?: string;
  createdAt: string;

  // Vietnamese aliases
  idBanAn?: string;
  tenBanAn?: string;
  ngayDat?: string;
  gioDat?: string;
  soLuongKhach?: number;
  ghiChu?: string;
  tenKhachHang?: string;
  soDienThoai?: string;
  hinhThuc?: ReservationOption;
  danhSachMonAn?: ReservationFoodItem[];
  tienMonAn?: number;
  soTienCoc?: number;
  trangThai?: ReservationStatus;
  trangThaiThanhToanCoc?: DepositStatus;
  thoiHanGiuCho?: string;
  taoLuc?: string;
}

export type ThongTinDatBan = Reservation;

// VNPay session
export interface VNPayPaymentSession {
  paymentUrl: string;
  txnRef: string;
  amount: number;
  expiresAt: string;

  // Vietnamese aliases
  duongDanThanhToan?: string;
  maGiaoDich?: string;
  soTien?: number;
  hetHanLuc?: string;
}

export type PhienThanhToanVNPay = VNPayPaymentSession;

// Promotion types
export interface Promotion {
  id: string;
  code: string;
  title: string;
  description: string;
  badge?: string;
  discountType: "percent" | "percentage" | "fixed" | "phan_tram" | "so_tien_co_dinh";
  discountValue: number;
  discountLabel?: string;
  minOrder?: number;
  endsAt?: string;
  expiresAt?: string;

  // Vietnamese aliases
  maGiamGia?: string;
  tieuDe?: string;
  moTa?: string;
  nhanGiamGia?: string;
  kieuGiamGia?: "phan_tram" | "so_tien_co_dinh";
  giaTriGiam?: number;
  donHangToiThieu?: number;
  hetHanLuc?: string;
}

export type KhuyenMai = Promotion;

// Blog types
export interface BlogPost {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  content: string;
  tag: string;
  author: string;
  createdAt: string;
  readMinutes: number;
  placeholderTone: 1 | 2 | 3 | 4 | 5 | 6;

  // Vietnamese aliases
  duongDan?: string;
  tieuDe?: string;
  tomTat?: string;
  noiDung?: string;
  theBaiViet?: string;
  tacGia?: string;
  taoLuc?: string;
  thoiGianDocPhut?: number;
  phongCachHienThi?: 1 | 2 | 3 | 4 | 5 | 6;
}

export type BaiVietBlog = BlogPost;

// Recommendation types
export interface Recommendation {
  food: Food;
  score: number;
  reason: string;

  // Vietnamese aliases
  monAn?: Food;
  diemTuongDong?: number;
  lyDoGoiY?: string;
}

export type GoiYMonAn = Recommendation;

// Branch / GIS types
export interface Branch {
  id: string;
  name: string;
  address: string;
  phone: string;
  lat: number;
  lng: number;
  openHours: string;
  isMain?: boolean;

  // Vietnamese aliases
  tenChiNhanh?: string;
  diaChi?: string;
  soDienThoai?: string;
  kinhDo?: number;
  viDo?: number;
  gioMoCua?: string;
  laChiNhanhChinh?: boolean;
}

export type ChiNhanh = Branch;

export interface RouteInfo {
  distanceKm: number;
  durationMinutes: number;
  geometry: [number, number][];

  // Vietnamese aliases
  khoangCachKm?: number;
  thoiGianPhut?: number;
  toaDoTuyenDuong?: [number, number][];
}

export type ThongTinTuyenDuong = RouteInfo;

// Inventory types
export interface Ingredient {
  id: string;
  name: string;
  unit: string;
  currentStock: number;
  minStock: number;
  isActive: boolean;

  // Vietnamese aliases
  ten?: string;
  donVi?: string;
  tonKhoHienTai?: number;
  tonKhoToiThieu?: number;
  conHoatDong?: boolean;
}
export type NguyenLieu = Ingredient;

export interface InventoryTransaction {
  id: string;
  ingredientId: string;
  ingredientName?: string;
  type: "nhap" | "xuat" | "dieu_chinh" | "tru_tu_dong";
  quantity: number;
  stockBefore: number;
  stockAfter: number;
  reason?: string;
  createdBy?: string;
  createdAt: string;
}
export type LichSuKho = InventoryTransaction;

// Refund Receipt types
export interface RefundReceipt {
  id: string;
  refundCode: string;
  reservationId: string;
  paymentId: string;
  originalDeposit: number;
  refundPercentage: number;
  refundAmount: number;
  penaltyAmount: number;
  timeMilestone: string;
  hoursBeforeBooking: number;
  cancelReason: string;
  status: "cho_xu_ly" | "da_hoan_tien" | "tu_choi";
  refundMethod: "vnpay" | "chuyen_khoan" | "tien_mat";
  createdAt: string;

  // Vietnamese aliases
  maPhieuHoan?: string;
  soTienCocGoc?: number;
  phanTramHoan?: number;
  soTienHoan?: number;
  soTienPhat?: number;
  mocThoiGian?: string;
  lyDoHuy?: string;
  trangThai?: string;
}
export type PhieuHoanTien = RefundReceipt;

// Chat types
export interface ChatMessage {
  id: number | string;
  conversationId: number | string;
  senderId: number | string;
  senderName: string;
  senderRole?: string;
  isStaff: boolean;
  message: string;
  messageType: "van_ban" | "hinh_anh" | "he_thong";
  isRead: boolean;
  createdAt: string;
}
export type TinNhan = ChatMessage;

export interface ChatConversation {
  id: number | string;
  customerId: number | string;
  customerName?: string;
  staffId?: number | string | null;
  staffName?: string | null;
  status: "mo" | "dong";
  lastMessageAt?: string;
  messages: ChatMessage[];
}
export type HoiThoai = ChatConversation;

