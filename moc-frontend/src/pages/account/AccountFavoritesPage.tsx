import { Heart } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getFoods } from "@/api/foods.api";
import { useFavoriteStore } from "@/store/favoriteStore";
import FoodCard from "@/components/food/FoodCard";

export default function AccountFavoritesPage() {
  const favoriteIds = useFavoriteStore((s) => s.ids);
  const { data: allFoods, loading } = useAsync(() => getFoods());
  const favoriteFoods = (allFoods ?? []).filter((f) => favoriteIds.has(f.id));

  return (
    <div>
      <h2 className="font-display text-xl mb-6">Món ăn yêu thích</h2>
      {loading ? (
        <div className="grid sm:grid-cols-2 gap-5">
          {Array.from({ length: 2 }).map((_, i) => (
            <div
              key={i}
              className="rounded-card aspect-4/5 bg-black/5 animate-pulse"
            />
          ))}
        </div>
      ) : favoriteFoods.length === 0 ? (
        <div className="card p-10 text-center">
          <Heart width={30} height={30} className="mx-auto mb-3 text-muted" />
          <p className="text-muted text-sm">
            Bạn chưa lưu món ăn yêu thích nào.
          </p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-5">
          {favoriteFoods.map((f) => (
            <FoodCard key={f.id} food={f} />
          ))}
        </div>
      )}
    </div>
  );
}
