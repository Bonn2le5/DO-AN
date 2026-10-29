import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { ordersStore } from "../api/admin.api";
import DataTable from "../components/DataTable";
import OrderDrawer from "../components/OrderDrawer";
import { PageHeader, StatusBadge, Tabs, inputCls } from "../components/primitives";
import { ORDER_META } from "../statusMeta";
import { fmtDateTime } from "../lib";
import type { OrderStatus } from "../types";

type Tab = "all" | OrderStatus;

export default function OrdersPage() {
  const [params, setParams] = useSearchParams();
  const tab = (params.get("status") as Tab) || "all";
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);
  const { data, loading, refetch } = useAsync(() => ordersStore.list());

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: data?.length ?? 0 };
    data?.forEach((o) => { c[o.status] = (c[o.status] ?? 0) + 1; });
    return c;
  }, [data]);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return data?.filter((o) => (tab === "all" || o.status === tab) && (!q || `${o.code} ${o.customer} ${o.phone}`.toLowerCase().includes(q)));
  }, [data, tab, query]);

  const setTab = (t: Tab) => setParams(t === "all" ? {} : { status: t }, { replace: true });

  return (
    <div>
      <PageHeader title="Đơn hàng" subtitle="Bấm vào một đơn để xem chi tiết và chuyển sang bước tiếp theo." />
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
        <Tabs<Tab> value={tab} onChange={setTab} items={[
          { key: "all", label: "Tất cả", count: counts.all },
          ...(Object.keys(ORDER_META) as OrderStatus[]).map((s) => ({ key: s as Tab, label: ORDER_META[s].label, count: counts[s] ?? 0 })),
        ]} />
        <div className="relative w-full lg:w-72">
          <Search width={15} height={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Mã đơn, tên, số điện thoại…" aria-label="Tìm đơn hàng" className={`${inputCls} pl-9`} />
        </div>
      </div>
      <DataTable
        loading={loading} rows={rows} onRowClick={(o) => setOpenId(o.id)} emptyTitle="Không có đơn nào" emptyHint="Thử đổi bộ lọc trạng thái hoặc từ khoá."
        columns={[
          { header: "Mã đơn", cell: (o) => <b>{o.code}</b> },
          { header: "Khách hàng", cell: (o) => <div><div className="font-medium">{o.customer}</div><div className="text-xs text-muted">{o.phone}</div></div> },
          { header: "Hình thức", cell: (o) => (o.type === "delivery" ? "Giao tận nơi" : "Tự đến lấy") },
          { header: "Tổng tiền", cell: (o) => <b>{formatCurrency(o.total)}</b> },
          { header: "Trạng thái", cell: (o) => <StatusBadge tone={ORDER_META[o.status].tone}>{ORDER_META[o.status].label}</StatusBadge> },
          { header: "Thời gian", cell: (o) => <span className="text-muted">{fmtDateTime(o.createdAt)}</span> },
        ]}
      />
      <OrderDrawer order={data?.find((o) => o.id === openId) ?? null} onClose={() => setOpenId(null)} onChanged={refetch} />
    </div>
  );
}
