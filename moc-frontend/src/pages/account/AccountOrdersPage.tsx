import { Package, Clock, ChefHat, CheckCircle2 } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { getMyOrders } from "@/api/orders.api";
import { formatCurrency, formatDate, cn } from "@/lib/utils";
import type { OrderStatus } from "@/types";

const STATUS_META: Partial<Record<
  OrderStatus,
  { label: string; icon: typeof Clock; color: string }
>> = {
  pending: { label: "Chờ xác nhận", icon: Clock, color: "text-muted" },
  confirmed: { label: "Đã xác nhận", icon: CheckCircle2, color: "text-accent" },
  preparing: { label: "Đang chế biến", icon: ChefHat, color: "text-primary" },
  ready: { label: "Sẵn sàng giao", icon: Package, color: "text-primary" },
  completed: { label: "Hoàn tất", icon: CheckCircle2, color: "text-success" },
  cancelled: { label: "Đã huỷ", icon: Clock, color: "text-muted" },
  cho_tiep_nhan: { label: "Chờ xác nhận", icon: Clock, color: "text-muted" },
  da_xac_nhan: { label: "Đã xác nhận", icon: CheckCircle2, color: "text-accent" },
  dang_che_bien: { label: "Đang chế biến", icon: ChefHat, color: "text-primary" },
  san_sang: { label: "Sẵn sàng giao", icon: Package, color: "text-primary" },
  hoan_tat: { label: "Hoàn tất", icon: CheckCircle2, color: "text-success" },
  da_huy: { label: "Đã huỷ", icon: Clock, color: "text-muted" },
};

export default function AccountOrdersPage() {
  const { data: orders, loading } = useAsync(getMyOrders);

  return (
    <div className="space-y-4">
      <h2 className="font-display text-xl mb-2">Lịch sử đơn hàng</h2>
      {loading
        ? Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-20 rounded-2xl bg-black/5 animate-pulse"
            />
          ))
        : orders?.map((order) => {
            const meta = STATUS_META[order.status] ?? STATUS_META.pending!;
            return (
              <div
                key={order.id}
                className="card p-5 flex items-center justify-between flex-wrap gap-3"
              >
                <div>
                  <div className="font-semibold text-sm">#{order.id}</div>
                  <div className="text-xs text-muted mt-1">
                    {formatDate(order.createdAt)} · {order.items} món
                  </div>
                </div>
                <div
                  className={cn(
                    "flex items-center gap-1.5 text-sm font-semibold",
                    meta.color,
                  )}
                >
                  <meta.icon width={16} height={16} />
                  {meta.label}
                </div>
                <div className="text-sm font-bold text-primary">
                  {formatCurrency(order.total)}
                </div>
              </div>
            );
          })}
    </div>
  );
}
