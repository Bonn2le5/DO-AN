import { Link } from "react-router-dom";
import { Heart, Plus, UtensilsCrossed } from "lucide-react";
import type { Food } from "@/types";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import RatingStars from "@/components/ui/RatingStars";
import { useCartStore } from "@/store/cartStore";
import { useFavoriteStore } from "@/store/favoriteStore";
import { formatCurrency, cn } from "@/lib/utils";

export default function FoodCard({ food }: { food: Food }) {
  const addItem = useCartStore((s) => s.addItem);
  const isFavorite = useFavoriteStore((s) => s.isFavorite(food.id));
  const toggleFavorite = useFavoriteStore((s) => s.toggle);

  return (
    <div className="card overflow-hidden group transition-all duration-400 hover:-translate-y-1.5 hover:shadow-lift">
      <Link
        to={`/thuc-don/${food.slug}`}
        className="block relative aspect-4/3 overflow-hidden"
      >
        <PlaceholderMedia
          tone={food.placeholderTone}
          icon={UtensilsCrossed}
          className="w-full h-full transition-transform duration-700 group-hover:scale-105"
        />
        {food.badge && (
          <span className="absolute top-3 left-3 bg-dark text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
            {food.badge}
          </span>
        )}
        {!food.available && (
          <span className="absolute inset-0 bg-dark/55 flex items-center justify-center text-white text-sm font-semibold">
            Tạm hết hàng
          </span>
        )}
        <button
          onClick={(e) => {
            e.preventDefault();
            toggleFavorite(food.id);
          }}
          className="absolute top-2.5 right-2.5 w-8.5 h-8.5 rounded-full bg-white/90 flex items-center justify-center hover:scale-110 transition-transform"
        >
          <Heart
            width={16}
            height={16}
            className={cn(
              isFavorite ? "fill-primary stroke-primary" : "stroke-dark",
            )}
          />
        </button>
      </Link>
      <div className="p-5">
        <div className="text-[11.5px] uppercase tracking-wider text-muted font-bold">
          {food.categoryLabel}
        </div>
        <Link to={`/thuc-don/${food.slug}`}>
          <h3 className="font-display text-xl mt-1.5 mb-1.5 hover:text-primary transition-colors">
            {food.name}
          </h3>
        </Link>
        <p className="text-[13.5px] text-muted leading-relaxed mb-3.5 min-h-9.5 line-clamp-2">
          {food.description}
        </p>
        <div className="flex items-center gap-1.5 text-[12.5px] text-muted mb-3">
          <RatingStars rating={food.rating} />
          <span>
            {food.rating} · {food.reviewCount} đánh giá
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-primary">
            {formatCurrency(food.price)}
          </span>
          <button
            disabled={!food.available}
            onClick={() => addItem(food)}
            className="w-10 h-10 rounded-full bg-dark text-white flex items-center justify-center hover:bg-primary hover:scale-105 transition-all disabled:opacity-30 disabled:hover:bg-dark disabled:hover:scale-100"
          >
            <Plus width={17} height={17} />
          </button>
        </div>
      </div>
    </div>
  );
}
