import { useEffect, useState } from "react";
import Drawer from "./Drawer";
import ConfirmModal from "./ConfirmModal";
import RefundPanel from "./RefundPanel";
import { StatusBadge, inputCls } from "./primitives";
import { useToast } from "./toast";
import { checkInReservation, setReservationStatus, startReservationSession } from "../api/admin.api";
import { useCan } from "../permissions";
import { DEPOSIT_META, RES_META } from "../statusMeta";
import { fmtDateTime } from "../lib";
import { formatCurrency } from "@/lib/utils";
import type { AdminDiningSession, AdminReservation, AdminTable, DepositPolicyData } from "../types";
import type { ReservationStatus } from "../types";

const OPTION = { table_only: "Chỉ đặt bàn", table_and_food: "Đặt bàn + gọi món trước", table_and_food_editable: "Đặt bàn + chọn món (được đổi)" };
const ACTIONS: Partial<Record<ReservationStatus, { to: ReservationStatus; label: string }[]>> = {
  pending_confirmation: [{ to: "confirmed", label: "Nhà hàng xác nhận" }],
  pending_payment: [{ to: "confirmed", label: "Xác nhận thủ công" }],
  confirmed: [{ to: "no_show", label: "Khách không đến" }],
};

interface Props { res: AdminReservation | null; tables: AdminTable[]; policy: DepositPolicyData | undefined; onClose: () => void; onChanged: () => void; onOpenSession?: (session: AdminDiningSession) => void }

export default function ReservationDrawer({ res, tables, policy, onClose, onChanged, onOpenSession }: Props) {
  const can = useCan();
  const push = useToast((s) => s.push);
  const [cancelling, setCancelling] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [selectedTableId, setSelectedTableId] = useState("");

  useEffect(() => { setSelectedTableId(res?.tableId ?? ""); }, [res?.id, res?.tableId]);

  const checkIn = async () => {
    if (!res) return;
    setBusy(true);
    try {
      await checkInReservation(res.id, res.version);
      push("Đã check-in khách. Chọn bàn để bắt đầu phục vụ.");
      onChanged();
    } catch (e) {
      push(e instanceof Error ? e.message : "Không thể check-in khách.", "err");
      onChanged();
    } finally { setBusy(false); }
  };

  const startService = async () => {
    if (!res || !selectedTableId) return push("Chọn bàn còn trống trước khi bắt đầu phục vụ.", "err");
    setBusy(true);
    try {
      if (res.status === "confirmed") await checkInReservation(res.id, res.version);
      const session = await startReservationSession(res.id, selectedTableId);
      push(`Đã check-in ${res.customer || "khách"} và xếp bàn.`);
      onChanged();
      onOpenSession?.(session);
    } catch (e) {
      push(e instanceof Error ? e.message : "Không thể bắt đầu phục vụ tại bàn này.", "err");
      onChanged();
    } finally { setBusy(false); }
  };

  const run = async (to: ReservationStatus, why?: string) => {
    if (!res) return;
    setBusy(true);
    try {
      await setReservationStatus(res.id, to, res.version, why);
      push(`Đặt bàn ${res.code}: ${RES_META[to].label}`);
      setCancelling(false); setReason(""); onChanged();
    } catch (e) {
      push(e instanceof Error ? e.message : "Không cập nhật được", "err");
      onChanged();
    } finally { setBusy(false); }
  };

  const editable = can("reservations", "update");
  const canSeat = !!res && !res.sessionId && (res.status === "confirmed" || res.status === "seated");
  // Huỷ đặt bàn và báo khách không đến ảnh hưởng tiền cọc: chỉ quản lý chi nhánh.
  const canVoid = can("reservations", "delete");
  const actions = (res ? ACTIONS[res.status] ?? [] : []).filter((a) => canVoid || (a.to !== "no_show" && a.to !== "cancelled"));
  const canCancel = canVoid && res && (["pending_confirmation", "pending_payment", "confirmed"] as ReservationStatus[]).includes(res.status);

  return (
    <>
      <Drawer
        open={!!res} onClose={onClose} title={res ? `Đặt bàn ${res.code}` : ""} width="sm:max-w-lg"
        footer={res && editable && (
          <>
            {canCancel && <button className="btn btn-outline py-2.5! px-5! text-sm! text-primary! border-primary!" onClick={() => setCancelling(true)}>Huỷ đặt bàn</button>}
            {res.status === "confirmed" && <button disabled={busy} onClick={() => void checkIn()} className="btn btn-outline py-2.5! px-4! text-sm!">Chỉ check-in</button>}
            {canSeat && <button disabled={busy || !selectedTableId} onClick={() => void startService()} className="btn btn-primary py-2.5! px-5! text-sm!">{res.status === "confirmed" ? "Check-in & xếp bàn" : "Xếp bàn & mở hóa đơn"}</button>}
            {res.sessionId && <button disabled={busy} onClick={() => onOpenSession?.({ id: res.sessionId!, code: "", branchId: res.branchId ?? "", tableId: res.tableId, tableLabel: res.tableLabel, orderId: res.orderId, orderCode: res.orderCode, reservationId: res.id, guestCount: res.partySize, customer: res.customer, phone: res.phone, note: res.note, status: "active", startedAt: "" })} className="btn btn-primary py-2.5! px-5! text-sm!">Mở phiên phục vụ</button>}
            {actions.map((a, i) => (
              <button key={a.to} disabled={busy} onClick={() => run(a.to)} className={`btn py-2.5! px-5! text-sm! ${i === 0 ? "btn-primary" : "btn-outline"}`}>{a.label}</button>
            ))}
          </>
        )}
      >
        {res && (
          <div className="space-y-6 text-sm">
            <div className="flex gap-2 flex-wrap">
              <StatusBadge tone={RES_META[res.status].tone}>{RES_META[res.status].label}</StatusBadge>
              {res.depositAmount > 0 && <StatusBadge tone={DEPOSIT_META[res.depositStatus].tone}>{DEPOSIT_META[res.depositStatus].label}</StatusBadge>}
            </div>
            <section className="grid grid-cols-2 gap-y-3 gap-x-4">
              {[["Khách", res.customer], ["Điện thoại", res.phone], ["Bàn", res.tableLabel], ["Số khách", String(res.partySize)], ["Giờ hẹn", `${res.time} · ${res.date.split("-").reverse().join("/")}`], ["Hình thức", OPTION[res.option]]].map(([k, v]) => (
                <div key={k}><div className="text-xs text-muted">{k}</div><div className="font-medium">{v}</div></div>
              ))}
            </section>
            {res.status === "confirmed" && <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">Khách tới: chọn bàn rồi bấm “Check-in & xếp bàn” để check-in và xếp bàn một lần. Hoá đơn được tạo khi gửi món đầu tiên xuống bếp. Chưa có bàn trống thì bấm “Chỉ check-in”.</div>}
            {res.status === "seated" && !res.tableLabel && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs leading-5 text-emerald-900">Đã check-in · chọn bàn còn trống đủ {res.partySize} chỗ để xếp bàn.</div>}
            {res.status === "seated" && res.sessionId && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs leading-5 text-emerald-900">Đã bắt đầu phục vụ tại <b>{res.tableLabel}</b>. Hóa đơn {res.orderCode || "đã được tạo"}.</div>}
            {editable && canSeat && (
              <label className="block">
                <span className="text-xs text-muted block mb-1.5">Xếp bàn cho khách</span>
                <select value={selectedTableId} disabled={busy} onChange={(e) => setSelectedTableId(e.target.value)} className={inputCls}>
                  <option value="">Chưa xếp bàn</option>
                  {tables.filter((t) => (!res.branchId || !t.branchId || t.branchId === res.branchId) && t.capacity >= res.partySize && t.status === "available").map((table) => (
                    <option key={table.id} value={table.id}>{table.number} · {table.zone} · {table.capacity} chỗ</option>
                  ))}
                </select>
                <span className="text-xs text-muted mt-1 block">Chỉ hiện bàn đang trống và đủ {res.partySize} chỗ. Có thể làm nhanh hơn ngay trên Sơ đồ bàn.</span>
              </label>
            )}
            {res.note && <div className="rounded-xl bg-accent/10 px-3 py-2">Yêu cầu: {res.note}</div>}
            {res.cancelReason && <div className="rounded-xl bg-black/5 px-3 py-2">Lý do huỷ: {res.cancelReason}{res.cancelledAt ? ` · ${fmtDateTime(res.cancelledAt)}` : ""}</div>}
            {res.foodItems.length > 0 && (
              <section>
                <h3 className="font-display text-base mb-2">Món đặt trước</h3>
                {res.foodItems.map((i) => (<div key={i.name} className="flex justify-between py-1"><span>{i.qty} × {i.name}</span><span className="text-muted">{formatCurrency(i.qty * i.price)}</span></div>))}
                <div className="flex justify-between border-t border-black/10 mt-2 pt-2 font-semibold"><span>Tiền cọc ({policy?.depositPercentage ?? 20}%)</span><span className="text-primary">{formatCurrency(res.depositAmount)}</span></div>
              </section>
            )}
            <RefundPanel key={res.id + res.version} res={res} policy={policy} onDone={onChanged} />
          </div>
        )}
      </Drawer>
      <ConfirmModal
        open={cancelling} danger busy={busy} title="Huỷ đặt bàn?" confirmLabel="Huỷ đặt bàn"
        message={res && res.depositStatus === "success" ? "Khách đã đặt cọc. Sau khi huỷ, khoản cọc sẽ vào hàng chờ hoàn thủ công." : "Bàn sẽ được nhả cho khách khác."}
        onConfirm={() => run("cancelled", reason || undefined)} onCancel={() => setCancelling(false)}
      >
        <label className="text-[13px] font-semibold text-muted block mb-1.5">Lý do huỷ</label>
        <input value={reason} onChange={(e) => setReason(e.target.value)} className={inputCls} placeholder="Ví dụ: khách báo bận" />
      </ConfirmModal>
    </>
  );
}
