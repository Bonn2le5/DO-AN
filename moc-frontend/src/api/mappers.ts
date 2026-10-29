import type {
  Food,
  Promotion,
  Review,
  BlogPost,
  Recommendation,
  RestaurantTable,
  Reservation,
} from "@/types";

const tinhPhongCach = (id: string | number) => (Number(id) % 6 + 1) as 1 | 2 | 3 | 4 | 5 | 6;

export function mapMonAn(raw: any): Food {
  const name = raw.ten ?? raw.name ?? "";
  const slug = raw.duong_dan ?? raw.slug ?? "";
  const price = Number(raw.don_gia_hien_tai ?? raw.don_gia ?? raw.price ?? 0);
  const category =
    raw.chi_tiet_danh_muc?.duong_dan ??
    raw.category_detail?.slug ??
    raw.danh_muc ??
    raw.category ??
    "main";
  const categoryLabel =
    raw.chi_tiet_danh_muc?.ten ??
    raw.category_detail?.name ??
    raw.ten_danh_muc ??
    "Thực đơn";
  const description = raw.mo_ta_ngan ?? raw.description ?? "";
  const longDescription = raw.mo_ta_chi_tiet ?? raw.long_description ?? "";
  const ingredients = raw.nguyen_lieu ?? raw.ingredients ?? [];
  const tags = raw.the_mon_an ?? raw.tags ?? [];
  const spicyLevel = Math.min(raw.do_cay ?? raw.spicy_level ?? 0, 3) as 0 | 1 | 2 | 3;
  const isVegetarian = Boolean(raw.la_mon_chay ?? raw.is_vegetarian ?? false);
  const rating = Number(raw.diem_danh_gia ?? raw.rating ?? 0);
  const reviewCount = Number(raw.so_luot_danh_gia ?? raw.review_count ?? 0);
  const available = Boolean(raw.con_hang ?? raw.is_available ?? raw.available ?? true);
  const stock = Number(raw.ton_kho_cache ?? raw.stock ?? 0);
  const placeholderTone = tinhPhongCach(raw.id);
  const createdAt = raw.tao_luc ?? raw.created_at ?? new Date().toISOString();
  const primaryImage = (raw.hinh_anh ?? raw.images ?? []).find((image: any) => image.la_anh_chinh || image.is_primary)
    ?? (raw.hinh_anh ?? raw.images ?? [])[0];
  const rawImageUrl = raw.image_url ?? raw.image ?? raw.anh ?? primaryImage?.anh ?? primaryImage?.image ?? "";
  const imageUrl = rawImageUrl
    ? (/^https?:\/\//i.test(rawImageUrl) ? rawImageUrl : new URL(rawImageUrl, import.meta.env.VITE_API_URL ?? window.location.origin).toString())
    : undefined;

  return {
    id: String(raw.id),
    name,
    slug,
    category,
    categoryLabel,
    price,
    imageUrl,
    description,
    longDescription,
    ingredients,
    tags,
    spicyLevel,
    isVegetarian,
    rating,
    reviewCount,
    available,
    stock,
    badge: raw.nhan_hien_thi ?? raw.badge ?? "",
    placeholderTone,
    createdAt,

    // Vietnamese aliases
    tenMon: name,
    duongDan: slug,
    danhMuc: category,
    tenDanhMuc: categoryLabel,
    donGia: price,
    moTaNgan: description,
    moTaChiTiet: longDescription,
    theMonAn: tags,
    doCay: spicyLevel,
    laMonChay: isVegetarian,
    diemDanhGia: rating,
    soLuotDanhGia: reviewCount,
    conHang: available,
    tonKho: stock,
    phongCachHienThi: placeholderTone,
    taoLuc: createdAt,
  };
}

export function mapBanAn(raw: any): RestaurantTable {
  const label = raw.so_ban ?? raw.label ?? `Bàn ${raw.id}`;
  const capacity = Number(raw.suc_chua ?? raw.capacity ?? 4);
  const rawStatus = raw.trang_thai ?? raw.status ?? "available";
  const status = ({
    trong: "available",
    available: "available",
    dang_giu: "held",
    held: "held",
    da_dat: "reserved",
    reserved: "reserved",
    dang_phuc_vu: "occupied",
    occupied: "occupied",
    bao_tri: "maintenance",
    maintenance: "maintenance",
  } as const)[rawStatus as string] ?? "maintenance";
  const zone = raw.khu_vuc ?? raw.zone ?? "Trong nhà";

  return {
    id: String(raw.id),
    label,
    capacity,
    status,
    zone,

    // Vietnamese aliases
    soBan: label,
    sucChua: capacity,
    trangThai: status,
    khuVuc: zone,
  };
}

export function mapThongTinDatBan(raw: any): Reservation {
  const foodItems = (raw.danh_sach_mon ?? raw.food_items ?? []).map((item: any) => ({
    food: mapMonAn(item.mon_an ?? item.food),
    quantity: item.so_luong ?? item.quantity ?? 1,
  }));

  const tableId = String(raw.ban_an_id ?? raw.table ?? "");
  const tableLabel = raw.ten_ban ?? raw.table_label ?? "";
  const date = raw.ngay_dat ?? raw.date ?? "";
  const time = raw.gio_bat_dau ?? raw.time ?? "";
  const partySize = Number(raw.so_luong_khach ?? raw.party_size ?? 2);
  const note = raw.ghi_chu ?? raw.note ?? "";
  const customerName = raw.ten_khach ?? raw.customer_name ?? "";
  const customerPhone = raw.sdt_khach ?? raw.phone ?? "";
  const option = raw.hinh_thuc ?? raw.option ?? "table_only";
  const foodSubtotal = Number(raw.tien_mon_an ?? raw.food_subtotal ?? 0);
  const depositAmount = Number(raw.so_tien_coc ?? raw.deposit_amount ?? 0);
  const status = raw.trang_thai ?? raw.status ?? "awaiting_payment";
  const depositStatus = raw.trang_thai_coc ?? raw.payment_status ?? "unpaid";
  const createdAt = raw.tao_luc ?? raw.created_at ?? new Date().toISOString();

  return {
    id: String(raw.id),
    tableId,
    tableLabel,
    date,
    time,
    partySize,
    note,
    customerName,
    customerPhone,
    option,
    foodItems,
    foodSubtotal,
    depositAmount,
    status,
    depositStatus,
    holdExpiresAt: raw.thoi_han_giu_cho ?? raw.hold_expires_at,
    createdAt,

    // Vietnamese aliases
    idBanAn: tableId,
    tenBanAn: tableLabel,
    ngayDat: date,
    gioDat: time,
    soLuongKhach: partySize,
    ghiChu: note,
    tenKhachHang: customerName,
    soDienThoai: customerPhone,
    hinhThuc: option,
    danhSachMonAn: foodItems,
    tienMonAn: foodSubtotal,
    soTienCoc: depositAmount,
    trangThai: status,
    trangThaiThanhToanCoc: depositStatus,
    thoiHanGiuCho: raw.thoi_han_giu_cho,
    taoLuc: createdAt,
  };
}

export function mapKhuyenMai(raw: any): Promotion {
  const code =
    raw.ma_giam_gia ??
    raw.code ??
    raw.danh_sach_ma?.[0]?.ma ??
    raw.codes?.[0]?.ma ??
    "";
  const title = raw.ten ?? raw.name ?? raw.title ?? "";
  const description = raw.mo_ta ?? raw.description ?? "";
  const discountType = raw.kieu_giam ?? raw.discount_type ?? "percentage";
  const discountValue = Number(raw.gia_tri_giam ?? raw.discount_value ?? 0);
  const minOrder = Number(raw.don_hang_toi_thieu ?? raw.min_order_value ?? 0);
  const endsAt = raw.ket_thuc_luc ?? raw.ends_at ?? "";
  const badge = raw.nhan_giam_gia ?? `${discountValue}${discountType === "percentage" || discountType === "phan_tram" ? "%" : "đ"}`;

  return {
    id: String(raw.id),
    code,
    title,
    description,
    badge,
    discountType,
    discountValue,
    minOrder,
    endsAt,

    // Vietnamese aliases
    maGiamGia: code,
    tieuDe: title,
    moTa: description,
    nhanGiamGia: badge,
    kieuGiamGia: discountType,
    giaTriGiam: discountValue,
    donHangToiThieu: minOrder,
    hetHanLuc: endsAt,
  };
}

export function mapDanhGia(raw: any): Review {
  const foodId = String(raw.mon_an_id ?? raw.mon_an ?? raw.food ?? "");
  const author = raw.ten_nguoi_dung ?? raw.user_name ?? raw.ten_khach ?? raw.customer_name ?? "Khách hàng";
  const rating = Number(raw.diem_danh_gia ?? raw.rating ?? 5);
  const comment = raw.nhan_xet ?? raw.comment ?? "";
  const createdAt = raw.tao_luc ?? raw.created_at ?? new Date().toISOString();

  return {
    id: String(raw.id),
    foodId,
    author,
    rating,
    comment,
    createdAt,

    // Vietnamese aliases
    idMonAn: foodId,
    tacGia: author,
    diemDanhGia: rating,
    nhanXet: comment,
    taoLuc: createdAt,
  };
}

export function mapBaiViet(raw: any): BlogPost {
  const slug = raw.duong_dan ?? raw.slug ?? "";
  const title = raw.tieu_de ?? raw.title ?? "";
  const excerpt = (raw.tom_tat ?? raw.excerpt) || "";
  const content = raw.noi_dung ?? raw.content ?? "";
  const tag = (raw.ten_danh_muc ?? raw.category_name) || "Ẩm thực";
  const author = (raw.ten_tac_gia ?? raw.author_name) || "Nhà hàng MỘC";
  const createdAt = (raw.dang_luc ?? raw.published_at) || raw.tao_luc || raw.created_at || new Date().toISOString();
  const placeholderTone = tinhPhongCach(raw.id);

  return {
    id: String(raw.id),
    slug,
    title,
    excerpt,
    content,
    tag,
    author,
    createdAt,
    readMinutes: 3,
    placeholderTone,

    // Vietnamese aliases
    duongDan: slug,
    tieuDe: title,
    tomTat: excerpt,
    noiDung: content,
    theBaiViet: tag,
    tacGia: author,
    taoLuc: createdAt,
    thoiGianDocPhut: 3,
    phongCachHienThi: placeholderTone,
  };
}

export function mapGoiY(raw: any): Recommendation {
  return {
    food: mapMonAn(raw.chi_tiet_mon_an ?? raw.food_detail ?? raw.mon_an ?? raw.food),
    score: Number(raw.diem_tuong_dong ?? raw.score ?? 1),
    reason: raw.ly_do_goi_y ?? raw.reason ?? "Gợi ý dành riêng cho bạn",
  };
}

// Export English aliases
export const mapFood = mapMonAn;
export const mapTable = mapBanAn;
export const mapReservation = mapThongTinDatBan;
export const mapPromotion = mapKhuyenMai;
export const mapReview = mapDanhGia;
export const mapPost = mapBaiViet;
export const mapRecommendation = mapGoiY;
