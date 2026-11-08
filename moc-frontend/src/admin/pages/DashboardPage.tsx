import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, RefreshCw } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { getDashboard, type DashboardBranch, type DashboardData, type LiveTableState, type Range } from "../api/admin.api";
import { useCan } from "../permissions";
import { PageHeader } from "../components/primitives";

const CELL: Record<LiveTableState, { cls: string; label: string }> = {
  busy: { cls: "bg-primary text-white", label: "Có khách" },
  cleaning: { cls: "bg-secondary text-dark", label: "Chờ dọn" },
  held: { cls: "bg-sky-200 text-sky-900", label: "Đang giữ" },
  free: { cls: "text-white/75 ring-1 ring-inset ring-white/45", label: "Trống" },
  maintenance: { cls: "bg-white/[0.07] text-white/30 bg-[repeating-linear-gradient(135deg,transparent_0_4px,rgb(255_255_255/0.08)_4px_6px)]", label: "Bảo trì" },
};
const RES_LABEL: Record<string, string> = { cho_xac_nhan: "Chờ xác nhận", cho_thanh_toan: "Chờ cọc", da_xac_nhan: "Đã xác nhận" };
const shortName = (name: string) => name.replace(/^Nhà hàng Mộc\s*-\s*/i, "");
const compact = (n: number) => n >= 1_000_000 ? `${(n / 1_000_000).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} tr` : n >= 1000 ? `${Math.round(n / 1000)}k` : String(Math.round(n));

export default function DashboardPage() {
  const can = useCan();
  const isAdmin = can("users", "view");
  const [range, setRange] = useState<Range>(7);
  const { data, loading, refetch } = useAsync(() => getDashboard(range), [range]);

  // Trang này hay được để mở ở quầy: tự làm mới mỗi phút.
  useEffect(() => { const id = window.setInterval(() => void refetch(), 60_000); return () => window.clearInterval(id); }, [refetch]);

  const single = data?.live.length === 1 ? data.live[0] : null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tổng quan"
        subtitle={single ? single.name : "Tất cả chi nhánh"}
        actions={<button onClick={() => void refetch()} className="btn btn-outline py-2! px-3! text-sm!"><RefreshCw size={15} className={loading ? "animate-spin" : ""} />{data?.now ? `Cập nhật lúc ${data.now}` : "Làm mới"}</button>}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-6">
          <NowSection data={data} single={single} />
          <TodaySentence data={data} />
          <RevenueSection data={data} range={range} setRange={setRange} isAdmin={isAdmin} />
        </div>
        <aside className="space-y-6">
          <TasksSection data={data} can={can} />
          <UpcomingSection data={data} multiBranch={!single} />
          <TopFoods data={data} range={range} />
        </aside>
      </div>
    </div>
  );
}

/** Lúc này: mỗi bàn là một ô; admin thấy các chi nhánh xếp chồng để so sánh. */
function NowSection({ data, single }: { data?: DashboardData; single: DashboardBranch | null }) {
  return (
    <section aria-labelledby="now-title" className="rounded-2xl bg-dark p-5 text-white sm:p-6">
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="now-title" className="font-display text-xl font-semibold">Lúc này ở nhà hàng</h2>
        <Link to="/admin/tables" className="text-sm text-white/70 hover:text-white">Mở sơ đồ bàn</Link>
      </div>
      {!data ? <div className="h-24 animate-pulse rounded-xl bg-white/10" /> : (
        <div className="space-y-6">
          {data.live.map((b) => {
            const active = b.tables.filter((t) => t.state !== "maintenance");
            const busy = b.tables.filter((t) => t.state === "busy").length;
            return (
              <div key={b.id}>
                {!single && <h3 className="mb-2 truncate text-sm font-medium text-white/85">{shortName(b.name)}</h3>}
                <div className="grid items-end gap-x-8 gap-y-3 md:grid-cols-[minmax(0,1fr)_auto]">
                  <ul className="flex flex-wrap gap-1.5" aria-label={`Bàn tại ${b.name}`}>
                    {b.tables.map((t) => (
                      <li key={t.name} title={`${t.name}: ${CELL[t.state].label}, ${t.seats} ghế`}
                        className={`flex items-center justify-center rounded-md text-[11px] font-semibold tabular-nums ${CELL[t.state].cls} ${single ? "h-14 w-14" : "h-8 w-8"}`}>
                        {single ? t.name.replace(/^.*?(\d+)$/, "$1") : null}
                        <span className="sr-only">{t.name} {CELL[t.state].label}</span>
                      </li>
                    ))}
                    {b.tables.length === 0 && <li className="text-sm text-white/50">Chưa có bàn</li>}
                  </ul>
                  <dl className="grid grid-cols-3 gap-6 text-sm md:w-[300px]">
                    <Fig label="bàn có khách" value={`${busy}/${active.length}`} />
                    <Fig label="khách" value={String(b.guests)} />
                    <Fig label="hoá đơn đang mở" value={b.openTotal ? compact(b.openTotal) : "0"} />
                  </dl>
                </div>
              </div>
            );
          })}
          <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-white/60" aria-label="Chú thích">
            {(["busy", "cleaning", "free", "maintenance"] as const).map((k) => <li key={k} className="inline-flex items-center gap-1.5"><span className={`h-2.5 w-2.5 rounded-sm ${CELL[k].cls}`} />{CELL[k].label}</li>)}
          </ul>
        </div>
      )}
    </section>
  );
}

function Fig({ label, value }: { label: string; value: string }) {
  return <div><dt className="sr-only">{label}</dt><dd className="font-display text-2xl font-semibold tabular-nums leading-none">{value}</dd><dd className="mt-1 text-xs text-white/60 md:whitespace-nowrap">{label}</dd></div>;
}

/** Số liệu hôm nay viết thành câu, đọc một lần là hiểu. */
function TodaySentence({ data }: { data?: DashboardData }) {
  if (!data) return <div className="h-20 animate-pulse rounded-2xl bg-black/[0.04]" />;
  const { revenue, bills, lastWeekSameTime, reservations, upcomingCount } = data.today;
  const diff = revenue - lastWeekSameTime;
  return (
    <section aria-label="Hôm nay" className="px-1">
      <p className="font-display text-2xl leading-snug sm:text-[28px]">
        Hôm nay đã thu <span className="font-bold tabular-nums">{formatCurrency(revenue)}</span> từ {bills} hoá đơn
        {bills > 0 && <>, trung bình {formatCurrency(Math.round(revenue / bills))} mỗi hoá đơn</>}.
      </p>
      <p className="mt-2 text-sm text-muted">
        {lastWeekSameTime > 0
          ? <>{diff >= 0 ? "Cao hơn" : "Thấp hơn"} {formatCurrency(Math.abs(diff))} so với cùng giờ tuần trước. </>
          : "Cùng giờ tuần trước chưa có doanh thu để so sánh. "}
        {reservations > 0 ? `${reservations} lượt đặt bàn hôm nay, còn ${upcomingCount} lượt chưa đến.` : "Hôm nay không có lượt đặt bàn."}
      </p>
    </section>
  );
}

function RevenueSection({ data, range, setRange, isAdmin }: { data?: DashboardData; range: Range; setRange: (r: Range) => void; isAdmin: boolean }) {
  const series = data?.series ?? [];
  const max = Math.max(...series.map((d) => d.value), 1);
  const total = series.reduce((n, d) => n + d.value, 0);
  const branches = data?.live ?? [];
  const topBranch = Math.max(...branches.map((b) => b.rangeRevenue), 1);
  return (
    <section aria-labelledby="rev-title" className="rounded-2xl bg-white p-5 ring-1 ring-black/[0.06] sm:p-6">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="rev-title" className="font-display text-lg font-semibold">Doanh thu {range} ngày</h2>
          <p className="text-sm text-muted tabular-nums">{data ? formatCurrency(total) : "…"}</p>
        </div>
        <div className="inline-flex rounded-lg bg-black/[0.04] p-0.5" role="tablist" aria-label="Khoảng thời gian">
          {([7, 30] as const).map((r) => <button key={r} role="tab" aria-selected={range === r} onClick={() => setRange(r)} className={`rounded-md px-3 py-1.5 text-sm font-medium ${range === r ? "bg-white shadow-sm" : "text-muted hover:text-dark"}`}>{r} ngày</button>)}
        </div>
      </div>

      {!data ? <div className="h-44 animate-pulse rounded-xl bg-black/[0.04]" /> : (
        <div className="flex h-44 items-end gap-[3px]" role="img" aria-label={`Doanh thu theo ngày, tổng ${formatCurrency(total)}`}>
          {series.map((d, i) => {
            const last = i === series.length - 1;
            return (
              <div key={d.label} className="group relative flex h-full min-w-0 flex-1 flex-col justify-end">
                <div className={`w-full rounded-t-[3px] ${last ? "bg-primary" : "bg-secondary/70 group-hover:bg-secondary"}`} style={{ height: `${Math.max(d.value ? 3 : 1, (d.value / max) * 100)}%` }} />
                <span className="pointer-events-none absolute bottom-full left-1/2 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded bg-dark px-1.5 py-0.5 text-[11px] text-white group-hover:block">{d.label}: {formatCurrency(d.value)}</span>
                {(range === 7 || i % 5 === 0 || last) && <span className={`mt-1 text-center text-[10px] tabular-nums ${last ? "font-semibold text-primary" : "text-muted"}`}>{last ? "Nay" : d.label}</span>}
              </div>
            );
          })}
        </div>
      )}

      {isAdmin && branches.length > 1 && (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <caption className="mb-2 text-left font-medium">So sánh chi nhánh</caption>
            <thead className="text-left text-xs text-muted">
              <tr><th className="py-2 font-normal">Chi nhánh</th><th className="py-2 text-right font-normal">Doanh thu</th><th className="py-2 text-right font-normal">Hoá đơn</th><th className="py-2 text-right font-normal">TB/hoá đơn</th><th className="py-2 text-right font-normal">Lượt khách</th></tr>
            </thead>
            <tbody>
              {[...branches].sort((a, b) => b.rangeRevenue - a.rangeRevenue).map((b) => (
                <tr key={b.id} className="border-t border-black/[0.06]">
                  <td className="py-2.5 pr-3">
                    <div className="max-w-[16rem] truncate" title={b.name}>{shortName(b.name)}</div>
                    <div className="mt-1 h-1 rounded-full bg-black/[0.05]"><div className="h-1 rounded-full bg-primary/70" style={{ width: `${(b.rangeRevenue / topBranch) * 100}%` }} /></div>
                  </td>
                  <td className="py-2.5 text-right font-medium tabular-nums">{formatCurrency(b.rangeRevenue)}</td>
                  <td className="py-2.5 text-right tabular-nums">{b.rangeBills}</td>
                  <td className="py-2.5 text-right tabular-nums">{b.rangeBills ? formatCurrency(Math.round(b.rangeRevenue / b.rangeBills)) : "–"}</td>
                  <td className="py-2.5 text-right tabular-nums">{b.rangeGuests}</td>
                </tr>
              ))}
              {data?.unassigned && (
                <tr className="border-t border-black/[0.06] text-muted">
                  <td className="py-2.5 pr-3" title="Hoá đơn cũ không gắn chi nhánh hay phiên phục vụ nào">Không gắn chi nhánh</td>
                  <td className="py-2.5 text-right tabular-nums">{formatCurrency(data.unassigned.revenue)}</td>
                  <td className="py-2.5 text-right tabular-nums">{data.unassigned.bills}</td>
                  <td className="py-2.5 text-right tabular-nums">{formatCurrency(Math.round(data.unassigned.revenue / data.unassigned.bills))}</td>
                  <td className="py-2.5 text-right">–</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function TasksSection({ data, can }: { data?: DashboardData; can: ReturnType<typeof useCan> }) {
  const tasks = data ? [
    { n: data.tasks.pendingConfirm, label: "lượt đặt bàn cần gọi xác nhận", to: "/admin/reservations?status=pending_confirmation", ok: can("reservations") },
    { n: data.tasks.pendingDeposits, label: "lượt đặt bàn chờ khách cọc", to: "/admin/reservations?status=needs_deposit", ok: can("reservations") },
    { n: data.tasks.refundQueue, label: "khoản cọc cần hoàn", to: "/admin/reservations?status=refund", ok: can("reservations") },
    { n: data.tasks.lowStock, label: "nguyên liệu dưới mức tối thiểu", to: "/admin/ingredients", ok: can("ingredients") },
    { n: data.tasks.unreadChats, label: "tin nhắn khách chưa đọc", to: "/admin/chat", ok: can("chat") },
  ].filter((t) => t.ok && t.n > 0) : null;
  return (
    <section aria-labelledby="tasks-title">
      <h2 id="tasks-title" className="mb-3 font-display text-lg font-semibold">Cần xử lý</h2>
      {!tasks ? <div className="h-28 animate-pulse rounded-2xl bg-black/[0.04]" /> : tasks.length === 0 ? (
        <p className="rounded-2xl bg-white px-4 py-5 text-sm text-muted ring-1 ring-black/[0.06]">Không có việc tồn đọng.</p>
      ) : (
        <ul className="divide-y divide-black/[0.06] overflow-hidden rounded-2xl bg-white ring-1 ring-black/[0.06]">
          {tasks.map((t) => (
            <li key={t.label}>
              <Link to={t.to} className="flex items-center gap-3 px-4 py-3 hover:bg-black/[0.02] focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                <span className="flex h-8 min-w-8 items-center justify-center rounded-full bg-secondary/25 px-2 font-semibold tabular-nums">{t.n}</span>
                <span className="flex-1 text-sm">{t.label}</span>
                <ChevronRight size={16} className="text-muted" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function UpcomingSection({ data, multiBranch }: { data?: DashboardData; multiBranch: boolean }) {
  return (
    <section aria-labelledby="up-title">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 id="up-title" className="font-display text-lg font-semibold">Khách sắp đến hôm nay</h2>
        <Link to="/admin/reservations" className="text-sm text-primary hover:underline">Sổ đặt bàn</Link>
      </div>
      {!data ? <div className="h-28 animate-pulse rounded-2xl bg-black/[0.04]" /> : data.upcoming.length === 0 ? (
        <p className="rounded-2xl bg-white px-4 py-5 text-sm text-muted ring-1 ring-black/[0.06]">Không còn lượt đặt bàn nào hôm nay.</p>
      ) : (
        <ul className="divide-y divide-black/[0.06] rounded-2xl bg-white ring-1 ring-black/[0.06]">
          {data.upcoming.map((r) => (
            <li key={r.id}>
              <Link to={`/admin/reservations?open=${r.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-black/[0.02]">
                <span className="w-11 font-display font-semibold tabular-nums">{r.time}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-medium">{r.customer || "Khách"} <span className="font-normal text-muted">{r.party} khách</span></span>
                  <span className="block truncate text-xs text-muted">{RES_LABEL[r.status] ?? r.status}{r.preorder ? ", có gọi món trước" : ""}{multiBranch ? `, ${r.branch}` : ""}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function TopFoods({ data, range }: { data?: DashboardData; range: Range }) {
  const items = data?.topFoods ?? [];
  const max = Math.max(...items.map((i) => i[1]), 1);
  return (
    <section aria-labelledby="top-title">
      <h2 id="top-title" className="mb-3 font-display text-lg font-semibold">Món bán chạy {range} ngày</h2>
      {!data ? <div className="h-28 animate-pulse rounded-2xl bg-black/[0.04]" /> : items.length === 0 ? (
        <p className="rounded-2xl bg-white px-4 py-5 text-sm text-muted ring-1 ring-black/[0.06]">Chưa có món nào được bán trong khoảng này.</p>
      ) : (
        <ol className="space-y-2.5 rounded-2xl bg-white p-4 ring-1 ring-black/[0.06]">
          {items.map(([name, qty]) => (
            <li key={name}>
              <div className="flex justify-between gap-3 text-sm"><span className="truncate">{name}</span><span className="tabular-nums text-muted">{qty} phần</span></div>
              <div className="mt-1 h-1.5 rounded-full bg-black/[0.05]"><div className="h-1.5 rounded-full bg-secondary" style={{ width: `${(qty / max) * 100}%` }} /></div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
