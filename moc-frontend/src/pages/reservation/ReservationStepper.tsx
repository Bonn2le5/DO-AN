import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReservationStep } from "@/hooks/useReservationFlow";

const STEPS: { key: ReservationStep; label: string }[] = [
  { key: "branch_time", label: "Đặt chỗ" },
  { key: "food", label: "Gọi món" },
  { key: "contact", label: "Xác nhận" },
];

export default function ReservationStepper({ current, compact = false }: { current: ReservationStep; compact?: boolean }) {
  const activeStep = current === "success" ? "contact" : current;
  const currentIndex = STEPS.findIndex((step) => step.key === activeStep);

  return (
    <ol className={cn("grid grid-cols-3 gap-2 sm:gap-3", compact ? "mb-4" : "mb-8 sm:mb-10")} aria-label="Các bước đặt bàn">
      {STEPS.map((step, index) => {
        const done = index < currentIndex;
        const active = index === currentIndex;
        return (
          <li key={step.key} aria-current={active ? "step" : undefined} className="min-w-0">
            <div className={cn("h-1 rounded-full mb-2.5", done || active ? "bg-primary" : "bg-black/10")} />
            <div className="flex items-center gap-2">
              <span className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0",
                done ? "bg-primary text-white" : active ? "border-[1.5px] border-primary text-primary" : "border border-black/20 text-muted",
              )}>
                {done ? <Check width={13} height={13} /> : index + 1}
              </span>
              <span className={cn("text-sm truncate", active ? "font-semibold text-text" : "text-muted")}>{step.label}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
