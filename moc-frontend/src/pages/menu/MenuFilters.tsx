import { SlidersHorizontal } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getCategories } from "@/api/foods.api";
import type { FoodCategory } from "@/types";
import { cn } from "@/lib/utils";

interface MenuFiltersProps {
  activeCategory: FoodCategory | null;
  onCategoryChange: (cat: FoodCategory | null) => void;
  open: boolean;
  onToggleOpen: () => void;
}

export default function MenuFilters({
  activeCategory,
  onCategoryChange,
  open,
  onToggleOpen,
}: MenuFiltersProps) {
  const { data: categories } = useAsync(getCategories);

  return (
    <aside className="md:w-52 shrink-0">
      <button
        className="md:hidden btn btn-outline w-full mb-4 rounded-md!"
        onClick={onToggleOpen}
      >
        <SlidersHorizontal width={16} height={16} />
        {open ? "Ẩn bộ lọc" : "Hiện bộ lọc"}
      </button>

      <div className={cn("space-y-6 md:border-r md:border-black/10 md:pr-6", !open && "hidden md:block")}>
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted mb-2.5">
            Danh mục
          </h3>
          <div className="flex flex-wrap md:flex-col gap-1.5 md:gap-0.5">
            <button
              onClick={() => onCategoryChange(null)}
              className={cn(
                "text-left px-3 py-1.5 rounded-sm text-sm transition-colors border border-black/10 md:border-transparent",
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
                  "text-left px-3 py-1.5 rounded-sm text-sm transition-colors border border-black/10 md:border-transparent",
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
      </div>
    </aside>
  );
}
