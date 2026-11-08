import { apiClient } from "./client";
import { mapReview } from "./mappers";
import type { Review } from "@/types";

export async function getReviewsByFood(foodId: string): Promise<Review[]> {
  const { data } = await apiClient.get("/reviews/", { params: { food: foodId } });
  return (Array.isArray(data) ? data : data.results).map(mapReview);
}

export async function getMyReviews(): Promise<Review[]> {
  const { data } = await apiClient.get("/reviews/", { params: { mine: 1 } });
  return (Array.isArray(data) ? data : data.results).map(mapReview);
}

// Backend tự tìm món khách đã dùng trong đơn tại bàn đã hoàn tất.
export async function createReview(foodId: string, rating: number, comment: string): Promise<void> {
  await apiClient.post("/reviews/", { mon_an: foodId, diem_danh_gia: rating, nhan_xet: comment });
}
