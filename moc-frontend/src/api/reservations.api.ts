import { apiClient } from "./client";
import { mapBanAn, mapThongTinDatBan } from "./mappers";
import type {
  RestaurantTable,
  DepositPolicy,
  Reservation,
  VNPayPaymentSession,
  ReservationOption,
  ReservationFoodItem,
  Branch,
} from "@/types";

export async function layDanhSachBan(chiNhanhId?: string): Promise<RestaurantTable[]> {
  try {
    const params = chiNhanhId ? { chi_nhanh: chiNhanhId } : {};
    const { data } = await apiClient.get("/tables/", { params });
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list.map(mapBanAn);
  } catch {
    return [];
  }
}

export async function layDanhSachChiNhanh(): Promise<Branch[]> {
  try {
    const { data } = await apiClient.get("/branches/");
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list.map((b: any) => ({
      id: String(b.id),
      name: b.ten ?? b.name ?? "",
      address: b.dia_chi ?? b.address ?? "",
      phone: b.so_dien_thoai ?? b.phone ?? "",
      lat: Number(b.vi_do ?? b.lat ?? b.latitude ?? 0),
      lng: Number(b.kinh_do ?? b.lng ?? b.longitude ?? 0),
      openHours: b.gio_mo_cua ?? b.opening_hours ?? "",
    }));
  } catch {
    return [];
  }
}

export async function layKhungGioTrong(params: {
  chiNhanhId: string;
  ngay: string;
  soKhach: number;
}): Promise<{ khungGio: string; conTrong: boolean }[]> {
  try {
    const { data } = await apiClient.get("/reservations/khung-gio-trong/", {
      params: { chi_nhanh_id: params.chiNhanhId, ngay: params.ngay, so_khach: params.soKhach },
    });
    return (data.slots ?? []).map((s: any) => ({
      khungGio: s.khung_gio,
      conTrong: s.con_trong,
    }));
  } catch {
    // Không báo các khung giờ là còn trống khi máy chủ chưa trả lời.
    return [];
  }
}

export async function layChinhSachDatCoc(chiNhanhId?: string): Promise<DepositPolicy> {
  try {
    const { data } = await apiClient.get("/reservations/chinh_sach_coc/", {
      params: chiNhanhId ? { branch: chiNhanhId } : {},
    });
    if (data) {
      return {
        depositPercentage: Number(data.phan_tram_coc ?? 20),
        cancellationRules: (data.quy_tac_huy ?? []).map((r: any) => ({
          timeBucket: r.moc_thoi_gian,
          refundPercentage: Number(r.phan_tram_hoan_tien ?? 0),
        })),
        holdMinutes: Number(data.thoi_gian_giu_cho_phut ?? 10),
        paymentExpiryMinutes: Number(data.han_thanh_toan_phut ?? 15),
      };
    }
  } catch {
    // Fallback default
  }
  return {
    depositPercentage: 20,
    holdMinutes: 10,
    paymentExpiryMinutes: 15,
    cancellationRules: [
      { timeBucket: "truoc_24h", refundPercentage: 100 },
      { timeBucket: "tu_6_den_24h", refundPercentage: 50 },
      { timeBucket: "trong_6h", refundPercentage: 0 },
      { timeBucket: "khach_khong_den", refundPercentage: 0 },
    ],
  };
}

export async function giuBan(params: {
  idBan: string;
  ngayDat: string;
  gioDat: string;
  soLuongKhach: number;
}): Promise<{ idGiuBan: string; thoiHanGiuCho: string; holdId: string; heldUntil: string }> {
  const { data } = await apiClient.post(`/tables/${params.idBan}/giu_ban/`, {
    ngay_dat: params.ngayDat,
    gio_bat_dau: params.gioDat,
    so_luong_khach: params.soLuongKhach,
  });
  const idGiuBan = data.id_giu_ban ?? data.hold_id ?? "";
  const thoiHanGiuCho = data.thoi_han_giu_cho ?? data.held_until ?? "";
  return {
    idGiuBan,
    thoiHanGiuCho,
    holdId: idGiuBan,
    heldUntil: thoiHanGiuCho,
  };
}

export async function taoDatBan(params: {
  idGiuBan?: string;
  idBan?: string;
  chiNhanhId?: string;
  ngayDat: string;
  gioDat: string;
  soLuongKhach: number;
  hinhThuc: ReservationOption;
  danhSachMon: ReservationFoodItem[];
  tenKhachHang: string;
  soDienThoai: string;
  ghiChu?: string;
}): Promise<Reservation> {
  const payload: Record<string, any> = {
    ngay_dat: params.ngayDat,
    gio_bat_dau: params.gioDat,
    so_luong_khach: params.soLuongKhach,
    hinh_thuc: {
      table_only: "chi_giu_cho",
      chi_giu_cho: "chi_giu_cho",
      table_and_food: "dat_ban_va_goi_mon",
      dat_ban_va_goi_mon: "dat_ban_va_goi_mon",
      table_and_food_editable: "dat_ban_goi_mon_chinh_sua",
      dat_ban_goi_mon_chinh_sua: "dat_ban_goi_mon_chinh_sua",
    }[params.hinhThuc],
    food_items: params.danhSachMon.map((i) => ({
      mon_an_id: i.food.id,
      so_luong: i.quantity,
    })),
    ten_khach: params.tenKhachHang,
    sdt_khach: params.soDienThoai,
    ghi_chu: params.ghiChu,
  };
  if (params.idGiuBan) payload.id_giu_ban = params.idGiuBan;
  if (params.idBan) payload.ban_an = params.idBan;
  if (params.chiNhanhId) payload.chi_nhanh = Number(params.chiNhanhId);

  const { data } = await apiClient.post("/reservations/", payload);
  return mapThongTinDatBan(data);
}

export async function layDatBanTheoId(id: string): Promise<Reservation> {
  const { data } = await apiClient.get(`/reservations/${id}/`);
  return mapThongTinDatBan(data);
}

export async function taoPhienThanhToanVNPay(
  idDatBan: string
): Promise<VNPayPaymentSession> {
  const { data } = await apiClient.post("/payments/vnpay/create/", {
    loai_thanh_toan: "tien_coc",
    dat_ban_id: Number(idDatBan),
  });
  return {
    paymentUrl: data.payment_url ?? data.duong_dan_thanh_toan ?? "",
    txnRef: data.txn_ref ?? data.ma_giao_dich ?? "",
    amount: Number(data.amount ?? data.so_tien ?? 0),
    expiresAt: data.expires_at ?? data.het_han_luc ?? "",
    duongDanThanhToan: data.payment_url ?? data.duong_dan_thanh_toan ?? "",
    maGiaoDich: data.txn_ref ?? data.ma_giao_dich ?? "",
    soTien: Number(data.amount ?? data.so_tien ?? 0),
    hetHanLuc: data.expires_at ?? data.het_han_luc ?? "",
  };
}

// English aliases
export const getTables = layDanhSachBan;
export const getDepositPolicy = layChinhSachDatCoc;
export const holdTable = giuBan;
export const createReservation = taoDatBan;
export const createVNPayPaymentSession = taoPhienThanhToanVNPay;
