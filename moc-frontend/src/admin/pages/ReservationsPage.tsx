import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Building2, CalendarDays, ChevronLeft, ChevronRight, Phone, Search, UtensilsCrossed } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { getDepositPolicy, getTableManagementBranches, needsRefund, reservationsStore, setReservationStatus, tablesStore } from "../api/admin.api";
import ReservationDrawer from "../components/ReservationDrawer";
import DiningSessionDrawer from "../components/DiningSessionDrawer";
import { PageHeader, StatusBadge, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan } from "../permissions";
import { DEPOSIT_META, RES_META } from "../statusMeta";
import { ymd } from "../lib";
import type { AdminDiningSession, AdminReservation, ReservationStatus } from "../types";
import { useAuthStore } from "@/store/authStore";

/** Hàng đợi việc cần làm, không phụ thuộc ngày đang xem. */
type Queue = "none" | "confirm" | "deposit" | "refund";
type DayFilter = "all" | "active" | "seated" | "done";

const WEEKDAY = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"];
const WEEKDAY_LONG = ["Chủ nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"];
const CLOSED: ReservationStatus[] = ["cancelled", "completed", "no_show"];

const parseDay = (d: string) => { const [y, m, day] = d.split("-").map(Number); return new Date(y, m - 1, day); };
const addDays = (d: string, n: number) => { const x = parseDay(d); x.setDate(x.getDate() + n); return ymd(Math.round((x.getTime() - parseDay(ymd(0)).getTime()) / 86400000)); };
const dmy = (d: string) => d.split("-").reverse().slice(0, 2).join("/");
const dayTitle = (d: string, today: string) => {
  const label = d === today ? "Hôm nay" : d === addDays(today, 1) ? "Ngày mai" : WEEKDAY_LONG[parseDay(d).getDay()];
  return `${label}, ${d.split("-").reverse().join("/")}`;
};
const needsDeposit = (r: AdminReservation) => r.depositAmount > 0 && ["unpaid", "pending", "failed"].includes(r.depositStatus) && ["pending_confirmation", "pending_payment"].includes(r.status);
const minutesOf = (t: string) => { const [h, m] = t.split(":").map(Number); return h * 60 + (m || 0); };

const BAR: Record<ReservationStatus, string> = {
  pending_confirmation: "bg-secondary", pending_payment: "bg-secondary", confirmed: "bg-sky-600",
  seated: "bg-success", completed: "bg-black/15", cancelled: "bg-primary/40", no_show: "bg-primary/40",
};

export default function ReservationsPage() {
  const user = useAuthStore((s) => s.nguoiDung);
  const isAdmin = Boolean(user?.laQuanTri || user?.danhSachVaiTro?.some((r) => ["admin", "quan_tri_vien"].includes(String(r).toLowerCase())));
  const can = useCan();
  const editable = can("reservations", "update");
  const push = useToast((s) => s.push);
  const [params, setParams] = useSearchParams();
  const today = ymd(0);
  const [day, setDay] = useState(today);
  const [weekStart, setWeekStart] = useState(today);
  const [dayFilter, setDayFilter] = useState<DayFilter>("all");
  const [query, setQuery] = useState("");
  const [branchId, setBranchId] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(params.get("open"));
  const [openSession, setOpenSession] = useState<AdminDiningSession | null>(null);
  const [now, setNow] = useState(() => new Date());
  const queueParam = params.get("status");
  const queue: Queue = queueParam === "pending_confirmation" ? "confirm" : queueParam === "needs_deposit" ? "deposit" : queueParam === "refund" ? "refund" : "none";

  const { data: reservations, loading, refetch } = useAsync(() => reservationsStore.list());
  const { data: tables } = useAsync(() => tablesStore.list());
  const { data: branches } = useAsync(() => getTableManagementBranches());
  const { data: policy } = useAsync(() => getDepositPolicy());

  useEffect(() => { const id = window.setInterval(() => setNow(new Date()), 60_000); return () => window.clearInterval(id); }, []);

  const all = useMemo(() => (reservations ?? []).filter((r) => !branchId || r.branchId === branchId), [reservations, branchId]);
  const branchTables = useMemo(() => tables?.filter((t) => !branchId || t.branchId === branchId) ?? [], [tables, branchId]);
  const week = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart]);
  const countByDay = useMemo(() => {
    const map = new Map<string, { total: number; pending: number }>();
    for (const r of all) {
      if (CLOSED.includes(r.status)) continue;
      const c = map.get(r.date) ?? { total: 0, pending: 0 };
      c.total += 1; if (r.status === "pending_confirmation") c.pending += 1;
      map.set(r.date, c);
    }
    return map;
  }, [all]);

  const queues = {
    confirm: all.filter((r) => r.status === "pending_confirmation" && r.date >= today),
    deposit: all.filter((r) => needsDeposit(r) && r.date >= today),
    refund: all.filter(needsRefund),
  };

  const q = query.trim().toLowerCase();
  const matchesQuery = (r: AdminReservation) => !q || `${r.code} ${r.customer} ${r.phone}`.toLowerCase().includes(q);
  const dayRows = all.filter((r) => r.date === day);
  const dayCounts = {
    all: dayRows.length,
    active: dayRows.filter((r) => ["pending_confirmation", "pending_payment", "confirmed"].includes(r.status)).length,
    seated: dayRows.filter((r) => r.status === "seated").length,
    done: dayRows.filter((r) => CLOSED.includes(r.status)).length,
  };
  const guestsToday = dayRows.filter((r) => !["cancelled", "no_show"].includes(r.status)).reduce((n, r) => n + r.partySize, 0);

  // Khi tìm kiếm hoặc mở hàng đợi: xem xuyên ngày, nhóm theo ngày. Bình thường: một ngày, nhóm theo giờ.
  const crossDay = queue !== "none" || !!q;
  const rows = (crossDay
    ? (queue === "none" ? all : queues[queue]).filter(matchesQuery)
    : dayRows.filter((r) => dayFilter === "all"
      || (dayFilter === "active" && ["pending_confirmation", "pending_payment", "confirmed"].includes(r.status))
      || (dayFilter === "seated" && r.status === "seated")
      || (dayFilter === "done" && CLOSED.includes(r.status)))
  ).slice().sort((a, b) => (a.date + a.time).localeCompare(b.date + b.time));

  const groups = useMemo(() => {
    const map = new Map<string, AdminReservation[]>();
    for (const r of rows) {
      const key = crossDay ? r.date : `${r.time.slice(0, 2)}:00`;
      map.set(key, [...(map.get(key) ?? []), r]);
    }
    return [...map.entries()];
  }, [rows, crossDay]);

  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  const nowGroupIndex = !crossDay && day === today ? groups.findIndex(([hour]) => minutesOf(hour) + 59 >= nowMinutes) : -1;

  const setQueue = (next: Queue) => {
    const value = next === "confirm" ? "pending_confirmation" : next === "deposit" ? "needs_deposit" : next === "refund" ? "refund" : "";
    if (value && value !== queueParam) setParams({ status: value }, { replace: true });
    else { params.delete("status"); setParams(params, { replace: true }); }
  };
  const pickDay = (d: string) => {
    setDay(d); setDayFilter("all"); if (queue !== "none") setQueue("none"); setQuery("");
    if (d < weekStart || d > addDays(weekStart, 6)) setWeekStart(d < today || d > addDays(today, 6) ? d : today);
  };
  const close = () => { setOpenId(null); if (params.get("open")) { params.delete("open"); setParams(params, { replace: true }); } };

  const confirm = async (r: AdminReservation) => {
    setBusyId(r.id);
    try {
      await setReservationStatus(r.id, "confirmed", r.version);
      push(`Đã xác nhận đặt bàn của ${r.customer || r.code}.`);
      await refetch();
    } catch (e) {
      push(e instanceof Error ? e.message : "Không xác nhận được đặt bàn.", "err");
      await refetch();
    } finally { setBusyId(null); }
  };

  const sessionOf = (r: AdminReservation): AdminDiningSession => ({ id: r.sessionId!, code: "", branchId: r.branchId ?? "", tableId: r.tableId, tableLabel: r.tableLabel, orderId: r.orderId, orderCode: r.orderCode, reservationId: r.id, guestCount: r.partySize, customer: r.customer, phone: r.phone, note: r.note, status: "active", startedAt: r.checkedInAt ?? "" });

  const action = (r: AdminReservation) => {
    if (!editable) return null;
    if (r.status === "pending_confirmation") return { label: busyId === r.id ? "Đang xác nhận…" : "Xác nhận", run: () => void confirm(r), primary: true };
    if (r.status === "confirmed" && r.date === today) return { label: "Check-in", run: () => setOpenId(r.id), primary: true };
    if (r.status === "seated" && !r.sessionId) return { label: "Xếp bàn", run: () => setOpenId(r.id), primary: true };
    if (r.status === "seated" && r.sessionId) return { label: "Mở phiên", run: () => setOpenSession(sessionOf(r)), primary: false };
    return null;
  };

  const renderRow = (r: AdminReservation) => {
    const act = action(r);
    const late = r.status === "confirmed" && r.date === today && nowMinutes - minutesOf(r.time) > 15;
    const faded = CLOSED.includes(r.status);
    return (
      <li key={r.id} className={`group relative flex items-stretch gap-3 rounded-xl bg-white pr-3 ring-1 ring-black/[0.06] transition-shadow hover:ring-black/15 ${faded ? "opacity-60" : ""}`}>
        <span aria-hidden className={`w-1 shrink-0 rounded-l-xl ${BAR[r.status]}`} />
        <button onClick={() => setOpenId(r.id)} className="flex min-w-0 flex-1 flex-col gap-1 py-3 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary sm:flex-row sm:items-center sm:gap-4">
          <span className="w-12 shrink-0 font-display text-base font-semibold tabular-nums">{r.time}</span>
          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-baseline gap-x-3">
              <span className="truncate font-semibold">{r.customer || "Khách"}</span>
              <span className="text-sm text-muted">{r.partySize} khách</span>
            </span>
            <span className="mt-1 flex flex-wrap items-center gap-1.5">
              <StatusBadge tone={RES_META[r.status].tone}>{RES_META[r.status].label}</StatusBadge>
              {late && <StatusBadge tone="danger">Trễ {nowMinutes - minutesOf(r.time)} phút</StatusBadge>}
              {r.depositAmount > 0 && <StatusBadge tone={DEPOSIT_META[r.depositStatus].tone}>{DEPOSIT_META[r.depositStatus].label} {formatCurrency(r.depositAmount)}</StatusBadge>}
              {r.foodItems.length > 0 && <span className="inline-flex items-center gap-1 text-xs text-muted"><UtensilsCrossed size={12} />{r.foodItems.reduce((n, i) => n + i.qty, 0)} món đặt trước</span>}
              {r.tableLabel && <span className="text-xs text-muted">Bàn {r.tableLabel}</span>}
            </span>
            {r.note && <span className="mt-1 block truncate text-xs italic text-dark/70">“{r.note}”</span>}
          </span>
        </button>
        <div className="flex shrink-0 items-center gap-2">
          {r.phone && <a href={`tel:${r.phone}`} className="hidden items-center gap-1.5 rounded-lg px-2 py-2 text-sm tabular-nums text-muted hover:bg-black/[0.04] hover:text-dark md:inline-flex" aria-label={`Gọi ${r.customer} ${r.phone}`}><Phone size={14} />{r.phone}</a>}
          {act && <button disabled={busyId === r.id} onClick={act.run} className={`btn py-2! px-3.5! text-sm! ${act.primary ? "btn-primary" : "btn-outline"} disabled:opacity-50`}>{act.label}</button>}
        </div>
      </li>
    );
  };

  return (
    <div>
      <PageHeader
        title="Đặt bàn"
        subtitle="Sổ đặt bàn theo ngày: xác nhận, check-in và theo dõi khách sắp đến."
        actions={isAdmin && <label className="relative min-w-56"><Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" /><select value={branchId} onChange={(e) => setBranchId(e.target.value)} aria-label="Chi nhánh" className={`${inputCls} pl-9!`}><option value="">Tất cả chi nhánh</option>{(branches ?? []).map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}</select></label>}
      />

      {/* Dải 7 ngày: số lượt mỗi ngày, chấm vàng khi có lượt chờ xác nhận. */}
      <nav className="mb-4 flex items-center gap-0.5 sm:gap-1.5" aria-label="Chọn ngày">
        <button onClick={() => setWeekStart(addDays(weekStart, -7))} aria-label="Tuần trước" className="icon-btn shrink-0 hover:bg-black/5"><ChevronLeft size={18} /></button>
        <div className="grid min-w-0 flex-1 grid-cols-7 gap-1 sm:gap-1.5">
          {week.map((d) => {
            const c = countByDay.get(d);
            const active = !crossDay && d === day;
            const date = parseDay(d);
            return (
              <button key={d} onClick={() => pickDay(d)} aria-pressed={active} aria-label={`${dayTitle(d, today)}, ${c?.total ?? 0} lượt`}
                className={`relative flex min-w-0 flex-col items-center rounded-xl px-0.5 py-2 transition-colors ${active ? "bg-dark text-white" : "bg-white ring-1 ring-black/[0.06] hover:ring-black/20"}`}>
                <span className={`text-[11px] ${active ? "text-white/70" : "text-muted"}`}>{d === today ? <><span className="sm:hidden">Nay</span><span className="max-sm:hidden">Hôm nay</span></> : WEEKDAY[date.getDay()]}</span>
                <span className="font-display text-lg font-semibold leading-tight tabular-nums">{date.getDate()}</span>
                <span className={`text-[11px] tabular-nums max-sm:hidden ${c?.total ? (active ? "text-white" : "text-dark") : active ? "text-white/50" : "text-black/25"}`}>{c?.total ? `${c.total} lượt` : "Trống"}</span>
                {c?.total ? <span className={`mt-1 h-1.5 w-1.5 rounded-full sm:hidden ${active ? "bg-white" : "bg-dark/60"}`} aria-hidden /> : <span className="mt-1 h-1.5 sm:hidden" aria-hidden />}
                {c?.pending ? <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-secondary" aria-hidden /> : null}
              </button>
            );
          })}
        </div>
        <button onClick={() => setWeekStart(addDays(weekStart, 7))} aria-label="Tuần sau" className="icon-btn shrink-0 hover:bg-black/5"><ChevronRight size={18} /></button>
        <label className="relative shrink-0" title="Chọn ngày khác">
          <span className="sr-only">Chọn ngày khác</span>
          <CalendarDays size={18} className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" />
          <input type="date" value={day} onChange={(e) => { if (e.target.value) pickDay(e.target.value); }} className="h-[38px] w-[38px] cursor-pointer rounded-[10px] opacity-0" />
        </label>
      </nav>

      {/* Hàng đợi việc cần làm + tìm kiếm */}
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="flex flex-wrap gap-2">
          {([["confirm", "Cần xác nhận", queues.confirm.length], ["deposit", "Chờ đặt cọc", queues.deposit.length], ["refund", "Cọc chờ hoàn", queues.refund.length]] as const).map(([key, label, n]) => (
            <button key={key} onClick={() => setQueue(queue === key ? "none" : key)} aria-pressed={queue === key} disabled={!n && queue !== key}
              className={`inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors disabled:cursor-default disabled:opacity-45 ${queue === key ? "border-dark bg-dark text-white" : n ? "border-secondary/60 bg-secondary/15 text-dark hover:border-secondary" : "border-black/10 text-muted"}`}>
              {label}<span className="tabular-nums">{n}</span>
            </button>
          ))}
        </div>
        <label className="relative w-full lg:ml-auto lg:w-72">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Tìm tên, số điện thoại, mã đặt bàn" aria-label="Tìm đặt bàn" className={`${inputCls} pl-9!`} />
        </label>
      </div>

      <section className="rounded-2xl bg-black/[0.025] p-3 sm:p-5">
        <header className="mb-4 flex flex-wrap items-baseline gap-x-4 gap-y-2 px-1">
          <h2 className="font-display text-xl font-semibold">
            {queue === "confirm" ? "Cần gọi xác nhận" : queue === "deposit" ? "Đang chờ khách đặt cọc" : queue === "refund" ? "Tiền cọc cần hoàn" : q ? `Kết quả cho “${query.trim()}”` : dayTitle(day, today)}
          </h2>
          {!crossDay && <span className="text-sm text-muted">{dayCounts.all} lượt, {guestsToday} khách</span>}
          {crossDay && <button onClick={() => { setQueue("none"); setQuery(""); }} className="text-sm font-medium text-primary hover:underline">Về sổ ngày {dmy(day)}</button>}
          {!crossDay && dayCounts.all > 0 && (
            <div className="flex gap-1 sm:ml-auto" role="tablist" aria-label="Lọc trong ngày">
              {([["all", "Tất cả"], ["active", "Sắp đến"], ["seated", "Đang ngồi"], ["done", "Đã xong"]] as const).map(([key, label]) => (
                <button key={key} role="tab" aria-selected={dayFilter === key} onClick={() => setDayFilter(key)} className={`rounded-full px-3 py-1 text-sm ${dayFilter === key ? "bg-white font-medium shadow-sm ring-1 ring-black/10" : "text-muted hover:text-dark"}`}>
                  {label} <span className="tabular-nums text-muted">{dayCounts[key]}</span>
                </button>
              ))}
            </div>
          )}
        </header>

        {loading ? (
          <div className="space-y-2">{Array.from({ length: 4 }, (_, i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-white" />)}</div>
        ) : groups.length === 0 ? (
          <EmptyDay crossDay={crossDay} day={day} today={today} nextDay={[...countByDay.keys()].filter((d) => d > day).sort()[0]} onPick={pickDay} />
        ) : (
          <ol className="space-y-5">
            {groups.map(([key, list], index) => (
              <li key={key}>
                {index === nowGroupIndex && <NowRule now={now} />}
                <div className="grid gap-2 sm:grid-cols-[4.5rem_minmax(0,1fr)]">
                  <h3 className="px-1 pt-3 text-sm font-semibold tabular-nums text-muted sm:text-right">{crossDay ? <>{WEEKDAY[parseDay(key).getDay()]}<br className="max-sm:hidden" /> {dmy(key)}</> : key}</h3>
                  <ul className="space-y-2">{list.map(renderRow)}</ul>
                </div>
              </li>
            ))}
            {nowGroupIndex === -1 && !crossDay && day === today && groups.length > 0 && <li><NowRule now={now} /></li>}
          </ol>
        )}
      </section>

      <ReservationDrawer res={reservations?.find((r) => r.id === openId) ?? null} tables={branchTables} policy={policy} onClose={close} onChanged={refetch} onOpenSession={(s) => { close(); setOpenSession(s); }} />
      <DiningSessionDrawer session={openSession} tables={branchTables} onClose={() => setOpenSession(null)} onChanged={refetch} />
    </div>
  );
}

function NowRule({ now }: { now: Date }) {
  const t = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
  return (
    <div className="mb-3 flex items-center gap-2" role="separator" aria-label={`Bây giờ ${t}`}>
      <span className="w-[4.5rem] shrink-0 text-right text-xs font-semibold tabular-nums text-primary">{t}</span>
      <span className="h-2 w-2 rounded-full bg-primary" />
      <span className="h-px flex-1 bg-primary/50" />
    </div>
  );
}

function EmptyDay({ crossDay, day, today, nextDay, onPick }: { crossDay: boolean; day: string; today: string; nextDay?: string; onPick: (d: string) => void }) {
  return (
    <div className="rounded-xl bg-white px-6 py-12 text-center ring-1 ring-black/[0.06]">
      <p className="font-medium">{crossDay ? "Không có đặt bàn nào khớp." : `${day === today ? "Hôm nay" : `Ngày ${dmy(day)}`} chưa có khách đặt bàn.`}</p>
      {!crossDay && nextDay && <button onClick={() => onPick(nextDay)} className="mt-3 text-sm font-medium text-primary hover:underline">Xem ngày có đặt bàn gần nhất: {dayTitle(nextDay, today)}</button>}
    </div>
  );
}
