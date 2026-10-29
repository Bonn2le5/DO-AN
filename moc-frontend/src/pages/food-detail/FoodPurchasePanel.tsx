import { useState } from "react";
import { Heart, Flame, Leaf, Minus, Plus } from "lucide-react";
import RatingStars from "@/components/ui/RatingStars";
import { useCartStore } from "@/store/cartStore";
import { useFavoriteStore } from "@/store/favoriteStore";
import { formatCurrency, cn } from "@/lib/utils";
import type { Food } from "@/types";

export default function FoodPurchasePanel({ food }: { food: Food }) {
  const [qty, setQty] = useState(1);
  const [note, setNote] = useState("");
  const addItem = useCartStore((s) => s.addItem);
  const isFavorite = useFavoriteStore((s) => s.isFavorite(food.id));
  const toggleFavorite = useFavoriteStore((s) => s.toggle);

  const handleAdd = () => {
    addItem(food, qty);
    setQty(1);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[12.5px] font-bold uppercase tracking-wide text-primary">
          {food.categoryLabel}
        </span>
        {food.badge && (
          <span className="bg-dark text-white text-[11px] font-bold px-2.5 py-1 rounded-full">
            {food.badge}
          </span>
        )}
      </div>
      <h1 className="font-display text-[32px] sm:text-[38px] mb-3">
        {food.name}
      </h1>

      <div className="flex items-center gap-2.5 mb-5">
        <RatingStars rating={food.rating} size={15} />
        <span className="text-sm text-muted">
          {food.rating} · {food.reviewCount} đánh giá
        </span>
      </div>

      <p className="text-[15px] text-muted leading-relaxed mb-6">
        {food.longDescription}
      </p>

      <div className="flex flex-wrap gap-2 mb-6">
        {food.isVegetarian && (
          <span className="inline-flex items-center gap-1.5 bg-success/10 text-success text-xs font-semibold px-3 py-1.5 rounded-full">
            <Leaf width={13} height={13} /> Món chay
          </span>
        )}
        {food.spicyLevel > 0 && (
          <span className="inline-flex items-center gap-1.5 bg-primary/10 text-primary text-xs font-semibold px-3 py-1.5 rounded-full">
            <Flame width={13} height={13} /> Độ cay {food.spicyLevel}/3
          </span>
        )}
        {food.tags.map((tag) => (
          <span
            key={tag}
            className="bg-black/5 text-xs font-medium px-3 py-1.5 rounded-full"
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-bold uppercase tracking-wide text-muted mb-2.5">
          Nguyên liệu chính
        </h3>
        <p className="text-sm text-text">{food.ingredients.join(", ")}</p>
      </div>

      <div className="border-t border-black/8 pt-6">
        <div className="flex items-baseline justify-between mb-5">
          <span className="font-display text-3xl text-primary">
            {formatCurrency(food.price)}
          </span>
          {!food.available ? (
            <span className="text-sm font-semibold text-primary">
              Tạm hết hàng
            </span>
          ) : (
            <span className="text-sm text-muted">
              Còn {food.stock} phần hôm nay
            </span>
          )}
        </div>

        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Ghi chú cho món ăn (ví dụ: ít cay, không hành...)"
          rows={2}
          className="w-full px-4 py-3 rounded-xl border border-black/15 text-sm outline-none focus:border-primary mb-5 resize-none"
        />

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3 border border-black/15 rounded-full px-2 py-1.5">
            <button
              onClick={() => setQty((q) => Math.max(1, q - 1))}
              className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-black/5"
            >
              <Minus width={14} height={14} />
            </button>
            <span className="w-5 text-center font-semibold">{qty}</span>
            <button
              onClick={() => setQty((q) => q + 1)}
              className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-black/5"
            >
              <Plus width={14} height={14} />
            </button>
          </div>
          <button
            onClick={handleAdd}
            disabled={!food.available}
            className="btn btn-primary flex-1 disabled:opacity-40"
          >
            Thêm vào giỏ · {formatCurrency(food.price * qty)}
          </button>
          <button
            onClick={() => toggleFavorite(food.id)}
            className="w-13 h-13 rounded-full border border-black/15 flex items-center justify-center shrink-0 hover:bg-black/5"
          >
            <Heart
              width={19}
              height={19}
              className={cn(
                isFavorite ? "fill-primary stroke-primary" : "stroke-dark",
              )}
            />
          </button>
        </div>
      </div>
    </div>
  );
}
