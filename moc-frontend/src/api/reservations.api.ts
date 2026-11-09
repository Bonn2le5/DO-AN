import { apiClient } from "./client";
import { mapBanAn, mapThongTinDatBan } from "./mappers";
import type {
  BanAn,
  ChinhSachDatCoc,
  ThongTinDatBan,
  PhienThanhToanVNPay,
  HinhThucDatBan,
  MonAnDatBan,
  ChiNhanh,
  QuyTacHuyCoc,
} from "@/types";

export async function layDanhSachBan(chiNhanhId?: string): Promise<BanAn[]> {
  try {
    const params = chiNhanhId ? { chi_nhanh: chiNhanhId } : {};
    const { data } = await apiClient.get("/tables/", { params });
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list.map(mapBanAn);
  } catch {
    return [];
  }
}

export async function layDanhSachChiNhanh(): Promise<ChiNhanh[]> {
  try {
    const { data } = await apiClient.get("/branches/");
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list.map((b: any): ChiNhanh => ({
      id: String(b.id),
      tenChiNhanh: b.ten ?? b.name ?? "",
      diaChi: b.dia_chi ?? b.address ?? "",
      soDienThoai: b.so_dien_thoai ?? b.phone ?? "",
      viDo: Number(b.vi_do ?? b.lat ?? b.latitude ?? 0),
      kinhDo: Number(b.kinh_do ?? b.lng ?? b.longitude ?? 0),
      gioMoCua: b.gio_mo_cua ?? b.opening_hours ?? "",
    }));
  } catch {
    return [];
  }
}

export async function layKhungGioTrong(params: {
  chiNhanhId: string;
  ngay: string;
  soKhach: number;
}): Promise<{ khungGio: string; conTrong: boolean; soChoConLai: number }[]> {
  try {
    const { data } = await apiClient.get("/reservations/khung-gio-trong/", {
      params: { chi_nhanh_id: params.chiNhanhId, ngay: params.ngay, so_khach: params.soKhach },
    });
    return (data.slots ?? []).map((s: any) => ({
      khungGio: s.khung_gio,
      conTrong: s.con_trong,
      soChoConLai: Number(s.so_cho_con_lai ?? 0),
    }));
  } catch {
    // Không báo các khung giờ là còn trống khi máy chủ chưa trả lời.
    return [];
  }
}

export async function layChinhSachDatCoc(chiNhanhId?: string): Promise<ChinhSachDatCoc> {
  try {
    const { data } = await apiClient.get("/reservations/chinh_sach_coc/", {
      params: chiNhanhId ? { branch: chiNhanhId } : {},
    });
    if (data) {
      return {
        phanTramCoc: Number(data.phan_tram_coc ?? 20),
        quyTacHuyBan: (data.quy_tac_huy ?? []).map((r: any): QuyTacHuyCoc => ({
          mocThoiGian: r.moc_thoi_gian,
          phanTramHoanTien: Number(r.phan_tram_hoan_tien ?? 0),
        })),
        thoiGianGiuChoPhut: Number(data.thoi_gian_giu_cho_phut ?? 10),
        hanThanhToanPhut: Number(data.han_thanh_toan_phut ?? 15),
      };
    }
  } catch {
    // Fallback default
  }
  return {
    phanTramCoc: 20,
    thoiGianGiuChoPhut: 10,
    hanThanhToanPhut: 15,
    quyTacHuyBan: [
      { mocThoiGian: "truoc_24h", phanTramHoanTien: 100 },
      { mocThoiGian: "tu_6_den_24h", phanTramHoanTien: 50 },
      { mocThoiGian: "trong_6h", phanTramHoanTien: 0 },
      { mocThoiGian: "khach_khong_den", phanTramHoanTien: 0 },
    ],
  };
}

export async function taoDatBan(params: {
  chiNhanhId?: string;
  ngayDat: string;
  gioDat: string;
  soLuongKhach: number;
  hinhThuc: HinhThucDatBan;
  danhSachMon: MonAnDatBan[];
  tenKhachHang: string;
  soDienThoai: string;
  ghiChu?: string;
}): Promise<ThongTinDatBan> {
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
      mon_an_id: i.monAn.id,
      so_luong: i.soLuong,
    })),
    ten_khach: params.tenKhachHang,
    sdt_khach: params.soDienThoai,
    ghi_chu: params.ghiChu,
  };
  if (params.chiNhanhId) payload.chi_nhanh = Number(params.chiNhanhId);

  const { data } = await apiClient.post("/reservations/", payload);
  return mapThongTinDatBan(data);
}

export async function layDatBanTheoId(id: string): Promise<ThongTinDatBan> {
  const { data } = await apiClient.get(`/reservations/${id}/`);
  return mapThongTinDatBan(data);
}

export async function layDatBanCuaToi(): Promise<ThongTinDatBan[]> {
  const { data } = await apiClient.get("/reservations/", { params: { mine: 1 } });
  return (Array.isArray(data) ? data : data.results).map(mapThongTinDatBan);
}

export async function taoPhienThanhToanVNPay(
  idDatBan: string
): Promise<PhienThanhToanVNPay> {
  const { data } = await apiClient.post("/payments/vnpay/create/", {
    loai_thanh_toan: "tien_coc",
    dat_ban_id: Number(idDatBan),
  });
  return {
    duongDanThanhToan: data.payment_url ?? data.duong_dan_thanh_toan ?? "",
    maGiaoDich: data.txn_ref ?? data.ma_giao_dich ?? "",
    soTien: Number(data.amount ?? data.so_tien ?? 0),
    hetHanLuc: data.expires_at ?? data.het_han_luc ?? "",
  };
}

