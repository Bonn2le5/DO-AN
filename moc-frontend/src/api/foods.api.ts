import { apiClient } from "./client";
import { mapMonAn } from "./mappers";
import type { Food, ComboItem, CategoryItem } from "@/types";
import { combos as mockCombos } from "@/data/mock";

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
  const cat = params?.danhMuc || params?.category;
  if (cat) {
    queryParams.category = cat;
    queryParams.danh_muc = cat;
  }
  const q = params?.timKiem || params?.search;
  if (q) {
    queryParams.search = q;
    queryParams.tim_kiem = q;
  }
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

export async function getCategories(): Promise<CategoryItem[]> {
  try {
    const { data } = await apiClient.get("/categories/");
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list
        .filter((cat: any) => cat.con_hoat_dong ?? cat.is_active ?? true)
        .map((cat: any) => ({
          id: String(cat.duong_dan || cat.slug || cat.id),
          numericId: cat.id,
          label: cat.ten || cat.name || "",
          slug: cat.duong_dan || cat.slug || String(cat.id),
          description: cat.mo_ta || cat.description || "",
          image: cat.anh_dai_dien || cat.image || "",
          icon: cat.icon,
          isActive: Boolean(cat.con_hoat_dong ?? cat.is_active ?? true),
        }));
  } catch (error) {
    console.warn("Failed to fetch categories from API:", error);
    return [];
  }
}

export async function getCombos(): Promise<ComboItem[]> {
  return mockCombos;
}

// English aliases
export const getFoods = layDanhSachMonAn;
export const getFoodBySlug = layChiTietMonAn;
export const getFoodById = layChiTietMonAn;
