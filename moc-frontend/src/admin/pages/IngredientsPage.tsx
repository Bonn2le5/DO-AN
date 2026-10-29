import { useState } from "react";
import { Minus, Plus } from "lucide-react";
import CrudPage from "../components/CrudPage";
import ConfirmModal from "../components/ConfirmModal";
import { StatusBadge, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import { adjustStock, ingredientsStore } from "../api/admin.api";
import { useCan } from "../permissions";
import type { AdminIngredient } from "../data/mockCatalog";

export default function IngredientsPage() {
  const can = useCan();
  const push = useToast((s) => s.push);
  const [target, setTarget] = useState<{ row: AdminIngredient; sign: 1 | -1; reload: () => void } | null>(null);
  const [qty, setQty] = useState("");
  const [busy, setBusy] = useState(false);

  const confirm = async () => {
    const n = Number(qty);
    if (!target || !(n > 0)) return push("Nhập số lượng lớn hơn 0", "err");
    setBusy(true);
    await adjustStock(target.row.id, n * target.sign);
    push(target.sign > 0 ? "Đã nhập kho" : "Đã xuất kho");
    target.reload(); setTarget(null); setQty(""); setBusy(false);
  };

  return (
    <>
      <CrudPage<AdminIngredient>
        title="Nguyên liệu & kho" noun="nguyên liệu" module="ingredients" store={ingredientsStore}
        subtitle="Theo dõi tồn kho; dòng đỏ là nguyên liệu dưới mức tối thiểu."
        blank={{ name: "", unit: "kg", currentStock: 0, minimumStock: 0, active: true }}
        searchText={(i) => i.name}
        columns={[
          { header: "Nguyên liệu", cell: (i) => <b>{i.name}</b> },
          { header: "Tồn hiện tại", cell: (i) => {
            const low = i.currentStock < i.minimumStock;
            return (
              <div className="min-w-40">
                <div className="flex justify-between text-xs mb-1"><span className={low ? "text-primary font-semibold" : ""}>{i.currentStock} {i.unit}</span><span className="text-muted">tối thiểu {i.minimumStock}</span></div>
                <div className="h-1.5 rounded-full bg-black/8"><div className={`h-full rounded-full ${low ? "bg-primary" : "bg-success"}`} style={{ width: `${Math.min(100, (i.currentStock / Math.max(i.minimumStock * 2, 1)) * 100)}%` }} /></div>
              </div>
            );
          } },
          { header: "Tình trạng", cell: (i) => (i.currentStock < i.minimumStock ? <StatusBadge tone="danger">Sắp hết</StatusBadge> : <StatusBadge tone="ok">Đủ dùng</StatusBadge>) },
        ]}
        fields={[
          { key: "name", label: "Tên nguyên liệu", type: "text", required: true, wide: true },
          { key: "unit", label: "Đơn vị", type: "text", required: true },
          { key: "currentStock", label: "Tồn hiện tại", type: "number" },
          { key: "minimumStock", label: "Tồn tối thiểu", type: "number", hint: "Dưới mức này sẽ cảnh báo trên trang Tổng quan." },
          { key: "active", label: "Đang sử dụng", type: "toggle" },
        ]}
        rowActions={(row, reload) => can("ingredients", "update") && (
          <>
            <button className="icon-btn w-8! h-8!" aria-label="Nhập kho" title="Nhập kho" onClick={() => setTarget({ row, sign: 1, reload })}><Plus width={15} height={15} /></button>
            <button className="icon-btn w-8! h-8!" aria-label="Xuất kho" title="Xuất kho" onClick={() => setTarget({ row, sign: -1, reload })}><Minus width={15} height={15} /></button>
          </>
        )}
      />
      <ConfirmModal
        open={!!target} busy={busy} confirmLabel={target?.sign === 1 ? "Nhập kho" : "Xuất kho"}
        title={`${target?.sign === 1 ? "Nhập" : "Xuất"} kho: ${target?.row.name ?? ""}`}
        onConfirm={confirm} onCancel={() => { setTarget(null); setQty(""); }}
      >
        <label className="text-[13px] font-semibold text-muted block mb-1.5">Số lượng ({target?.row.unit})</label>
        <input type="number" min={0} value={qty} onChange={(e) => setQty(e.target.value)} className={inputCls} autoFocus />
      </ConfirmModal>
    </>
  );
}
