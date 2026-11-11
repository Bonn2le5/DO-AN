import { apiClient } from "./client";
import { mapKhuyenMai } from "./mappers";
import type { KhuyenMai } from "@/types";

export async function getPromotions(): Promise<KhuyenMai[]> {
  const { data } = await apiClient.get("/khuyen-mai/", { params: { con_han: true } });
  return (Array.isArray(data) ? data : data.results).map(mapKhuyenMai);
}
