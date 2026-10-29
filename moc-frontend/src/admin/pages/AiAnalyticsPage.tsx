import { useState } from "react";
import { useAsync } from "@/hooks/useAsync";
import { getAiAnalytics } from "../api/admin.api";
import DataTable from "../components/DataTable";
import { BarList } from "../components/Charts";
import { PageHeader, StatCard, Tabs } from "../components/primitives";

type Key = "recommended" | "viewed" | "ordered" | "favorited";
const TABS: { key: Key; label: string; unit: string }[] = [
  { key: "recommended", label: "Được gợi ý nhiều", unit: " lượt" }, { key: "viewed", label: "Xem nhiều", unit: " lượt" },
  { key: "ordered", label: "Đặt nhiều", unit: " đơn" }, { key: "favorited", label: "Yêu thích nhiều", unit: " lượt" },
];

export default function AiAnalyticsPage() {
  const { data, loading } = useAsync(() => getAiAnalytics());
  const [tab, setTab] = useState<Key>("recommended");
  if (loading || !data) return <div className="card h-96 animate-pulse bg-black/5" />;

  return (
    <div className="space-y-6">
      <PageHeader title="AI gợi ý món" subtitle="Hiệu quả của mục “Đề xuất dành riêng cho bạn” trên trang chủ." />
      <div className="grid sm:grid-cols-3 gap-4">
        <StatCard label="Lượt gợi ý đã hiển thị" value={data.overview.suggested.toLocaleString("vi-VN")} />
        <StatCard label="Tỉ lệ bấm vào gợi ý" value={`${data.overview.ctr}%`} />
        <StatCard label="Tỉ lệ đặt sau khi bấm" value={`${data.overview.conversion}%`} />
      </div>
      <div className="card p-6">
        <div className="mb-5"><Tabs value={tab} onChange={setTab} items={TABS.map(({ key, label }) => ({ key, label }))} /></div>
        <BarList items={data.top[tab]} unit={TABS.find((t) => t.key === tab)?.unit} />
      </div>
      <div>
        <h2 className="font-display text-lg mb-3">Gợi ý gần đây</h2>
        <DataTable
          rows={data.recent.map((r, i) => ({ ...r, id: String(i) }))}
          columns={[
            { header: "Khách", cell: (r) => r.user },
            { header: "Món được gợi ý", cell: (r) => <b>{r.food}</b> },
            { header: "Độ phù hợp", cell: (r) => (r.score ? `${Math.round(r.score * 100)}%` : "—") },
            { header: "Lý do", cell: (r) => <span className="text-muted">{r.reason}</span> },
          ]}
        />
      </div>
    </div>
  );
}
