import { Minus, Plus, UtensilsCrossed } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getFoods } from "@/api/foods.api";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { formatCurrency } from "@/lib/utils";
import type { ReservationFoodItem, Food } from "@/types";

const FILTERS = [
  { id: "all", label: "Tất cả" },
  { id: "appetizer", label: "Khai vị" },
  { id: "main", label: "Món chính" },
  { id: "dessert", label: "Tráng miệng" },
];

const foodGroup = (food: Food) => {
  const category = `${food.category} ${food.categoryLabel ?? ""}`.toLocaleLowerCase("vi");
  if (category.includes("khai") || category.includes("appetizer")) return "appetizer";
  if (category.includes("tráng") || category.includes("dessert")) return "dessert";
  return "main";
};

interface FoodStepProps {
  foodItems: ReservationFoodItem[];
  onAdd: (food: Food) => void;
  onUpdateQty: (foodId: string, quantity: number) => void;
  subtotal: number;
  depositAmount: number;
  activeCategory: string;
  onCategoryChange: (category: string) => void;
  highPeak: boolean;
  onContinue: () => void;
}

export default function FoodStep({
  foodItems,
  onAdd,
  onUpdateQty,
  subtotal,
  depositAmount,
  activeCategory,
  onCategoryChange,
  highPeak,
  onContinue,
}: FoodStepProps) {
  const { data: foods, loading } = useAsync(() => getFoods());
  const selectedCount = foodItems.reduce((count, item) => count + item.quantity, 0);
  const visibleFoods = (foods ?? []).filter((food) => activeCategory === "all" || foodGroup(food) === activeCategory);
  const qtyOf = (foodId: string) => foodItems.find((item) => item.food.id === foodId)?.quantity ?? 0;

  return (
    <div className="pb-28">
      <div className="flex items-center justify-between gap-4 mb-5">
        <div>
          <h2 className="font-display text-3xl mb-2">Gọi món trước?</h2>
          <p className="text-muted">Món được chuẩn bị sẵn trước giờ bạn đến. Bạn có thể bỏ qua và gọi món tại nhà hàng.</p>
        </div>
      </div>

      {highPeak && (
        <div className="rounded-xl bg-primary/8 border border-primary/15 px-4 py-3 text-sm mb-6">
          Bạn đặt vào khung giờ cao điểm. Gọi món trước giúp bạn không phải chờ lâu.
        </div>
      )}

      {foodItems.length > 0 && (
        <section className="card p-4 md:p-5 mb-6">
          <h3 className="font-display text-lg mb-3">Món đã chọn</h3>
          <div className="space-y-3">
            {foodItems.map(({ food, quantity }) => (
              <div key={food.id} className="flex items-center gap-3">
                <FoodImage food={food} className="w-12 h-12 rounded-lg" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold truncate">{food.name}</div>
                  <div className="text-sm text-muted">{formatCurrency(food.price)}</div>
                </div>
                <QuantityControl quantity={quantity} onDecrease={() => onUpdateQty(food.id, quantity - 1)} onIncrease={() => onUpdateQty(food.id, quantity + 1)} />
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="flex gap-2 overflow-x-auto pb-2 mb-4" role="tablist" aria-label="Lọc nhóm món">
        {FILTERS.map((filter) => (
          <button key={filter.id} type="button" role="tab" aria-selected={activeCategory === filter.id}
            onClick={() => onCategoryChange(filter.id)}
            className={`rounded-full px-4 py-2 text-sm font-medium whitespace-nowrap border transition-colors ${activeCategory === filter.id ? "bg-dark text-white border-dark" : "border-black/15 hover:border-dark"}`}>
            {filter.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, index) => <div key={index} className="h-64 rounded-2xl bg-black/5 animate-pulse" />)}
        </div>
      ) : visibleFoods.length === 0 ? (
        <p className="card p-8 text-center text-muted">Không có món trong nhóm này.</p>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {visibleFoods.map((food) => {
            const quantity = qtyOf(food.id);
            return (
              <article key={food.id} className="card overflow-hidden">
                <FoodImage food={food} className="w-full aspect-[1.6]" />
                <div className="p-4">
                  <h3 className="font-display text-lg leading-snug mb-3">{food.name}</h3>
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-bold text-primary">{formatCurrency(food.price)}</span>
                    {quantity === 0 ? (
                      <button type="button" onClick={() => onAdd(food)} className="btn btn-outline px-3! py-1.5! text-sm!">Thêm món</button>
                    ) : (
                      <QuantityControl quantity={quantity} onDecrease={() => onUpdateQty(food.id, quantity - 1)} onIncrease={() => onUpdateQty(food.id, quantity + 1)} />
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-black/10 bg-bg/95 backdrop-blur px-5 py-3 md:px-8">
        <div className="max-w-275 mx-auto flex items-center justify-between gap-4">
          <div className="min-w-0">
            {selectedCount === 0 ? (
              <span className="text-sm text-muted">Chưa chọn món nào</span>
            ) : (
              <div className="flex flex-col sm:flex-row sm:items-center sm:gap-5">
                <span className="text-sm text-muted">{selectedCount} món · Tổng {formatCurrency(subtotal)}</span>
                <span className="text-sm font-semibold text-primary">Cọc dự kiến {formatCurrency(depositAmount)}</span>
              </div>
            )}
          </div>
          <button type="button" onClick={onContinue} className="btn btn-primary shrink-0 px-6!">
            {selectedCount === 0 ? "Bỏ qua" : "Tiếp tục"}
          </button>
        </div>
      </div>
    </div>
  );
}

function FoodImage({ food, className }: { food: Food; className: string }) {
  return food.imageUrl
    ? <img src={food.imageUrl} alt={food.name} className={`${className} object-cover bg-black/5`} />
    : <PlaceholderMedia tone={food.placeholderTone} icon={UtensilsCrossed} className={className} iconClassName="w-8 h-8" />;
}

function QuantityControl({ quantity, onDecrease, onIncrease }: { quantity: number; onDecrease: () => void; onIncrease: () => void }) {
  return (
    <div className="flex items-center gap-2 shrink-0">
      <button type="button" aria-label="Giảm số lượng" onClick={onDecrease} className="w-8 h-8 rounded-full border border-black/15 flex items-center justify-center"><Minus width={13} height={13} /></button>
      <span className="w-5 text-center text-sm font-semibold">{quantity}</span>
      <button type="button" aria-label="Tăng số lượng" onClick={onIncrease} className="w-8 h-8 rounded-full border border-black/15 flex items-center justify-center"><Plus width={13} height={13} /></button>
    </div>
  );
}
