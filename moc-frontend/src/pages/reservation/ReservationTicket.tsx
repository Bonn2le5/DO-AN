import type { ReactNode } from "react";
import { MapPin, Users, UtensilsCrossed } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import type { MonAnDatBan } from "@/types";

export function formatLongDate(value: string) {
  if (!value) return "";
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  const weekday = new Intl.DateTimeFormat("vi-VN", { weekday: "long" }).format(date);
  const day = new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
  return `${weekday.charAt(0).toUpperCase()}${weekday.slice(1)}, ${day}`;
}

const REFUND_LABELS: Record<string, string> = {
  truoc_24h: "Huỷ trước giờ hẹn 24 tiếng trở lên",
  tu_6_den_24h: "Huỷ trước giờ hẹn 6 đến 24 tiếng",
  trong_6h: "Huỷ trong vòng 6 tiếng trước giờ hẹn",
  khach_khong_den: "Không đến mà không báo trước",
};

export const refundLabel = (bucket: string) => REFUND_LABELS[bucket] ?? bucket;

interface ReservationTicketProps {
  branchName: string;
  date: string;
  time: string;
  partySize: number;
  foodItems: MonAnDatBan[];
  foodSubtotal: number;
  tableLabel?: string;
  /** Dòng nhỏ phía trên giờ hẹn, ví dụ mã đặt bàn hoặc trạng thái */
  topLine?: ReactNode;
  onEditTime?: () => void;
  onEditFood?: () => void;
  children?: ReactNode;
}

/** Phiếu đặt bàn: phần trên là giờ hẹn, phần dưới là chi tiết, ngăn bằng đường răng cưa. */
export default function ReservationTicket({
  branchName, date, time, partySize, foodItems, foodSubtotal, tableLabel,
  topLine, onEditTime, onEditFood, children,
}: ReservationTicketProps) {
  const dishCount = foodItems.reduce((total, item) => total + item.soLuong, 0);
  const subtotal = foodSubtotal || foodItems.reduce((total, { monAn: food, soLuong: quantity }) => total + (food.donGia ?? 0) * quantity, 0);

  return (
    <section className="bg-white rounded-[20px] border border-black/[0.07] shadow-soft" aria-label="Phiếu đặt bàn">
      <div className="px-5 sm:px-7 pt-6 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="text-sm text-muted">{topLine ?? "Giờ hẹn"}</div>
          {onEditTime && <EditButton onClick={onEditTime} label="Sửa giờ hẹn">Sửa</EditButton>}
        </div>
        <div className="font-display font-bold! text-[52px] sm:text-[60px] leading-none tracking-[-0.03em] text-primary mt-1 tabular-nums">{time ? time.slice(0, 5) : "--:--"}</div>
        <div className="font-display text-xl sm:text-[22px] mt-2">{formatLongDate(date)}</div>
        <div className="mt-4 grid gap-2 text-[15px]">
          {branchName && (
            <div className="flex items-start gap-2.5">
              <MapPin size={17} className="text-muted mt-0.5 shrink-0" />
              <span>{branchName}</span>
            </div>
          )}
          <div className="flex items-start gap-2.5">
            <Users size={17} className="text-muted mt-0.5 shrink-0" />
            <span>{partySize} khách<span className="text-muted"> · {tableLabel || "nhân viên xếp bàn khi bạn đến"}</span></span>
          </div>
        </div>
      </div>

      <div className="ticket-tear" aria-hidden="true" />

      <div className="px-5 sm:px-7 pt-3 pb-6">
        <div className="flex items-center justify-between gap-4 mb-3">
          <h3 className="font-display text-lg flex items-center gap-2">
            <UtensilsCrossed size={16} className="text-muted" />
            {dishCount > 0 ? `Món gọi trước (${dishCount})` : "Món gọi trước"}
          </h3>
          {onEditFood && <EditButton onClick={onEditFood} label="Sửa món đã chọn">{dishCount > 0 ? "Sửa" : "Thêm món"}</EditButton>}
        </div>

        {foodItems.length === 0 ? (
          <p className="text-sm text-muted leading-relaxed">Bạn chỉ giữ chỗ, sẽ gọi món tại nhà hàng. Không cần đặt cọc.</p>
        ) : (
          <>
            <ul className="space-y-2.5">
              {foodItems.map(({ monAn: food, soLuong: quantity }) => (
                <li key={food.id} className="flex items-baseline gap-3 text-[15px]">
                  <span className="w-7 shrink-0 text-muted tabular-nums">{quantity}×</span>
                  <span className="flex-1 min-w-0">{food.tenMon}</span>
                  <span className="tabular-nums text-right">{formatCurrency((food.donGia ?? 0) * quantity)}</span>
                </li>
              ))}
            </ul>
            <div className="flex items-baseline justify-between gap-3 mt-4 pt-3 border-t border-black/8 text-[15px]">
              <span className="text-muted">Tổng tiền món</span>
              <span className="font-semibold tabular-nums">{formatCurrency(subtotal)}</span>
            </div>
          </>
        )}

        {children}
      </div>
    </section>
  );
}

function EditButton({ onClick, label, children }: { onClick: () => void; label: string; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} className="text-sm font-semibold text-primary underline underline-offset-4 decoration-primary/30 hover:decoration-primary shrink-0">
      {children}
    </button>
  );
}
