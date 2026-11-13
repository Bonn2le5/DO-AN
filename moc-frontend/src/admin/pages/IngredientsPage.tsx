import { useCallback, useMemo, useState } from "react";
import { ArrowDownUp, ArrowRightLeft, History, Trash2 } from "lucide-react";
import { useAsync } from "@/hooks/useAsync";
import { useAuthStore } from "@/store/authStore";
import CrudPage from "../components/CrudPage";
import ConfirmModal from "../components/ConfirmModal";
import DataTable from "../components/DataTable";
import Drawer from "../components/Drawer";
import { PageHeader, StatusBadge, Tabs, inputCls } from "../components/primitives";
import { useToast } from "../components/toast";
import {
  createRecipe, createStockMove, deleteRecipe, foodsStore, getTableManagementBranches, ingredientsStoreFor, listRecipes,
  listStockMoves, transferStock, updateBranchMinimum, updateRecipe,
  type StockMove, type StockMoveType,
} from "../api/admin.api";
import { useCan } from "../permissions";
import { fmtDateTime } from "../lib";
import type { AdminBranch, AdminIngredient, BranchStock } from "../data/mockCatalog";

const ALL = "all";
const qtyFmt = (n: number) => n.toLocaleString("vi-VN", { maximumFractionDigits: 3 });
// Khớp với backend (TonKhoChiNhanh.sap_het): hết hàng, hoặc tồn <= tối thiểu.
const isOut = (stock: number) => stock <= 0;
const isLow = (stock: number, min: number) => !isOut(stock) && min > 0 && stock <= min;
const shortBranch = (name: string) => name.replace(/^Nhà hàng Mộc\s*-\s*/i, "").replace(/^Chi nhánh\s*/i, "");

const errMsg = (e: unknown, fallback: string) => {
  const data = (e as { response?: { data?: unknown } })?.response?.data;
  if (data && typeof data === "object") {
    const msgs = Object.values(data as Record<string, unknown>).flatMap((v) => (Array.isArray(v) ? v.map(String) : typeof v === "string" ? [v] : []));
    if (msgs.length) return msgs.join(" · ");
  }
  if (typeof data === "string" && data) return data;
  return e instanceof Error ? e.message : fallback;
};

const MOVE_META: Record<StockMoveType, { label: string; tone: "ok" | "danger" | "info" }> = {
  nhap: { label: "Nhập kho", tone: "ok" },
  xuat: { label: "Xuất kho", tone: "danger" },
  dieu_chinh: { label: "Kiểm kê", tone: "info" },
};

const refLabel = (m: StockMove) =>
  m.refType === "don_hang" ? `Đơn hàng #${m.refId}`
    : m.refType === "ton_dau_ky" ? "Tồn đầu kỳ"
      : m.refType === "chuyen_kho" ? "Chuyển kho"
        : m.refType && m.refType !== "thu_cong" ? `${m.refType}${m.refId ? ` #${m.refId}` : ""}` : "Thủ công";

const signedQty = (m: StockMove) => {
  const delta = m.after - m.before;
  return `${delta > 0 ? "+" : delta < 0 ? "−" : "±"}${qtyFmt(Math.abs(delta))} ${m.unit}`;
};

function StockBadge({ stock, min, active = true }: { stock: number; min: number; active?: boolean }) {
  if (!active) return <StatusBadge tone="neutral">Ngừng dùng</StatusBadge>;
  if (isOut(stock)) return <StatusBadge tone="danger">Hết hàng</StatusBadge>;
  if (isLow(stock, min)) return <StatusBadge tone="warn">Sắp hết</StatusBadge>;
  return <StatusBadge tone="ok">Đủ dùng</StatusBadge>;
}

function StockBar({ stock, min, unit }: { stock: number; min: number; unit: string }) {
  const bad = isOut(stock) || isLow(stock, min);
  const pct = Math.min(100, (stock / Math.max(min * 2, 1)) * 100);
  return (
    <div className="min-w-40">
      <div className="flex justify-between text-xs mb-1">
        <span className={bad ? "text-primary font-semibold" : ""}>{qtyFmt(stock)} {unit}</span>
        <span className="text-muted">tối thiểu {qtyFmt(min)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-black/8"><div className={`h-full rounded-full ${bad ? "bg-primary" : "bg-success"}`} style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

/** Chế độ "Tất cả chi nhánh": tồn từng chi nhánh trên một dòng. */
function BranchBreakdown({ row }: { row: AdminIngredient }) {
  return (
    <div className="flex flex-col gap-0.5 min-w-48">
      {(row.stocks ?? []).map((b) => {
        const bad = isOut(b.stock) || isLow(b.stock, b.minimum);
        return (
          <div key={b.branchId} className="flex justify-between gap-3 text-xs">
            <span className="text-muted truncate">{shortBranch(b.branchName)}</span>
            <span className={`whitespace-nowrap ${bad ? "text-primary font-semibold" : ""}`}>{qtyFmt(b.stock)} {row.unit}</span>
          </div>
        );
      })}
    </div>
  );
}

function AllBranchesStatus({ row }: { row: AdminIngredient }) {
  if (!row.active) return <StatusBadge tone="neutral">Ngừng dùng</StatusBadge>;
  const stocks = row.stocks ?? [];
  const bad = stocks.filter((b) => isOut(b.stock) || isLow(b.stock, b.minimum)).length;
  if (!bad) return <StatusBadge tone="ok">Đủ dùng</StatusBadge>;
  return <StatusBadge tone={bad === stocks.length ? "danger" : "warn"}>Thiếu ở {bad}/{stocks.length} chi nhánh</StatusBadge>;
}

/* ---------- Phiếu nhập / xuất / kiểm kê ---------- */
function StockMoveModal({ target, onClose, onDone }: { target: { row: AdminIngredient; branch: AdminBranch } | null; onClose: () => void; onDone: () => void }) {
  const push = useToast((s) => s.push);
  const [type, setType] = useState<StockMoveType>("nhap");
  const [qty, setQty] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const row = target?.row;
  const n = Number(qty);
  const after = row ? (type === "nhap" ? row.currentStock + n : type === "xuat" ? row.currentStock - n : n) : 0;

  const close = () => { setType("nhap"); setQty(""); setNote(""); onClose(); };
  const submit = async () => {
    if (!target || !row) return;
    if (qty === "" || Number.isNaN(n) || n < 0 || (type !== "dieu_chinh" && n === 0)) return push(type === "dieu_chinh" ? "Nhập tồn thực tế (≥ 0)" : "Nhập số lượng lớn hơn 0", "err");
    if (type === "xuat" && n > row.currentStock) return push(`Chỉ còn ${qtyFmt(row.currentStock)} ${row.unit}, không đủ để xuất`, "err");
    setBusy(true);
    try {
      await createStockMove(row.id, target.branch.id, type, n, note.trim());
      push(`${MOVE_META[type].label}: ${row.name} · ${shortBranch(target.branch.name)}`);
      onDone(); close();
    } catch (e) {
      push(errMsg(e, "Không ghi được phiếu kho"), "err");
    } finally { setBusy(false); }
  };

  return (
    <ConfirmModal open={!!target} busy={busy} confirmLabel={MOVE_META[type].label} title={`Phiếu kho: ${row?.name ?? ""}`} onConfirm={submit} onCancel={close}>
      <div className="mt-3 space-y-3">
        <p className="text-xs text-muted">Kho: <b className="text-dark">{target ? shortBranch(target.branch.name) : ""}</b></p>
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

/* ---------- Chuyển kho giữa chi nhánh ---------- */
function TransferModal({ target, branches, onClose, onDone }: {
  target: { row: AdminIngredient; branch: AdminBranch } | null; branches: AdminBranch[]; onClose: () => void; onDone: () => void;
}) {
  const push = useToast((s) => s.push);
  const [to, setTo] = useState("");
  const [qty, setQty] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const row = target?.row;
  const n = Number(qty);
  const options = branches.filter((b) => b.id !== target?.branch.id);

  const close = () => { setTo(""); setQty(""); setNote(""); onClose(); };
  const submit = async () => {
    if (!target || !row) return;
    if (!to) return push("Chọn chi nhánh nhận", "err");
    if (!(n > 0)) return push("Nhập số lượng lớn hơn 0", "err");
    if (n > row.currentStock) return push(`Kho gửi chỉ còn ${qtyFmt(row.currentStock)} ${row.unit}`, "err");
    setBusy(true);
    try {
      await transferStock(row.id, target.branch.id, to, n, note.trim());
      push(`Đã chuyển ${qtyFmt(n)} ${row.unit} ${row.name} sang ${shortBranch(options.find((b) => b.id === to)?.name ?? "")}`);
      onDone(); close();
    } catch (e) {
      push(errMsg(e, "Không chuyển được kho"), "err");
    } finally { setBusy(false); }
  };

  return (
    <ConfirmModal open={!!target} busy={busy} confirmLabel="Chuyển kho" title={`Chuyển kho: ${row?.name ?? ""}`} onConfirm={submit} onCancel={close}>
      <div className="mt-3 space-y-3">
        <p className="text-xs text-muted">Từ <b className="text-dark">{target ? shortBranch(target.branch.name) : ""}</b> (còn {row ? qtyFmt(row.currentStock) : 0} {row?.unit})</p>
        <div>
          <label htmlFor="transfer-to" className="text-[13px] font-semibold text-muted block mb-1.5">Chi nhánh nhận</label>
          <select id="transfer-to" value={to} onChange={(e) => setTo(e.target.value)} className={inputCls}>
            <option value="">Chọn chi nhánh…</option>
            {options.map((b) => <option key={b.id} value={b.id}>{shortBranch(b.name)}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="transfer-qty" className="text-[13px] font-semibold text-muted block mb-1.5">Số lượng ({row?.unit})</label>
          <input id="transfer-qty" type="number" min={0} step="any" value={qty} onChange={(e) => setQty(e.target.value)} className={inputCls} />
          {row && qty !== "" && n > 0 && <p className={`text-xs mt-1.5 ${n > row.currentStock ? "text-primary" : "text-muted"}`}>Kho gửi: {qtyFmt(row.currentStock)} → <b>{qtyFmt(row.currentStock - n)}</b> {row.unit}</p>}
        </div>
        <div>
          <label htmlFor="transfer-note" className="text-[13px] font-semibold text-muted block mb-1.5">Ghi chú</label>
          <input id="transfer-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="VD: Chi nhánh nhận hết hàng cuối tuần" className={inputCls} />
        </div>
      </div>
    </ConfirmModal>
  );
}

/* ---------- Bảng lịch sử ---------- */
function MovesTable({ rows, loading, showIngredient, showBranch }: { rows: StockMove[] | undefined; loading: boolean; showIngredient?: boolean; showBranch?: boolean }) {
  return (
    <DataTable<StockMove>
      rows={rows} loading={loading} pageSize={15}
      emptyTitle="Chưa có giao dịch kho" emptyHint="Phiếu nhập, xuất, kiểm kê, chuyển kho và xuất kho khi gửi bếp sẽ hiện ở đây."
      columns={[
        { header: "Thời gian", cell: (m) => <span className="whitespace-nowrap text-sm">{fmtDateTime(m.at)}</span> },
        ...(showBranch ? [{ header: "Chi nhánh", cell: (m: StockMove) => <span className="text-sm whitespace-nowrap">{shortBranch(m.branchName)}</span> }] : []),
        ...(showIngredient ? [{ header: "Nguyên liệu", cell: (m: StockMove) => <b>{m.ingredientName}</b> }] : []),
        { header: "Loại", cell: (m) => <StatusBadge tone={MOVE_META[m.type]?.tone ?? "neutral"}>{MOVE_META[m.type]?.label ?? m.type}</StatusBadge> },
        { header: "Biến động", cell: (m) => <span className={`font-semibold whitespace-nowrap ${m.after < m.before ? "text-primary" : "text-[#456543]"}`}>{signedQty(m)}</span> },
        { header: "Tồn", cell: (m) => <span className="text-sm whitespace-nowrap text-muted">{qtyFmt(m.before)} → <b className="text-dark">{qtyFmt(m.after)}</b></span> },
        { header: "Nguồn", cell: (m) => <span className="text-sm whitespace-nowrap">{refLabel(m)}</span> },
        { header: "Ghi chú", cell: (m) => <span className="block min-w-56 text-sm text-muted">{m.note ? m.note.replace(/Nhà hàng Mộc\s*-\s*Chi nhánh\s*/gi, "") : "—"}</span> },
        { header: "Người tạo", cell: (m) => <span className="text-sm whitespace-nowrap">{m.by || "Hệ thống"}</span> },
      ]}
    />
  );
}

type HistoryFilter = "all" | StockMoveType | "chuyen_kho";

function HistoryTab({ branchId }: { branchId?: string }) {
  const [type, setType] = useState<HistoryFilter>("all");
  const { data, loading } = useAsync(() => listStockMoves({ branchId }), [branchId]);
  const match = (m: StockMove, k: HistoryFilter) => (k === "all" ? true : k === "chuyen_kho" ? m.refType === "chuyen_kho" : m.type === k);
  const rows = useMemo(() => data?.filter((m) => match(m, type)), [data, type]);
  const count = (k: HistoryFilter) => data?.filter((m) => match(m, k)).length;
  return (
    <div className="space-y-4">
      <Tabs value={type} onChange={setType} items={[
        { key: "all", label: "Tất cả", count: data?.length },
        { key: "nhap", label: "Nhập kho", count: count("nhap") },
        { key: "xuat", label: "Xuất kho", count: count("xuat") },
        { key: "dieu_chinh", label: "Kiểm kê", count: count("dieu_chinh") },
        { key: "chuyen_kho", label: "Chuyển kho", count: count("chuyen_kho") },
      ]} />
      <MovesTable rows={rows} loading={loading} showIngredient showBranch={!branchId} />
    </div>
  );
}

/* ---------- Chi tiết: tồn từng chi nhánh, định mức món, lịch sử ---------- */
function BranchStockTable({ row, editable, onChanged }: { row: AdminIngredient; editable: boolean; onChanged: () => void }) {
  const push = useToast((s) => s.push);
  const saveMin = async (b: BranchStock, value: string, input: HTMLInputElement) => {
    const n = Number(value);
    if (n === b.minimum) return;
    if (value === "" || Number.isNaN(n) || n < 0) { input.value = String(b.minimum); return push("Tồn tối thiểu phải ≥ 0", "err"); }
    try {
      await updateBranchMinimum(b.id, n);
      push(`Đã lưu mức tối thiểu ở ${shortBranch(b.branchName)}`);
      onChanged();
    } catch (e) { input.value = String(b.minimum); push(errMsg(e, "Không lưu được mức tối thiểu"), "err"); }
  };
  return (
    <div className="rounded-xl border border-black/8 bg-white overflow-x-auto">
      <table className="w-full text-sm">
        <thead><tr className="text-left text-xs text-muted border-b border-black/6">
          <th className="px-4 py-2 font-medium">Chi nhánh</th><th className="px-4 py-2 font-medium">Tồn</th>
          <th className="px-4 py-2 font-medium">Tối thiểu ({row.unit})</th><th className="px-4 py-2 font-medium">Tình trạng</th>
        </tr></thead>
        <tbody className="divide-y divide-black/6">
          {(row.stocks ?? []).map((b) => (
            <tr key={b.branchId}>
              <td className="px-4 py-2.5 font-medium">{shortBranch(b.branchName)}</td>
              <td className="px-4 py-2.5 whitespace-nowrap">{qtyFmt(b.stock)} {row.unit}</td>
              <td className="px-4 py-2.5">
                {editable && b.id ? (
                  <input type="number" min={0} step="any" defaultValue={b.minimum} aria-label={`Tồn tối thiểu ở ${b.branchName}`}
                    className={`${inputCls} w-24! py-1.5!`} onBlur={(e) => void saveMin(b, e.target.value, e.target)} />
                ) : qtyFmt(b.minimum)}
              </td>
              <td className="px-4 py-2.5"><StockBadge stock={b.stock} min={b.minimum} active={row.active} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function IngredientDetail({ row, branchId, onClose, onChanged }: { row: AdminIngredient | null; branchId?: string; onClose: () => void; onChanged: () => void }) {
  const can = useCan();
  const push = useToast((s) => s.push);
  const editable = can("ingredients", "update");
  const canStock = can("stock", "create");
  const [tab, setTab] = useState<"stock" | "recipes" | "history">("stock");
  const id = row?.id;
  const recipes = useAsync(() => (id ? listRecipes(id) : Promise.resolve([])), [id]);
  const moves = useAsync(() => (id ? listStockMoves({ ingredientId: id, branchId }) : Promise.resolve([])), [id, branchId]);
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
    <Drawer open={!!row} title={row?.name ?? ""} onClose={() => { setTab("stock"); onClose(); }} width="sm:max-w-2xl">
      {row && (
        <div className="space-y-5">
          <Tabs value={tab} onChange={setTab} items={[
            { key: "stock", label: "Tồn theo chi nhánh", count: row.stocks?.length },
            { key: "recipes", label: "Định mức món", count: recipes.data?.length },
            { key: "history", label: "Lịch sử xuất nhập", count: moves.data?.length },
          ]} />

          {tab === "stock" && (
            <div className="space-y-2">
              <BranchStockTable row={row} editable={canStock} onChanged={onChanged} />
              <p className="text-xs text-muted">Mỗi chi nhánh có kho và mức tối thiểu riêng. Tồn chỉ thay đổi qua phiếu kho, chuyển kho hoặc khi gửi bếp.</p>
            </div>
          )}

          {tab === "recipes" && (
            <div className="space-y-3">
              <p className="text-xs text-muted">Lượng {row.unit} dùng cho 1 phần món, dùng chung cho mọi chi nhánh. Khi gửi bếp, kho của chi nhánh phục vụ tự trừ theo định mức × số phần.</p>
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
          {tab === "history" && <MovesTable rows={moves.data} loading={moves.loading} showBranch={!branchId} />}
        </div>
      )}
    </Drawer>
  );
}

export default function IngredientsPage() {
  const can = useCan();
  const user = useAuthStore((s) => s.nguoiDung);
  const isAdmin = Boolean(user?.laQuanTri || user?.danhSachVaiTro?.some((r) => r === "admin" || r === "quan_tri_vien"));
  const myBranch = user?.idChiNhanh;
  const branchesQ = useAsync(() => getTableManagementBranches(), []);
  const branches = useMemo(
    () => (branchesQ.data ?? []).filter((b) => (isAdmin ? b.active : b.id === myBranch)),
    [branchesQ.data, isAdmin, myBranch],
  );
  const [picked, setPicked] = useState<string>(isAdmin ? ALL : "");
  const branchId = isAdmin ? (picked === ALL ? undefined : picked) : myBranch;
  const branch = branches.find((b) => b.id === branchId);
  const store = useMemo(() => ingredientsStoreFor(branchId), [branchId]);

  const [view, setView] = useState<"list" | "history">("list");
  const [moveTarget, setMoveTarget] = useState<{ row: AdminIngredient; branch: AdminBranch; reload: () => void } | null>(null);
  const [transferTarget, setTransferTarget] = useState<{ row: AdminIngredient; branch: AdminBranch; reload: () => void } | null>(null);
  const [detail, setDetail] = useState<{ row: AdminIngredient; reload: () => void } | null>(null);
  const [historyKey, setHistoryKey] = useState(0);
  const canStock = can("stock", "create");
  // Chuyển kho cần biết các chi nhánh nhận; quản lý chi nhánh chỉ thấy chi nhánh mình nên dùng danh sách đầy đủ.
  const allBranches = useMemo(() => (branchesQ.data ?? []).filter((b) => b.active), [branchesQ.data]);

  const afterMove = useCallback((reload?: () => void) => { reload?.(); setHistoryKey((k) => k + 1); }, []);

  if (!isAdmin && !myBranch) {
    return (
      <>
        <PageHeader title="Nguyên liệu & kho" />
        <p className="card p-6 text-sm text-muted">Tài khoản chưa được gán chi nhánh. Quản trị viên cần chọn chi nhánh phụ trách trong mục Người dùng.</p>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Nguyên liệu & kho"
        subtitle="Mỗi chi nhánh một kho riêng. Danh mục nguyên liệu và định mức món dùng chung; tồn kho chỉ đổi qua phiếu kho, chuyển kho và khi gửi bếp."
        actions={isAdmin ? (
          <select value={picked} onChange={(e) => setPicked(e.target.value)} aria-label="Chọn chi nhánh" className={`${inputCls} w-auto! min-w-56`}>
            <option value={ALL}>Tất cả chi nhánh</option>
            {branches.map((b) => <option key={b.id} value={b.id}>{shortBranch(b.name)}</option>)}
          </select>
        ) : branch ? <span className="text-sm font-medium rounded-full bg-black/5 px-3.5 py-2">{shortBranch(branch.name)}</span> : null}
      />
      <div className="mb-4">
        <Tabs value={view} onChange={setView} items={[{ key: "list", label: "Nguyên liệu" }, { key: "history", label: "Lịch sử xuất nhập" }]} />
      </div>

      {view === "history" ? <HistoryTab key={`${historyKey}-${branchId ?? ALL}`} branchId={branchId} /> : (
        <CrudPage<AdminIngredient>
          hideHeader title="Nguyên liệu & kho" noun="nguyên liệu" module="ingredients" store={store}
          blank={{ name: "", unit: "kg", currentStock: 0, minimumStock: 0, active: true }}
          searchText={(i) => i.name}
          columns={[
            { header: "Nguyên liệu", cell: (i) => <div className={i.active ? "" : "opacity-50"}><b>{i.name}</b><div className="text-xs text-muted">Đơn vị: {i.unit}</div></div> },
            branchId
              ? { header: "Tồn hiện tại", cell: (i) => <StockBar stock={i.currentStock} min={i.minimumStock} unit={i.unit} /> }
              : { header: "Tồn các chi nhánh", cell: (i) => <BranchBreakdown row={i} /> },
            { header: "Món dùng", cell: (i) => <span className={`text-sm ${i.recipeCount ? "" : "text-muted"}`}>{i.recipeCount ? `${i.recipeCount} món` : "Chưa có"}</span> },
            { header: "Tình trạng", cell: (i) => (branchId ? <StockBadge stock={i.currentStock} min={i.minimumStock} active={i.active} /> : <AllBranchesStatus row={i} />) },
          ]}
          fields={[
            { key: "name", label: "Tên nguyên liệu", type: "text", required: true, wide: true },
            { key: "unit", label: "Đơn vị", type: "text", required: true, hint: "VD: kg, g, lít, ml, cái" },
            { key: "minimumStock", label: "Tồn tối thiểu mỗi chi nhánh", type: "number", hint: "Áp cho mọi chi nhánh khi tạo; sửa riêng từng chi nhánh trong mục Chi tiết. Tồn ban đầu là 0 — dùng Nhập kho.", showWhen: (v) => !(v as { id?: string }).id },
            { key: "active", label: "Đang sử dụng", type: "toggle" },
          ]}
          rowActions={(row, reload) => (
            <>
              {canStock && branch && <button className="icon-btn w-8! h-8!" aria-label="Nhập / xuất kho" title={`Nhập / xuất / kiểm kê · ${shortBranch(branch.name)}`} onClick={() => setMoveTarget({ row, branch, reload })}><ArrowDownUp width={15} height={15} /></button>}
              {canStock && branch && allBranches.length > 1 && <button className="icon-btn w-8! h-8!" aria-label="Chuyển kho" title="Chuyển sang chi nhánh khác" onClick={() => setTransferTarget({ row, branch, reload })}><ArrowRightLeft width={15} height={15} /></button>}
              <button className="icon-btn w-8! h-8!" aria-label="Chi tiết" title="Tồn theo chi nhánh, định mức món & lịch sử" onClick={() => setDetail({ row, reload })}><History width={15} height={15} /></button>
            </>
          )}
        />
      )}
      {view === "list" && !branchId && canStock && <p className="text-xs text-muted mt-3">Chọn một chi nhánh để nhập / xuất / kiểm kê hoặc chuyển kho.</p>}

      <StockMoveModal target={moveTarget} onClose={() => setMoveTarget(null)} onDone={() => afterMove(moveTarget?.reload)} />
      <TransferModal target={transferTarget} branches={allBranches} onClose={() => setTransferTarget(null)} onDone={() => afterMove(transferTarget?.reload)} />
      <IngredientDetail
        row={detail?.row ?? null} branchId={branchId}
        onClose={() => setDetail(null)}
        onChanged={() => detail?.reload()}
      />
    </>
  );
}
