import { apiClient } from "./client";
import { mapGoiY } from "./mappers";
import { useAuthStore } from "@/store/authStore";
import type { GoiYMonAn } from "@/types";

/** Vị trí hiển thị gợi ý — khớp SuKienGoiY.ViTri ở backend, dùng để đo CTR theo từng chỗ. */
export type ViTriGoiY = "trang_chu" | "chi_tiet_mon" | "goi_mon";
/** Loại tương tác client được ghi — "dat_mon" / "danh_gia" do backend tự ghi từ đơn và đánh giá. */
export type LoaiTuongTac = "xem" | "yeu_thich";

const toList = (data: any) => (Array.isArray(data) ? data : data?.results ?? []);

// Chống ghi trùng cùng một sự kiện trong 2 giây (React StrictMode chạy effect 2 lần, double-click...)
const daGuiGanDay = new Map<string, number>();
function vuaGui(khoa: string): boolean {
  const now = Date.now();
  const truoc = daGuiGanDay.get(khoa);
  daGuiGanDay.set(khoa, now);
  return truoc !== undefined && now - truoc < 2000;
}

/** Top-N món gợi ý cá nhân (TF-IDF + Cosine) hoặc món phổ biến với khách mới / chưa đăng nhập. */
export async function layGoiYMonAn(gioiHan = 6): Promise<GoiYMonAn[]> {
  try {
    const { data } = await apiClient.get("/goi-y/", { params: { limit: gioiHan } });
    return toList(data).map(mapGoiY);
  } catch {
    return [];
  }
}

/** Món tương tự (Item-to-Item TF-IDF) cho trang chi tiết món. */
export async function layMonTuongTu(monAnId: string, gioiHan = 3): Promise<GoiYMonAn[]> {
  try {
    const { data } = await apiClient.get("/goi-y/tuong-tu/", { params: { mon_an: monAnId, limit: gioiHan } });
    return toList(data).map(mapGoiY);
  } catch {
    return [];
  }
}

/** Ghi tương tác (xem / yêu thích) để cập nhật vector khẩu vị. Bỏ qua khi chưa đăng nhập. */
export function ghiTuongTac(monAnId: string, loai: LoaiTuongTac): void {
  if (!useAuthStore.getState().daDangNhap || !monAnId) return;
  // Yêu thích idempotent ở backend nên không cần chặn trùng (chặn sẽ làm mất lượt thích lại ngay sau khi bỏ)
  if (loai === "xem" && vuaGui(`tt|${loai}|${monAnId}`)) return;
  apiClient.post("/tuong-tac/", { mon_an: Number(monAnId), loai_tuong_tac: loai }).catch(() => {});
}

/** Bỏ yêu thích: xoá tín hiệu "yeu_thich" để vector khẩu vị không còn kéo về món này. */
export function boYeuThich(monAnId: string): void {
  if (!useAuthStore.getState().daDangNhap || !monAnId) return;
  apiClient.post("/tuong-tac/bo-yeu-thich/", { mon_an: Number(monAnId) }).catch(() => {});
}

/** Ghi lượt hiển thị / nhấp món gợi ý (đo CTR & Conversion). Không chặn giao diện nếu lỗi. */
export function ghiSuKienGoiY(
  loai: "hien_thi" | "nhap",
  viTri: ViTriGoiY,
  goiY: GoiYMonAn[],
): void {
  const ids = goiY.map((g) => Number(g.monAn.id)).filter((id) => id > 0);
  if (ids.length === 0 || vuaGui(`sk|${loai}|${viTri}|${ids.join(",")}`)) return;
  apiClient
    .post("/goi-y/su-kien/", {
      loai_su_kien: loai,
      vi_tri: viTri,
      mon_an_ids: ids,
      phien_ban_model: goiY[0]?.phienBanMoHinh ?? "",
    })
    .catch(() => {});
}

