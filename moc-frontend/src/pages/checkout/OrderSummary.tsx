import { UtensilsCrossed } from "lucide-react";
import PlaceholderMedia from "@/components/ui/PlaceholderMedia";
import { formatCurrency } from "@/lib/utils";
import type { CartItem, Promotion } from "@/types";

interface OrderSummaryProps {
  items: CartItem[];
  subtotal: number;
  discount: number;
  total: number;
  appliedPromo: Promotion | null;
}

export default function OrderSummary({ items, subtotal, discount, total, appliedPromo }: OrderSummaryProps) {
  return (
    <div className="card p-6 sticky top-24">
      <h3 className="font-display text-lg mb-4">Đơn hàng của bạn</h3>
      <div className="space-y-4 mb-5">
        {items.map((item) => (
          <div key={item.food.id} className="flex gap-3">
            <div className="w-14 h-14 rounded-lg overflow-hidden flex-shrink-0">
              <PlaceholderMedia tone={item.food.placeholderTone} icon={UtensilsCrossed} className="w-full h-full" iconClassName="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium line-clamp-1">{item.food.name}</div>
              <div className="text-xs text-muted">SL: {item.quantity}</div>
            </div>
            <div className="text-sm font-semibold">{formatCurrency(item.food.price * item.quantity)}</div>
          </div>
        ))}
      </div>
      <div className="space-y-2 pt-4 border-t border-black/[0.08]">
        <div className="flex justify-between text-sm">
          <span className="text-muted">Tạm tính</span>
          <span>{formatCurrency(subtotal)}</span>
        </div>
        {appliedPromo && discount > 0 && (
          <div className="flex justify-between text-sm text-success">
            <span>Mã {appliedPromo.code}</span>
            <span>-{formatCurrency(discount)}</span>
          </div>
        )}
        <div className="flex justify-between text-base font-bold pt-2 border-t border-black/[0.08]">
          <span>Tổng cộng</span>
          <span className="text-primary">{formatCurrency(total)}</span>
        </div>
      </div>
    </div>
  );
}
