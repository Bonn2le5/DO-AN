import { useCallback, useMemo, useState } from "react";
import { ArrowDownUp, History, Trash2 } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import CrudPage from "../components/CrudPage";
import ConfirmModal from "../components/ConfirmModal";
import DataTable from "../components/DataTable";
import Drawer from "../components/Drawer";
import { PageHeader, StatusBadge, Tabs, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import {
  createRecipe, createStockMove, deleteRecipe, foodsStore, ingredientsStore, listRecipes, listStockMoves, updateRecipe,
  type StockMove, type StockMoveType,
} from "../api/admin.api";
import { useCan } from "../permissions";
import { fmtDateTime } from "../lib";
import type { AdminIngredient } from "../data/mockCatalog";

const qtyFmt = (n: number) => n.toLocaleString("vi-VN", { maximumFractionDigits: 3 });
const isOut = (i: AdminIngredient) => i.currentStock <= 0;
// Khớp với backend (canh_bao_sap_het): tồn <= tối thiểu là sắp hết.
const isLow = (i: AdminIngredient) => !isOut(i) && i.minimumStock > 0 && i.currentStock <= i.minimumStock;

const errMsg = (e: unknown, fallback: string) => {
  const data = (e as { response?: { data?: unknown } })?.response?.data;
  if (data && typeof data === "object") {
    const msgs = Object.values(data as Record<string, unknown>).flatMap((v) => (Array.isArray(v) ? v.map(String) : typeof v === "string" ? [v] : []));
    if (msgs.length) return msgs.join(" · ");
  }
  return e instanceof Error ? e.message : fallback;
};

const MOVE_META: Record<StockMoveType, { label: string; tone: "ok" | "danger" | "info" }> = {
  nhap: { label: "Nhập kho", tone: "ok" },
  xuat: { label: "Xuất kho", tone: "danger" },
  dieu_chinh: { label: "Kiểm kê", tone: "info" },
};

const refLabel = (m: StockMove) =>
  m.refType === "don_hang" ? `Đơn hàng #${m.refId}` : m.refType === "ton_dau_ky" ? "Tồn đầu kỳ" : m.refType && m.refType !== "thu_cong" ? `${m.refType}${m.refId ? ` #${m.refId}` : ""}` : "Thủ công";

const signedQty = (m: StockMove) => {
  const delta = m.after - m.before;
  return `${delta > 0 ? "+" : delta < 0 ? "−" : "±"}${qtyFmt(Math.abs(delta))} ${m.unit}`;
};

function StockStatus({ row }: { row: AdminIngredient }) {
  if (!row.active) return <StatusBadge tone="neutral">Ngừng dùng</StatusBadge>;
  if (isOut(row)) return <StatusBadge tone="danger">Hết hàng</StatusBadge>;
  if (isLow(row)) return <StatusBadge tone="warn">Sắp hết</StatusBadge>;
  return <StatusBadge tone="ok">Đủ dùng</StatusBadge>;
}

function StockBar({ row }: { row: AdminIngredient }) {
  const bad = isOut(row) || isLow(row);
  const pct = Math.min(100, (row.currentStock / Math.max(row.minimumStock * 2, 1)) * 100);
  return (
    <div className="min-w-40">
      <div className="flex justify-between text-xs mb-1">
        <span className={bad ? "text-primary font-semibold" : ""}>{qtyFmt(row.currentStock)} {row.unit}</span>
        <span className="text-muted">tối thiểu {qtyFmt(row.minimumStock)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-black/8"><div className={`h-full rounded-full ${bad ? "bg-primary" : "bg-success"}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

/* ---------- Phiếu nhập / xuất / kiểm kê ---------- */
function StockMoveModal({ row, onClose, onDone }: { row: AdminIngredient | null; onClose: () => void; onDone: () => void }) {
  const push = useToast((s) => s.push);
  const [type, setType] = useState<StockMoveType>("nhap");
  const [qty, setQty] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const n = Number(qty);
  const after = row ? (type === "nhap" ? row.currentStock + n : type === "xuat" ? row.currentStock - n : n) : 0;

  const close = () => { setType("nhap"); setQty(""); setNote(""); onClose(); };
  const submit = async () => {
    if (!row) return;
    if (qty === "" || Number.isNaN(n) || n < 0 || (type !== "dieu_chinh" && n === 0)) return push(type === "dieu_chinh" ? "Nhập tồn thực tế (≥ 0)" : "Nhập số lượng lớn hơn 0", "err");
    if (type === "xuat" && n > row.currentStock) return push(`Chỉ còn ${qtyFmt(row.currentStock)} ${row.unit}, không đủ để xuất`, "err");
    setBusy(true);
    try {
      await createStockMove(row.id, type, n, note.trim());
      push(`${MOVE_META[type].label}: ${row.name}`);
      onDone(); close();
    } catch (e) {
      push(errMsg(e, "Không ghi được phiếu kho"), "err");
    } finally { setBusy(false); }
  };

  return (
    <ConfirmModal open={!!row} busy={busy} confirmLabel={MOVE_META[type].label} title={`Phiếu kho: ${row?.name ?? ""}`} onConfirm={submit} onCancel={close}>
      <div className="mt-3 space-y-3">
        <div role="tablist" className="grid grid-cols-3 gap-1 rounded-xl bg-black/5 p-1">
          {(Object.keys(MOVE_META) as StockMoveType[]).map((k) => (
            <button key={k} role="tab" aria-selected={type === k} onClick={() => setType(k)} className={`rounded-lg py-1.5 text-sm font-medium ${type === k ? "bg-white shadow-sm" : "text-muted hover:text-dark"}`}>{MOVE_META[k].label}</button>
          ))}
        </div>
        <div>
          <label htmlFor="stock-qty" className="text-[13px] font-semibold text-muted block mb-1.5">
            {type === "dieu_chinh" ? "Tồn thực tế sau kiểm kê" : "Số lượng"} ({row?.unit})
          </label>
          <input id="stock-qty" type="number" min={0} step="any" value={qty} onChange={(e) => setQty(e.target.value)} className={inputCls} autoFocus />
          {row && qty !== "" && !Number.isNaN(n) && (
            <p className={`text-xs mt-1.5 ${after < 0 ? "text-primary" : "text-muted"}`}>Tồn: {qtyFmt(row.currentStock)} → <b>{qtyFmt(after)}</b> {row.unit}</p>
          )}
        </div>
        <div>
          <label htmlFor="stock-note" className="text-[13px] font-semibold text-muted block mb-1.5">Ghi chú</label>
          <input id="stock-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder={type === "nhap" ? "VD: Nhập từ NCC Hải Sản Minh Phát" : type === "xuat" ? "VD: Hỏng, hết hạn" : "VD: Kiểm kê cuối ngày"} className={inputCls} />
        </div>
      </div>
    </ConfirmModal>
  );
}

/* ---------- Bảng lịch sử ---------- */
function MovesTable({ rows, loading, showIngredient }: { rows: StockMove[] | undefined; loading: boolean; showIngredient?: boolean }) {
  return (
    <DataTable<StockMove>
      rows={rows} loading={loading} pageSize={15}
      emptyTitle="Chưa có giao dịch kho" emptyHint="Phiếu nhập, xuất, kiểm kê và xuất kho khi gửi bếp sẽ hiện ở đây."
      columns={[
        { header: "Thời gian", cell: (m) => <span className="whitespace-nowrap text-sm">{fmtDateTime(m.at)}</span> },
        ...(showIngredient ? [{ header: "Nguyên liệu", cell: (m: StockMove) => <b>{m.ingredientName}</b> }] : []),
        { header: "Loại", cell: (m) => <StatusBadge tone={MOVE_META[m.type]?.tone ?? "neutral"}>{MOVE_META[m.type]?.label ?? m.type}</StatusBadge> },
        { header: "Biến động", cell: (m) => <span className={`font-semibold whitespace-nowrap ${m.after < m.before ? "text-primary" : "text-[#456543]"}`}>{signedQty(m)}</span> },
        { header: "Tồn", cell: (m) => <span className="text-sm whitespace-nowrap text-muted">{qtyFmt(m.before)} → <b className="text-dark">{qtyFmt(m.after)}</b></span> },
        { header: "Nguồn", cell: (m) => <span className="text-sm whitespace-nowrap">{refLabel(m)}</span> },
        { header: "Ghi chú", cell: (m) => <span className="text-sm text-muted">{m.note || "—"}</span> },
        { header: "Người tạo", cell: (m) => <span className="text-sm whitespace-nowrap">{m.by || "Hệ thống"}</span> },
      ]}
    />
  );
}

function HistoryTab() {
  const [type, setType] = useState<"all" | StockMoveType>("all");
  const { data, loading } = useAsync(() => listStockMoves(), []);
  const rows = useMemo(() => (type === "all" ? data : data?.filter((m) => m.type === type)), [data, type]);
  const count = (k: StockMoveType) => data?.filter((m) => m.type === k).length;
  return (
    <div className="space-y-4">
      <Tabs value={type} onChange={setType} items={[
        { key: "all", label: "Tất cả", count: data?.length },
        { key: "nhap", label: "Nhập kho", count: count("nhap") },
        { key: "xuat", label: "Xuất kho", count: count("xuat") },
        { key: "dieu_chinh", label: "Kiểm kê", count: count("dieu_chinh") },
      ]} />
      <MovesTable rows={rows} loading={loading} showIngredient />
    </div>
  );
}

/* ---------- Chi tiết: định mức món + lịch sử ---------- */
function IngredientDetail({ row, onClose, onChanged }: { row: AdminIngredient | null; onClose: () => void; onChanged: () => void }) {
  const can = useCan();
  const push = useToast((s) => s.push);
  const editable = can("ingredients", "update");
  const [tab, setTab] = useState<"recipes" | "history">("recipes");
  const id = row?.id;
  const recipes = useAsync(() => (id ? listRecipes(id) : Promise.resolve([])), [id]);
  const moves = useAsync(() => (id ? listStockMoves(id) : Promise.resolve([])), [id]);
  const foods = useAsync(() => (id && editable ? foodsStore.list() : Promise.resolve([])), [id, editable]);
  const [foodId, setFoodId] = useState("");
  const [qty, setQty] = useState("");
  const [busy, setBusy] = useState(false);

  const used = new Set(recipes.data?.map((r) => r.foodId));
  const options = (foods.data ?? []).filter((f) => !used.has(f.id)).sort((a, b) => a.name.localeCompare(b.name, "vi"));

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setBusy(true);
    try { await fn(); push(ok); recipes.refetch(); onChanged(); return true; }
    catch (e) { push(errMsg(e, "Không lưu được định mức"), "err"); return false; }
    finally { setBusy(false); }
  };
  const add = async () => {
    const n = Number(qty);
    if (!id || !foodId) return push("Chọn món", "err");
    if (!(n > 0)) return push("Định mức phải lớn hơn 0", "err");
    if (await run(() => createRecipe(id, foodId, n), "Đã thêm định mức")) { setFoodId(""); setQty(""); }
  };

  return (
    <Drawer open={!!row} title={row?.name ?? ""} onClose={() => { setTab("recipes"); onClose(); }} width="sm:max-w-2xl">
      {row && (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-3">
            <div className="card p-4"><div className="text-xs text-muted">Tồn hiện tại</div><div className="font-display text-xl mt-1">{qtyFmt(row.currentStock)} <span className="text-sm text-muted">{row.unit}</span></div></div>
            <div className="card p-4"><div className="text-xs text-muted">Tồn tối thiểu</div><div className="font-display text-xl mt-1">{qtyFmt(row.minimumStock)} <span className="text-sm text-muted">{row.unit}</span></div></div>
            <div className="card p-4"><div className="text-xs text-muted">Tình trạng</div><div className="mt-2"><StockStatus row={row} /></div></div>
          </div>
          <Tabs value={tab} onChange={setTab} items={[
            { key: "recipes", label: "Định mức món", count: recipes.data?.length },
            { key: "history", label: "Lịch sử xuất nhập", count: moves.data?.length },
          ]} />

          {tab === "recipes" && (
            <div className="space-y-3">
              <p className="text-xs text-muted">Lượng {row.unit} dùng cho 1 phần món. Khi gửi bếp, kho tự trừ theo định mức × số phần.</p>
              {editable && (
                <div className="flex gap-2 items-end flex-wrap">
                  <div className="flex-1 min-w-48">
                    <label htmlFor="recipe-food" className="text-[13px] font-semibold text-muted block mb-1.5">Món</label>
                    <select id="recipe-food" value={foodId} onChange={(e) => setFoodId(e.target.value)} className={inputCls}>
                      <option value="">{foods.loading ? "Đang tải món…" : "Chọn món…"}</option>
                      {options.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
                    </select>
                  </div>
                  <div className="w-32">
                    <label htmlFor="recipe-qty" className="text-[13px] font-semibold text-muted block mb-1.5">Định mức ({row.unit})</label>
                    <input id="recipe-qty" type="number" min={0} step="any" value={qty} onChange={(e) => setQty(e.target.value)} className={inputCls} />
                  </div>
                  <button disabled={busy} onClick={() => void add()} className="btn btn-primary py-2.5! px-4! text-sm! disabled:opacity-50">Thêm</button>
                </div>
              )}
              {recipes.loading ? <p className="text-sm text-muted py-6 text-center">Đang tải…</p> : !recipes.data?.length ? (
                <p className="text-sm text-muted py-6 text-center">Chưa món nào dùng nguyên liệu này — gửi bếp sẽ không trừ kho.</p>
              ) : (
                <ul className="divide-y divide-black/6 rounded-xl border border-black/8 bg-white">
                  {recipes.data.map((r) => (
                    <li key={r.id} className="flex items-center gap-3 px-4 py-2.5">
                      <span className="flex-1 text-sm font-medium">{r.foodName}</span>
                      {editable ? (
                        <input
                          type="number" min={0} step="any" defaultValue={r.qty} aria-label={`Định mức ${r.foodName}`}
                          className={`${inputCls} w-28! py-1.5!`}
                          onBlur={(e) => { const n = Number(e.target.value); if (n !== r.qty) { if (n > 0) void run(() => updateRecipe(r.id, n), "Đã lưu định mức"); else { e.target.value = String(r.qty); push("Định mức phải lớn hơn 0", "err"); } } }}
                        />
                      ) : <span className="text-sm">{qtyFmt(r.qty)}</span>}
                      <span className="text-sm text-muted w-10">{r.unit}</span>
                      {editable && <button disabled={busy} onClick={() => void run(() => deleteRecipe(r.id), "Đã xoá định mức")} className="icon-btn w-8! h-8! hover:text-primary" aria-label={`Xoá định mức ${r.foodName}`}><Trash2 width={15} height={15} /></button>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {tab === "history" && <MovesTable rows={moves.data} loading={moves.loading} />}
        </div>
      )}
    </Drawer>
  );
}

export default function IngredientsPage() {
  const can = useCan();
  const [view, setView] = useState<"list" | "history">("list");
  const [moveRow, setMoveRow] = useState<{ row: AdminIngredient; reload: () => void } | null>(null);
  const [detail, setDetail] = useState<{ row: AdminIngredient; reload: () => void } | null>(null);
  const [historyKey, setHistoryKey] = useState(0);

  const afterMove = useCallback(() => { moveRow?.reload(); setHistoryKey((k) => k + 1); }, [moveRow]);

  return (
    <>
      <PageHeader title="Nguyên liệu & kho" subtitle="Tồn kho chỉ thay đổi qua phiếu nhập / xuất / kiểm kê và khi gửi bếp, mọi biến động đều có lịch sử." />
      <div className="mb-4">
        <Tabs value={view} onChange={setView} items={[{ key: "list", label: "Nguyên liệu" }, { key: "history", label: "Lịch sử xuất nhập" }]} />
      </div>

      {view === "history" ? <HistoryTab key={historyKey} /> : (
        <CrudPage<AdminIngredient>
          hideHeader title="Nguyên liệu & kho" noun="nguyên liệu" module="ingredients" store={ingredientsStore}
          blank={{ name: "", unit: "kg", currentStock: 0, minimumStock: 0, active: true }}
          searchText={(i) => i.name}
          columns={[
            { header: "Nguyên liệu", cell: (i) => <div className={i.active ? "" : "opacity-50"}><b>{i.name}</b><div className="text-xs text-muted">Đơn vị: {i.unit}</div></div> },
            { header: "Tồn hiện tại", cell: (i) => <StockBar row={i} /> },
            { header: "Món dùng", cell: (i) => <span className={`text-sm ${i.recipeCount ? "" : "text-muted"}`}>{i.recipeCount ? `${i.recipeCount} món` : "Chưa có"}</span> },
            { header: "Tình trạng", cell: (i) => <StockStatus row={i} /> },
          ]}
          fields={[
            { key: "name", label: "Tên nguyên liệu", type: "text", required: true, wide: true },
            { key: "unit", label: "Đơn vị", type: "text", required: true, hint: "VD: kg, g, lít, ml, cái" },
            { key: "minimumStock", label: "Tồn tối thiểu", type: "number", hint: "Tồn ≤ mức này sẽ cảnh báo khi gửi bếp và ở Tổng quan." },
            { key: "currentStock", label: "Tồn đầu kỳ", type: "number", hint: "Ghi thành phiếu nhập đầu tiên. Sau đó dùng Nhập / Xuất / Kiểm kê.", showWhen: (v) => !(v as { id?: string }).id },
            { key: "active", label: "Đang sử dụng", type: "toggle" },
          ]}
          rowActions={(row, reload) => (
            <>
              {can("stock", "create") && <button className="icon-btn w-8! h-8!" aria-label="Nhập / xuất kho" title="Nhập / xuất / kiểm kê" onClick={() => setMoveRow({ row, reload })}><ArrowDownUp width={15} height={15} /></button>}
              <button className="icon-btn w-8! h-8!" aria-label="Chi tiết" title="Định mức món & lịch sử" onClick={() => setDetail({ row, reload })}><History width={15} height={15} /></button>
            </>
          )}
        />
      )}

      <StockMoveModal row={moveRow?.row ?? null} onClose={() => setMoveRow(null)} onDone={afterMove} />
      <IngredientDetail row={detail?.row ?? null} onClose={() => setDetail(null)} onChanged={() => detail?.reload()} />
    </>
  );
}
