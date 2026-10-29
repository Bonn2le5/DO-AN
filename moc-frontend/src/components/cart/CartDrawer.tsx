import { useState } from "react";
import { Link } from "react-router-dom";
import { X, Minus, Plus, Trash2, ShoppingBag, UtensilsCrossed } from "lucide-react";
import { useCartStore } from "@/store/cartStore";
import { useAsync } from "@/hooks/useAsync";
import { getPromotions } from "@/api/promotions.api";
import { formatCurrency, cn } from "@/lib/utils";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import type { CartItem } from "@/types";

export default function CartDrawer() {
  const {
    items,
    isDrawerOpen,
    closeDrawer,
    updateQuantity,
    removeItem,
    appliedPromo,
    applyPromo,
    subtotal,
    discount,
    total,
  } = useCartStore();
  const [promoInput, setPromoInput] = useState("");
  const [promoError, setPromoError] = useState("");
  const { data: promotions } = useAsync(getPromotions);

  const handleApplyPromo = () => {
    const found = promotions?.find((p) => p.code.toLowerCase() === promoInput.trim().toLowerCase());
    if (!found) {
      setPromoError("Mã khuyến mãi không hợp lệ");
      return;
    }
    if (found.minOrder && subtotal() < found.minOrder) {
      setPromoError(`Đơn tối thiểu ${formatCurrency(found.minOrder)} để dùng mã này`);
      return;
    }
    setPromoError("");
    applyPromo(found);
  };

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 bg-black/40 z-[90] transition-opacity duration-300",
          isDrawerOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        )}
        onClick={closeDrawer}
      />
      <aside
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-[420px] bg-bg z-[100] shadow-lift flex flex-col transition-transform duration-400",
          isDrawerOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-black/[0.07]">
          <h2 className="font-display text-xl">Giỏ hàng của bạn</h2>
          <button onClick={closeDrawer} className="icon-btn">
            <X width={19} height={19} />
          </button>
        </div>

        {items.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
            <div className="w-16 h-16 rounded-full bg-black/[0.05] flex items-center justify-center mb-5">
              <ShoppingBag width={26} height={26} className="text-muted" />
            </div>
            <h3 className="font-display text-lg mb-2">Giỏ hàng đang trống</h3>
            <p className="text-sm text-muted mb-6">Khám phá thực đơn để tìm món yêu thích</p>
            <Link to="/thuc-don" onClick={closeDrawer} className="btn btn-primary">
              Xem thực đơn
            </Link>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
              {items.map((item: CartItem) => (
                <div key={item.food.id} className="flex gap-3.5">
                  <Link
                    to={`/thuc-don/${item.food.slug}`}
                    onClick={closeDrawer}
                    className="w-[72px] h-[72px] rounded-xl overflow-hidden flex-shrink-0"
                  >
                    <PlaceholderMedia
                      tone={item.food.placeholderTone}
                      icon={UtensilsCrossed}
                      className="w-full h-full"
                      iconClassName="w-6 h-6"
                    />
                  </Link>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="text-[14.5px] font-semibold leading-snug line-clamp-2">
                        {item.food.name}
                      </h4>
                      <button
                        onClick={() => removeItem(item.food.id)}
                        className="text-muted hover:text-primary transition-colors flex-shrink-0"
                      >
                        <Trash2 width={15} height={15} />
                      </button>
                    </div>
                    <div className="text-[13px] text-muted mt-0.5">
                      {formatCurrency(item.food.price)}
                    </div>
                    <div className="flex items-center gap-2.5 mt-2">
                      <button
                        onClick={() => updateQuantity(item.food.id, item.quantity - 1)}
                        className="w-7 h-7 rounded-full border border-black/15 flex items-center justify-center hover:bg-black/5"
                      >
                        <Minus width={12} height={12} />
                      </button>
                      <span className="text-sm font-semibold w-4 text-center">{item.quantity}</span>
                      <button
                        onClick={() => updateQuantity(item.food.id, item.quantity + 1)}
                        className="w-7 h-7 rounded-full border border-black/15 flex items-center justify-center hover:bg-black/5"
                      >
                        <Plus width={12} height={12} />
                      </button>
                      <span className="ml-auto text-sm font-bold text-primary">
                        {formatCurrency(item.food.price * item.quantity)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="px-6 pt-4 pb-2 border-t border-black/[0.07]">
              <div className="flex gap-2 mb-1">
                <input
                  value={promoInput}
                  onChange={(e) => setPromoInput(e.target.value.toUpperCase())}
                  placeholder="Mã khuyến mãi"
                  className="flex-1 min-w-0 px-3.5 py-2.5 rounded-lg border border-black/15 text-sm outline-none focus:border-primary"
                />
                <button onClick={handleApplyPromo} className="btn btn-outline !py-2.5 !px-4 !text-[13px]">
                  Áp dụng
                </button>
              </div>
              {promoError && <p className="text-xs text-primary mb-1">{promoError}</p>}
              {appliedPromo && (
                <p className="text-xs text-success mb-1">
                  Đã áp dụng mã {appliedPromo.code} ({appliedPromo.discountLabel})
                </p>
              )}
            </div>

            <div className="px-6 py-5 border-t border-black/[0.07] space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted">Tạm tính</span>
                <span>{formatCurrency(subtotal())}</span>
              </div>
              {discount() > 0 && (
                <div className="flex justify-between text-sm text-success">
                  <span>Giảm giá</span>
                  <span>-{formatCurrency(discount())}</span>
                </div>
              )}
              <div className="flex justify-between text-base font-bold pt-2 border-t border-black/[0.07]">
                <span>Tổng cộng</span>
                <span className="text-primary">{formatCurrency(total())}</span>
              </div>
              <Link
                to="/thanh-toan"
                onClick={closeDrawer}
                className="btn btn-primary w-full mt-3"
              >
                Tiến hành đặt món
              </Link>
            </div>
          </>
        )}
      </aside>
    </>
  );
}
