import { useAsync } from "@/hooks/useAsync";
import { getCategories } from "@/api/foods.api";
import type { LoaiMonAn } from "@/types";
import { cn } from "@/lib/utils";

interface MenuFiltersProps {
  activeCategory: LoaiMonAn | null;
  onCategoryChange: (cat: LoaiMonAn | null) => void;
}

/** Hàng nút danh mục (lấy từ backend), cuộn ngang trên màn hình nhỏ. */
export default function MenuFilters({
  activeCategory,
  onCategoryChange,
}: MenuFiltersProps) {
  const { data: categories } = useAsync(getCategories);

  const chip = (active: boolean) =>
    cn(
      "shrink-0 whitespace-nowrap px-3.5 py-1.5 rounded-md border text-sm transition-colors",
      active
        ? "bg-dark border-dark text-white font-semibold"
        : "border-black/15 hover:border-black/40",
    );

  return (
    <nav
      aria-label="Danh mục món"
      className="-mx-5 px-5 md:mx-0 md:px-0 flex gap-2 overflow-x-auto lg:flex-wrap [scrollbar-width:none]"
    >
      <button
        onClick={() => onCategoryChange(null)}
        className={chip(!activeCategory)}
      >
        Tất cả
      </button>
      {categories?.map((cat) => (
        <button
          key={cat.id}
          onClick={() => onCategoryChange(cat.id)}
          className={chip(activeCategory === cat.id)}
        >
          {cat.ten}
        </button>
      ))}
    </nav>
  );
}
