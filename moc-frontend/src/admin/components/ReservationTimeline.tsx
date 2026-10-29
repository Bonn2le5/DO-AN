import { cn } from "@/lib/utils";
import { RES_META } from "../statusMeta";
import type { AdminReservation, AdminTable } from "../types";

const START = 10, END = 22, SPAN = END - START;
const HOURS = Array.from({ length: SPAN + 1 }, (_, i) => START + i);
const COLOR: Record<AdminReservation["status"], string> = {
  pending_confirmation: "bg-secondary/70 text-[#5c2f10]", pending_payment: "bg-secondary/70 text-[#5c2f10]", confirmed: "bg-accent/80 text-white", seated: "bg-success text-white",
  completed: "bg-black/15 text-muted", cancelled: "bg-primary/20 text-primary-dark line-through", no_show: "bg-primary/20 text-primary-dark line-through",
};

export default function ReservationTimeline({ tables, reservations, onOpen }: { tables: AdminTable[]; reservations: AdminReservation[]; onOpen: (r: AdminReservation) => void }) {
  const zones = [...new Set(tables.map((t) => t.zone))];
  return (
    <div className="card overflow-x-auto">
      <div className="min-w-205">
        <div className="grid grid-cols-[110px_1fr] border-b border-black/[0.07] text-xs text-muted">
          <div className="px-4 py-2.5">Bàn</div>
          <div className="relative h-9">{HOURS.map((h) => (<span key={h} className="absolute top-2.5 -translate-x-1/2" style={{ left: `${((h - START) / SPAN) * 100}%` }}>{h}:00</span>))}</div>
        </div>
        {zones.map((zone) => (
          <div key={zone}>
            <div className="px-4 py-1.5 text-xs font-semibold bg-black/3 text-muted">{zone}</div>
            {tables.filter((t) => t.zone === zone).map((t) => (
              <div key={t.id} className="grid grid-cols-[110px_1fr] border-b border-black/5 last:border-0">
                <div className="px-4 py-3 text-sm"><b>{t.number}</b><span className="text-xs text-muted ml-1.5">{t.capacity} chỗ</span></div>
                <div className="relative h-12">
                  {HOURS.map((h) => (<span key={h} className="absolute top-0 bottom-0 border-l border-black/5" style={{ left: `${((h - START) / SPAN) * 100}%` }} />))}
                  {reservations.filter((r) => r.tableId === t.id).map((r) => {
                    const start = Number(r.time.slice(0, 2)) + Number(r.time.slice(3)) / 60;
                    return (
                      <button
                        key={r.id} onClick={() => onOpen(r)} title={`${r.customer} · ${RES_META[r.status].label}`}
                        className={cn("absolute top-1.5 bottom-1.5 rounded-lg px-2 text-xs font-medium text-left truncate hover:brightness-95 focus-visible:ring-2 focus-visible:ring-dark", COLOR[r.status])}
                        style={{ left: `${((start - START) / SPAN) * 100}%`, width: `${(2 / SPAN) * 100}%` }}
                      >
                        {r.time} {r.customer}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
