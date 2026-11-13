import { useMenuFilters } from "@/hooks/useMenuFilters";
import MenuFilters from "./MenuFilters";
import MenuResults from "./MenuResults";

/**
 * MenuPage composes the category bar (MenuFilters) and results (MenuResults).
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
    filteredFoods,
    loading,
  } = useMenuFilters();

  return (
    <div className="max-w-310 mx-auto px-5 md:px-8 py-12">
      <div className="mb-8">
        <div className="eyebrow">Thực đơn</div>
        <h1 className="font-display text-[34px] sm:text-[42px]">
          Toàn bộ món ăn
        </h1>
      </div>

      <MenuResults
        foods={filteredFoods}
        loading={loading}
        search={search}
        onSearchChange={setSearch}
        sort={sort}
        onSortChange={setSort}
        categoryBar={
          <MenuFilters
            activeCategory={activeCategory}
            onCategoryChange={setCategory}
          />
        }
      />
    </div>
  );
}
