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
  const [vegOnly, setVegOnly] = useState(false);
  const [maxPrice, setMaxPrice] = useState(300000);
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
    if (activeCategory) list = list.filter((f) => f.category === activeCategory);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (f) => f.name.toLowerCase().includes(q) || f.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    if (vegOnly) list = list.filter((f) => f.isVegetarian);
    list = list.filter((f) => f.price <= maxPrice);

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
  }, [allFoods, activeCategory, search, sort, vegOnly, maxPrice]);

  return {
    activeCategory,
    setCategory,
    search,
    setSearch,
    sort,
    setSort,
    vegOnly,
    setVegOnly,
    maxPrice,
    setMaxPrice,
    filteredFoods,
    loading,
  };
}
