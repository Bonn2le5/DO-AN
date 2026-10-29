import { useMemo, useState } from "react";
import { Plus, Users } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { tablesStore } from "../api/admin.api";
import RecordDrawer, { type FieldDef } from "../components/RecordDrawer";
import { PageHeader, StatusBadge, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import { useCan } from "../permissions";
import { TABLE_META } from "../statusMeta";
import type { AdminTable } from "../types";
import type { TableStatus } from "../types";

const zoneOptions = ["Trong nhà", "Ban công", "Sân vườn"].map((v) => ({ value: v, label: v }));
const statusOptions = (Object.keys(TABLE_META) as TableStatus[]).map((s) => ({ value: s, label: TABLE_META[s].label }));
const fields: FieldDef<AdminTable>[] = [
  { key: "number", label: "Tên bàn", type: "text", required: true },
  { key: "zone", label: "Khu vực", type: "select", options: zoneOptions, required: true },
  { key: "capacity", label: "Sức chứa (khách)", type: "number", required: true },
  { key: "status", label: "Tình trạng", type: "select", options: statusOptions, required: true },
];
const blank: Partial<AdminTable> = { number: "", zone: "Trong nhà", capacity: 4, status: "available" };

export default function TablesPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const { data, loading, refetch } = useAsync(() => tablesStore.list());
  const [editing, setEditing] = useState<AdminTable | "new" | null>(null);
  const [saving, setSaving] = useState(false);
  const initial = useMemo(() => (editing && editing !== "new" ? editing : blank), [editing]);
  const zones = [...new Set(data?.map((t) => t.zone))];

  const changeStatus = async (t: AdminTable, status: TableStatus) => {
    await tablesStore.update(t.id, { status });
    push(`${t.number}: ${TABLE_META[status].label}`);
    refetch();
  };

  const save = async (v: Partial<AdminTable>) => {
    setSaving(true);
    try {
      if (editing === "new") await tablesStore.create(v as Omit<AdminTable, "id">);
      else if (editing) await tablesStore.update(editing.id, v);
      push("Đã lưu bàn"); setEditing(null); refetch();
    } finally { setSaving(false); }
  };

  return (
    <div>
      <PageHeader
        title="Sơ đồ bàn" subtitle="Tình trạng từng bàn theo khu vực. Đổi nhanh tình trạng ngay trên thẻ."
        actions={can("tables", "create") && <button className="btn btn-primary py-2.5! px-5! text-sm!" onClick={() => setEditing("new")}><Plus width={16} height={16} />Thêm bàn</button>}
      />
      {loading ? <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-32 rounded-2xl bg-black/5 animate-pulse" />)}</div> : (
        <div className="space-y-8">
          {zones.map((zone) => (
            <section key={zone}>
              <h2 className="font-display text-lg mb-3">{zone}</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                {data?.filter((t) => t.zone === zone).map((t) => (
                  <div key={t.id} className="card p-4 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <button disabled={!can("tables", "update")} onClick={() => setEditing(t)} className="font-display text-lg text-left hover:text-primary disabled:hover:text-text">{t.number}</button>
                        <div className="flex items-center gap-1 text-xs text-muted mt-0.5"><Users width={12} height={12} />{t.capacity} khách</div>
                      </div>
                      <StatusBadge tone={TABLE_META[t.status].tone}>{TABLE_META[t.status].label}</StatusBadge>
                    </div>
                    <select
                      aria-label={`Tình trạng ${t.number}`} value={t.status} disabled={!can("tables", "update")}
                      onChange={(e) => changeStatus(t, e.target.value as TableStatus)} className={`${inputCls} py-2!`}
                    >
                      {statusOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
      <RecordDrawer<AdminTable> open={editing !== null} title={editing === "new" ? "Thêm bàn" : "Sửa bàn"} fields={fields} initial={initial} saving={saving} onClose={() => setEditing(null)} onSave={save} />
    </div>
  );
}
