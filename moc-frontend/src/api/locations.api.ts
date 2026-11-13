import { apiClient } from "./client";
import type { ChiNhanh, ThongTinTuyenDuong } from "@/types";

export async function getBranches(): Promise<ChiNhanh[]> {
  const { data } = await apiClient.get("/chi-nhanh/");
  return (Array.isArray(data) ? data : data.results).map((branch: any): ChiNhanh => ({
    id: String(branch.id), tenChiNhanh: branch.ten, diaChi: branch.dia_chi, soDienThoai: branch.so_dien_thoai,
    viDo: Number(branch.vi_do), kinhDo: Number(branch.kinh_do), gioMoCua: branch.opening_hours,
    laChiNhanhChinh: branch.is_main,
  }));
}

export interface UserCoords {
  lat: number;
  lng: number;
}

function layViTri(options: PositionOptions): Promise<UserCoords> {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      reject,
      options,
    );
  });
}

/**
 * Lấy vị trí người dùng. Thử chế độ thường trước (Wi-Fi/IP — nhanh, chạy được trên PC không có GPS),
 * thất bại vì lý do khác "từ chối quyền" thì thử lại với độ chính xác cao. Cần HTTPS hoặc localhost.
 */
export async function getUserLocation(): Promise<UserCoords> {
  if (!navigator.geolocation) throw new Error("Trình duyệt không hỗ trợ định vị.");
  try {
    return await layViTri({ enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 });
  } catch (err) {
    const loi = err as GeolocationPositionError;
    if (loi.code !== 1) {
      try {
        return await layViTri({ enableHighAccuracy: true, timeout: 20000, maximumAge: 0 });
      } catch (err2) {
        throw new Error(mapGeolocationError(err2 as GeolocationPositionError));
      }
    }
    throw new Error(mapGeolocationError(loi));
  }
}

// So sánh bằng số (1/2/3) thay vì err.PERMISSION_DENIED: một số trình duyệt/extension trả về object thường.
function mapGeolocationError(err: GeolocationPositionError): string {
  switch (err?.code) {
    case 1:
      return "Trình duyệt hoặc hệ điều hành đang chặn định vị. Hãy cho phép vị trí cho trang web, và trên Windows bật Settings › Privacy & security › Location (cả mục \"Let desktop apps access your location\").";
    case 2:
      return "Thiết bị không xác định được vị trí. Trên máy tính, hãy bật dịch vụ định vị của hệ điều hành (Windows: Settings › Privacy & security › Location; macOS: System Settings › Privacy & Security › Location Services) rồi thử lại.";
    case 3:
      return "Định vị quá lâu không phản hồi. Vui lòng thử lại.";
    default:
      return `Không thể lấy vị trí của bạn${err?.message ? ` (${err.message})` : ""}.`;
  }
}

/** Khoảng cách đường chim bay (km) giữa 2 toạ độ — dùng để sắp chi nhánh gần nhất. */
export function khoangCachKm(a: UserCoords, b: UserCoords): number {
  const R = 6371;
  const rad = (d: number) => (d * Math.PI) / 180;
  const dLat = rad(b.lat - a.lat);
  const dLng = rad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/**
 * Fetches a driving route between two points using OSRM's free public demo
 * server (https://project-osrm.org) — no API key required, suitable for
 * prototypes/coursework. For production, self-host OSRM or swap to a paid
 * provider (Goong Maps / Mapbox / Google Directions) by editing this file only.
 */
export async function getRoute(from: UserCoords, to: UserCoords): Promise<ThongTinTuyenDuong> {
  const url = `https://router.project-osrm.org/route/v1/driving/${from.lng},${from.lat};${to.lng},${to.lat}?overview=full&geometries=geojson`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Không tìm được đường đi. Vui lòng thử lại.");
  const data = await res.json();
  const route = data.routes?.[0];
  if (!route) throw new Error("Không tìm thấy tuyến đường phù hợp.");

  const geometry: [number, number][] = route.geometry.coordinates.map(
    ([lng, lat]: [number, number]) => [lat, lng]
  );

  return {
    khoangCachKm: Math.round((route.distance / 1000) * 10) / 10,
    thoiGianPhut: Math.max(1, Math.round(route.duration / 60)),
    toaDoTuyenDuong: geometry,
  };
}
