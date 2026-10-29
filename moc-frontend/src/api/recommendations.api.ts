import { apiClient } from "./client";
import { mapGoiY } from "./mappers";
import type { Recommendation } from "@/types";

export async function layGoiYMonAn(gioiHan = 6): Promise<Recommendation[]> {
  try {
    const { data } = await apiClient.get("/recommendations/", { params: { limit: gioiHan } });
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list.map(mapGoiY);
  } catch {
    return [];
  }
}

export const getRecommendations = layGoiYMonAn;
