import { useEffect, type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message?: string;
  confirmLabel: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children?: ReactNode;
}

export default function ConfirmModal({ open, title, message, confirmLabel, danger, busy, onConfirm, onCancel, children }: ConfirmModalProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-70 flex items-center justify-center p-5">
      <div className="absolute inset-0 bg-dark/50" onClick={onCancel} />
      <div role="alertdialog" aria-modal="true" aria-label={title} className="relative bg-white rounded-2xl shadow-lift w-full max-w-sm p-6">
        <h3 className="font-display text-xl mb-2">{title}</h3>
        {message && <p className="text-sm text-muted leading-relaxed">{message}</p>}
        {children && <div className="mt-4">{children}</div>}
        <div className="flex justify-end gap-2 mt-6">
          <button onClick={onCancel} className="btn btn-outline py-2.5! px-5! text-sm!">Quay lại</button>
          <button
            onClick={onConfirm} disabled={busy}
            className={cn("btn py-2.5! px-5! text-sm! text-white disabled:opacity-50", danger ? "bg-primary-dark hover:bg-primary" : "bg-dark hover:bg-primary")}
          >
            {busy ? "Đang xử lý..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
