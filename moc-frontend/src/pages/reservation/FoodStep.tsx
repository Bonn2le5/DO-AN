import { useMemo } from "react";
import { Minus, Plus, UtensilsCrossed } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getFoods, getCategories } from "@/api/foods.api";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { cn, formatCurrency } from "@/lib/utils";
import { formatLongDate } from "./ReservationTicket";
import FoodSuggestions from "./FoodSuggestions";
import type { ReservationFoodItem, Food } from "@/types";

const FALLBACK_FILTERS = [
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
  depositPercentage: number;
  activeCategory: string;
  onCategoryChange: (category: string) => void;
  highPeak: boolean;
  time: string;
  date: string;
  partySize: number;
  branchName: string;
  onContinue: () => void;
}

export default function FoodStep({
  foodItems,
  onAdd,
  onUpdateQty,
  subtotal,
  depositAmount,
  depositPercentage,
  activeCategory,
  onCategoryChange,
  highPeak,
  time,
  date,
  partySize,
  branchName,
  onContinue,
}: FoodStepProps) {
  const { data: foods, loading } = useAsync(() => getFoods());
  const { data: dbCategories } = useAsync(getCategories);

  const filters = useMemo(() => {
    if (dbCategories && dbCategories.length > 0) {
      return [
        { id: "all", label: "Tất cả" },
        ...dbCategories.map((c) => ({ id: c.id, label: c.label })),
      ];
    }
    return FALLBACK_FILTERS;
  }, [dbCategories]);

  const selectedCount = foodItems.reduce((count, item) => count + item.quantity, 0);
  const visibleFoods = (foods ?? []).filter((food) => {
    if (activeCategory === "all") return true;
    if (food.category === activeCategory) return true;
    if (food.categoryLabel && food.categoryLabel.toLowerCase() === activeCategory.toLowerCase()) return true;
    return foodGroup(food) === activeCategory;
  });
  const qtyOf = (foodId: string) => foodItems.find((item) => item.food.id === foodId)?.quantity ?? 0;
  const continueLabel = selectedCount === 0 ? "Bỏ qua, chỉ giữ chỗ" : "Tiếp tục xác nhận";

  return (
    <div className="pb-28 lg:pb-0">
      <p className="text-muted max-w-[62ch] mb-5">
        Món gọi trước được bếp chuẩn bị sẵn, lên bàn ngay khi bạn đến. Gọi món trước cần cọc {depositPercentage}% tiền món. Không muốn gọi trước? Bỏ qua bước này và gọi tại nhà hàng.
      </p>

      {highPeak && (
        <div className="rounded-xl bg-accent/12 border border-accent/30 px-4 py-3 text-sm mb-6">
          {time} tối cuối tuần là giờ đông khách. Gọi món trước giúp bạn không phải chờ bếp.
        </div>
      )}

      <div className="grid lg:grid-cols-[minmax(0,1fr)_320px] gap-8 items-start">
        <div className="min-w-0">
          <FoodSuggestions selectedFoods={foodItems.map((item) => item.food)} onAdd={onAdd} />

          <div className="flex gap-2 overflow-x-auto pb-2 mb-4 -mx-4 px-4 sm:mx-0 sm:px-0 [scrollbar-width:none]" role="tablist" aria-label="Lọc nhóm món">
            {filters.map((filter) => (
              <button key={filter.id} type="button" role="tab" aria-selected={activeCategory === filter.id}
                onClick={() => onCategoryChange(filter.id)}
                className={cn(
                  "rounded-full px-4 py-2 text-sm font-medium whitespace-nowrap border transition-colors",
                  activeCategory === filter.id ? "bg-primary text-white border-primary" : "bg-white border-black/12 hover:border-primary hover:text-primary",
                )}>
                {filter.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="grid grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
              {Array.from({ length: 6 }).map((_, index) => <div key={index} className="h-60 rounded-2xl bg-black/5 animate-pulse" />)}
            </div>
          ) : visibleFoods.length === 0 ? (
            <p className="bg-white rounded-2xl border border-black/[0.07] p-8 text-center text-muted">Nhóm này chưa có món. Chọn nhóm khác để xem thực đơn.</p>
          ) : (
            <div className="grid grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
              {visibleFoods.map((food) => {
                const quantity = qtyOf(food.id);
                return (
                  <article key={food.id} className={cn("bg-white rounded-2xl border overflow-hidden flex flex-col transition-colors", quantity > 0 ? "border-primary/50" : "border-black/[0.07]")}>
                    <FoodImage food={food} className="w-full aspect-[4/3]" />
                    <div className="p-3 sm:p-4 flex flex-col flex-1">
                      <h3 className="font-display text-[15px] sm:text-[17px] leading-snug mb-1">{food.name}</h3>
                      <span className="text-sm text-muted tabular-nums mb-3">{formatCurrency(food.price)}</span>
                      <div className="mt-auto">
                        {quantity === 0 ? (
                          <button type="button" onClick={() => onAdd(food)} className="w-full h-9 rounded-lg border border-black/15 text-sm font-semibold hover:border-primary hover:text-primary inline-flex items-center justify-center gap-1.5">
                            <Plus size={15} /> Thêm
                          </button>
                        ) : (
                          <QuantityControl wide quantity={quantity} onDecrease={() => onUpdateQty(food.id, quantity - 1)} onIncrease={() => onUpdateQty(food.id, quantity + 1)} />
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <aside className="hidden lg:block sticky top-24">
          <div className="bg-white rounded-[20px] border border-black/[0.07] shadow-soft">
            <div className="p-5 pb-4">
              <div className="font-display text-[32px] leading-none text-primary tabular-nums">{time}</div>
              <div className="text-sm text-muted mt-1.5">{formatLongDate(date)} · {partySize} khách</div>
              {branchName && <div className="text-sm text-muted">{branchName}</div>}
            </div>
            <div className="ticket-tear" aria-hidden="true" />
            <div className="p-5 pt-3">
              <h3 className="font-display text-lg mb-3">Món đã chọn</h3>
              {foodItems.length === 0 ? (
                <p className="text-sm text-muted">Chưa có món nào. Bấm Thêm ở món bạn muốn bếp chuẩn bị sẵn.</p>
              ) : (
                <ul className="space-y-3 max-h-[40vh] overflow-y-auto -mr-2 pr-2">
                  {foodItems.map(({ food, quantity }) => (
                    <li key={food.id} className="flex items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium leading-snug">{food.name}</div>
                        <div className="text-xs text-muted tabular-nums">{formatCurrency(food.price * quantity)}</div>
                      </div>
                      <QuantityControl quantity={quantity} onDecrease={() => onUpdateQty(food.id, quantity - 1)} onIncrease={() => onUpdateQty(food.id, quantity + 1)} />
                    </li>
                  ))}
                </ul>
              )}
              {selectedCount > 0 && (
                <div className="mt-4 pt-3 border-t border-black/8 space-y-1.5 text-sm">
                  <div className="flex justify-between"><span className="text-muted">Tổng tiền món</span><span className="tabular-nums">{formatCurrency(subtotal)}</span></div>
                  <div className="flex justify-between font-semibold"><span>Cọc {depositPercentage}%</span><span className="text-primary tabular-nums">{formatCurrency(depositAmount)}</span></div>
                </div>
              )}
              <button type="button" onClick={onContinue} className={cn("btn w-full mt-5", selectedCount === 0 ? "btn-outline" : "btn-primary")}>
                {continueLabel}
              </button>
            </div>
          </div>
        </aside>
      </div>

      <div className="lg:hidden reservation-sticky-bar fixed inset-x-0 bottom-0 z-30 border-t border-black/10 bg-bg/95 backdrop-blur px-4 py-3">
        <div className="max-w-xl mx-auto flex items-center justify-between gap-3">
          <div className="min-w-0">
            {selectedCount === 0 ? (
              <>
                <div className="font-display text-lg leading-tight tabular-nums">{time} · {partySize} khách</div>
                <div className="text-xs text-muted">Chưa chọn món</div>
              </>
            ) : (
              <>
                <div className="text-sm font-semibold">{selectedCount} món · {formatCurrency(subtotal)}</div>
                <div className="text-xs text-primary font-semibold tabular-nums">Cọc {formatCurrency(depositAmount)}</div>
              </>
            )}
          </div>
          <button type="button" onClick={onContinue} className={cn("btn shrink-0 px-5! py-3! text-sm!", selectedCount === 0 ? "btn-outline" : "btn-primary")}>
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

function QuantityControl({ quantity, onDecrease, onIncrease, wide }: { quantity: number; onDecrease: () => void; onIncrease: () => void; wide?: boolean }) {
  return (
    <div className={cn("flex items-center shrink-0 rounded-lg border border-primary/40 bg-primary/[0.04] h-9", wide ? "w-full justify-between" : "")}>
      <button type="button" aria-label="Giảm số lượng" onClick={onDecrease} className="w-9 h-full flex items-center justify-center text-primary hover:bg-primary/10 rounded-l-lg"><Minus width={14} height={14} /></button>
      <span className="min-w-6 text-center text-sm font-semibold tabular-nums" aria-live="polite">{quantity}</span>
      <button type="button" aria-label="Tăng số lượng" onClick={onIncrease} className="w-9 h-full flex items-center justify-center text-primary hover:bg-primary/10 rounded-r-lg"><Plus width={14} height={14} /></button>
    </div>
  );
}
