import { SlidersHorizontal } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getCategories } from "@/api/foods.api";
import type { FoodCategory } from "@/types";
import { cn } from "@/lib/utils";

interface MenuFiltersProps {
  activeCategory: FoodCategory | null;
  onCategoryChange: (cat: FoodCategory | null) => void;
  maxPrice: number;
  onMaxPriceChange: (price: number) => void;
  vegOnly: boolean;
  onVegOnlyChange: (value: boolean) => void;
  open: boolean;
  onToggleOpen: () => void;
}

export default function MenuFilters({
  activeCategory,
  onCategoryChange,
  maxPrice,
  onMaxPriceChange,
  vegOnly,
  onVegOnlyChange,
  open,
  onToggleOpen,
}: MenuFiltersProps) {
  const { data: categories } = useAsync(getCategories);

  return (
    <aside className="md:w-65 shrink-0">
      <button
        className="md:hidden btn btn-outline w-full mb-4"
        onClick={onToggleOpen}
      >
        <SlidersHorizontal width={16} height={16} />
        {open ? "Ẩn bộ lọc" : "Hiện bộ lọc"}
      </button>

      <div className={cn("space-y-8", !open && "hidden md:block")}>
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wide text-muted mb-3.5">
            Danh mục
          </h3>
          <div className="flex flex-wrap md:flex-col gap-2">
            <button
              onClick={() => onCategoryChange(null)}
              className={cn(
                "text-left px-3.5 py-2.5 rounded-lg text-sm transition-colors",
                !activeCategory
                  ? "bg-dark text-white font-semibold"
                  : "hover:bg-black/5",
              )}
            >
              Tất cả món
            </button>
            {categories?.map((cat) => (
              <button
                key={cat.id}
                onClick={() => onCategoryChange(cat.id)}
                className={cn(
                  "text-left px-3.5 py-2.5 rounded-lg text-sm transition-colors",
                  activeCategory === cat.id
                    ? "bg-dark text-white font-semibold"
                    : "hover:bg-black/5",
                )}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-bold uppercase tracking-wide text-muted mb-3.5">
            Mức giá tối đa
          </h3>
          <input
            type="range"
            min={30000}
            max={300000}
            step={10000}
            value={maxPrice}
            onChange={(e) => onMaxPriceChange(Number(e.target.value))}
            className="w-full accent-primary"
          />
          <div className="text-sm text-muted mt-1.5">
            Đến {maxPrice.toLocaleString("vi-VN")}đ
          </div>
        </div>

        <label className="flex items-center gap-2.5 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={vegOnly}
            onChange={(e) => onVegOnlyChange(e.target.checked)}
            className="w-4 h-4 accent-primary"
          />
          Chỉ hiện món chay
        </label>
      </div>
    </aside>
  );
}
