import { useAsync } from "@/hooks/useAsync";
import { getRelatedFoods } from "@/api/foods.api";
import FoodCard from "@/components/food/FoodCard";
import type { Food } from "@/types";

export default function RelatedFoods({ food }: { food: Food }) {
  const { data: related, loading } = useAsync(
    () => getRelatedFoods(food),
    [food.id],
  );

  if (!loading && (!related || related.length === 0)) return null;

  return (
    <div className="mt-20">
      <h2 className="font-display text-2xl mb-6">Món tương tự</h2>
      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="rounded-card aspect-4/5 bg-black/5 animate-pulse"
            />
          ))}
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {related?.map((f) => (
            <FoodCard key={f.id} food={f} />
          ))}
        </div>
      )}
    </div>
  );
}
