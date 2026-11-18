import { Check, CheckCheck } from "lucide-react";
import { cn } from "@/lib/utils";

/** Giờ gửi + dấu tích ở góc dưới bong bóng tin của mình: một tích = đã gửi, hai tích = đã xem. */
export default function MessageMeta({ time, mine, isRead, className }: { time: string; mine: boolean; isRead?: boolean; className?: string }) {
  return (
    <div className={cn("mt-1 flex items-center justify-end gap-1 text-[10px] leading-none tabular-nums", className)}>
      <span>{time}</span>
      {mine && (isRead
        ? <CheckCheck size={14} strokeWidth={2.25} className="shrink-0 text-white" aria-label="Đã xem" />
        : <Check size={14} strokeWidth={2.25} className="shrink-0 opacity-80" aria-label="Đã gửi" />)}
    </div>
  );
}
