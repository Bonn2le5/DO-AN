import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { getDepositPolicy, reservationsStore, tablesStore, needsRefund } from "../api/admin.api";
import DataTable from "../components/DataTable";
import ReservationDrawer from "../components/ReservationDrawer";
import ReservationTimeline from "../components/ReservationTimeline";
import { PageHeader, StatusBadge, Tabs, inputCls } from "../components/primitives";
import { DEPOSIT_META, RES_META } from "../statusMeta";
import { ymd } from "../lib";
import type { AdminReservation, ReservationStatus } from "../types";

type View = "timeline" | "list";
type Filter = "all" | ReservationStatus | "refund" | "needs_deposit";

const needsDeposit = (r: AdminReservation) =>
  r.depositAmount > 0 && ["unpaid", "pending", "failed"].includes(r.depositStatus)
  && ["pending_confirmation", "pending_payment"].includes(r.status);

export default function ReservationsPage() {
  const [params, setParams] = useSearchParams();
  const [view, setView] = useState<View>("timeline");
  const [date, setDate] = useState(ymd(0));
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(params.get("open"));
  const filter = (params.get("status") as Filter) || "all";

  const { data: reservations, loading, refetch } = useAsync(() => reservationsStore.list());
  const { data: tables } = useAsync(() => tablesStore.list());
  const { data: policy } = useAsync(() => getDepositPolicy());

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return reservations?.filter((r) => {
      const okFilter = filter === "all" || (filter === "refund" ? needsRefund(r) : filter === "needs_deposit" ? needsDeposit(r) : r.status === filter);
      return okFilter && (!q || `${r.code} ${r.customer} ${r.phone}`.toLowerCase().includes(q));
    });
  }, [reservations, filter, query]);

  const close = () => { setOpenId(null); if (params.get("open")) { params.delete("open"); setParams(params, { replace: true }); } };
  const setFilter = (f: Filter) => setParams(f === "all" ? {} : { status: f }, { replace: true });
  const count = (f: Filter) => reservations?.filter((r) => (f === "all" ? true : f === "refund" ? needsRefund(r) : f === "needs_deposit" ? needsDeposit(r) : r.status === f)).length ?? 0;

  return (
    <div>
      <PageHeader title="Đặt bàn" subtitle="Xem theo lịch từng bàn trong ngày, hoặc theo danh sách để lọc nhanh." />
      <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
        <Tabs<View> value={view} onChange={setView} items={[{ key: "timeline", label: "Lịch theo bàn" }, { key: "list", label: "Danh sách" }]} />
        {view === "timeline"
          ? <input type="date" value={date} onChange={(e) => setDate(e.target.value)} aria-label="Chọn ngày" className={`${inputCls} w-auto!`} />
          : <div className="relative w-full sm:w-72"><Search width={15} height={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Mã, tên, số điện thoại…" aria-label="Tìm đặt bàn" className={`${inputCls} pl-9`} /></div>}
      </div>

      {view === "timeline" ? (
        loading || !tables ? <div className="card h-80 animate-pulse bg-black/5" /> : (
          <>
            <ReservationTimeline tables={tables} reservations={(reservations ?? []).filter((r) => r.date === date)} onOpen={(r) => setOpenId(r.id)} />
            <div className="flex gap-4 flex-wrap mt-3 text-xs text-muted">
              {(["pending_confirmation", "pending_payment", "confirmed", "seated", "completed", "cancelled"] as ReservationStatus[]).map((s) => <span key={s}>{RES_META[s].label}</span>)}
            </div>
          </>
        )
      ) : (
        <>
          <div className="mb-4">
            <Tabs<Filter> value={filter} onChange={setFilter} items={[
              { key: "all", label: "Tất cả", count: count("all") },
              { key: "pending_confirmation", label: "Chờ xác nhận", count: count("pending_confirmation") },
              { key: "needs_deposit", label: "Chờ đặt cọc", count: count("needs_deposit") },
              { key: "pending_payment", label: "Chờ đặt cọc", count: count("pending_payment") },
              { key: "confirmed", label: "Đã xác nhận", count: count("confirmed") },
              { key: "refund", label: "Cọc chờ hoàn", count: count("refund") },
              { key: "cancelled", label: "Đã huỷ", count: count("cancelled") },
            ]} />
          </div>
          <DataTable
            loading={loading} rows={rows} onRowClick={(r) => setOpenId(r.id)} emptyTitle="Không có đặt bàn nào"
            columns={[
              { header: "Mã", cell: (r) => <b>{r.code}</b> },
              { header: "Khách", cell: (r) => <div><div className="font-medium">{r.customer}</div><div className="text-xs text-muted">{r.phone}</div></div> },
              { header: "Giờ hẹn", cell: (r) => `${r.time} · ${r.date.split("-").reverse().join("/")}` },
              { header: "Bàn", cell: (r) => `${r.tableLabel} · ${r.partySize} khách` },
              { header: "Tiền cọc", cell: (r) => (r.depositAmount ? <div><div>{formatCurrency(r.depositAmount)}</div><StatusBadge tone={DEPOSIT_META[r.depositStatus].tone}>{DEPOSIT_META[r.depositStatus].label}</StatusBadge></div> : <span className="text-muted">Không cọc</span>) },
              { header: "Trạng thái", cell: (r) => <StatusBadge tone={RES_META[r.status].tone}>{RES_META[r.status].label}</StatusBadge> },
            ]}
          />
        </>
      )}
      <ReservationDrawer res={reservations?.find((r) => r.id === openId) ?? null} policy={policy} onClose={close} onChanged={refetch} />
    </div>
  );
}
