import { apiClient } from "./client";
import type { Branch, RouteInfo } from "@/types";

export async function getBranches(): Promise<Branch[]> {
  const { data } = await apiClient.get("/branches/");
  return (Array.isArray(data) ? data : data.results).map((branch: any) => ({
    id: String(branch.id), name: branch.name, address: branch.address, phone: branch.phone,
    lat: Number(branch.latitude), lng: Number(branch.longitude), openHours: branch.opening_hours,
    isMain: branch.is_main,
  }));
}

export interface UserCoords {
  lat: number;
  lng: number;
}

/** Wraps the browser Geolocation API in a Promise. Requires HTTPS (or localhost) and user permission. */
export function getUserLocation(): Promise<UserCoords> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Trình duyệt không hỗ trợ định vị."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      (err) => reject(new Error(mapGeolocationError(err))),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
}

function mapGeolocationError(err: GeolocationPositionError): string {
  switch (err.code) {
    case err.PERMISSION_DENIED:
      return "Bạn chưa cho phép truy cập vị trí. Hãy bật quyền định vị cho trang web.";
    case err.POSITION_UNAVAILABLE:
      return "Không thể xác định vị trí hiện tại.";
    case err.TIMEOUT:
      return "Yêu cầu định vị hết thời gian chờ.";
    default:
      return "Không thể lấy vị trí của bạn.";
  }
}

/**
 * Fetches a driving route between two points using OSRM's free public demo
 * server (https://project-osrm.org) — no API key required, suitable for
 * prototypes/coursework. For production, self-host OSRM or swap to a paid
 * provider (Goong Maps / Mapbox / Google Directions) by editing this file only.
 */
export async function getRoute(from: UserCoords, to: UserCoords): Promise<RouteInfo> {
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
    distanceKm: Math.round((route.distance / 1000) * 10) / 10,
    durationMinutes: Math.round(route.duration / 60),
    geometry,
  };
}
