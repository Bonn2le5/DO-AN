import { apiClient } from "./client";
import { mapPromotion } from "./mappers";
import type { Promotion } from "@/types";

export async function getPromotions(): Promise<Promotion[]> {
  const { data } = await apiClient.get("/promotions/", { params: { active: true } });
  return (Array.isArray(data) ? data : data.results).map(mapPromotion);
}
