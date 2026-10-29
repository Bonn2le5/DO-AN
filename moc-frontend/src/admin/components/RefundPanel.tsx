import { useState } from "react";
import { Info } from "lucide-react";
import ConfirmModal from "./ConfirmModal";
import { StatusBadge, inputCls } from "./primitives";
import { useToast } from "./toast";
import { recordRefund, refundBucket, needsRefund } from "../api/admin.api";
import { useCan } from "../permissions";
import { fmtDateTime } from "../lib";
import { formatCurrency } from "@/lib/utils";
import type { AdminReservation, DepositPolicyData } from "../types";

const BUCKET_LABEL = { ">24h": "Huỷ trước giờ hẹn hơn 24 giờ", "6-24h": "Huỷ trước giờ hẹn 6–24 giờ", "<6h": "Huỷ trong vòng 6 giờ trước giờ hẹn", no_show: "Khách không đến" } as const;

export default function RefundPanel({ res, policy, onDone }: { res: AdminReservation; policy: DepositPolicyData | undefined; onDone: () => void }) {
  const can = useCan();
  const push = useToast((s) => s.push);
  const bucket = refundBucket(res);
  const suggested = policy?.rules.find((r) => r.bucket === bucket)?.refundPercentage ?? 0;
  const [percent, setPercent] = useState(String(suggested));
  const [reference, setReference] = useState("");
  const [note, setNote] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  if (res.refund) {
    const r = res.refund;
    return (
      <div className="rounded-2xl border border-black/10 bg-white p-4 text-sm space-y-1.5">
        <div className="flex items-center justify-between"><b>Hoàn cọc</b><StatusBadge tone={r.percent > 0 ? "info" : "neutral"}>{r.percent > 0 ? "Đã chuyển khoản" : "Không hoàn"}</StatusBadge></div>
        <div>{r.percent}% · {formatCurrency(r.amount)}</div>
        {r.reference && <div className="text-muted">Mã chuyển khoản: {r.reference}</div>}
        {r.note && <div className="text-muted">Ghi chú: {r.note}</div>}
        <div className="text-xs text-muted">{fmtDateTime(r.at)} · {r.by}</div>
        {r.percent > 0 && <p className="text-xs text-muted pt-1">Tiền về tài khoản khách theo thời gian xử lý của ngân hàng.</p>}
      </div>
    );
  }
  if (!needsRefund(res)) return null;

  const pct = Math.min(100, Math.max(0, Number(percent) || 0));
  const amount = Math.round((res.depositAmount * pct) / 100);

  const submit = async () => {
    setBusy(true);
    try {
      await recordRefund(res, { percent: pct, amount, reference: reference.trim(), note: note.trim() });
      push(pct > 0 ? "Đã ghi nhận hoàn cọc" : "Đã ghi nhận không hoàn cọc");
      setConfirming(false); onDone();
    } catch (e) {
      push(e instanceof Error ? e.message : "Không ghi nhận được", "err");
    } finally { setBusy(false); }
  };

  return (
    <div className="rounded-2xl border-[1.5px] border-secondary/60 bg-secondary/10 p-4 text-sm space-y-4">
      <div className="flex gap-2.5">
        <Info width={17} height={17} className="shrink-0 mt-0.5 text-[#8a4b1d]" />
        <div>
          <div className="font-semibold">Cọc chờ hoàn · {formatCurrency(res.depositAmount)}</div>
          <p className="text-muted mt-1 leading-relaxed">Hệ thống không tự hoàn tiền. Khách liên hệ lễ tân/CSKH{policy ? ` (${policy.hotline})` : ""}; nhân viên xác minh, chuyển khoản thủ công rồi ghi nhận tại đây. Khách sẽ chờ tiền về tài khoản.</p>
        </div>
      </div>
      <div className="text-[13px]">Mốc huỷ: <b>{BUCKET_LABEL[bucket]}</b> → theo chính sách hoàn <b>{suggested}%</b></div>
      {can("payments", "update") ? (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[13px] font-semibold text-muted block mb-1.5" htmlFor="rf-pct">Tỉ lệ hoàn (%)</label>
              <input id="rf-pct" type="number" min={0} max={100} value={percent} onChange={(e) => setPercent(e.target.value)} className={inputCls} />
            </div>
            <div>
              <div className="text-[13px] font-semibold text-muted mb-1.5">Số tiền hoàn</div>
              <div className="py-2.5 font-display text-xl text-primary">{formatCurrency(amount)}</div>
            </div>
          </div>
          <div>
            <label className="text-[13px] font-semibold text-muted block mb-1.5" htmlFor="rf-ref">Mã giao dịch chuyển khoản</label>
            <input id="rf-ref" value={reference} onChange={(e) => setReference(e.target.value)} className={inputCls} placeholder="Ví dụ: VCB-0910-2231" />
          </div>
          <div>
            <label className="text-[13px] font-semibold text-muted block mb-1.5" htmlFor="rf-note">Ghi chú xác minh</label>
            <input id="rf-note" value={note} onChange={(e) => setNote(e.target.value)} className={inputCls} placeholder="Đã gọi xác nhận với khách…" />
          </div>
          <button className="btn btn-primary w-full py-2.5! text-sm!" onClick={() => (pct > 0 && !reference.trim() ? push("Nhập mã giao dịch chuyển khoản", "err") : setConfirming(true))}>
            {pct > 0 ? "Ghi nhận đã chuyển khoản hoàn cọc" : "Ghi nhận không hoàn cọc"}
          </button>
        </>
      ) : <p className="text-muted">Bạn chưa có quyền ghi nhận hoàn cọc.</p>}
      <ConfirmModal
        open={confirming} busy={busy} confirmLabel="Ghi nhận" title="Xác nhận ghi nhận?"
        message={pct > 0 ? `Bạn xác nhận đã chuyển khoản hoàn ${formatCurrency(amount)} cho khách. Thao tác này không thể hoàn tác.` : "Khách sẽ không được hoàn cọc theo chính sách. Thao tác này không thể hoàn tác."}
        onConfirm={submit} onCancel={() => setConfirming(false)}
      />
    </div>
  );
}
