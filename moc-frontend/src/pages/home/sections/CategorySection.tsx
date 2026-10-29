import { Link } from "react-router-dom";
import {
  ArrowRight,
  UtensilsCrossed,
  Salad,
  CupSoda,
  IceCreamBowl,
  LayoutGrid,
} from "lucide-react";
import SectionHeading from "@/components/ui/SectionHeading";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { useAsync } from "@/hooks/useAsync";
import { getCategories } from "@/api/foods.api";

const CATEGORY_ICONS = {
  main: UtensilsCrossed,
  appetizer: Salad,
  drink: CupSoda,
  dessert: IceCreamBowl,
  combo: LayoutGrid,
};

export default function CategorySection() {
  const { data: categories, loading } = useAsync(getCategories);

  return (
    <section className="py-20">
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow="Thực đơn"
          title="Chọn theo danh mục"
          linkTo="/thuc-don"
          linkLabel="Xem toàn bộ thực đơn"
        />
        {loading ? (
          <CategoryGridSkeleton />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 md:gap-5">
            {categories?.map((cat, i) => {
              const Icon = CATEGORY_ICONS[cat.id];
              return (
                <Link
                  key={cat.id}
                  to={`/thuc-don?category=${cat.id}`}
                  className="relative rounded-[20px] overflow-hidden aspect-3/4 group"
                >
                  <PlaceholderMedia
                    tone={((i % 6) + 1) as 1 | 2 | 3 | 4 | 5 | 6}
                    icon={Icon}
                    className="absolute inset-0 w-full h-full transition-transform duration-600 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-linear-to-t from-black/55 via-black/5 to-transparent" />
                  <div className="absolute left-4 right-4 bottom-4 flex items-center justify-between text-white">
                    <span className="font-display text-lg">{cat.label}</span>
                    <span className="w-7 h-7 rounded-full bg-white/20 backdrop-blur flex items-center justify-center group-hover:bg-primary group-hover:rotate-45 transition-all duration-300">
                      <ArrowRight width={13} height={13} />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}

function CategoryGridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 md:gap-5">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="rounded-[20px] aspect-3/4 bg-black/5 animate-pulse"
        />
      ))}
    </div>
  );
}
