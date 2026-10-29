import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DrawerProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  width?: string;
}

export default function Drawer({ open, title, onClose, children, footer, width = "sm:max-w-md" }: DrawerProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      <div
        className={cn("fixed inset-0 z-60 bg-dark/40 transition-opacity duration-200", open ? "opacity-100" : "opacity-0 pointer-events-none")}
        onClick={onClose}
      />
      <aside
        role="dialog" aria-modal="true" aria-label={title} aria-hidden={!open}
        className={cn("fixed top-0 right-0 z-61 h-full w-full bg-bg shadow-lift flex flex-col transition-transform duration-300", width, open ? "translate-x-0" : "translate-x-full")}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-black/[0.07]">
          <h2 className="font-display text-xl">{title}</h2>
          <button onClick={onClose} className="icon-btn" aria-label="Đóng"><X width={18} height={18} /></button>
        </div>
        <div className="flex-1 overflow-y-auto px-6 py-5">{open && children}</div>
        {footer && open && <div className="px-6 py-4 border-t border-black/[0.07] flex gap-2 justify-end flex-wrap">{footer}</div>}
      </aside>
    </>
  );
}
