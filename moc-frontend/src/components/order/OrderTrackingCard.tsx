/**
 * Visual FSM Order Lifecycle Stepper Component.
 * Supports: cho_tiep_nhan -> da_xac_nhan -> dang_che_bien -> san_sang -> hoan_tat (or da_huy)
 * Path: moc-frontend/src/components/order/OrderTrackingCard.tsx
 */

import { CheckCircle2, Clock, ChefHat, Package, AlertCircle } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import { useOrderTracking } from "@/hooks/useOrderTracking";
import type { OrderStatus } from "@/types";

interface OrderTrackingCardProps {
  orderIdOrCode: string | number;
  className?: string;
}

const STEPS: { key: OrderStatus; label: string; icon: any }[] = [
  { key: "cho_tiep_nhan", label: "Tiếp nhận", icon: Clock },
  { key: "da_xac_nhan", label: "Đã xác nhận", icon: CheckCircle2 },
  { key: "dang_che_bien", label: "Đang nấu", icon: ChefHat },
  { key: "san_sang", label: "Sẵn sàng", icon: Package },
  { key: "hoan_tat", label: "Hoàn tất", icon: CheckCircle2 },
];

function getCanonicalIndex(status: string): number {
  switch (status) {
    case "cho_tiep_nhan":
    case "pending":
      return 0;
    case "da_xac_nhan":
    case "confirmed":
      return 1;
    case "dang_che_bien":
    case "preparing":
      return 2;
    case "san_sang":
    case "ready":
      return 3;
    case "hoan_tat":
    case "completed":
      return 4;
    default:
      return -1;
  }
}

export default function OrderTrackingCard({ orderIdOrCode, className }: OrderTrackingCardProps) {
  const { snapshot, isConnected, error } = useOrderTracking(orderIdOrCode);

  if (error) {
    return (
      <div className={cn("p-4 rounded-xl bg-red-50 text-red-700 text-sm flex items-center gap-2", className)}>
        <AlertCircle width={18} height={18} />
        {error}
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className={cn("card p-6 bg-white animate-pulse space-y-4", className)}>
        <div className="h-5 bg-black/10 rounded w-1/3"></div>
        <div className="h-10 bg-black/5 rounded"></div>
      </div>
    );
  }

  const isCancelled = snapshot.status === "da_huy" || snapshot.status === "cancelled";
  const currentIndex = getCanonicalIndex(snapshot.status);

  return (
    <div className={cn("card p-6 bg-white border border-black/10 rounded-2xl shadow-sm", className)}>
      <div className="flex items-center justify-between border-b pb-4 mb-6">
        <div>
          <div className="text-xs uppercase tracking-wider text-muted font-bold">Mã đơn hàng</div>
          <div className="font-display text-xl font-bold text-dark">#{snapshot.orderNumber}</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted">Tổng thanh toán</div>
          <div className="font-bold text-primary text-lg">{formatCurrency(snapshot.total)}</div>
        </div>
      </div>

      {isCancelled ? (
        <div className="p-4 rounded-xl bg-red-50 text-red-700 flex items-center gap-3">
          <AlertCircle width={22} height={22} />
          <div>
            <div className="font-bold">Đơn hàng đã bị hủy</div>
            {snapshot.note && <div className="text-xs mt-0.5">{snapshot.note}</div>}
          </div>
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-5 gap-2 relative">
            {/* Progress line */}
            <div className="absolute top-4 left-6 right-6 h-1 bg-black/10 -z-0" />
            <div
              className="absolute top-4 left-6 h-1 bg-primary transition-all duration-500 -z-0"
              style={{ width: `${Math.min(100, Math.max(0, (currentIndex / 4) * 100))}%` }}
            />

            {STEPS.map((step, idx) => {
              const isPast = idx < currentIndex;
              const isCurrent = idx === currentIndex;
              const Icon = step.icon;

              return (
                <div key={step.key} className="flex flex-col items-center text-center relative z-10">
                  <div
                    className={cn(
                      "w-9 h-9 rounded-full flex items-center justify-center transition-all duration-300",
                      isCurrent && "bg-primary text-white ring-4 ring-primary/20 scale-110",
                      isPast && "bg-primary text-white",
                      !isPast && !isCurrent && "bg-white border-2 border-black/20 text-muted"
                    )}
                  >
                    <Icon width={16} height={16} />
                  </div>
                  <span
                    className={cn(
                      "text-[11px] sm:text-xs mt-2 font-medium leading-tight",
                      isCurrent ? "text-primary font-bold" : "text-muted"
                    )}
                  >
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-6 pt-4 border-t border-black/5 flex items-center justify-between text-xs text-muted">
            <div className="flex items-center gap-1.5">
              <span className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-400")} />
              <span>{isConnected ? "Cập nhật trực tiếp theo thời gian thực" : "Đang kết nối lại..."}</span>
            </div>
            {snapshot.lastUpdated && (
              <div>Cập nhật lúc: {new Date(snapshot.lastUpdated).toLocaleTimeString()}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
