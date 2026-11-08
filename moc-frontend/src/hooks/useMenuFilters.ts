import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getFoods } from "@/api/foods.api";
import type { Food, FoodCategory } from "@/types";

export type SortKey = "popular" | "price-asc" | "price-desc" | "rating";

export const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "popular", label: "Phổ biến nhất" },
  { key: "rating", label: "Đánh giá cao nhất" },
  { key: "price-asc", label: "Giá tăng dần" },
  { key: "price-desc", label: "Giá giảm dần" },
];

export function useMenuFilters() {
  const [params, setParams] = useSearchParams();
  const activeCategory = params.get("category") as FoodCategory | null;

  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<SortKey>("popular");
  const [allFoods, setAllFoods] = useState<Food[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getFoods()
      .then(setAllFoods)
      .finally(() => setLoading(false));
  }, []);

  const setCategory = (cat: FoodCategory | null) => {
    if (cat) params.set("category", cat);
    else params.delete("category");
    setParams(params, { replace: true });
  };

  const filteredFoods = useMemo(() => {
    let list = [...allFoods];
    if (activeCategory) {
      list = list.filter((f) => {
        if (f.category === activeCategory) return true;
        const norm = (str?: string) => (str ?? "").trim().toLowerCase();
        const catNorm = norm(String(f.category));
        const activeNorm = norm(activeCategory);
        if (catNorm === activeNorm) return true;
        if (f.categoryLabel && norm(f.categoryLabel) === activeNorm) return true;

        const isAppetizer = (c: string) => c.includes("appetizer") || c.includes("khai-vi") || c.includes("khai vị");
        const isMain = (c: string) => c.includes("main") || c.includes("mon-chinh") || c.includes("món chính");
        const isDrink = (c: string) => c.includes("drink") || c.includes("do-uong") || c.includes("đồ uống");
        const isDessert = (c: string) => c.includes("dessert") || c.includes("trang-mieng") || c.includes("tráng miệng");
        const isCombo = (c: string) => c.includes("combo");

        if (isAppetizer(activeNorm) && (isAppetizer(catNorm) || isAppetizer(norm(f.categoryLabel)))) return true;
        if (isMain(activeNorm) && (isMain(catNorm) || isMain(norm(f.categoryLabel)))) return true;
        if (isDrink(activeNorm) && (isDrink(catNorm) || isDrink(norm(f.categoryLabel)))) return true;
        if (isDessert(activeNorm) && (isDessert(catNorm) || isDessert(norm(f.categoryLabel)))) return true;
        if (isCombo(activeNorm) && (isCombo(catNorm) || isCombo(norm(f.categoryLabel)))) return true;

        return false;
      });
    }
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (f) => f.name.toLowerCase().includes(q) || f.tags.some((t) => t.toLowerCase().includes(q))
      );
    }

    switch (sort) {
      case "price-asc":
        return list.sort((a, b) => a.price - b.price);
      case "price-desc":
        return list.sort((a, b) => b.price - a.price);
      case "rating":
        return list.sort((a, b) => b.rating - a.rating);
      default:
        return list.sort((a, b) => b.reviewCount - a.reviewCount);
    }
  }, [allFoods, activeCategory, search, sort]);

  return {
    activeCategory,
    setCategory,
    search,
    setSearch,
    sort,
    setSort,
    filteredFoods,
    loading,
  };
}
