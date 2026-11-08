import { useMemo, useState } from "react";
import { useAsync } from "@/hooks/useAsync";
import { formatCurrency } from "@/lib/utils";
import { createInvoice, ordersStore, reservationsStore } from "../api/admin.api";
import type { AdminOrder, AdminReservation } from "../types";
import { useToast } from "./toast";
import Drawer from "./Drawer";
import { inputCls } from "./primitives";

type TargetType = "order" | "deposit";

export default function CreateInvoiceDrawer({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const push = useToast((s) => s.push);
  const [targetType, setTargetType] = useState<TargetType>("order");
  const [targetId, setTargetId] = useState("");
  const [method, setMethod] = useState<"tien_mat" | "chuyen_khoan">("tien_mat");
  const [busy, setBusy] = useState(false);
  const { data: orders } = useAsync(() => ordersStore.list(), [open]);
  const { data: reservations } = useAsync(() => reservationsStore.list(), [open]);

  const targets = targetType === "order"
    ? orders ?? []
    : (reservations ?? []).filter((r) => r.depositAmount > 0 && ["unpaid", "pending", "failed"].includes(r.depositStatus));
  const selected = targets.find((item) => item.id === targetId) as AdminOrder | AdminReservation | undefined;
  const amount = selected ? (targetType === "order" ? (selected as AdminOrder).total : (selected as AdminReservation).depositAmount) : 0;
  const targetLabel = useMemo(() => (targetType === "order" ? "Đơn hàng" : "Đặt bàn có tiền cọc"), [targetType]);

  const submit = async () => {
    if (!selected || !amount) {
      push(`Chọn ${targetLabel.toLowerCase()} cần lập hóa đơn.`, "err");
      return;
    }
    setBusy(true);
    try {
      await createInvoice({ targetType, targetId, method, amount });
      push("Đã lập hóa đơn.");
      setTargetId("");
      onClose();
      onCreated();
    } catch (error) {
      const data = (error as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const detail = data && Object.values(data).flatMap((v) => Array.isArray(v) ? v.map(String) : typeof v === "string" ? [v] : [])[0];
      push(detail || (error instanceof Error ? error.message : "Không lập được hóa đơn."), "err");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Drawer
      open={open}
      title="Lập hóa đơn"
      onClose={onClose}
      footer={<>
        <button className="btn btn-outline py-2.5! px-5! text-sm!" onClick={onClose}>Huỷ</button>
        <button className="btn btn-primary py-2.5! px-5! text-sm! disabled:opacity-50" disabled={busy || !selected} onClick={submit}>{busy ? "Đang lưu…" : "Tạo hóa đơn"}</button>
      </>}
    >
      <div className="space-y-5">
        <div>
          <label className="text-[13px] font-semibold text-muted block mb-1.5">Hóa đơn cho</label>
          <select value={targetType} onChange={(e) => { setTargetType(e.target.value as TargetType); setTargetId(""); }} className={inputCls}>
            <option value="order">Đơn hàng</option>
            <option value="deposit">Tiền cọc đặt bàn</option>
          </select>
        </div>
        <div>
          <label className="text-[13px] font-semibold text-muted block mb-1.5">{targetLabel}</label>
          <select value={targetId} onChange={(e) => setTargetId(e.target.value)} className={inputCls}>
            <option value="">Chọn…</option>
            {targets.map((item) => (
              <option key={item.id} value={item.id}>
                {targetType === "order"
                  ? `${(item as AdminOrder).code} · ${(item as AdminOrder).customer} · ${formatCurrency((item as AdminOrder).total)}`
                  : `${(item as AdminReservation).code} · ${(item as AdminReservation).customer} · ${formatCurrency((item as AdminReservation).depositAmount)}`}
              </option>
            ))}
          </select>
          {targets.length === 0 && <p className="mt-1.5 text-xs text-muted">Không có mục nào đủ điều kiện lập hóa đơn.</p>}
        </div>
        <div>
          <label className="text-[13px] font-semibold text-muted block mb-1.5">Phương thức</label>
          <select value={method} onChange={(e) => setMethod(e.target.value as typeof method)} className={inputCls}>
            <option value="tien_mat">Tiền mặt</option>
            <option value="chuyen_khoan">Chuyển khoản</option>
          </select>
        </div>
        <div className="rounded-xl bg-black/[0.04] p-4">
          <div className="text-sm text-muted">Số tiền hóa đơn</div>
          <div className="mt-1 text-xl font-bold text-primary">{formatCurrency(amount)}</div>
        </div>
      </div>
    </Drawer>
  );
}
