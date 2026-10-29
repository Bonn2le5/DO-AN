import { useState } from "react";
import Drawer from "./Drawer";
import ConfirmModal from "./ConfirmModal";
import { StatusBadge, inputCls } from "./primitives";
import { useToast } from "./toast";
import { setOrderStatus } from "../api/admin.api";
import { useCan } from "../permissions";
import { ORDER_META, ORDER_NEXT } from "../statusMeta";
import { fmtDateTime } from "../lib";
import { formatCurrency } from "@/lib/utils";
import type { AdminOrder } from "../types";

const PAYMENT = { cod: "Thanh toán khi nhận", bank: "Chuyển khoản", vnpay: "VNPay" };

export default function OrderDrawer({ order, onClose, onChanged }: { order: AdminOrder | null; onClose: () => void; onChanged: () => void }) {
  const can = useCan();
  const push = useToast((s) => s.push);
  const [cancelling, setCancelling] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  const run = async (to: AdminOrder["status"], note?: string) => {
    if (!order) return;
    setBusy(true);
    try {
      await setOrderStatus(order, to, note);
      push(`Đơn ${order.code}: ${ORDER_META[to].label}`);
      setCancelling(false); setReason(""); onChanged(); onClose();
    } catch (e) {
      push(e instanceof Error ? e.message : "Không đổi được trạng thái", "err");
    } finally { setBusy(false); }
  };

  const next = order && ORDER_NEXT[order.status];
  const canCancel = order && (order.status === "pending" || order.status === "confirmed");
  const editable = can("orders", "update");

  return (
    <>
      <Drawer
        open={!!order} onClose={onClose} title={order ? `Đơn ${order.code}` : ""}
        footer={order && editable && (
          <>
            {canCancel && <button className="btn btn-outline py-2.5! px-5! text-sm! text-primary! border-primary!" onClick={() => setCancelling(true)}>Huỷ đơn</button>}
            {next && <button disabled={busy} className="btn btn-primary py-2.5! px-5! text-sm!" onClick={() => run(next.to)}>{next.label}</button>}
          </>
        )}
      >
        {order && (
          <div className="space-y-6 text-sm">
            <StatusBadge tone={ORDER_META[order.status].tone}>{ORDER_META[order.status].label}</StatusBadge>
            <section className="space-y-1.5">
              <div className="font-semibold">{order.customer} · {order.phone}</div>
              <div className="text-muted">{order.type === "delivery" ? `Giao tới: ${order.address ?? "—"}` : "Khách tự đến lấy"}</div>
              <div className="text-muted">Thanh toán: {PAYMENT[order.payment]}</div>
              {order.note && <div className="rounded-xl bg-accent/10 px-3 py-2">Ghi chú: {order.note}</div>}
            </section>
            <section>
              <h3 className="font-display text-base mb-2">Món đã đặt</h3>
              {order.items.map((i) => (
                <div key={i.name} className="flex justify-between py-1.5"><span>{i.qty} × {i.name}</span><span className="text-muted">{formatCurrency(i.qty * i.price)}</span></div>
              ))}
              <div className="border-t border-black/10 mt-2 pt-2 space-y-1">
                <div className="flex justify-between text-muted"><span>Tạm tính</span><span>{formatCurrency(order.subtotal)}</span></div>
                {order.discount > 0 && <div className="flex justify-between text-success"><span>Giảm giá</span><span>-{formatCurrency(order.discount)}</span></div>}
                <div className="flex justify-between font-bold text-base"><span>Tổng cộng</span><span className="text-primary">{formatCurrency(order.total)}</span></div>
              </div>
            </section>
            <section>
              <h3 className="font-display text-base mb-3">Lịch sử trạng thái</h3>
              <ol className="relative border-l border-black/15 ml-1.5 space-y-4">
                {order.history.map((h, i) => (
                  <li key={i} className="pl-5 relative">
                    <span className="absolute -left-1.25 top-1 w-2.5 h-2.5 rounded-full bg-primary" />
                    <div className="font-medium">{ORDER_META[h.to].label}</div>
                    <div className="text-xs text-muted">{fmtDateTime(h.at)} · {h.by}{h.note ? ` · ${h.note}` : ""}</div>
                  </li>
                ))}
              </ol>
            </section>
          </div>
        )}
      </Drawer>
      <ConfirmModal
        open={cancelling} danger busy={busy} title="Huỷ đơn hàng?" confirmLabel="Huỷ đơn"
        message="Khách sẽ nhận được thông báo đơn đã bị huỷ." onConfirm={() => run("cancelled", reason || undefined)} onCancel={() => setCancelling(false)}
      >
        <label className="text-[13px] font-semibold text-muted block mb-1.5">Lý do huỷ</label>
        <input value={reason} onChange={(e) => setReason(e.target.value)} className={inputCls} placeholder="Ví dụ: hết nguyên liệu" />
      </ConfirmModal>
    </>
  );
}
