import { useState } from "react";
import { Link } from "react-router-dom";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { getDashboard, type Range } from "../api/admin.api";
import { useCan } from "../permissions";
import { PageHeader, StatCard, Tabs } from "../components/primitives";
import { BarList, Donut, LineChart } from "../components/Charts";
import { ORDER_META } from "../statusMeta";

const COLORS = ["#d99a64", "#c89b3c", "#b85c38", "#6e8f6c", "#171717", "#c9c2b8"];

export default function DashboardPage() {
  const can = useCan();
  const isAdmin = can("users", "view");
  const [range, setRange] = useState<Range>(7);
  const { data, loading } = useAsync(() => getDashboard(range), [range]);

  const tasks = data && [
    { n: data.tasks.pendingOrders, label: "đơn chờ xác nhận", to: "/admin/orders?status=pending" },
    { n: data.tasks.pendingDeposits, label: "đặt bàn chờ cọc", to: "/admin/reservations?status=needs_deposit" },
    { n: data.tasks.refundQueue, label: "cọc chờ hoàn", to: "/admin/payments" },
    { n: data.tasks.unreadChats, label: "tin nhắn chưa đọc", to: "/admin/chat" },
    { n: data.tasks.lowStock, label: "nguyên liệu sắp hết", to: "/admin/ingredients" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Tổng quan" subtitle="Những việc cần xử lý trước, số liệu kinh doanh bên dưới." />

      <section aria-label="Việc cần xử lý" className="rounded-[22px] bg-dark text-white p-6 md:p-8">
        <h2 className="font-display text-xl mb-5">Cần xử lý ngay</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {(tasks ?? Array.from({ length: 5 }, () => null)).map((t, i) =>
            t ? (
              <Link key={t.label} to={t.to} className="rounded-2xl bg-white/6 hover:bg-white/12 transition-colors p-4 block">
                <div className={`font-display text-[34px] leading-none ${t.n > 0 ? "text-secondary" : "text-white/40"}`}>{t.n}</div>
                <div className="text-[13px] text-white/65 mt-2">{t.label}</div>
              </Link>
            ) : (<div key={i} className="h-24 rounded-2xl bg-white/6 animate-pulse" />),
          )}
        </div>
      </section>

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <h2 className="font-display text-xl">Kinh doanh</h2>
        <Tabs value={String(range) as "1" | "7" | "30"} onChange={(k) => setRange(Number(k) as Range)} items={[{ key: "1", label: "Hôm nay" }, { key: "7", label: "7 ngày" }, { key: "30", label: "30 ngày" }]} />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isAdmin && <StatCard label="Doanh thu" value={loading || !data ? "…" : formatCurrency(Math.round(data.revenue))} />}
        <StatCard label="Đơn hàng" value={loading || !data ? "…" : String(data.orderCount)} />
        <StatCard label="Đặt bàn hôm nay" value={loading || !data ? "…" : String(data.reservationsToday)} />
        <StatCard label="Khách mới" value={loading || !data ? "…" : String(data.newCustomers)} />
      </div>

      {data && (
        <div className="grid lg:grid-cols-3 gap-4">
          {isAdmin && (
            <div className="card p-6 lg:col-span-2">
              <h3 className="font-display text-lg mb-4">Doanh thu theo ngày</h3>
              <LineChart data={data.series} />
            </div>
          )}
          <div className={`card p-6 ${isAdmin ? "" : "lg:col-span-3"}`}>
            <h3 className="font-display text-lg mb-4">Đơn theo trạng thái</h3>
            <Donut parts={data.byStatus.map((s, i) => ({ label: ORDER_META[s.status].label, value: s.value, color: COLORS[i] }))} />
          </div>
          <div className="card p-6 lg:col-span-3">
            <h3 className="font-display text-lg mb-4">Món bán chạy</h3>
            <BarList items={data.topFoods} unit=" phần" />
          </div>
        </div>
      )}
    </div>
  );
}
