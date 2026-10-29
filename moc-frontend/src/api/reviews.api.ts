import { apiClient } from "./client";
import { mapReview } from "./mappers";
import type { Review } from "@/types";

export async function getReviewsByFood(foodId: string): Promise<Review[]> {
  const { data } = await apiClient.get("/reviews/", { params: { food: foodId } });
  return (Array.isArray(data) ? data : data.results).map(mapReview);
}
