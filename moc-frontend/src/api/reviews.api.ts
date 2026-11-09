import { apiClient } from "./client";
import { mapDanhGia } from "./mappers";
import type { DanhGiaMonAn } from "@/types";

export async function getReviewsByFood(foodId: string): Promise<DanhGiaMonAn[]> {
  const { data } = await apiClient.get("/reviews/", { params: { mon_an: foodId } });
  return (Array.isArray(data) ? data : data.results).map(mapDanhGia);
}

export async function getMyReviews(): Promise<DanhGiaMonAn[]> {
  const { data } = await apiClient.get("/reviews/", { params: { mine: 1 } });
  return (Array.isArray(data) ? data : data.results).map(mapDanhGia);
}

// Backend tự tìm món khách đã dùng trong đơn tại bàn đã hoàn tất.
export async function createReview(foodId: string, rating: number, comment: string): Promise<void> {
  await apiClient.post("/reviews/", { mon_an: foodId, diem_danh_gia: rating, nhan_xet: comment });
}
