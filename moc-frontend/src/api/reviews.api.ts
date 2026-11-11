import { apiClient } from "./client";
import { mapDanhGia } from "./mappers";
import type { BuaAnChoDanhGia, DanhGiaMonAn } from "@/types";

export async function getReviewsByFood(foodId: string): Promise<DanhGiaMonAn[]> {
  const { data } = await apiClient.get("/danh-gia/", { params: { mon_an: foodId } });
  return (Array.isArray(data) ? data : data.results).map(mapDanhGia);
}

export async function getMyReviews(): Promise<DanhGiaMonAn[]> {
  const { data } = await apiClient.get("/danh-gia/", { params: { mine: 1 } });
  return (Array.isArray(data) ? data : data.results).map(mapDanhGia);
}

// Backend tự tìm món khách đã dùng trong đơn tại bàn đã hoàn tất.
export async function createReview(foodId: string, rating: number, comment: string): Promise<void> {
  await apiClient.post("/danh-gia/", { mon_an: foodId, diem_danh_gia: rating, nhan_xet: comment });
}

const urlAnh = (duongDan: string) =>
  !duongDan
    ? undefined
    : /^https?:\/\//i.test(duongDan)
      ? duongDan
      : new URL(duongDan, import.meta.env.VITE_API_URL ?? window.location.origin).toString();

/** Các bữa ăn đã hoàn tất còn món hoặc phần đánh giá chung chưa chấm. */
export async function layBuaAnChoDanhGia(): Promise<BuaAnChoDanhGia[]> {
  const { data } = await apiClient.get("/danh-gia/cho-danh-gia/");
  return (data as any[]).map((d) => ({
    id: String(d.id),
    maDonHang: d.ma_don_hang,
    taoLuc: d.tao_luc,
    chiNhanh: d.chi_nhanh ?? "",
    mon: (d.mon as any[]).map((m) => ({
      idChiTiet: String(m.chi_tiet_don_hang),
      idMonAn: String(m.mon_an),
      duongDanMon: m.duong_dan_mon ?? String(m.mon_an),
      tenMon: m.ten_mon,
      duongDanAnh: urlAnh(m.anh),
      soLuong: Number(m.so_luong),
      danhGia: m.danh_gia ? { diemDanhGia: m.danh_gia.diem_danh_gia, nhanXet: m.danh_gia.nhan_xet } : null,
    })),
    danhGiaChung: d.danh_gia_bua_an
      ? {
          diemPhucVu: d.danh_gia_bua_an.diem_phuc_vu,
          diemKhongGian: d.danh_gia_bua_an.diem_khong_gian,
          nhanXet: d.danh_gia_bua_an.nhan_xet,
        }
      : null,
  }));
}

export interface GuiDanhGiaBuaAn {
  idDonHang: string;
  mon: { idChiTiet: string; diemDanhGia: number; nhanXet: string }[];
  chung?: { diemPhucVu: number; diemKhongGian: number; nhanXet: string };
}

/** Gửi một lần cho cả bữa: điểm từng món và/hoặc điểm chung (phục vụ, không gian). */
export async function guiDanhGiaBuaAn(body: GuiDanhGiaBuaAn): Promise<void> {
  await apiClient.post("/danh-gia/bua-an/", {
    don_hang: Number(body.idDonHang),
    mon: body.mon.map((m) => ({ chi_tiet_don_hang: Number(m.idChiTiet), diem_danh_gia: m.diemDanhGia, nhan_xet: m.nhanXet })),
    ...(body.chung
      ? { diem_phuc_vu: body.chung.diemPhucVu, diem_khong_gian: body.chung.diemKhongGian, nhan_xet: body.chung.nhanXet }
      : {}),
  });
}

/** Khách đã dùng món này (đơn hoàn tất) và còn lượt đánh giá chưa? */
export async function coTheDanhGiaMon(foodId: string): Promise<boolean> {
  const { data } = await apiClient.get("/danh-gia/co-the/", { params: { mon_an: foodId } });
  return Boolean(data?.co_the);
}
