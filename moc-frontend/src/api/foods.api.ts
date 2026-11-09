import { apiClient } from "./client";
import { mapMonAn } from "./mappers";
import type { MonAn, ComboMonAn, MucDanhMuc } from "@/types";
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
}): Promise<MonAn[]> {
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

export async function layChiTietMonAn(slugOrId: string): Promise<MonAn | null> {
  try {
    const { data } = await apiClient.get(`/foods/${slugOrId}/`);
    return mapMonAn(data);
  } catch {
    return null;
  }
}

export async function getBestSellers(limit = 6): Promise<MonAn[]> {
  const all = await layDanhSachMonAn();
  return all.sort((a, b) => b.soLuotDanhGia - a.soLuotDanhGia).slice(0, limit);
}

export async function getRelatedFoods(food: MonAn, limit = 3): Promise<MonAn[]> {
  const all = await layDanhSachMonAn({ category: food.danhMuc });
  return all.filter((f) => f.id !== food.id).slice(0, limit);
}

export async function getCategories(): Promise<MucDanhMuc[]> {
  try {
    const { data } = await apiClient.get("/categories/");
    const list = Array.isArray(data) ? data : data.results ?? [];
    return list
        .filter((cat: any) => cat.con_hoat_dong ?? cat.is_active ?? true)
        .map((cat: any): MucDanhMuc => ({
          id: String(cat.duong_dan || cat.slug || cat.id),
          idSo: cat.id,
          ten: cat.ten || cat.name || "",
          duongDan: cat.duong_dan || cat.slug || String(cat.id),
          moTa: cat.mo_ta || cat.description || "",
          hinhAnh: cat.anh_dai_dien || cat.image || "",
          bieuTuong: cat.icon,
          conHoatDong: Boolean(cat.con_hoat_dong ?? cat.is_active ?? true),
        }));
  } catch (error) {
    console.warn("Failed to fetch categories from API:", error);
    return [];
  }
}

export async function getCombos(): Promise<ComboMonAn[]> {
  return mockCombos;
}

