import { apiClient } from "./client";
import { mapMonAn } from "./mappers";
import type { Food, ComboItem } from "@/types";
import { categories as mockCategories, combos as mockCombos } from "@/data/mock";

export async function layDanhSachMonAn(params?: {
  danhMuc?: string;
  category?: string;
  timKiem?: string;
  search?: string;
  laMonChay?: boolean;
  vegetarian?: boolean;
  doCay?: number;
  spicy?: number;
}): Promise<Food[]> {
  const queryParams: Record<string, any> = {};
  if (params?.danhMuc || params?.category) queryParams.category = params?.danhMuc || params?.category;
  if (params?.timKiem || params?.search) queryParams.search = params?.timKiem || params?.search;
  if (params?.laMonChay || params?.vegetarian) queryParams.vegetarian = "true";
  if (params?.doCay !== undefined || params?.spicy !== undefined) {
    queryParams.spicy = String(params?.doCay ?? params?.spicy);
  }

  try {
    const { data } = await apiClient.get("/foods/", { params: queryParams });
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list.map(mapMonAn);
  } catch {
    return [];
  }
}

export async function layChiTietMonAn(slugOrId: string): Promise<Food | null> {
  try {
    const { data } = await apiClient.get(`/foods/${slugOrId}/`);
    return mapMonAn(data);
  } catch {
    return null;
  }
}

export async function getBestSellers(limit = 6): Promise<Food[]> {
  const all = await layDanhSachMonAn();
  return all.sort((a, b) => b.reviewCount - a.reviewCount).slice(0, limit);
}

export async function getRelatedFoods(food: Food, limit = 3): Promise<Food[]> {
  const all = await layDanhSachMonAn({ category: food.category });
  return all.filter((f) => f.id !== food.id).slice(0, limit);
}

export async function getCategories(): Promise<{ id: "main" | "appetizer" | "drink" | "dessert" | "combo"; label: string; icon: string }[]> {
  return mockCategories as any;
}

export async function getCombos(): Promise<ComboItem[]> {
  return mockCombos;
}

// English aliases
export const getFoods = layDanhSachMonAn;
export const getFoodBySlug = layChiTietMonAn;
export const getFoodById = layChiTietMonAn;
