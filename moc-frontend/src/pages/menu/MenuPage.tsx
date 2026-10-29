import { useState } from "react";
import { useMenuFilters } from "@/hooks/useMenuFilters";
import MenuFilters from "./MenuFilters";
import MenuResults from "./MenuResults";

/**
 * MenuPage composes the sidebar (MenuFilters) and results grid (MenuResults).
 * All filter/sort/search STATE lives in useMenuFilters (src/hooks) so this
 * file only wires props together — no business logic here.
 */
export default function MenuPage() {
  const {
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
  } = useMenuFilters();
  const [filtersOpen, setFiltersOpen] = useState(false);

  return (
    <div className="max-w-310 mx-auto px-5 md:px-8 py-12">
      <div className="mb-10">
        <div className="eyebrow">Thực đơn</div>
        <h1 className="font-display text-[34px] sm:text-[42px]">
          Toàn bộ món ăn
        </h1>
        <p className="text-muted mt-2 max-w-lg">
          {loading
            ? "Đang tải..."
            : `${filteredFoods.length} món phù hợp với lựa chọn của bạn`}
        </p>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        <MenuFilters
          activeCategory={activeCategory}
          onCategoryChange={setCategory}
          maxPrice={maxPrice}
          onMaxPriceChange={setMaxPrice}
          vegOnly={vegOnly}
          onVegOnlyChange={setVegOnly}
          open={filtersOpen}
          onToggleOpen={() => setFiltersOpen((v) => !v)}
        />
        <MenuResults
          foods={filteredFoods}
          loading={loading}
          search={search}
          onSearchChange={setSearch}
          sort={sort}
          onSortChange={setSort}
        />
      </div>
    </div>
  );
}
