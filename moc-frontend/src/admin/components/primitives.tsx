import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { Tone } from "../statusMeta";

export const inputCls =
  "w-full px-3.5 py-2.5 rounded-xl border border-black/15 bg-white text-sm outline-none focus:border-primary focus-visible:ring-2 focus-visible:ring-primary/20";

const TONES: Record<Tone, string> = {
  neutral: "bg-black/6 text-muted",
  info: "bg-accent/15 text-[#7a5c14]",
  warn: "bg-secondary/25 text-[#8a4b1d]",
  ok: "bg-success/15 text-[#456543]",
  danger: "bg-primary/12 text-primary-dark",
  dark: "bg-dark text-white",
};

export function StatusBadge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold whitespace-nowrap", TONES[tone])}>{children}</span>;
}

export function Toggle({ checked, onChange, label, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <button
      type="button" role="switch" aria-checked={checked} aria-label={label} disabled={disabled}
      onClick={(e) => { e.stopPropagation(); onChange(!checked); }}
      className={cn("relative w-10 h-6 rounded-full transition-colors shrink-0 disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-primary/40", checked ? "bg-success" : "bg-black/20")}
    >
      <span className={cn("absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform", checked && "translate-x-4")} />
    </button>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="flex items-end justify-between gap-4 flex-wrap mb-6">
      <div>
        <h1 className="font-display text-[28px] sm:text-[32px] leading-tight">{title}</h1>
        {subtitle && <p className="text-sm text-muted mt-1 max-w-xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 flex-wrap">{actions}</div>}
    </div>
  );
}

export function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card p-5">
      <div className="text-[13px] text-muted">{label}</div>
      <div className="font-display text-[28px] mt-1 leading-none">{value}</div>
      {hint && <div className="text-xs text-muted mt-2">{hint}</div>}
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="text-center py-16 px-5">
      <div className="font-display text-lg mb-1">{title}</div>
      {hint && <p className="text-sm text-muted max-w-sm mx-auto">{hint}</p>}
    </div>
  );
}

export function Tabs<K extends string>({ value, onChange, items }: { value: K; onChange: (k: K) => void; items: { key: K; label: string; count?: number }[] }) {
  return (
    <div role="tablist" className="flex gap-1.5 overflow-x-auto pb-1">
      {items.map((t) => (
        <button
          key={t.key} role="tab" aria-selected={value === t.key} onClick={() => onChange(t.key)}
          className={cn("px-3.5 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors", value === t.key ? "bg-dark text-white" : "hover:bg-black/5")}
        >
          {t.label}
          {t.count !== undefined && <span className={cn("ml-1.5 text-xs", value === t.key ? "text-white/60" : "text-muted")}>{t.count}</span>}
        </button>
      ))}
    </div>
  );
}
