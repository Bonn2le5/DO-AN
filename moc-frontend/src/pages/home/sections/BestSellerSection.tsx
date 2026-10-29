import SectionHeading from "@/components/ui/SectionHeading";
import FoodCard from "@/components/food/FoodCard";
import { useAsync } from "@/hooks/useAsync";
import { getBestSellers } from "@/api/foods.api";

export default function BestSellerSection() {
  const { data: bestSellers, loading } = useAsync(() => getBestSellers(6));

  return (
    <section className="py-20">
      <div className="max-w-310 mx-auto px-5 md:px-8">
        <SectionHeading
          eyebrow="Được yêu thích nhất"
          title="Món bán chạy"
          linkTo="/thuc-don"
        />
        {loading ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="rounded-card aspect-4/5 bg-black/5 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {bestSellers?.map((food) => (
              <FoodCard key={food.id} food={food} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
