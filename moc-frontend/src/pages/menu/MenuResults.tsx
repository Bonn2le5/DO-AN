import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { Search, X } from "lucide-react";
import FoodCard from "@/components/food/FoodCard";
import { SORT_OPTIONS, type SortKey } from "@/hooks/useMenuFilters";
import type { Food } from "@/types";

interface MenuResultsProps {
  foods: Food[];
  loading: boolean;
  search: string;
  onSearchChange: (value: string) => void;
  sort: SortKey;
  onSortChange: (value: SortKey) => void;
}

export default function MenuResults({
  foods,
  loading,
  search,
  onSearchChange,
  sort,
  onSortChange,
}: MenuResultsProps) {
  const location = useLocation();

  useEffect(() => {
    if (new URLSearchParams(location.search).get("focusSearch") === "1") {
      document.getElementById("menu-search")?.focus();
    }
  }, [location.search]);

  return (
    <div className="flex-1">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-7">
        <div className="relative w-full sm:max-w-xs">
          <Search
            width={15}
            height={15}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <input
            id="menu-search"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Tìm món ăn, nguyên liệu..."
            aria-label="Tìm món ăn hoặc nguyên liệu"
            className="w-full pl-9 pr-8 py-2 rounded-md border border-black/15 text-sm outline-none focus:border-primary"
          />
          {search && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted"
            >
              <X width={15} height={15} />
            </button>
          )}
        </div>
        <select
          value={sort}
          onChange={(e) => onSortChange(e.target.value as SortKey)}
          className="px-3 py-2 rounded-md border border-black/15 text-sm outline-none bg-white"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.key} value={opt.key}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-card aspect-4/5 bg-black/5 animate-pulse"
            />
          ))}
        </div>
      ) : foods.length === 0 ? (
        <div className="text-center py-24 text-muted">
          Không tìm thấy món ăn phù hợp. Hãy thử điều chỉnh bộ lọc.
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {foods.map((food) => (
            <FoodCard key={food.id} food={food} />
          ))}
        </div>
      )}
    </div>
  );
}
