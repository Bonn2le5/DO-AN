import { create } from "zustand";
import { Check, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ToastItem { id: number; text: string; tone: "ok" | "err" }
interface ToastState { items: ToastItem[]; push: (text: string, tone?: ToastItem["tone"]) => void }

export const useToast = create<ToastState>((set) => ({
  items: [],
  push: (text, tone = "ok") => {
    const id = Date.now() + Math.random();
    set((s) => ({ items: [...s.items, { id, text, tone }] }));
    setTimeout(() => set((s) => ({ items: s.items.filter((t) => t.id !== id) })), 3200);
  },
}));

export function Toaster() {
  const items = useToast((s) => s.items);
  return (
    <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-80 flex flex-col gap-2 items-center" aria-live="polite">
      {items.map((t) => (
        <div key={t.id} className={cn("flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-medium shadow-lift text-white", t.tone === "ok" ? "bg-dark" : "bg-primary-dark")}>
          {t.tone === "ok" ? <Check width={15} height={15} /> : <AlertCircle width={15} height={15} />}
          {t.text}
        </div>
      ))}
    </div>
  );
}
