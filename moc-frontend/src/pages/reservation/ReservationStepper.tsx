import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ReservationStep } from "@/hooks/useReservationFlow";

const STEPS: { key: ReservationStep; label: string }[] = [
  { key: "branch_time", label: "Đặt chỗ" },
  { key: "food", label: "Gọi món" },
  { key: "contact", label: "Xác nhận" },
];

export default function ReservationStepper({ current }: { current: ReservationStep }) {
  const activeStep = current === "success" ? "contact" : current;
  const currentIndex = STEPS.findIndex((step) => step.key === activeStep);

  return (
    <div className="flex items-center gap-2 mb-10 overflow-x-auto pb-1">
      {STEPS.map((step, index) => {
        const done = index < currentIndex;
        const active = index === currentIndex;
        return (
          <div key={step.key} className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-2">
              <span className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
                done ? "bg-success text-white" : active ? "bg-primary text-white" : "bg-black/8 text-muted",
              )}>
                {done ? <Check width={14} height={14} /> : index + 1}
              </span>
              <span className={cn("text-sm font-medium whitespace-nowrap", active ? "text-text" : "text-muted")}>{step.label}</span>
            </div>
            {index < STEPS.length - 1 && <div className="w-8 h-px bg-black/15 shrink-0" />}
          </div>
        );
      })}
    </div>
  );
}
